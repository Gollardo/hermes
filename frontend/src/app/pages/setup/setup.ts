import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AuthService, apiErrorMessage } from '../../core/auth.service';

const CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP', 'CNY', 'JPY', 'KZT', 'TRY', 'AED', 'CHF'];

@Component({
  selector: 'app-setup-page',
  imports: [ReactiveFormsModule],
  templateUrl: './setup.html',
  styleUrl: './setup.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SetupPage {
  private readonly auth = inject(AuthService);
  private readonly formBuilder = inject(NonNullableFormBuilder);

  protected readonly currencies = CURRENCIES;
  protected readonly timezones = supportedTimezones();
  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly form = this.formBuilder.group({
    password: ['', [Validators.required, Validators.minLength(12), Validators.maxLength(1024)]],
    passwordConfirmation: ['', Validators.required],
    baseCurrency: ['RUB', [Validators.required, Validators.pattern(/^[A-Za-z]{3}$/)]],
    timezone: [detectedTimezone(), Validators.required],
  });

  protected canSubmit(): boolean {
    const value = this.form.getRawValue();
    return this.form.valid && value.password === value.passwordConfirmation && !this.submitting();
  }

  protected submit(): void {
    this.error.set(null);
    if (!this.canSubmit()) {
      this.form.markAllAsTouched();
      const value = this.form.getRawValue();
      if (this.form.valid && value.password !== value.passwordConfirmation) {
        this.error.set('Пароли не совпадают.');
      }
      return;
    }
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.auth
      .setup({
        master_password: value.password,
        base_currency: value.baseCurrency,
        timezone: value.timezone,
      })
      .subscribe({
        next: () => this.submitting.set(false),
        error: (error: unknown) => {
          this.submitting.set(false);
          this.error.set(apiErrorMessage(error, 'Не удалось завершить первоначальную настройку.'));
        },
      });
  }
}

function detectedTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

function supportedTimezones(): string[] {
  const intl = Intl as typeof Intl & { supportedValuesOf?: (key: 'timeZone') => string[] };
  const values = intl.supportedValuesOf?.('timeZone') ?? ['UTC', detectedTimezone()];
  return [...new Set(['UTC', detectedTimezone(), ...values])].sort();
}
