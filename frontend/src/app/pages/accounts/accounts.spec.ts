import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AccountsPage } from './accounts';

describe('AccountsPage', () => {
  let fixture: ComponentFixture<AccountsPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AccountsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(AccountsPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('creates an account with initial balance as a string', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/accounts').flush([]);
    fixture.detectChanges();
    const name = fixture.nativeElement.querySelector('#account-name') as HTMLInputElement;
    name.value = 'Wallet';
    name.dispatchEvent(new Event('input'));
    const balance = fixture.nativeElement.querySelector('#initial-balance') as HTMLInputElement;
    balance.value = '10.2500';
    balance.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/accounts');
    expect(request.request.method).toBe('POST');
    expect(request.request.body.initial_balance).toBe('10.2500');
    request.flush({});
    http.expectOne('/api/v1/accounts').flush([]);
  });

  it('does not submit a negative initial balance', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/accounts').flush([]);
    fixture.detectChanges();
    const name = fixture.nativeElement.querySelector('#account-name') as HTMLInputElement;
    name.value = 'Wallet';
    name.dispatchEvent(new Event('input'));
    const balance = fixture.nativeElement.querySelector('#initial-balance') as HTMLInputElement;
    balance.value = '-1';
    balance.dispatchEvent(new Event('input'));
    fixture.nativeElement.querySelector('form').dispatchEvent(new Event('submit'));
    http.expectNone('/api/v1/accounts');
  });
});
