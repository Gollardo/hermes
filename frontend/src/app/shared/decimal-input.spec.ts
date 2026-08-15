import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';

import { DecimalInput, decimalPayload } from './decimal-input';

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

  it('groups a formatted value on blur and ungroups it for valid editing', () => {
    const input = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    input.value = '1000,5';
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new FocusEvent('blur'));
    expect(input.value).toBe('1 000.50');
    expect(fixture.componentInstance.control.value).toBe('1000.50');

    input.dispatchEvent(new FocusEvent('focus'));
    expect(input.value).toBe('1000.50');
    expect(fixture.componentInstance.control.valid).toBe(true);
  });
});
