/**
 * Integration tests for FormGeneratorService with format conversion
 */

import { FormGeneratorService } from './form-generator-service';

describe('FormGeneratorService with Format Conversion', () => {
  let service: FormGeneratorService;

  beforeEach(() => {
    service = new FormGeneratorService();
  });

  afterEach(async () => {
    // Only disconnect if connected
    try {
      await service.disconnect();
    } catch (error) {
      // Ignore disconnect errors in tests
    }
  });

  describe('Format Template API', () => {
    test('should provide format template for date', () => {
      const template = service.getFormatTemplate('date');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
      expect(template.hints.length).toBeGreaterThan(0);
    });

    test('should provide format template for phone', () => {
      const template = service.getFormatTemplate('phone');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
    });

    test('should provide format template for number', () => {
      const template = service.getFormatTemplate('number');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
    });
  });

  describe('Format Conversion API', () => {
    test('should convert date through API', () => {
      const result = service.convertToFormat('15-08-1990', 'date');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    });

    test('should convert phone through API', () => {
      const result = service.convertToFormat('9876543210', 'phone');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBe(1.0);
    });

    test('should convert number through API', () => {
      const result = service.convertToFormat('one lakh', 'number');
      expect(result.value).toBe(100000);
      expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    });

    test('should convert Aadhaar through API', () => {
      const result = service.convertToFormat('1234 5678 9012', 'text', 'aadhaarNumber');
      expect(result.value).toBe('123456789012');
      expect(result.confidence).toBe(1.0);
    });

    test('should convert IFSC through API', () => {
      const result = service.convertToFormat('sbin0001234', 'text', 'ifscCode');
      expect(result.value).toBe('SBIN0001234');
      expect(result.confidence).toBe(1.0);
    });

    test('should convert PIN code through API', () => {
      const result = service.convertToFormat('110001', 'text', 'pincode');
      expect(result.value).toBe('110001');
      expect(result.confidence).toBe(1.0);
    });

    test('should convert address through API', () => {
      const result = service.convertToFormat('House No. 123, Village Rampur, District Meerut', 'address');
      expect(result.value).toHaveProperty('village');
      expect(result.value).toHaveProperty('district');
      expect(result.confidence).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid date gracefully', () => {
      const result = service.convertToFormat('invalid date', 'date');
      expect(result.confidence).toBe(0);
      expect(result.originalInput).toBe('invalid date');
    });

    test('should handle invalid phone gracefully', () => {
      const result = service.convertToFormat('123', 'phone');
      expect(result.confidence).toBe(0);
    });

    test('should handle empty input gracefully', () => {
      const result = service.convertToFormat('', 'date');
      expect(result.confidence).toBe(0);
    });

    test('should handle invalid Aadhaar gracefully', () => {
      const result = service.convertToFormat('123', 'text', 'aadhaarNumber');
      expect(result.confidence).toBe(0);
    });

    test('should handle invalid IFSC gracefully', () => {
      const result = service.convertToFormat('invalid', 'text', 'ifscCode');
      expect(result.confidence).toBe(0);
    });
  });

  describe('Multiple Format Conversions', () => {
    test('should handle date in multiple formats', () => {
      const formats = [
        '15-08-1990',
        '15/08/1990',
        '15 August 1990',
        'August 15, 1990',
        '1990-08-15'
      ];

      formats.forEach(format => {
        const result = service.convertToFormat(format, 'date');
        expect(result.value).toBe('1990-08-15');
        expect(result.confidence).toBeGreaterThan(0.8);
      });
    });

    test('should handle phone numbers with various formats', () => {
      const formats = [
        '9876543210',
        '98765 43210',
        '98765-43210',
        '+919876543210',
        '09876543210'
      ];

      formats.forEach(format => {
        const result = service.convertToFormat(format, 'phone');
        expect(result.value).toBe('9876543210');
        expect(result.confidence).toBeGreaterThan(0.8);
      });
    });

    test('should handle numbers in various formats', () => {
      const testCases = [
        { input: '100', expected: 100 },
        { input: '2.5', expected: 2.5 },
        { input: '1,00,000', expected: 100000 },
        { input: 'one lakh', expected: 100000 },
        { input: 'two crore', expected: 20000000 }
      ];

      testCases.forEach(({ input, expected }) => {
        const result = service.convertToFormat(input, 'number');
        expect(result.value).toBe(expected);
        expect(result.confidence).toBeGreaterThan(0.8);
      });
    });
  });
});
