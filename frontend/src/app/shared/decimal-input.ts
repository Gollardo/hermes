import { Directive, HostListener, inject } from '@angular/core';
import { NgControl } from '@angular/forms';

const DECIMAL = /^-?\d{1,16}(?:[.,]\d{1,4})?$/;

export function decimalPayload(value: string): string {
  return value.trim().replace(/\s/g, '').replace(',', '.');
}

@Directive({ selector: 'input[appDecimalInput]' })
export class DecimalInput {
  private readonly ngControl = inject(NgControl, { optional: true });

  @HostListener('focus', ['$event'])
  ungroupForEditing(event: FocusEvent): void {
    const input = event.target as HTMLInputElement;
    if (!input.value.includes(' ')) return;
    const editable = decimalPayload(input.value);
    this.ngControl?.control?.setValue(editable);
    input.value = editable;
  }

  @HostListener('blur', ['$event'])
  normalize(event: FocusEvent): void {
    const input = event.target as HTMLInputElement;
    const raw = input.value.trim().replace(/\s/g, '');
    if (!raw) {
      input.setCustomValidity('');
      this.ngControl?.control?.setValue('');
      this.ngControl?.control?.markAsTouched();
      this.ngControl?.control?.updateValueAndValidity();
      return;
    }
    if (!DECIMAL.test(raw)) {
      input.setCustomValidity(
        'Введите число, например 100 000,00. Допустимо до 4 знаков после запятой.',
      );
      this.ngControl?.control?.setErrors({
        ...(this.ngControl?.control?.errors ?? {}),
        decimalFormat: true,
      });
      this.ngControl?.control?.markAsTouched();
      return;
    }
    input.setCustomValidity('');
    const [integer, fraction = ''] = decimalPayload(raw).split('.');
    const normalizedFraction = fraction.replace(/0+$/, '').padEnd(2, '0');
    const normalizedInteger = BigInt(integer).toString();
    const normalized = `${normalizedInteger}.${normalizedFraction}`;
    this.ngControl?.control?.setValue(normalized);
    this.ngControl?.control?.markAsTouched();
    this.ngControl?.control?.updateValueAndValidity();
    input.value = `${normalizedInteger.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}.${normalizedFraction}`;
  }
}
