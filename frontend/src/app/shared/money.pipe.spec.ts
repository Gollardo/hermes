import {
  currencySymbol,
  formatMoney,
  formatPercentageBreakdown,
  formatPercentageBreakdownFromAmounts,
} from './money.pipe';

describe('formatMoney', () => {
  it('groups thousands and renders exactly two digits with a comma', () => {
    expect(formatMoney('100000.0000')).toBe('100 000,00');
    expect(formatMoney('-12.5000')).toBe('-12,50');
    expect(formatMoney('+12.5000')).toBe('+12,50');
    expect(formatMoney('0')).toBe('0,00');
  });

  it('uses exact ROUND_HALF_UP for positive and negative values', () => {
    expect(formatMoney('1234.5649')).toBe('1 234,56');
    expect(formatMoney('1234.5650')).toBe('1 234,57');
    expect(formatMoney('-1234.5650')).toBe('-1 234,57');
    expect(formatMoney('-0.0049')).toBe('0,00');
    expect(formatMoney('9999999999999999.9950')).toBe('10 000 000 000 000 000,00');
  });

  it('accepts comma and grouped values without changing the exact source', () => {
    expect(formatMoney(' 100 000,2550 ')).toBe('100 000,26');
  });
});

describe('formatPercentageBreakdown', () => {
  it('smooths an exact 100 percent breakdown by largest remainder', () => {
    expect(formatPercentageBreakdown(['33.3333', '33.3333', '33.3334'])).toEqual([
      '33,33',
      '33,33',
      '33,34',
    ]);
  });

  it('uses stable source order to break equal remainder ties', () => {
    expect(formatPercentageBreakdown(['33.3333', '33.3333', '33.3333', '0.0001'])).toEqual([
      '33,34',
      '33,33',
      '33,33',
      '0,00',
    ]);
  });

  it('rounds independently when the exact shares do not total 100 percent', () => {
    expect(formatPercentageBreakdown(['12.345', '10.004'])).toEqual(['12,35', '10,00']);
  });
});

describe('formatPercentageBreakdownFromAmounts', () => {
  it('derives a closed display breakdown from exact amounts', () => {
    expect(formatPercentageBreakdownFromAmounts(['1.0000', '1.0000', '1.0000'], '3.0000')).toEqual([
      '33,34',
      '33,33',
      '33,33',
    ]);
  });

  it('rejects an incomplete or invalid breakdown', () => {
    expect(formatPercentageBreakdownFromAmounts(['1.0000'], '2.0000')).toBeNull();
    expect(formatPercentageBreakdownFromAmounts(['-1.0000', '2.0000'], '1.0000')).toBeNull();
  });
});

describe('currencySymbol', () => {
  it('uses familiar symbols and falls back to the exact currency code', () => {
    expect(currencySymbol('RUB')).toBe('₽');
    expect(currencySymbol('EUR')).toBe('€');
    expect(currencySymbol('KZT')).toBe('₸');
    expect(currencySymbol('CHF')).toBe('CHF');
  });
});
