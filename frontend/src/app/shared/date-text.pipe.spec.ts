import { formatTextDate, formatTextTimestamp } from './date-text.pipe';

describe('date text formatting', () => {
  it('formats an ISO calendar date without a timezone shift', () => {
    expect(formatTextDate('2025-01-20')).toBe('20 января 2025');
    expect(formatTextDate(null)).toBe('—');
  });

  it('keeps the confirmed full textual date inside timestamps', () => {
    const value = formatTextTimestamp('2025-01-20T12:34:00Z');
    expect(value).toMatch(/^20 января 2025, \d{2}:\d{2}$/);
  });
});
