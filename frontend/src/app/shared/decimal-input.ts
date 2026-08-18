import {
  AfterViewInit,
  Directive,
  ElementRef,
  HostListener,
  OnDestroy,
  inject,
} from '@angular/core';
import { NgControl } from '@angular/forms';
import { Subscription } from 'rxjs';

import { formatMoney } from './money.pipe';

const DECIMAL = /^-?\d{1,16}(?:[.,]\d{1,4})?$/;

export function decimalPayload(value: string): string {
  return value.trim().replace(/\s/g, '').replace(',', '.');
}

@Directive({ selector: 'input[appDecimalInput]' })
export class DecimalInput implements AfterViewInit, OnDestroy {
  private readonly ngControl = inject(NgControl, { optional: true });
  private readonly element = inject<ElementRef<HTMLInputElement>>(ElementRef);
  private readonly subscriptions = new Subscription();
  private focused = false;

  ngAfterViewInit(): void {
    const input = this.element.nativeElement;
    const markEditing = (): void => {
      this.focused = true;
    };
    input.addEventListener('input', markEditing, { capture: true });
    this.subscriptions.add(() =>
      input.removeEventListener('input', markEditing, { capture: true }),
    );
    this.render(this.ngControl?.control?.value);
    const values = this.ngControl?.control?.valueChanges;
    if (values) {
      this.subscriptions.add(values.subscribe((value) => this.render(value)));
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  @HostListener('focus', ['$event'])
  ungroupForEditing(event: FocusEvent): void {
    this.focused = true;
    const input = event.target as HTMLInputElement;
    const controlValue = this.ngControl?.control?.value;
    const editable =
      typeof controlValue === 'string' && controlValue.trim()
        ? decimalPayload(controlValue)
        : decimalPayload(input.value);
    this.ngControl?.control?.setValue(editable);
    input.value = editable;
  }

  @HostListener('blur', ['$event'])
  normalize(event: FocusEvent): void {
    this.focused = false;
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
    input.value = formatMoney(normalized);
  }

  private render(value: unknown): void {
    if (this.focused || typeof value !== 'string' || !value.trim()) return;
    this.element.nativeElement.value = formatMoney(value);
  }
}
