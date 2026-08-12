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
      base_currency_locked: false,
      updated_at: '2026-08-02T00:00:00Z',
    });
    fixture.detectChanges();

    const currency = fixture.nativeElement.querySelector('#settings-currency') as HTMLInputElement;
    currency.value = 'EUR';
    currency.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));

    const request = http.expectOne('/api/v1/settings');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body.base_currency).toBe('EUR');
    request.flush({
      base_currency: 'EUR',
      timezone: 'Europe/Moscow',
      base_currency_locked: false,
      updated_at: '2026-08-02T00:01:00Z',
    });
  });

  it('validates a selected backup and shows the replacement summary', async () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      base_currency_locked: true,
      updated_at: '2026-08-12T00:00:00Z',
    });
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
      app_version: '0.1.0-rc.1',
      exported_at: '2026-08-12T00:00:00Z',
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
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
    expect(fixture.nativeElement.textContent).toContain('2 операций');
    expect(fixture.nativeElement.textContent).toContain('ЗАМЕНИТЬ ВСЕ ДАННЫЕ');
  });

  it('does not submit restore until the exact confirmation matches', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'Europe/Moscow',
      base_currency_locked: true,
      updated_at: '2026-08-12T00:00:00Z',
    });
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
      base_currency_locked: true,
      updated_at: '2026-08-12T00:00:00Z',
    });
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
