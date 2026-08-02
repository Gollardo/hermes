import { HttpClient } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { environment } from '../../../environments/environment';
import { AuthService, apiErrorMessage } from '../../core/auth.service';

interface ApplicationSettings {
  base_currency: string;
  timezone: string;
  base_currency_locked: boolean;
  updated_at: string;
}

const CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP', 'CNY', 'JPY', 'KZT', 'TRY', 'AED', 'CHF'];

@Component({
  selector: 'app-settings-page',
  imports: [ReactiveFormsModule],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsPage implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly formBuilder = inject(NonNullableFormBuilder);

  protected readonly currencies = CURRENCIES;
  protected readonly timezones = supportedTimezones();
  protected readonly loading = signal(true);
  protected readonly savingSettings = signal(false);
  protected readonly changingPassword = signal(false);
  protected readonly settingsError = signal<string | null>(null);
  protected readonly settingsSuccess = signal<string | null>(null);
  protected readonly passwordError = signal<string | null>(null);
  protected readonly passwordSuccess = signal<string | null>(null);
  protected readonly currencyLocked = signal(false);

  protected readonly settingsForm = this.formBuilder.group({
    baseCurrency: ['RUB', [Validators.required, Validators.pattern(/^[A-Za-z]{3}$/)]],
    timezone: ['UTC', Validators.required],
  });

  protected readonly passwordForm = this.formBuilder.group({
    currentPassword: ['', [Validators.required, Validators.maxLength(1024)]],
    newPassword: ['', [Validators.required, Validators.minLength(12), Validators.maxLength(1024)]],
    newPasswordConfirmation: ['', Validators.required],
  });

  ngOnInit(): void {
    this.loadSettings();
  }

  protected saveSettings(): void {
    this.settingsError.set(null);
    this.settingsSuccess.set(null);
    if (this.settingsForm.invalid) {
      this.settingsForm.markAllAsTouched();
      return;
    }
    const value = this.settingsForm.getRawValue();
    this.savingSettings.set(true);
    this.http
      .put<ApplicationSettings>(`${environment.apiBaseUrl}/settings`, {
        base_currency: value.baseCurrency,
        timezone: value.timezone,
      })
      .subscribe({
        next: (settings) => {
          this.savingSettings.set(false);
          this.applySettings(settings);
          this.settingsSuccess.set('Настройки сохранены.');
        },
        error: (error: unknown) => {
          this.savingSettings.set(false);
          this.settingsError.set(apiErrorMessage(error, 'Не удалось сохранить настройки.'));
        },
      });
  }

  protected changePassword(): void {
    this.passwordError.set(null);
    this.passwordSuccess.set(null);
    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      return;
    }
    const value = this.passwordForm.getRawValue();
    if (value.newPassword !== value.newPasswordConfirmation) {
      this.passwordError.set('Новые пароли не совпадают.');
      return;
    }
    this.changingPassword.set(true);
    this.auth
      .changePassword({
        current_password: value.currentPassword,
        new_master_password: value.newPassword,
      })
      .subscribe({
        next: () => {
          this.changingPassword.set(false);
          this.passwordForm.reset();
          this.passwordSuccess.set('Мастер-пароль изменён. Остальные сессии завершены.');
        },
        error: (error: unknown) => {
          this.changingPassword.set(false);
          this.passwordError.set(apiErrorMessage(error, 'Не удалось изменить мастер-пароль.'));
        },
      });
  }

  protected logoutAll(): void {
    this.auth.logoutAll().subscribe({
      error: (error: unknown) =>
        this.settingsError.set(apiErrorMessage(error, 'Не удалось завершить все сессии.')),
    });
  }

  private loadSettings(): void {
    this.loading.set(true);
    this.http.get<ApplicationSettings>(`${environment.apiBaseUrl}/settings`).subscribe({
      next: (settings) => {
        this.loading.set(false);
        this.applySettings(settings);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.settingsError.set(apiErrorMessage(error, 'Не удалось загрузить настройки.'));
      },
    });
  }

  private applySettings(settings: ApplicationSettings): void {
    this.currencyLocked.set(settings.base_currency_locked);
    this.settingsForm.setValue({
      baseCurrency: settings.base_currency,
      timezone: settings.timezone,
    });
    if (settings.base_currency_locked) {
      this.settingsForm.controls.baseCurrency.disable();
    }
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
