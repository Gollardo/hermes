import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';

import { DecimalInput, decimalPayload, moneyExpressionPayload } from './decimal-input';

@Component({
  imports: [ReactiveFormsModule, DecimalInput],
  template: '<input appDecimalInput [formControl]="control" />',
})
class DecimalHost {
  readonly control = new FormControl('', Validators.pattern(/^\d+(?:[.,]\d+)?$/));
}

describe('DecimalInput', () => {
  let fixture: ComponentFixture<DecimalHost>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [DecimalHost] }).compileComponents();
    fixture = TestBed.createComponent(DecimalHost);
    fixture.detectChanges();
  });

  it('leaves an optional empty field valid after blur', () => {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    input.dispatchEvent(new FocusEvent('blur'));
    fixture.detectChanges();
    expect(fixture.componentInstance.control.valid).toBe(true);
    expect(fixture.componentInstance.control.value).toBe('');
  });

  it('normalizes comma payloads even when submit happens before blur', () => {
    expect(decimalPayload(' 100 000,25 ')).toBe('100000.25');
  });

  it('evaluates addition and subtraction exactly with mixed decimal separators', () => {
    expect(moneyExpressionPayload('354.23 + 234,54 -23,32')).toBe('565.45');
    expect(moneyExpressionPayload('0,0001 + 0.0002')).toBe('0.0003');
    expect(moneyExpressionPayload('12.3400')).toBe('12.3400');
    expect(moneyExpressionPayload('+00012,3')).toBe('00012.3');
  });

  it('rejects unsupported or malformed money expressions', () => {
    expect(moneyExpressionPayload('10 * 2')).toBeNull();
    expect(moneyExpressionPayload('10 +')).toBeNull();
    expect(moneyExpressionPayload('(10 + 2)')).toBeNull();
    expect(moneyExpressionPayload(`1${'+1'.repeat(256)}`)).toBeNull();
    expect(moneyExpressionPayload(`1${' '.repeat(512)}`)).toBeNull();
  });

  it('formats a programmatic exact value but restores it for editing', () => {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    fixture.componentInstance.control.setValue('1234.5678');
    fixture.detectChanges();
    expect(input.value).toBe('1 234,57');

    input.dispatchEvent(new FocusEvent('focus'));
    expect(input.value).toBe('1234.5678');
  });

  it('groups and rounds display on blur while restoring exact input on focus', () => {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    input.value = '1000,565';
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new FocusEvent('blur'));
    expect(input.value).toBe('1 000,57');
    expect(fixture.componentInstance.control.value).toBe('1000.565');

    input.dispatchEvent(new FocusEvent('focus'));
    expect(input.value).toBe('1000.565');
    expect(fixture.componentInstance.control.valid).toBe(true);
  });
});
