import { createClient, RedisClientType } from 'redis';
import {
  FormSession,
  FormUpdate,
  FormTemplate,
  FormField,
  ValidationError,
  ConversationMessage,
  PDFDocument,
  ValidationResult
} from '../../../shared/types';
import { QuestionGenerator } from './question-generator';
import { FormatConverter, ConversionResult } from './format-converter';
import { PDFGenerator } from './pdf-generator';

export class FormGeneratorService {
  private redisClient: RedisClientType;
  private formTemplates: Map<string, FormTemplate>;
  private questionGenerator: QuestionGenerator;
  private formatConverter: FormatConverter;
  private pdfGenerator: PDFGenerator;

  constructor() {
    this.redisClient = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379'
    });
    this.formTemplates = new Map();
    this.questionGenerator = new QuestionGenerator();
    this.formatConverter = new FormatConverter();
    this.pdfGenerator = new PDFGenerator();
    this.initializeTemplates();
  }

  async connect(): Promise<void> {
    await this.redisClient.connect();
  }

  async disconnect(): Promise<void> {
    await this.redisClient.disconnect();
  }

  private initializeTemplates(): void {
    // Sample template for PM-KISAN scheme
    this.formTemplates.set('pm-kisan', {
      schemeId: 'pm-kisan',
      schemeName: 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
      fields: [
        { name: 'fullName', label: 'Full Name', type: 'text', required: true },
        { name: 'fatherName', label: "Father's Name", type: 'text', required: true },
        { name: 'dateOfBirth', label: 'Date of Birth', type: 'date', required: true },
        { name: 'aadhaarNumber', label: 'Aadhaar Number', type: 'text', required: true, 
          validation: { pattern: '^[0-9]{12}$', minLength: 12, maxLength: 12 } },
        { name: 'mobileNumber', label: 'Mobile Number', type: 'phone', required: true,
          validation: { pattern: '^[6-9][0-9]{9}$', minLength: 10, maxLength: 10 } },
        { name: 'address', label: 'Address', type: 'address', required: true },
        { name: 'village', label: 'Village', type: 'text', required: true },
        { name: 'district', label: 'District', type: 'text', required: true },
        { name: 'state', label: 'State', type: 'text', required: true },
        { name: 'pincode', label: 'PIN Code', type: 'text', required: true,
          validation: { pattern: '^[0-9]{6}$', minLength: 6, maxLength: 6 } },
        { name: 'landArea', label: 'Land Area (in hectares)', type: 'number', required: true,
          validation: { min: 0 } },
        { name: 'bankAccountNumber', label: 'Bank Account Number', type: 'text', required: true },
        { name: 'ifscCode', label: 'IFSC Code', type: 'text', required: true,
          validation: { pattern: '^[A-Z]{4}0[A-Z0-9]{6}$', minLength: 11, maxLength: 11 } }
      ],
      instructions: 'Please provide accurate information for PM-KISAN scheme application'
    });
  }

  async startFormFilling(schemeId: string, userId: string): Promise<FormSession> {
    const template = this.formTemplates.get(schemeId);
    if (!template) {
      throw new Error(`Form template not found for scheme: ${schemeId}`);
    }

    const sessionId = `form_${userId}_${schemeId}_${Date.now()}`;
    const session: FormSession = {
      sessionId,
      userId,
      schemeId,
      formData: {},
      missingFields: template.fields.filter(f => f.required).map(f => f.name),
      conversationHistory: [{
        role: 'system',
        content: `Starting form filling for ${template.schemeName}`,
        timestamp: new Date()
      }],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Use intelligent missing information detection to prioritize fields
    session.missingFields = this.questionGenerator.detectMissingInformation(session, template);

    // Generate initial context-aware question
    if (session.missingFields.length > 0) {
      const initialQuestion = this.questionGenerator.generateContextAwareQuestion(
        session.missingFields[0],
        session,
        template
      );
      session.conversationHistory.push({
        role: 'assistant',
        content: initialQuestion,
        timestamp: new Date()
      });
    }

    await this.saveSession(session);
    return session;
  }

  async processUserResponse(sessionId: string, response: string): Promise<FormUpdate> {
    const session = await this.loadSession(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    const template = this.formTemplates.get(session.schemeId);
    if (!template) {
      throw new Error(`Form template not found for scheme: ${session.schemeId}`);
    }

    // Add user message to conversation history
    session.conversationHistory.push({
      role: 'user',
      content: response,
      timestamp: new Date()
    });

    // Extract data from natural language response
    const extractedData = this.extractDataFromResponse(response, session.missingFields, template);
    
    // Update form data
    Object.assign(session.formData, extractedData);

    // Validate extracted data
    const validationErrors = this.validateExtractedData(extractedData, template);

    // Use intelligent missing information detection
    session.missingFields = this.questionGenerator.detectMissingInformation(session, template);

    // Generate next question using context-aware generation
    let nextQuestion: string | undefined;
    if (session.missingFields.length > 0 && validationErrors.length === 0) {
      nextQuestion = this.questionGenerator.generateContextAwareQuestion(
        session.missingFields[0],
        session,
        template
      );
      if (nextQuestion) {
        session.conversationHistory.push({
          role: 'assistant',
          content: nextQuestion,
          timestamp: new Date()
        });
      }
    }

    session.updatedAt = new Date();
    await this.saveSession(session);

    return {
      sessionId,
      extractedData,
      nextQuestion,
      isComplete: session.missingFields.length === 0 && validationErrors.length === 0,
      validationErrors: validationErrors.length > 0 ? validationErrors : undefined
    };
  }

  private extractDataFromResponse(
    response: string,
    missingFields: string[],
    template: FormTemplate
  ): Record<string, any> {
    const extracted: Record<string, any> = {};
    const lowerResponse = response.toLowerCase();

    // Use format converter for intelligent extraction
    for (const fieldName of missingFields) {
      const field = template.fields.find(f => f.name === fieldName);
      if (!field) continue;

      let conversionResult: ConversionResult | null = null;

      switch (field.type) {
        case 'date':
          conversionResult = this.formatConverter.convertDate(response);
          if (conversionResult.confidence >= 0.7) {
            extracted[fieldName] = conversionResult.value;
          }
          break;

        case 'phone':
          conversionResult = this.formatConverter.convertPhoneNumber(response);
          if (conversionResult.confidence >= 0.7) {
            extracted[fieldName] = conversionResult.value;
          }
          break;

        case 'number':
          conversionResult = this.formatConverter.convertNumber(response, fieldName);
          if (conversionResult.confidence >= 0.7) {
            extracted[fieldName] = conversionResult.value;
          }
          break;

        case 'address':
          conversionResult = this.formatConverter.convertAddress(response);
          if (conversionResult.confidence >= 0.5) { // Lower threshold for addresses
            extracted[fieldName] = conversionResult.value;
          }
          break;

        case 'text':
          // Special handling for specific text fields
          if (fieldName === 'aadhaarNumber') {
            conversionResult = this.formatConverter.convertAadhaarNumber(response);
            if (conversionResult.confidence >= 0.7) {
              extracted[fieldName] = conversionResult.value;
            }
          } else if (fieldName === 'pincode') {
            conversionResult = this.formatConverter.convertPincode(response);
            if (conversionResult.confidence >= 0.7) {
              extracted[fieldName] = conversionResult.value;
            }
          } else if (fieldName === 'ifscCode') {
            conversionResult = this.formatConverter.convertIfscCode(response);
            if (conversionResult.confidence >= 0.7) {
              extracted[fieldName] = conversionResult.value;
            }
          } else {
            // Generic text extraction
            if (fieldName === 'fullName' && (lowerResponse.includes('name is') || lowerResponse.includes('naam hai'))) {
              const match = response.match(/(?:name is|naam hai)\s+([a-zA-Z\s]+)/i);
              if (match) extracted[fieldName] = match[1].trim();
            } else {
              // Extract the response as-is for generic text fields
              const cleanedResponse = response.trim();
              if (cleanedResponse.length > 0) {
                extracted[fieldName] = cleanedResponse;
              }
            }
          }
          break;

        default:
          // Fallback: extract as-is
          const cleanedResponse = response.trim();
          if (cleanedResponse.length > 0) {
            extracted[fieldName] = cleanedResponse;
          }
      }
    }

    return extracted;
  }

  private validateExtractedData(
    data: Record<string, any>,
    template: FormTemplate
  ): ValidationError[] {
    const errors: ValidationError[] = [];

    for (const [fieldName, value] of Object.entries(data)) {
      const field = template.fields.find(f => f.name === fieldName);
      if (!field || !field.validation) continue;

      const validation = field.validation;

      // Use format converter for validation and error correction
      let conversionResult: ConversionResult | null = null;
      const valueStr = String(value);

      switch (field.type) {
        case 'date':
          conversionResult = this.formatConverter.convertDate(valueStr);
          break;
        case 'phone':
          conversionResult = this.formatConverter.convertPhoneNumber(valueStr);
          break;
        case 'number':
          conversionResult = this.formatConverter.convertNumber(valueStr, fieldName);
          break;
        case 'text':
          if (fieldName === 'aadhaarNumber') {
            conversionResult = this.formatConverter.convertAadhaarNumber(valueStr);
          } else if (fieldName === 'pincode') {
            conversionResult = this.formatConverter.convertPincode(valueStr);
          } else if (fieldName === 'ifscCode') {
            conversionResult = this.formatConverter.convertIfscCode(valueStr);
          }
          break;
      }

      // Check conversion result and generate errors with suggestions
      if (conversionResult && conversionResult.confidence < 0.7) {
        const conversionError = this.formatConverter.validateAndCorrect(
          fieldName,
          field.type,
          valueStr,
          conversionResult
        );
        if (conversionError) {
          errors.push({
            field: fieldName,
            message: conversionError.error,
            suggestedFormat: conversionError.examples.join(', '),
            suggestions: conversionError.suggestions
          });
          continue;
        }
      }

      // Pattern validation
      if (validation.pattern && typeof value === 'string') {
        const regex = new RegExp(validation.pattern);
        if (!regex.test(value)) {
          const template = this.formatConverter.getFormatTemplate(field.type);
          errors.push({
            field: fieldName,
            message: `Invalid format for ${field.label}`,
            suggestedFormat: template.examples.join(', '),
            suggestions: template.hints
          });
        }
      }

      // Length validation
      if (typeof value === 'string') {
        if (validation.minLength && value.length < validation.minLength) {
          errors.push({
            field: fieldName,
            message: `${field.label} must be at least ${validation.minLength} characters`
          });
        }
        if (validation.maxLength && value.length > validation.maxLength) {
          errors.push({
            field: fieldName,
            message: `${field.label} must not exceed ${validation.maxLength} characters`
          });
        }
      }

      // Number range validation
      if (typeof value === 'number') {
        if (validation.min !== undefined && value < validation.min) {
          errors.push({
            field: fieldName,
            message: `${field.label} must be at least ${validation.min}`
          });
        }
        if (validation.max !== undefined && value > validation.max) {
          errors.push({
            field: fieldName,
            message: `${field.label} must not exceed ${validation.max}`
          });
        }
      }
    }

    return errors;
  }

  private getSuggestedFormat(field: FormField): string {
    switch (field.type) {
      case 'phone':
        return '10-digit mobile number starting with 6-9';
      case 'date':
        return 'DD-MM-YYYY or DD/MM/YYYY';
      default:
        if (field.validation?.pattern) {
          if (field.name === 'aadhaarNumber') return '12-digit Aadhaar number';
          if (field.name === 'pincode') return '6-digit PIN code';
          if (field.name === 'ifscCode') return '11-character IFSC code';
        }
        return `Valid ${field.label}`;
    }
  }

  private generateNextQuestion(fieldName: string, template: FormTemplate): string {
    const field = template.fields.find(f => f.name === fieldName);
    if (!field) return 'Please provide the next information.';

    const questions: Record<string, string> = {
      fullName: 'What is your full name?',
      fatherName: "What is your father's name?",
      dateOfBirth: 'What is your date of birth? Please provide in DD-MM-YYYY format.',
      aadhaarNumber: 'What is your 12-digit Aadhaar number?',
      mobileNumber: 'What is your mobile number?',
      address: 'What is your complete address?',
      village: 'Which village do you live in?',
      district: 'Which district do you live in?',
      state: 'Which state do you live in?',
      pincode: 'What is your area PIN code?',
      landArea: 'How much land do you own in hectares?',
      bankAccountNumber: 'What is your bank account number?',
      ifscCode: 'What is your bank IFSC code?'
    };

    return questions[fieldName] || `Please provide your ${field.label}.`;
  }

  private async saveSession(session: FormSession): Promise<void> {
    const key = `session:${session.sessionId}`;
    await this.redisClient.set(key, JSON.stringify(session), {
      EX: 3600 // 1 hour expiry
    });
  }

  private async loadSession(sessionId: string): Promise<FormSession | null> {
    const key = `session:${sessionId}`;
    const data = await this.redisClient.get(key);
    if (!data) return null;

    const session = JSON.parse(data);
    // Convert date strings back to Date objects
    session.createdAt = new Date(session.createdAt);
    session.updatedAt = new Date(session.updatedAt);
    session.conversationHistory = session.conversationHistory.map((msg: any) => ({
      ...msg,
      timestamp: new Date(msg.timestamp)
    }));

    return session;
  }

  getFormTemplate(schemeId: string): FormTemplate | undefined {
    return this.formTemplates.get(schemeId);
  }

  addFormTemplate(template: FormTemplate): void {
    this.formTemplates.set(template.schemeId, template);
  }

  /**
   * Get optimized conversation flow for a session
   * Useful for advanced UI that can handle multiple questions at once
   */
  getOptimizedConversationFlow(sessionId: string): Promise<{
    questions: string[];
    canGroupQuestions: boolean;
    suggestedGroupSize: number;
  }> {
    return this.loadSession(sessionId).then(session => {
      if (!session) {
        throw new Error(`Session not found: ${sessionId}`);
      }

      const template = this.formTemplates.get(session.schemeId);
      if (!template) {
        throw new Error(`Form template not found for scheme: ${session.schemeId}`);
      }

      return this.questionGenerator.optimizeConversationFlow(
        session.missingFields,
        session,
        template
      );
    });
  }

  /**
   * Get format template and examples for a specific field type
   */
  getFormatTemplate(fieldType: string): { description: string; examples: string[]; hints: string[] } {
    return this.formatConverter.getFormatTemplate(fieldType);
  }

  /**
   * Convert natural language input to specific format
   */
  convertToFormat(input: string, fieldType: string, fieldName?: string): ConversionResult {
    switch (fieldType) {
      case 'date':
        return this.formatConverter.convertDate(input);
      case 'phone':
        return this.formatConverter.convertPhoneNumber(input);
      case 'number':
        return this.formatConverter.convertNumber(input, fieldName);
      case 'address':
        return this.formatConverter.convertAddress(input);
      default:
        if (fieldName === 'aadhaarNumber') {
          return this.formatConverter.convertAadhaarNumber(input);
        } else if (fieldName === 'pincode') {
          return this.formatConverter.convertPincode(input);
        } else if (fieldName === 'ifscCode') {
          return this.formatConverter.convertIfscCode(input);
        }
        return {
          value: input,
          confidence: 0.5,
          originalInput: input,
          format: fieldType
        };
    }
  }

  /**
   * Generate PDF document for a completed form
   */
  async generatePDF(sessionId: string): Promise<PDFDocument> {
    const session = await this.loadSession(sessionId);
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }

    const template = this.formTemplates.get(session.schemeId);
    if (!template) {
      throw new Error(`Form template not found for scheme: ${session.schemeId}`);
    }

    // Validate form is complete before generating PDF
    const validationResult = await this.validateForm(session.formData, session.schemeId);
    if (!validationResult.isValid) {
      throw new Error(`Form validation failed: ${validationResult.errors.map(e => e.message).join(', ')}`);
    }

    return this.pdfGenerator.generatePDF(session, template);
  }

  /**
   * Validate form data against template requirements
   */
  async validateForm(formData: Record<string, any>, schemeId: string): Promise<ValidationResult> {
    const template = this.formTemplates.get(schemeId);
    if (!template) {
      throw new Error(`Form template not found for scheme: ${schemeId}`);
    }

    const errors: ValidationError[] = [];
    const warnings: string[] = [];

    // Check all required fields are present
    for (const field of template.fields) {
      if (field.required && !formData[field.name]) {
        errors.push({
          field: field.name,
          message: `${field.label} is required`
        });
      }
    }

    // Validate field values
    const validationErrors = this.validateExtractedData(formData, template);
    errors.push(...validationErrors);

    // Add warnings for optional fields that are missing
    for (const field of template.fields) {
      if (!field.required && !formData[field.name]) {
        warnings.push(`Optional field ${field.label} is not provided`);
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings: warnings.length > 0 ? warnings : undefined
    };
  }

  /**
   * Get PDF template for a scheme
   */
  getPDFTemplate(schemeId: string) {
    return this.pdfGenerator.getTemplate(schemeId);
  }

  /**
   * Add custom PDF template for a scheme
   */
  addPDFTemplate(template: any): void {
    this.pdfGenerator.addTemplate(template);
  }
}
