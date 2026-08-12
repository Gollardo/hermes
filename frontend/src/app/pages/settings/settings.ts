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

interface BackupPreview {
  app_version: string;
  exported_at: string;
  base_currency: string;
  timezone: string;
  integrity_verified: boolean;
  counts: Record<string, number>;
}

interface BackupDocumentEnvelope {
  exported_at: string;
}

const CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP', 'CNY', 'JPY', 'KZT', 'TRY', 'AED', 'CHF'];
const RESTORE_CONFIRMATION = 'ЗАМЕНИТЬ ВСЕ ДАННЫЕ';

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
  protected readonly backupDocument = signal<unknown | null>(null);
  protected readonly backupPreview = signal<BackupPreview | null>(null);
  protected readonly backupBusy = signal(false);
  protected readonly backupError = signal<string | null>(null);
  protected readonly backupSuccess = signal<string | null>(null);
  protected readonly restoreConfirmation = RESTORE_CONFIRMATION;
  protected readonly formatTimestamp = formatTimestamp;
  private selectedBackupSequence = 0;

  protected readonly settingsForm = this.formBuilder.group({
    baseCurrency: ['RUB', [Validators.required, Validators.pattern(/^[A-Za-z]{3}$/)]],
    timezone: ['UTC', Validators.required],
  });

  protected readonly passwordForm = this.formBuilder.group({
    currentPassword: ['', [Validators.required, Validators.maxLength(1024)]],
    newPassword: ['', [Validators.required, Validators.minLength(12), Validators.maxLength(1024)]],
    newPasswordConfirmation: ['', Validators.required],
  });

  protected readonly restoreForm = this.formBuilder.group({
    confirmation: ['', Validators.required],
    masterPassword: ['', [Validators.required, Validators.maxLength(1024)]],
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

  protected exportBackup(): void {
    this.backupBusy.set(true);
    this.backupError.set(null);
    this.backupSuccess.set(null);
    this.http.get<BackupDocumentEnvelope>(`${environment.apiBaseUrl}/backup/export`).subscribe({
      next: (document) => {
        this.backupBusy.set(false);
        const blob = new Blob([JSON.stringify(document, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = window.document.createElement('a');
        link.href = url;
        link.download = `hermes-backup-${new Date().toISOString().slice(0, 10)}.json`;
        link.click();
        URL.revokeObjectURL(url);
        this.backupSuccess.set(
          `Backup от ${formatTimestamp(document.exported_at)} сформирован и проверен. ` +
            'Сохраните файл в защищённом месте.',
        );
      },
      error: (error: unknown) => {
        this.backupBusy.set(false);
        this.backupError.set(apiErrorMessage(error, 'Не удалось создать backup.'));
      },
    });
  }

  protected chooseBackup(event: Event): void {
    const sequence = ++this.selectedBackupSequence;
    const file = (event.target as HTMLInputElement).files?.[0];
    this.backupPreview.set(null);
    this.backupDocument.set(null);
    this.backupError.set(null);
    this.backupSuccess.set(null);
    this.restoreForm.reset();
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      this.backupError.set('Файл больше допустимых 50 МБ.');
      return;
    }
    file
      .text()
      .then((text) => {
        if (sequence !== this.selectedBackupSequence) return;
        let document: unknown;
        try {
          document = JSON.parse(text);
        } catch {
          this.backupError.set('Файл не является корректным JSON.');
          return;
        }
        this.backupBusy.set(true);
        this.http
          .post<BackupPreview>(`${environment.apiBaseUrl}/backup/preview`, document)
          .subscribe({
            next: (preview) => {
              if (sequence !== this.selectedBackupSequence) return;
              this.backupBusy.set(false);
              this.backupDocument.set(document);
              this.backupPreview.set(preview);
            },
            error: (error: unknown) => {
              if (sequence !== this.selectedBackupSequence) return;
              this.backupBusy.set(false);
              this.backupError.set(apiErrorMessage(error, 'Backup не прошёл проверку.'));
            },
          });
      })
      .catch(() => {
        if (sequence !== this.selectedBackupSequence) return;
        this.backupBusy.set(false);
        this.backupError.set('Не удалось прочитать выбранный файл. Выберите его повторно.');
      });
  }

  protected restoreBackup(): void {
    const backup = this.backupDocument();
    const value = this.restoreForm.getRawValue();
    if (!backup || this.restoreForm.invalid || value.confirmation !== RESTORE_CONFIRMATION) {
      this.restoreForm.markAllAsTouched();
      if (value.confirmation !== RESTORE_CONFIRMATION) {
        this.backupError.set('Фраза подтверждения не совпадает. Данные не изменены.');
      }
      return;
    }
    this.backupBusy.set(true);
    this.backupError.set(null);
    this.http
      .post(`${environment.apiBaseUrl}/backup/restore`, {
        backup,
        confirmation: value.confirmation,
        master_password: value.masterPassword,
      })
      .subscribe({
        next: () => {
          this.backupBusy.set(false);
          this.backupSuccess.set('Данные восстановлены полностью. Обновляем приложение…');
          window.location.reload();
        },
        error: (error: unknown) => {
          this.backupBusy.set(false);
          this.restoreForm.controls.masterPassword.reset();
          this.backupError.set(
            apiErrorMessage(error, 'Восстановление отменено, данные не изменены.'),
          );
        },
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

function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}
