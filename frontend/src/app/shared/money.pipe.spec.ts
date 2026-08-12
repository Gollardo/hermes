import { formatMoney } from './money.pipe';

describe('formatMoney', () => {
  it('groups thousands and shows at least two exact decimal places', () => {
    expect(formatMoney('100000.0000')).toBe('100 000.00');
    expect(formatMoney('1234.5678')).toBe('1 234.5678');
    expect(formatMoney('-12.5000')).toBe('-12.50');
    expect(formatMoney('0')).toBe('0.00');
  });
});
