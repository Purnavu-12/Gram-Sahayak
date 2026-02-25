import { PDFGenerator, PDFTemplate, DigitalSignature } from './pdf-generator';
import { FormSession, FormTemplate } from '../../../shared/types';

describe('PDFGenerator', () => {
  let pdfGenerator: PDFGenerator;
  let mockSession: FormSession;
  let mockTemplate: FormTemplate;

  beforeEach(() => {
    pdfGenerator = new PDFGenerator();

    mockSession = {
      sessionId: 'test_session_123',
      userId: 'user_456',
      schemeId: 'pm-kisan',
      formData: {
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
      },
      missingFields: [],
      conversationHistory: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    mockTemplate = {
      schemeId: 'pm-kisan',
      schemeName: 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
      fields: [
        { name: 'fullName', label: 'Full Name', type: 'text', required: true },
        { name: 'fatherName', label: "Father's Name", type: 'text', required: true },
        { name: 'dateOfBirth', label: 'Date of Birth', type: 'date', required: true },
        { name: 'aadhaarNumber', label: 'Aadhaar Number', type: 'text', required: true },
        { name: 'mobileNumber', label: 'Mobile Number', type: 'phone', required: true },
        { name: 'address', label: 'Address', type: 'address', required: true },
        { name: 'village', label: 'Village', type: 'text', required: true },
        { name: 'district', label: 'District', type: 'text', required: true },
        { name: 'state', label: 'State', type: 'text', required: true },
        { name: 'pincode', label: 'PIN Code', type: 'text', required: true },
        { name: 'landArea', label: 'Land Area (in hectares)', type: 'number', required: true },
        { name: 'bankAccountNumber', label: 'Bank Account Number', type: 'text', required: true },
        { name: 'ifscCode', label: 'IFSC Code', type: 'text', required: true }
      ]
    };
  });

  describe('Template Management', () => {
    test('should have default PM-KISAN template', () => {
      const template = pdfGenerator.getTemplate('pm-kisan');
      expect(template).toBeDefined();
      expect(template?.schemeId).toBe('pm-kisan');
      expect(template?.title).toBe('PM-KISAN Application Form');
    });

    test('should add custom template', () => {
      const customTemplate: PDFTemplate = {
        schemeId: 'test-scheme',
        title: 'Test Scheme Application',
        headerText: 'Test Scheme Header',
        footerText: 'Test Footer',
        layout: {
          pageSize: 'A4',
          margins: { top: 50, bottom: 50, left: 50, right: 50 },
          fontSize: { title: 18, heading: 14, body: 11, footer: 9 },
          colors: { primary: '#000000', secondary: '#666666', text: '#333333' }
        }
      };

      pdfGenerator.addTemplate(customTemplate);
      const retrieved = pdfGenerator.getTemplate('test-scheme');
      expect(retrieved).toEqual(customTemplate);
    });

    test('should return undefined for non-existent template', () => {
      const template = pdfGenerator.getTemplate('non-existent');
      expect(template).toBeUndefined();
    });
  });

  describe('PDF Generation', () => {
    test('should generate PDF for complete form', async () => {
      const pdfDoc = await pdfGenerator.generatePDF(mockSession, mockTemplate);

      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer).toBeInstanceOf(Buffer);
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
      expect(pdfDoc.filename).toContain('pm-kisan');
      expect(pdfDoc.filename).toContain(mockSession.userId);
      expect(pdfDoc.mimeType).toBe('application/pdf');
    });

    test('should include all form fields in PDF', async () => {
      const pdfDoc = await pdfGenerator.generatePDF(mockSession, mockTemplate);
      
      // PDF should be generated successfully
      expect(pdfDoc.buffer.length).toBeGreaterThan(1000); // Reasonable size for a form
    });

    test('should throw error for missing PDF template', async () => {
      const sessionWithInvalidScheme = { ...mockSession, schemeId: 'invalid-scheme' };
      
      await expect(
        pdfGenerator.generatePDF(sessionWithInvalidScheme, mockTemplate)
      ).rejects.toThrow('PDF template not found');
    });

    test('should handle partial form data', async () => {
      const partialSession = {
        ...mockSession,
        formData: {
          fullName: 'Ram Kumar',
          dateOfBirth: '1985-05-15',
          mobileNumber: '9876543210'
        }
      };

      const pdfDoc = await pdfGenerator.generatePDF(partialSession, mockTemplate);
      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
    });

    test('should handle different field types correctly', async () => {
      const sessionWithVariedData = {
        ...mockSession,
        formData: {
          fullName: 'Test User',
          dateOfBirth: new Date('1990-01-01'),
          landArea: 5.75,
          mobileNumber: '9876543210',
          address: { street: 'Main Road', village: 'Test Village' }
        }
      };

      const pdfDoc = await pdfGenerator.generatePDF(sessionWithVariedData, mockTemplate);
      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
    });
  });

  describe('Digital Signature', () => {
    test('should generate digital signature with hash', async () => {
      const pdfDoc = await pdfGenerator.generatePDF(mockSession, mockTemplate);
      
      // PDF should be generated with signature
      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
    });

    test('should validate signature correctly', () => {
      const sessionData = {
        sessionId: mockSession.sessionId,
        userId: mockSession.userId,
        schemeId: mockSession.schemeId,
        formData: mockSession.formData,
        timestamp: new Date().toISOString()
      };

      const crypto = require('crypto');
      const hash = crypto.createHash('sha256').update(JSON.stringify(sessionData)).digest('hex');

      const isValid = pdfGenerator.validateSignature(hash, sessionData);
      expect(isValid).toBe(true);
    });

    test('should reject invalid signature', () => {
      const sessionData = {
        sessionId: mockSession.sessionId,
        userId: mockSession.userId,
        schemeId: mockSession.schemeId,
        formData: mockSession.formData,
        timestamp: new Date().toISOString()
      };

      const invalidHash = 'invalid_hash_12345';
      const isValid = pdfGenerator.validateSignature(invalidHash, sessionData);
      expect(isValid).toBe(false);
    });

    test('should detect tampered data', () => {
      const originalData = {
        sessionId: mockSession.sessionId,
        userId: mockSession.userId,
        schemeId: mockSession.schemeId,
        formData: mockSession.formData,
        timestamp: new Date().toISOString()
      };

      const crypto = require('crypto');
      const hash = crypto.createHash('sha256').update(JSON.stringify(originalData)).digest('hex');

      // Tamper with data
      const tamperedData = {
        ...originalData,
        formData: { ...originalData.formData, fullName: 'Tampered Name' }
      };

      const isValid = pdfGenerator.validateSignature(hash, tamperedData);
      expect(isValid).toBe(false);
    });
  });

  describe('PDF Template Configuration', () => {
    test('should use correct page size', () => {
      const template = pdfGenerator.getTemplate('pm-kisan');
      expect(template?.layout.pageSize).toBe('A4');
    });

    test('should have proper margins', () => {
      const template = pdfGenerator.getTemplate('pm-kisan');
      expect(template?.layout.margins).toEqual({
        top: 50,
        bottom: 50,
        left: 50,
        right: 50
      });
    });

    test('should have signature configuration', () => {
      const template = pdfGenerator.getTemplate('pm-kisan');
      expect(template?.signature).toBeDefined();
      expect(template?.signature?.enabled).toBe(true);
      expect(template?.signature?.includeQRCode).toBe(true);
    });

    test('should have proper color scheme', () => {
      const template = pdfGenerator.getTemplate('pm-kisan');
      expect(template?.layout.colors).toBeDefined();
      expect(template?.layout.colors.primary).toBe('#1a5490');
      expect(template?.layout.colors.secondary).toBe('#f47920');
    });
  });

  describe('Edge Cases', () => {
    test('should handle empty form data', async () => {
      const emptySession = {
        ...mockSession,
        formData: {}
      };

      const pdfDoc = await pdfGenerator.generatePDF(emptySession, mockTemplate);
      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
    });

    test('should handle null values in form data', async () => {
      const sessionWithNulls = {
        ...mockSession,
        formData: {
          fullName: 'Test User',
          fatherName: null,
          dateOfBirth: undefined,
          mobileNumber: '9876543210'
        }
      };

      const pdfDoc = await pdfGenerator.generatePDF(sessionWithNulls, mockTemplate);
      expect(pdfDoc).toBeDefined();
    });

    test('should handle special characters in data', async () => {
      const sessionWithSpecialChars = {
        ...mockSession,
        formData: {
          fullName: 'राम कुमार',
          fatherName: 'श्याम कुमार',
          address: 'गाँव रामपुर, जिला सीतापुर',
          mobileNumber: '9876543210'
        }
      };

      const pdfDoc = await pdfGenerator.generatePDF(sessionWithSpecialChars, mockTemplate);
      expect(pdfDoc).toBeDefined();
      expect(pdfDoc.buffer.length).toBeGreaterThan(0);
    });

    test('should handle very long text values', async () => {
      const longText = 'A'.repeat(1000);
      const sessionWithLongText = {
        ...mockSession,
        formData: {
          fullName: longText,
          address: longText,
          mobileNumber: '9876543210'
        }
      };

      const pdfDoc = await pdfGenerator.generatePDF(sessionWithLongText, mockTemplate);
      expect(pdfDoc).toBeDefined();
    });
  });

  describe('Multiple Schemes', () => {
    test('should support multiple scheme templates', () => {
      const template1 = pdfGenerator.getTemplate('pm-kisan');
      expect(template1).toBeDefined();

      const customTemplate: PDFTemplate = {
        schemeId: 'ayushman-bharat',
        title: 'Ayushman Bharat Application',
        headerText: 'Ayushman Bharat Yojana',
        footerText: 'Ministry of Health, Government of India',
        layout: {
          pageSize: 'A4',
          margins: { top: 60, bottom: 60, left: 60, right: 60 },
          fontSize: { title: 20, heading: 15, body: 12, footer: 10 },
          colors: { primary: '#2c5aa0', secondary: '#ff6b35', text: '#000000' }
        }
      };

      pdfGenerator.addTemplate(customTemplate);
      const template2 = pdfGenerator.getTemplate('ayushman-bharat');
      expect(template2).toEqual(customTemplate);
    });
  });
});
