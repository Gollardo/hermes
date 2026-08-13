import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { SetupPage } from './setup';

describe('SetupPage', () => {
  let fixture: ComponentFixture<SetupPage>;
  const auth = {
    setup: vi.fn(() => of({ authenticated: true, expires_at: '2026-08-09T00:00:00Z' })),
    restoreSetup: vi.fn(() => of({ authenticated: true, expires_at: '2026-08-09T00:00:00Z' })),
  };

  beforeEach(async () => {
    auth.setup.mockClear();
    auth.restoreSetup.mockClear();
    await TestBed.configureTestingModule({
      imports: [SetupPage],
      providers: [{ provide: AuthService, useValue: auth }],
    }).compileComponents();
    fixture = TestBed.createComponent(SetupPage);
    fixture.detectChanges();
  });

  function startFresh(): void {
    ([...fixture.nativeElement.querySelectorAll('button')] as HTMLButtonElement[])
      .find((button) => button.textContent.includes('Начать с чистого листа'))!
      .click();
    fixture.detectChanges();
  }

  function fillPasswords(confirmation = 'long-master-password'): void {
    const password = fixture.nativeElement.querySelector('#setup-password') as HTMLInputElement;
    const repeated = fixture.nativeElement.querySelector(
      '#setup-password-confirmation',
    ) as HTMLInputElement;
    password.value = 'long-master-password';
    password.dispatchEvent(new Event('input'));
    repeated.value = confirmation;
    repeated.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  it('creates selected expense groups and the default income categories', () => {
    startFresh();
    fillPasswords();
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('.question-option input') as HTMLInputElement).click();
    fixture.detectChanges();
    ([...fixture.nativeElement.querySelectorAll('button')] as HTMLButtonElement[])
      .find((button) => button.textContent.trim() === 'Создать приложение')!
      .click();

    expect(auth.setup).toHaveBeenCalledWith(
      expect.objectContaining({
        master_password: 'long-master-password',
        create_default_categories: true,
        onboarding_expense_groups: ['housing'],
      }),
    );
  });

  it('does not continue with mismatched passwords', () => {
    startFresh();
    fillPasswords('another-long-password');
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    expect(auth.setup).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Пароли не совпадают');
  });

  it('allows skipping every expense question while still requesting income defaults', () => {
    startFresh();
    fillPasswords();
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    ([...fixture.nativeElement.querySelectorAll('button')] as HTMLButtonElement[])
      .find((button) => button.textContent.trim() === 'Пропустить и создать приложение')!
      .click();

    expect(auth.setup).toHaveBeenCalledWith(
      expect.objectContaining({
        create_default_categories: true,
        onboarding_expense_groups: [],
      }),
    );
  });

  it('keeps the primary action disabled until the credentials are valid', () => {
    startFresh();
    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fillPasswords('another-long-password');
    expect(button.disabled).toBe(true);
    fillPasswords();
    expect(button.disabled).toBe(false);
  });

  it('sends a selected backup to the atomic restore setup endpoint', async () => {
    const backup = { format: 'hermes-json-backup', schema_version: 1 };
    const file = {
      name: 'previous-version.json',
      size: 128,
      text: () => Promise.resolve(JSON.stringify(backup)),
    };
    const input = fixture.nativeElement.querySelector('#setup-backup') as HTMLInputElement;
    Object.defineProperty(input, 'files', { value: [file] });
    input.dispatchEvent(new Event('change'));
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('previous-version.json');
    expect(fixture.nativeElement.querySelector('#setup-currency')).toBeNull();
    fillPasswords();
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));

    expect(auth.restoreSetup).toHaveBeenCalledWith({
      master_password: 'long-master-password',
      backup,
    });
    expect(auth.setup).not.toHaveBeenCalled();
  });
});
