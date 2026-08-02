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
});
