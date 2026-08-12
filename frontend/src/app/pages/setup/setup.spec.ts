import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { SetupPage } from './setup';

describe('SetupPage', () => {
  let fixture: ComponentFixture<SetupPage>;
  const auth = {
    setup: vi.fn(() => of({ authenticated: true, expires_at: '2026-08-09T00:00:00Z' })),
  };

  beforeEach(async () => {
    auth.setup.mockClear();
    await TestBed.configureTestingModule({
      imports: [SetupPage],
      providers: [{ provide: AuthService, useValue: auth }],
    }).compileComponents();
    fixture = TestBed.createComponent(SetupPage);
    fixture.detectChanges();
  });

  it('submits password, currency, and timezone as one setup request', () => {
    const inputs = fixture.nativeElement.querySelectorAll('input') as NodeListOf<HTMLInputElement>;
    inputs[0].value = 'long-master-password';
    inputs[0].dispatchEvent(new Event('input'));
    inputs[1].value = 'long-master-password';
    inputs[1].dispatchEvent(new Event('input'));

    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));

    expect(auth.setup).toHaveBeenCalledWith(
      expect.objectContaining({
        master_password: 'long-master-password',
        base_currency: 'RUB',
      }),
    );
  });

  it('does not submit mismatched passwords', () => {
    const inputs = fixture.nativeElement.querySelectorAll('input') as NodeListOf<HTMLInputElement>;
    inputs[0].value = 'long-master-password';
    inputs[0].dispatchEvent(new Event('input'));
    inputs[1].value = 'another-long-password';
    inputs[1].dispatchEvent(new Event('input'));

    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    fixture.detectChanges();

    expect(auth.setup).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Пароли не совпадают');
  });

  it('keeps the primary action disabled until the form and confirmation are valid', () => {
    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    const inputs = fixture.nativeElement.querySelectorAll('input') as NodeListOf<HTMLInputElement>;
    inputs[0].value = 'long-master-password';
    inputs[0].dispatchEvent(new Event('input'));
    inputs[1].value = 'another-long-password';
    inputs[1].dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(button.disabled).toBe(true);

    inputs[1].value = 'long-master-password';
    inputs[1].dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(button.disabled).toBe(false);
  });
});
