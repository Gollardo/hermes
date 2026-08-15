import { Pipe, PipeTransform } from '@angular/core';

/** Formats exact decimal strings without converting domain money to Number. */
export function formatMoney(value: string | null | undefined): string {
  if (value === null || value === undefined) return '—';
  const match = /^([+-]?)(\d+)(?:\.(\d+))?$/.exec(value.trim());
  if (!match) return value;

  const grouped = match[2].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const rawFraction = match[3] ?? '';
  const fraction = rawFraction.padEnd(2, '0').replace(/0+$/, '');
  const exactFraction = fraction.length < 2 ? fraction.padEnd(2, '0') : fraction;
  return `${match[1]}${grouped}.${exactFraction}`;
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
