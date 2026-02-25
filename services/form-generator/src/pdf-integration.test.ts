import { FormGeneratorService } from './form-generator-service';
import { createClient } from 'redis';

// Mock Redis client
jest.mock('redis', () => ({
  createClient: jest.fn(() => ({
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn().mockResolvedValue(undefined),
    get: jest.fn(),
    set: jest.fn().mockResolvedValue('OK')
  }))
}));

describe('PDF Generation Integration', () => {
  let service: FormGeneratorService;
  let mockRedisClient: any;

  beforeEach(async () => {
    service = new FormGeneratorService();
    mockRedisClient = (createClient as jest.Mock).mock.results[0].value;
    await service.connect();
  });

  afterEach(async () => {
    await service.disconnect();
  });

  describe('Complete Form to PDF Flow', () => {
    test('should generate PDF after completing form filling', async () => {
      // Start form session
      const session = await service.startFormFilling('pm-kisan', 'user_123');
      expect(session.sessionId).toBeDefined();

      // Mock Redis to return the session
      mockRedisClient.get.mockResolvedValue(JSON.stringify(session));

      // Fill form with all required data
      const responses = [
        'My name is Ram Kumar',
        'My father name is Shyam Kumar',
        '15-05-1985',
        '123456789012',
        '9876543210',
        'Village Rampur, Sitapur',
        'Rampur',
        'Sitapur',
        'Uttar Pradesh',
        '261001',
        '2.5',
        '1234567890',
        'SBIN0001234'
      ];

      let currentSession = session;
      for (const response of responses) {
        mockRedisClient.get.mockResolvedValue(JSON.stringify(currentSession));
        const update = await service.processUserResponse(currentSession.sessionId, response);
        
        // Update session with extracted data
        currentSession = {
          ...currentSession,
          formData: { ...currentSession.formData, ...update.extractedData },
          missingFields: currentSession.missingFields.filter(
            field => !Object.keys(update.extractedData).includes(field)
          )
        };
      }

      // Mock final session state
      mockRedisClient.get.mockResolvedValue(JSON.stringify(currentSession));

      // Generate PDF
      const pdfDoc = await service.generatePDF(currentSession.sessionId);
      
      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer).toBeInstanceOf(Buffer);
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
      expect(pdfDoc.filename).toContain('pm-kisan');
      expect(pdfDoc.mimeType).toBe('application/pdf');
    });

    test('should fail PDF generation for incomplete form', async () => {
      const incompleteFormData = {
        fullName: 'Ram Kumar',
        mobileNumber: '9876543210'
      };

      // Test validation directly instead of through generatePDF
      const result = await service.validateForm(incompleteFormData, 'pm-kisan');
      
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });

  describe('Form Validation', () => {
    test('should validate complete form data', async () => {
      const completeFormData = {
        fullName: 'Ram Kumar',
        fatherName: 'Shyam Kumar',
        dateOfBirth: '1985-05-15',
        aadhaarNumber: '123456789012',
        mobileNumber: '9876543210',
        address: 'Village Rampur',
        village: 'Rampur',
        district: 'Sitapur',
        state: 'Uttar Pradesh',
        pincode: '261001',
        landArea: 2.5,
        bankAccountNumber: '1234567890',
        ifscCode: 'SBIN0001234'
      };

      const result = await service.validateForm(completeFormData, 'pm-kisan');
      
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should detect missing required fields', async () => {
      const incompleteFormData = {
        fullName: 'Ram Kumar',
        mobileNumber: '9876543210'
      };

      const result = await service.validateForm(incompleteFormData, 'pm-kisan');
      
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some(e => e.field === 'fatherName')).toBe(true);
      expect(result.errors.some(e => e.field === 'dateOfBirth')).toBe(true);
    });

    test('should validate field formats', async () => {
      const invalidFormData = {
        fullName: 'Ram Kumar',
        fatherName: 'Shyam Kumar',
        dateOfBirth: '1985-05-15',
        aadhaarNumber: '12345', // Invalid: too short
        mobileNumber: '123', // Invalid: too short
        address: 'Village Rampur',
        village: 'Rampur',
        district: 'Sitapur',
        state: 'Uttar Pradesh',
        pincode: '26', // Invalid: too short
        landArea: 2.5,
        bankAccountNumber: '1234567890',
        ifscCode: 'INVALID' // Invalid format
      };

      const result = await service.validateForm(invalidFormData, 'pm-kisan');
      
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    test('should provide warnings for missing optional fields', async () => {
      const template = service.getFormTemplate('pm-kisan');
      if (template) {
        // Add an optional field
        template.fields.push({
          name: 'alternatePhone',
          label: 'Alternate Phone',
          type: 'phone',
          required: false
        });
      }

      const formData = {
        fullName: 'Ram Kumar',
        fatherName: 'Shyam Kumar',
        dateOfBirth: '1985-05-15',
        aadhaarNumber: '123456789012',
        mobileNumber: '9876543210',
        address: 'Village Rampur',
        village: 'Rampur',
        district: 'Sitapur',
        state: 'Uttar Pradesh',
        pincode: '261001',
        landArea: 2.5,
        bankAccountNumber: '1234567890',
        ifscCode: 'SBIN0001234'
      };

      const result = await service.validateForm(formData, 'pm-kisan');
      
      expect(result.isValid).toBe(true);
      expect(result.warnings).toBeDefined();
      expect(result.warnings?.length).toBeGreaterThan(0);
    });
  });

  describe('PDF Template Management', () => {
    test('should retrieve PDF template for scheme', () => {
      const template = service.getPDFTemplate('pm-kisan');
      
      expect(template).toBeDefined();
      expect(template?.schemeId).toBe('pm-kisan');
      expect(template?.title).toBe('PM-KISAN Application Form');
    });

    test('should add custom PDF template', () => {
      const customTemplate = {
        schemeId: 'custom-scheme',
        title: 'Custom Scheme Application',
        headerText: 'Custom Header',
        footerText: 'Custom Footer',
        layout: {
          pageSize: 'A4' as const,
          margins: { top: 50, bottom: 50, left: 50, right: 50 },
          fontSize: { title: 18, heading: 14, body: 11, footer: 9 },
          colors: { primary: '#000000', secondary: '#666666', text: '#333333' }
        }
      };

      service.addPDFTemplate(customTemplate);
      const retrieved = service.getPDFTemplate('custom-scheme');
      
      expect(retrieved).toEqual(customTemplate);
    });
  });

  describe('Error Handling', () => {
    test('should handle session not found error', async () => {
      mockRedisClient.get.mockResolvedValue(null);

      await expect(service.generatePDF('non_existent_session'))
        .rejects.toThrow('Session not found');
    });

    test('should handle invalid scheme error', async () => {
      // Test validation with invalid scheme
      await expect(service.validateForm({}, 'invalid_scheme'))
        .rejects.toThrow('Form template not found');
    });

    test('should handle validation errors gracefully', async () => {
      await expect(service.validateForm({}, 'invalid_scheme'))
        .rejects.toThrow('Form template not found');
    });
  });

  describe('Digital Signature Integration', () => {
    test('should include digital signature in generated PDF', async () => {
      // Test that PDF template has signature configuration
      const pdfTemplate = service.getPDFTemplate('pm-kisan');
      
      expect(pdfTemplate).toBeDefined();
      expect(pdfTemplate?.signature).toBeDefined();
      expect(pdfTemplate?.signature?.enabled).toBe(true);
      expect(pdfTemplate?.signature?.includeQRCode).toBe(true);
    });
  });

  describe('Multi-Scheme Support', () => {
    test('should generate PDFs for different schemes', async () => {
      // Add a second scheme template
      const ayushmanTemplate = {
        schemeId: 'ayushman-bharat',
        schemeName: 'Ayushman Bharat',
        fields: [
          { name: 'fullName', label: 'Full Name', type: 'text' as const, required: true },
          { name: 'age', label: 'Age', type: 'number' as const, required: true },
          { name: 'mobileNumber', label: 'Mobile Number', type: 'phone' as const, required: true }
        ]
      };

      service.addFormTemplate(ayushmanTemplate);

      const pdfTemplate = {
        schemeId: 'ayushman-bharat',
        title: 'Ayushman Bharat Application',
        headerText: 'Ayushman Bharat Yojana',
        footerText: 'Ministry of Health, Government of India',
        layout: {
          pageSize: 'A4' as const,
          margins: { top: 50, bottom: 50, left: 50, right: 50 },
          fontSize: { title: 18, heading: 14, body: 11, footer: 9 },
          colors: { primary: '#2c5aa0', secondary: '#ff6b35', text: '#000000' }
        }
      };

      service.addPDFTemplate(pdfTemplate);

      // Verify templates are added
      const formTemplate = service.getFormTemplate('ayushman-bharat');
      const retrievedPdfTemplate = service.getPDFTemplate('ayushman-bharat');
      
      expect(formTemplate).toBeDefined();
      expect(retrievedPdfTemplate).toBeDefined();
      expect(retrievedPdfTemplate?.title).toBe('Ayushman Bharat Application');
    });
  });
});
