/**
 * Utility Functions Tests
 */

describe('Currency Formatting', () => {
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  it('should format positive amounts correctly', () => {
    expect(formatCurrency(10)).toBe('$10.00');
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
    expect(formatCurrency(0.99)).toBe('$0.99');
  });

  it('should format zero correctly', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('should format large amounts with commas', () => {
    expect(formatCurrency(1000000)).toBe('$1,000,000.00');
  });
});

describe('Date Formatting', () => {
  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  it('should format dates correctly', () => {
    // Use explicit time to avoid timezone issues
    const date = new Date(2024, 2, 15); // March 15, 2024 (month is 0-indexed)
    expect(formatDate(date)).toBe('Mar 15, 2024');
  });
});

describe('SKU Validation', () => {
  const isValidSKU = (sku: string): boolean => {
    // SKU format: LETTERS-NUMBERS (e.g., TEST-001)
    return /^[A-Z]+-\d+$/.test(sku);
  };

  it('should validate correct SKU format', () => {
    expect(isValidSKU('TEST-001')).toBe(true);
    expect(isValidSKU('PROD-12345')).toBe(true);
    expect(isValidSKU('ABC-1')).toBe(true);
  });

  it('should reject invalid SKU formats', () => {
    expect(isValidSKU('test-001')).toBe(false); // lowercase
    expect(isValidSKU('TEST001')).toBe(false); // no hyphen
    expect(isValidSKU('TEST-')).toBe(false); // no number
    expect(isValidSKU('-001')).toBe(false); // no letters
    expect(isValidSKU('')).toBe(false); // empty
  });
});

describe('Barcode Validation', () => {
  const isValidBarcode = (barcode: string): boolean => {
    // Support UPC-A (12 digits) and EAN-13 (13 digits)
    return /^\d{12,13}$/.test(barcode);
  };

  it('should validate UPC-A barcodes (12 digits)', () => {
    expect(isValidBarcode('012345678901')).toBe(true);
  });

  it('should validate EAN-13 barcodes (13 digits)', () => {
    expect(isValidBarcode('0123456789012')).toBe(true);
  });

  it('should reject invalid barcodes', () => {
    expect(isValidBarcode('12345')).toBe(false); // too short
    expect(isValidBarcode('12345678901234')).toBe(false); // too long
    expect(isValidBarcode('12345678901A')).toBe(false); // contains letter
  });
});

describe('Email Validation', () => {
  const isValidEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  it('should validate correct email formats', () => {
    expect(isValidEmail('test@example.com')).toBe(true);
    expect(isValidEmail('user.name@company.org')).toBe(true);
    expect(isValidEmail('user+tag@domain.co.uk')).toBe(true);
  });

  it('should reject invalid email formats', () => {
    expect(isValidEmail('invalid')).toBe(false);
    expect(isValidEmail('invalid@')).toBe(false);
    expect(isValidEmail('@domain.com')).toBe(false);
    expect(isValidEmail('user @domain.com')).toBe(false);
  });
});

describe('Phone Number Formatting', () => {
  const formatPhoneNumber = (phone: string): string => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    }
    return phone;
  };

  it('should format 10-digit phone numbers', () => {
    expect(formatPhoneNumber('1234567890')).toBe('(123) 456-7890');
    expect(formatPhoneNumber('123-456-7890')).toBe('(123) 456-7890');
    expect(formatPhoneNumber('(123) 456-7890')).toBe('(123) 456-7890');
  });

  it('should return original for non-10-digit numbers', () => {
    expect(formatPhoneNumber('123')).toBe('123');
    expect(formatPhoneNumber('12345678901')).toBe('12345678901');
  });
});

describe('Percentage Calculations', () => {
  const calculatePercentage = (value: number, total: number): number => {
    if (total === 0) return 0;
    return Math.round((value / total) * 100 * 100) / 100;
  };

  it('should calculate percentages correctly', () => {
    expect(calculatePercentage(25, 100)).toBe(25);
    expect(calculatePercentage(1, 3)).toBe(33.33);
    expect(calculatePercentage(50, 200)).toBe(25);
  });

  it('should handle zero total', () => {
    expect(calculatePercentage(10, 0)).toBe(0);
  });

  it('should handle zero value', () => {
    expect(calculatePercentage(0, 100)).toBe(0);
  });
});
