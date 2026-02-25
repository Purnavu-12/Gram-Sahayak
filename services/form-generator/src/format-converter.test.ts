/**
 * Unit tests for FormatConverter
 */

import { FormatConverter } from './format-converter';

describe('FormatConverter', () => {
  let converter: FormatConverter;

  beforeEach(() => {
    converter = new FormatConverter();
  });

  describe('Date Conversion', () => {
    test('should convert DD-MM-YYYY format', () => {
      const result = converter.convertDate('15-08-1990');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    });

    test('should convert DD/MM/YYYY format', () => {
      const result = converter.convertDate('15/08/1990');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    });

    test('should convert date with month name', () => {
      const result = converter.convertDate('15 August 1990');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should convert date with abbreviated month', () => {
      const result = converter.convertDate('15 Aug 1990');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should convert Month DD, YYYY format', () => {
      const result = converter.convertDate('August 15, 1990');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should handle YYYY-MM-DD format', () => {
      const result = converter.convertDate('1990-08-15');
      expect(result.value).toBe('1990-08-15');
      expect(result.confidence).toBe(1.0);
    });

    test('should reject invalid dates', () => {
      const result = converter.convertDate('32-13-1990');
      expect(result.confidence).toBe(0);
    });

    test('should handle leap year dates', () => {
      const result = converter.convertDate('29-02-2020');
      expect(result.value).toBe('2020-02-29');
      expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    });

    test('should reject invalid leap year dates', () => {
      const result = converter.convertDate('29-02-2021');
      expect(result.confidence).toBe(0);
    });
  });

  describe('Phone Number Conversion', () => {
    test('should convert valid 10-digit mobile number', () => {
      const result = converter.convertPhoneNumber('9876543210');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle phone number with spaces', () => {
      const result = converter.convertPhoneNumber('98765 43210');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle phone number with dashes', () => {
      const result = converter.convertPhoneNumber('98765-43210');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBe(1.0);
    });

    test('should remove country code +91', () => {
      const result = converter.convertPhoneNumber('+919876543210');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    });

    test('should remove leading zero', () => {
      const result = converter.convertPhoneNumber('09876543210');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should reject invalid phone numbers', () => {
      const result = converter.convertPhoneNumber('1234567890');
      expect(result.confidence).toBe(0);
    });

    test('should handle all valid starting digits', () => {
      for (const digit of ['6', '7', '8', '9']) {
        const result = converter.convertPhoneNumber(`${digit}876543210`);
        expect(result.confidence).toBe(1.0);
      }
    });
  });

  describe('Number Conversion', () => {
    test('should convert simple numbers', () => {
      const result = converter.convertNumber('100');
      expect(result.value).toBe(100);
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should convert decimal numbers', () => {
      const result = converter.convertNumber('2.5');
      expect(result.value).toBe(2.5);
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should handle Indian number format with commas', () => {
      const result = converter.convertNumber('1,00,000');
      expect(result.value).toBe(100000);
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should convert "one lakh"', () => {
      const result = converter.convertNumber('one lakh');
      expect(result.value).toBe(100000);
      expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    });

    test('should convert "two crore"', () => {
      const result = converter.convertNumber('two crore');
      expect(result.value).toBe(20000000);
      expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    });

    test('should convert "2.5 lakh"', () => {
      const result = converter.convertNumber('2.5 lakh');
      expect(result.value).toBe(250000);
      expect(result.confidence).toBeGreaterThanOrEqual(0.8);
    });

    test('should handle "point" notation', () => {
      const result = converter.convertNumber('2 point 5');
      expect(result.value).toBe(2.5);
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });

    test('should ignore filler words', () => {
      const result = converter.convertNumber('it is about 100');
      expect(result.value).toBe(100);
      expect(result.confidence).toBeGreaterThanOrEqual(0.85);
    });
  });

  describe('Aadhaar Number Conversion', () => {
    test('should convert valid 12-digit Aadhaar', () => {
      const result = converter.convertAadhaarNumber('123456789012');
      expect(result.value).toBe('123456789012');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle Aadhaar with spaces', () => {
      const result = converter.convertAadhaarNumber('1234 5678 9012');
      expect(result.value).toBe('123456789012');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle Aadhaar with dashes', () => {
      const result = converter.convertAadhaarNumber('1234-5678-9012');
      expect(result.value).toBe('123456789012');
      expect(result.confidence).toBe(1.0);
    });

    test('should reject invalid length', () => {
      const result = converter.convertAadhaarNumber('12345678901');
      expect(result.confidence).toBe(0);
    });
  });

  describe('PIN Code Conversion', () => {
    test('should convert valid 6-digit PIN', () => {
      const result = converter.convertPincode('110001');
      expect(result.value).toBe('110001');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle PIN with spaces', () => {
      const result = converter.convertPincode('11 00 01');
      expect(result.value).toBe('110001');
      expect(result.confidence).toBe(1.0);
    });

    test('should reject invalid length', () => {
      const result = converter.convertPincode('11001');
      expect(result.confidence).toBe(0);
    });
  });

  describe('IFSC Code Conversion', () => {
    test('should convert valid IFSC code', () => {
      const result = converter.convertIfscCode('SBIN0001234');
      expect(result.value).toBe('SBIN0001234');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle lowercase IFSC', () => {
      const result = converter.convertIfscCode('sbin0001234');
      expect(result.value).toBe('SBIN0001234');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle IFSC with spaces', () => {
      const result = converter.convertIfscCode('SBIN 0001234');
      expect(result.value).toBe('SBIN0001234');
      expect(result.confidence).toBe(1.0);
    });

    test('should reject invalid format', () => {
      const result = converter.convertIfscCode('SBIN1001234');
      expect(result.confidence).toBe(0);
    });

    test('should reject invalid length', () => {
      const result = converter.convertIfscCode('SBIN000123');
      expect(result.confidence).toBe(0);
    });
  });

  describe('Address Conversion', () => {
    test('should parse address with explicit markers', () => {
      const result = converter.convertAddress('House No. 123, Village Rampur, District Meerut, 250001');
      expect(result.value).toHaveProperty('village');
      expect(result.value).toHaveProperty('district');
      expect(result.value).toHaveProperty('pincode');
      expect(result.value.village).toBe('Rampur');
      expect(result.value.district).toBe('Meerut');
      expect(result.value.pincode).toBe('250001');
    });

    test('should parse comma-separated address', () => {
      const result = converter.convertAddress('123 Main Street, Rampur, Meerut');
      expect(result.value).toHaveProperty('street');
      expect(result.value).toHaveProperty('village');
      expect(result.value).toHaveProperty('district');
    });

    test('should extract PIN code from address', () => {
      const result = converter.convertAddress('My address is 123 Street, City 110001');
      expect(result.value.pincode).toBe('110001');
    });
  });

  describe('Validation and Error Correction', () => {
    test('should provide suggestions for invalid date', () => {
      const result = converter.convertDate('invalid date');
      const error = converter.validateAndCorrect('dateOfBirth', 'date', 'invalid date', result);
      
      expect(error).not.toBeNull();
      expect(error?.error).toContain('date');
      expect(error?.examples.length).toBeGreaterThan(0);
      expect(error?.suggestions.length).toBeGreaterThan(0);
    });

    test('should provide suggestions for invalid phone', () => {
      const result = converter.convertPhoneNumber('123');
      const error = converter.validateAndCorrect('mobileNumber', 'phone', '123', result);
      
      expect(error).not.toBeNull();
      expect(error?.error).toContain('phone');
      expect(error?.examples.length).toBeGreaterThan(0);
    });

    test('should return null for valid conversion', () => {
      const result = converter.convertDate('15-08-1990');
      const error = converter.validateAndCorrect('dateOfBirth', 'date', '15-08-1990', result);
      
      expect(error).toBeNull();
    });
  });

  describe('Format Templates', () => {
    test('should provide date format template', () => {
      const template = converter.getFormatTemplate('date');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
      expect(template.hints.length).toBeGreaterThan(0);
    });

    test('should provide phone format template', () => {
      const template = converter.getFormatTemplate('phone');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
    });

    test('should provide number format template', () => {
      const template = converter.getFormatTemplate('number');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
    });

    test('should provide Aadhaar format template', () => {
      const template = converter.getFormatTemplate('aadhaar');
      expect(template.description).toBeTruthy();
      expect(template.examples.length).toBeGreaterThan(0);
    });

    test('should provide default template for unknown type', () => {
      const template = converter.getFormatTemplate('unknown');
      expect(template.description).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    test('should handle empty input', () => {
      const result = converter.convertDate('');
      expect(result.confidence).toBe(0);
    });

    test('should handle whitespace-only input', () => {
      const result = converter.convertPhoneNumber('   ');
      expect(result.confidence).toBe(0);
    });

    test('should handle very long input', () => {
      const longInput = 'a'.repeat(1000);
      const result = converter.convertDate(longInput);
      expect(result.confidence).toBe(0);
    });

    test('should handle special characters in phone', () => {
      const result = converter.convertPhoneNumber('(98765) 43210');
      expect(result.value).toBe('9876543210');
      expect(result.confidence).toBe(1.0);
    });

    test('should handle mixed case in IFSC', () => {
      const result = converter.convertIfscCode('SbIn0001234');
      expect(result.value).toBe('SBIN0001234');
      expect(result.confidence).toBe(1.0);
    });
  });
});
