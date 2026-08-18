import { Pipe, PipeTransform } from '@angular/core';

interface ParsedDecimal {
  readonly sign: '' | '+' | '-';
  readonly integer: string;
  readonly fraction: string;
}

/** Formats an exact decimal string with ROUND_HALF_UP without using Number. */
export function formatMoney(value: string | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const parsed = parseDecimal(value);
  if (!parsed) return value;

  const fraction = parsed.fraction.padEnd(3, '0');
  let cents = BigInt(parsed.integer) * 100n + BigInt(fraction.slice(0, 2));
  if (fraction[2] >= '5') cents += 1n;
  return formatCents(cents, parsed.sign);
}

/**
 * Formats a percentage breakdown. When exact non-negative shares total 100%,
 * displayed hundredths are assigned by largest remainder so the UI also totals
 * exactly 100,00%. Server values are never changed.
 */
export function formatPercentageBreakdown(values: readonly string[]): string[] {
  const parsed = values.map(parseDecimal);
  if (parsed.some((value) => value === null || value.sign === '-')) {
    return values.map((value) => formatMoney(value));
  }

  const decimals = parsed as ParsedDecimal[];
  const scale = Math.max(2, ...decimals.map((value) => value.fraction.length));
  const scaleFactor = 10n ** BigInt(scale);
  const centFactor = 10n ** BigInt(scale - 2);
  const units = decimals.map(
    (value) =>
      BigInt(value.integer) * scaleFactor + BigInt(value.fraction.padEnd(scale, '0') || '0'),
  );
  if (units.reduce((sum, value) => sum + value, 0n) !== 100n * scaleFactor) {
    return values.map((value) => formatMoney(value));
  }

  const cents = units.map((value) => value / centFactor);
  let missing = 10_000n - cents.reduce((sum, value) => sum + value, 0n);
  const remainderOrder = units
    .map((value, index) => ({ index, remainder: value % centFactor }))
    .sort((left, right) =>
      left.remainder === right.remainder
        ? left.index - right.index
        : left.remainder > right.remainder
          ? -1
          : 1,
    );
  for (const item of remainderOrder) {
    if (missing === 0n) break;
    cents[item.index] += 1n;
    missing -= 1n;
  }
  return cents.map((value) => formatCents(value, ''));
}

/** Builds a display-only 100% breakdown from exact non-negative amounts. */
export function formatPercentageBreakdownFromAmounts(
  amounts: readonly string[],
  total: string,
): string[] | null {
  const parsed = [...amounts.map(parseDecimal), parseDecimal(total)];
  if (parsed.some((value) => value === null || value.sign === '-')) return null;

  const decimals = parsed as ParsedDecimal[];
  const scale = Math.max(0, ...decimals.map((value) => value.fraction.length));
  const scaleFactor = 10n ** BigInt(scale);
  const units = decimals.map(
    (value) =>
      BigInt(value.integer) * scaleFactor + BigInt(value.fraction.padEnd(scale, '0') || '0'),
  );
  const totalUnits = units.at(-1) ?? 0n;
  const amountUnits = units.slice(0, -1);
  if (totalUnits <= 0n || amountUnits.reduce((sum, value) => sum + value, 0n) !== totalUnits) {
    return null;
  }

  const cents = amountUnits.map((value) => (value * 10_000n) / totalUnits);
  let missing = 10_000n - cents.reduce((sum, value) => sum + value, 0n);
  const remainderOrder = amountUnits
    .map((value, index) => ({ index, remainder: (value * 10_000n) % totalUnits }))
    .sort((left, right) =>
      left.remainder === right.remainder
        ? left.index - right.index
        : left.remainder > right.remainder
          ? -1
          : 1,
    );
  for (const item of remainderOrder) {
    if (missing === 0n) break;
    cents[item.index] += 1n;
    missing -= 1n;
  }
  return cents.map((value) => formatCents(value, ''));
}

function parseDecimal(value: string): ParsedDecimal | null {
  const match = /^([+-]?)(\d+)(?:[.,](\d+))?$/.exec(value.trim().replace(/\s/g, ''));
  if (!match) return null;
  return {
    sign: match[1] === '-' ? '-' : match[1] === '+' ? '+' : '',
    integer: match[2],
    fraction: match[3] ?? '',
  };
}

function formatCents(cents: bigint, sign: ParsedDecimal['sign']): string {
  const grouped = (cents / 100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const fraction = String(cents % 100n).padStart(2, '0');
  return `${cents === 0n ? '' : sign}${grouped},${fraction}`;
}

export function currencySymbol(code: string): string {
  return (
    (
      {
        RUB: '₽',
        USD: '$',
        EUR: '€',
        GBP: '£',
        JPY: '¥',
        CNY: '¥',
        KRW: '₩',
        INR: '₹',
        KZT: '₸',
        TRY: '₺',
      } as Record<string, string>
    )[code] ?? code
  );
}

@Pipe({ name: 'money', standalone: true })
export class MoneyPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    return formatMoney(value);
  }
}
