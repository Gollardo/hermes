import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AuthService } from '../../core/auth.service';
import { SettingsPage } from './settings';

describe('SettingsPage', () => {
  let fixture: ComponentFixture<SettingsPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: AuthService,
          useValue: {
            changePassword: vi.fn(() => of(undefined)),
            logoutAll: vi.fn(() => of(undefined)),
          },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(SettingsPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('loads and updates application settings', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      default_account_id: null,
      base_currency_locked: false,
      updated_at: '2026-08-02T00:00:00Z',
    });
    http
      .expectOne('/api/v1/accounts')
      .flush([{ id: 'account-1', name: 'Основной', archived: false }]);
    fixture.detectChanges();

    const currency = fixture.nativeElement.querySelector('#settings-currency') as HTMLInputElement;
    currency.value = 'EUR';
    currency.dispatchEvent(new Event('input'));
    const defaultAccount = fixture.nativeElement.querySelector(
      '#settings-default-account',
    ) as HTMLInputElement;
    defaultAccount.value = 'Осн';
    defaultAccount.dispatchEvent(new Event('input'));
    defaultAccount.dispatchEvent(new Event('focus'));
    fixture.detectChanges();
    (
      fixture.nativeElement.querySelector('[data-option-id="account-1"]') as HTMLButtonElement
    ).click();
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));

    const request = http.expectOne('/api/v1/settings');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body.base_currency).toBe('EUR');
    expect(request.request.body.default_account_id).toBe('account-1');
    request.flush({
      base_currency: 'EUR',
      timezone: 'Europe/Moscow',
      default_account_id: 'account-1',
      base_currency_locked: false,
      updated_at: '2026-08-02T00:01:00Z',
    });
  });

  it('keeps security and backup settings available when accounts cannot load', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      default_account_id: null,
      base_currency_locked: false,
      updated_at: '2026-08-02T00:00:00Z',
    });
    http
      .expectOne('/api/v1/accounts')
      .flush({ detail: 'Unavailable' }, { status: 503, statusText: 'Service Unavailable' });
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('#settings-currency')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('#current-password')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('#backup-file')).not.toBeNull();
    expect(
      (fixture.nativeElement.querySelector('#settings-default-account') as HTMLInputElement)
        .disabled,
    ).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Остальные настройки доступны');
  });

  it('validates a selected backup and shows the replacement summary', async () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      default_account_id: null,
      base_currency_locked: true,
      updated_at: '2026-08-12T00:00:00Z',
    });
    http.expectOne('/api/v1/accounts').flush([]);
    fixture.detectChanges();

    const input = fixture.nativeElement.querySelector('#backup-file') as HTMLInputElement;
    const file = new File(['{"format":"hermes-json-backup"}'], 'backup.json', {
      type: 'application/json',
    });
    Object.defineProperty(input, 'files', { value: [file] });
    input.dispatchEvent(new Event('change'));
    await file.text();
    fixture.detectChanges();

    const request = http.expectOne('/api/v1/backup/preview');
    expect(request.request.method).toBe('POST');
    request.flush({
      app_version: '0.3.0',
      exported_at: '2026-08-12T00:00:00Z',
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      default_account_id: null,
      integrity_verified: true,
      counts: {
        accounts: 1,
        categories: 1,
        operations: 2,
        account_movements: 2,
        funds: 1,
        fund_events: 1,
        fund_movements: 1,
        recurring_rules: 1,
        expected_occurrences: 3,
      },
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Целостность подтверждена');
    expect(fixture.nativeElement.textContent).toContain('12 августа 2026');
    expect(fixture.nativeElement.textContent).toContain('2 операций');
    expect(fixture.nativeElement.textContent).toContain('ЗАМЕНИТЬ ВСЕ ДАННЫЕ');
  });

  it('does not submit restore until the exact confirmation matches', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      default_account_id: null,
      base_currency_locked: true,
      updated_at: '2026-08-12T00:00:00Z',
    });
    http.expectOne('/api/v1/accounts').flush([]);
    const page = fixture.componentInstance as unknown as {
      backupDocument: { set: (value: unknown) => void };
      restoreForm: { setValue: (value: { confirmation: string; masterPassword: string }) => void };
      restoreBackup: () => void;
    };
    page.backupDocument.set({ format: 'hermes-json-backup' });
    page.restoreForm.setValue({ confirmation: 'не совпадает', masterPassword: 'secret' });
    page.restoreBackup();
    fixture.detectChanges();
    http.expectNone('/api/v1/backup/restore');
    expect(fixture.nativeElement.textContent).toContain('Фраза подтверждения не совпадает');
  });

  it('submits the previewed backup only after exact confirmation', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      default_account_id: null,
      base_currency_locked: true,
      updated_at: '2026-08-12T00:00:00Z',
    });
    http.expectOne('/api/v1/accounts').flush([]);
    const backup = { format: 'hermes-json-backup', schema_version: 1 };
    const page = fixture.componentInstance as unknown as {
      backupDocument: { set: (value: unknown) => void };
      restoreForm: {
        setValue: (value: { confirmation: string; masterPassword: string }) => void;
        getRawValue: () => { confirmation: string; masterPassword: string };
      };
      restoreBackup: () => void;
    };
    page.backupDocument.set(backup);
    page.restoreForm.setValue({
      confirmation: 'ЗАМЕНИТЬ ВСЕ ДАННЫЕ',
      masterPassword: 'correct-master-password',
    });
    page.restoreBackup();

    const request = http.expectOne('/api/v1/backup/restore');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      backup,
      confirmation: 'ЗАМЕНИТЬ ВСЕ ДАННЫЕ',
      master_password: 'correct-master-password',
    });
    request.flush(
      { detail: { code: 'invalid_backup' } },
      { status: 422, statusText: 'Unprocessable Content' },
    );
    expect(page.restoreForm.getRawValue().masterPassword).toBe('');
  });
});
