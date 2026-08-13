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
});
