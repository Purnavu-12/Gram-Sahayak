/**
 * Type definitions for Form Generator service
 */

export interface FormSession {
  sessionId: string;
  userId: string;
  schemeId: string;
  formData: Record<string, any>;
  missingFields: string[];
  conversationHistory: ConversationMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ConversationMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface FormUpdate {
  sessionId: string;
  extractedData: Record<string, any>;
  nextQuestion?: string;
  isComplete: boolean;
  validationErrors?: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
  suggestedFormat?: string;
  suggestions?: string[];
}

export interface PDFDocument {
  buffer: Buffer;
  filename: string;
  mimeType: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings?: string[];
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'address' | 'phone' | 'email' | 'select';
  required: boolean;
  validation?: FieldValidation;
  options?: string[];
}

export interface FieldValidation {
  pattern?: string;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
}

export interface FormTemplate {
  schemeId: string;
  schemeName: string;
  fields: FormField[];
  instructions?: string;
}
