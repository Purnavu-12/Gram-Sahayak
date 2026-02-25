/**
 * Data Format Converter
 * Converts natural language inputs to specific formats required by government forms
 */

export interface ConversionResult {
  value: any;
  confidence: number;
  originalInput: string;
  format: string;
}

export interface ConversionError {
  field: string;
  input: string;
  error: string;
  suggestions: string[];
  examples: string[];
}

export class FormatConverter {
  /**
   * Convert natural language date to standard format (YYYY-MM-DD)
   */
  convertDate(input: string): ConversionResult {
    const originalInput = input.trim();
    let confidence = 0;
    let value: string | null = null;

    // Try various date formats
    const formats = [
      // DD-MM-YYYY or DD/MM/YYYY
      { pattern: /(\d{1,2})[-/](\d{1,2})[-/](\d{4})/, handler: (m: RegExpMatchArray) => {
        const day = parseInt(m[1]);
        const month = parseInt(m[2]);
        const year = parseInt(m[3]);
        if (this.isValidDate(day, month, year)) {
          confidence = 0.95;
          return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        }
        return null;
      }},
      // DD Month YYYY (e.g., "15 August 1990")
      { pattern: /(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})/i,
        handler: (m: RegExpMatchArray) => {
          const day = parseInt(m[1]);
          const month = this.parseMonth(m[2]);
          const year = parseInt(m[3]);
          if (month && this.isValidDate(day, month, year)) {
            confidence = 0.9;
            return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          }
          return null;
        }
      },
      // Month DD, YYYY (e.g., "August 15, 1990")
      { pattern: /(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2}),?\s+(\d{4})/i,
        handler: (m: RegExpMatchArray) => {
          const month = this.parseMonth(m[1]);
          const day = parseInt(m[2]);
          const year = parseInt(m[3]);
          if (month && this.isValidDate(day, month, year)) {
            confidence = 0.9;
            return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          }
          return null;
        }
      },
      // YYYY-MM-DD (already standard)
      { pattern: /(\d{4})[-/](\d{1,2})[-/](\d{1,2})/, handler: (m: RegExpMatchArray) => {
        const year = parseInt(m[1]);
        const month = parseInt(m[2]);
        const day = parseInt(m[3]);
        if (this.isValidDate(day, month, year)) {
          confidence = 1.0;
          return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        }
        return null;
      }}
    ];

    for (const format of formats) {
      const match = originalInput.match(format.pattern);
      if (match) {
        value = format.handler(match);
        if (value) break;
      }
    }

    return {
      value: value || originalInput,
      confidence: value ? confidence : 0,
      originalInput,
      format: 'date'
    };
  }

  /**
   * Convert natural language number to numeric format
   */
  convertNumber(input: string, fieldContext?: string): ConversionResult {
    const originalInput = input.trim();
    let confidence = 0;
    let value: number | null = null;

    // Remove common words
    let cleaned = input.toLowerCase()
      .replace(/\b(is|are|about|approximately|around|roughly)\b/g, '')
      .trim();

    // Handle decimal numbers with words (e.g., "2.5 hectares", "3 point 5") - check first
    const decimalMatch = cleaned.match(/(\d+)\s*(?:point|decimal)\s*(\d+)/);
    if (decimalMatch) {
      value = parseFloat(`${decimalMatch[1]}.${decimalMatch[2]}`);
      confidence = 0.9;
    }

    // Handle written numbers (e.g., "one lakh", "two crore")
    if (value === null) {
      const indianNumbers = this.parseIndianNumber(cleaned);
      if (indianNumbers !== null) {
        value = indianNumbers;
        confidence = 0.85;
      }
    }

    // Try direct numeric extraction if no Indian number found
    if (value === null) {
      // Handle Indian number format (e.g., 1,00,000)
      const numMatch = cleaned.match(/(\d+(?:[.,]\d+)*)/);
      if (numMatch) {
        const numStr = numMatch[1].replace(/,/g, '');
        value = parseFloat(numStr);
        confidence = 0.95;
      }
    }

    return {
      value: value !== null ? value : originalInput,
      confidence: value !== null ? confidence : 0,
      originalInput,
      format: 'number'
    };
  }

  /**
   * Convert natural language address to structured format
   */
  convertAddress(input: string): ConversionResult {
    const originalInput = input.trim();
    
    // Parse address components
    const addressParts = this.parseAddressComponents(input);
    
    const confidence = addressParts.street || addressParts.village || addressParts.city ? 0.8 : 0.3;

    return {
      value: addressParts,
      confidence,
      originalInput,
      format: 'address'
    };
  }

  /**
   * Convert phone number to standard format
   */
  convertPhoneNumber(input: string): ConversionResult {
    const originalInput = input.trim();
    let confidence = 0;
    let value: string | null = null;

    // Remove all non-digit characters
    const digits = input.replace(/\D/g, '');

    // Indian mobile number: 10 digits starting with 6-9
    if (/^[6-9]\d{9}$/.test(digits)) {
      value = digits;
      confidence = 1.0;
    }
    // With country code +91
    else if (/^91[6-9]\d{9}$/.test(digits)) {
      value = digits.substring(2); // Remove country code
      confidence = 0.95;
    }
    // 11 digits starting with 0
    else if (/^0[6-9]\d{9}$/.test(digits)) {
      value = digits.substring(1); // Remove leading 0
      confidence = 0.9;
    }

    return {
      value: value || originalInput,
      confidence: value ? confidence : 0,
      originalInput,
      format: 'phone'
    };
  }

  /**
   * Convert Aadhaar number to standard format
   */
  convertAadhaarNumber(input: string): ConversionResult {
    const originalInput = input.trim();
    let confidence = 0;
    let value: string | null = null;

    // Remove all non-digit characters
    const digits = input.replace(/\D/g, '');

    // Aadhaar: exactly 12 digits
    if (/^\d{12}$/.test(digits)) {
      value = digits;
      confidence = 1.0;
    }

    return {
      value: value || originalInput,
      confidence: value ? confidence : 0,
      originalInput,
      format: 'aadhaar'
    };
  }

  /**
   * Convert PIN code to standard format
   */
  convertPincode(input: string): ConversionResult {
    const originalInput = input.trim();
    let confidence = 0;
    let value: string | null = null;

    // Remove all non-digit characters
    const digits = input.replace(/\D/g, '');

    // PIN code: exactly 6 digits
    if (/^\d{6}$/.test(digits)) {
      value = digits;
      confidence = 1.0;
    }

    return {
      value: value || originalInput,
      confidence: value ? confidence : 0,
      originalInput,
      format: 'pincode'
    };
  }

  /**
   * Convert IFSC code to standard format
   */
  convertIfscCode(input: string): ConversionResult {
    const originalInput = input.trim().toUpperCase();
    let confidence = 0;
    let value: string | null = null;

    // Remove spaces and convert to uppercase
    const cleaned = input.replace(/\s/g, '').toUpperCase();

    // IFSC: 11 characters (4 letters, 0, 6 alphanumeric)
    if (/^[A-Z]{4}0[A-Z0-9]{6}$/.test(cleaned)) {
      value = cleaned;
      confidence = 1.0;
    }

    return {
      value: value || originalInput,
      confidence: value ? confidence : 0,
      originalInput,
      format: 'ifsc'
    };
  }

  /**
   * Validate and suggest corrections for conversion errors
   */
  validateAndCorrect(
    fieldName: string,
    fieldType: string,
    input: string,
    conversionResult: ConversionResult
  ): ConversionError | null {
    if (conversionResult.confidence >= 0.7) {
      return null; // Conversion successful
    }

    const error: ConversionError = {
      field: fieldName,
      input,
      error: '',
      suggestions: [],
      examples: []
    };

    switch (fieldType) {
      case 'date':
        error.error = 'Unable to parse date. Please provide in a standard format.';
        error.examples = [
          '15-08-1990',
          '15/08/1990',
          '15 August 1990',
          'August 15, 1990'
        ];
        error.suggestions = this.suggestDateCorrections(input);
        break;

      case 'phone':
        error.error = 'Invalid phone number. Must be 10 digits starting with 6-9.';
        error.examples = ['9876543210', '8123456789'];
        error.suggestions = this.suggestPhoneCorrections(input);
        break;

      case 'number':
        error.error = 'Unable to parse number. Please provide a numeric value.';
        error.examples = ['100', '2.5', '1000'];
        error.suggestions = this.suggestNumberCorrections(input);
        break;

      case 'aadhaar':
        error.error = 'Invalid Aadhaar number. Must be exactly 12 digits.';
        error.examples = ['123456789012'];
        error.suggestions = this.suggestAadhaarCorrections(input);
        break;

      case 'pincode':
        error.error = 'Invalid PIN code. Must be exactly 6 digits.';
        error.examples = ['110001', '400001'];
        error.suggestions = this.suggestPincodeCorrections(input);
        break;

      case 'ifsc':
        error.error = 'Invalid IFSC code. Must be 11 characters (4 letters, 0, 6 alphanumeric).';
        error.examples = ['SBIN0001234', 'HDFC0000123'];
        error.suggestions = this.suggestIfscCorrections(input);
        break;

      case 'address':
        error.error = 'Unable to parse address. Please provide more details.';
        error.examples = ['House No. 123, Village Rampur, District Meerut'];
        error.suggestions = ['Include house number, village/city, and district'];
        break;

      default:
        error.error = 'Invalid format';
        error.examples = [];
        error.suggestions = [];
    }

    return error;
  }

  /**
   * Get format-specific templates and examples
   */
  getFormatTemplate(fieldType: string): { description: string; examples: string[]; hints: string[] } {
    const templates: Record<string, { description: string; examples: string[]; hints: string[] }> = {
      date: {
        description: 'Date in DD-MM-YYYY or DD/MM/YYYY format',
        examples: ['15-08-1990', '01/01/2000', '15 August 1990'],
        hints: ['You can say the date in any common format', 'Month names are also accepted']
      },
      phone: {
        description: '10-digit mobile number starting with 6, 7, 8, or 9',
        examples: ['9876543210', '8123456789'],
        hints: ['Do not include country code', 'Remove any spaces or dashes']
      },
      number: {
        description: 'Numeric value (can include decimals)',
        examples: ['100', '2.5', '1000', 'one lakh'],
        hints: ['You can use words like lakh, crore', 'Decimals are allowed']
      },
      aadhaar: {
        description: '12-digit Aadhaar number',
        examples: ['123456789012'],
        hints: ['Remove any spaces or dashes', 'Must be exactly 12 digits']
      },
      pincode: {
        description: '6-digit PIN code',
        examples: ['110001', '400001', '560001'],
        hints: ['Must be exactly 6 digits']
      },
      ifsc: {
        description: '11-character IFSC code',
        examples: ['SBIN0001234', 'HDFC0000123'],
        hints: ['First 4 letters are bank code', 'Fifth character is always 0']
      },
      address: {
        description: 'Complete address with house number, village/city, and district',
        examples: ['House No. 123, Village Rampur, District Meerut'],
        hints: ['Include as many details as possible', 'Mention landmarks if available']
      }
    };

    return templates[fieldType] || {
      description: 'Standard format',
      examples: [],
      hints: []
    };
  }

  // Helper methods

  private isValidDate(day: number, month: number, year: number): boolean {
    if (month < 1 || month > 12) return false;
    if (day < 1 || day > 31) return false;
    if (year < 1900 || year > new Date().getFullYear()) return false;

    // Check days in month
    const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    
    // Leap year check
    if (month === 2 && this.isLeapYear(year)) {
      return day <= 29;
    }

    return day <= daysInMonth[month - 1];
  }

  private isLeapYear(year: number): boolean {
    return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
  }

  private parseMonth(monthStr: string): number | null {
    const months: Record<string, number> = {
      january: 1, jan: 1,
      february: 2, feb: 2,
      march: 3, mar: 3,
      april: 4, apr: 4,
      may: 5,
      june: 6, jun: 6,
      july: 7, jul: 7,
      august: 8, aug: 8,
      september: 9, sep: 9,
      october: 10, oct: 10,
      november: 11, nov: 11,
      december: 12, dec: 12
    };

    return months[monthStr.toLowerCase()] || null;
  }

  private parseIndianNumber(input: string): number | null {
    const units: Record<string, number> = {
      lakh: 100000,
      lac: 100000,
      lakhs: 100000,
      crore: 10000000,
      crores: 10000000,
      thousand: 1000,
      thousands: 1000,
      hundred: 100,
      hundreds: 100
    };

    const words: Record<string, number> = {
      zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5,
      six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
      eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15,
      sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19, twenty: 20,
      thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70,
      eighty: 80, ninety: 90
    };

    let total = 0;
    let current = 0;
    let hasIndianUnit = false;

    const tokens = input.toLowerCase().split(/\s+/);

    for (const token of tokens) {
      if (words[token] !== undefined) {
        current += words[token];
      } else if (units[token] !== undefined) {
        hasIndianUnit = true;
        if (current === 0) current = 1;
        total += current * units[token];
        current = 0;
      } else {
        const num = parseFloat(token);
        if (!isNaN(num)) {
          current += num;
        }
      }
    }

    total += current;

    // Only return if we found Indian units (lakh, crore, etc.)
    return hasIndianUnit && total > 0 ? total : null;
  }

  private parseAddressComponents(input: string): {
    street?: string;
    village?: string;
    city?: string;
    district?: string;
    state?: string;
    pincode?: string;
  } {
    const components: any = {};

    // Extract PIN code
    const pincodeMatch = input.match(/\b(\d{6})\b/);
    if (pincodeMatch) {
      components.pincode = pincodeMatch[1];
    }

    // Extract district
    const districtMatch = input.match(/(?:district|dist\.?|distt\.?)\s+([a-zA-Z\s]+?)(?:,|$|\s+(?:state|pin))/i);
    if (districtMatch) {
      components.district = districtMatch[1].trim();
    }

    // Extract village
    const villageMatch = input.match(/(?:village|vill\.?|gram)\s+([a-zA-Z\s]+?)(?:,|$|\s+(?:district|dist))/i);
    if (villageMatch) {
      components.village = villageMatch[1].trim();
    }

    // Extract city
    const cityMatch = input.match(/(?:city|town)\s+([a-zA-Z\s]+?)(?:,|$|\s+(?:district|dist|state))/i);
    if (cityMatch) {
      components.city = cityMatch[1].trim();
    }

    // If no specific markers, try to extract from comma-separated parts
    if (!components.village && !components.city) {
      const parts = input.split(',').map(p => p.trim());
      if (parts.length > 0) {
        components.street = parts[0];
      }
      if (parts.length > 1 && !components.village) {
        components.village = parts[1];
      }
      if (parts.length > 2 && !components.district) {
        components.district = parts[2];
      }
    }

    return components;
  }

  private suggestDateCorrections(input: string): string[] {
    const suggestions: string[] = [];
    
    // Check if there are numbers that could be dates
    const numbers = input.match(/\d+/g);
    if (numbers && numbers.length >= 3) {
      suggestions.push(`Try format: ${numbers[0]}-${numbers[1]}-${numbers[2]}`);
    }

    suggestions.push('Use format DD-MM-YYYY (e.g., 15-08-1990)');
    suggestions.push('Or say the date with month name (e.g., 15 August 1990)');

    return suggestions;
  }

  private suggestPhoneCorrections(input: string): string[] {
    const suggestions: string[] = [];
    const digits = input.replace(/\D/g, '');

    if (digits.length > 10) {
      suggestions.push('Remove country code or extra digits');
    } else if (digits.length < 10) {
      suggestions.push('Add missing digits (need 10 total)');
    }

    if (digits.length === 10 && !/^[6-9]/.test(digits)) {
      suggestions.push('Mobile number should start with 6, 7, 8, or 9');
    }

    return suggestions;
  }

  private suggestNumberCorrections(input: string): string[] {
    const suggestions: string[] = [];
    
    suggestions.push('Provide just the number (e.g., 100, 2.5)');
    suggestions.push('You can use words like "one lakh" or "two crore"');

    return suggestions;
  }

  private suggestAadhaarCorrections(input: string): string[] {
    const suggestions: string[] = [];
    const digits = input.replace(/\D/g, '');

    if (digits.length > 12) {
      suggestions.push('Remove extra digits (need exactly 12)');
    } else if (digits.length < 12) {
      suggestions.push(`Add ${12 - digits.length} more digit(s)`);
    }

    return suggestions;
  }

  private suggestPincodeCorrections(input: string): string[] {
    const suggestions: string[] = [];
    const digits = input.replace(/\D/g, '');

    if (digits.length > 6) {
      suggestions.push('Remove extra digits (need exactly 6)');
    } else if (digits.length < 6) {
      suggestions.push(`Add ${6 - digits.length} more digit(s)`);
    }

    return suggestions;
  }

  private suggestIfscCorrections(input: string): string[] {
    const suggestions: string[] = [];
    const cleaned = input.replace(/\s/g, '').toUpperCase();

    if (cleaned.length !== 11) {
      suggestions.push('IFSC code must be exactly 11 characters');
    }

    if (!/^[A-Z]{4}/.test(cleaned)) {
      suggestions.push('First 4 characters should be letters (bank code)');
    }

    if (cleaned.length >= 5 && cleaned[4] !== '0') {
      suggestions.push('Fifth character should be 0');
    }

    return suggestions;
  }
}
