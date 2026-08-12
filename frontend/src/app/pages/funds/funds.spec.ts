import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FundsPage } from './funds';

describe('FundsPage', () => {
  let fixture: ComponentFixture<FundsPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FundsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(FundsPage);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne('/api/v1/settings').flush({ timezone: 'Europe/Moscow', base_currency: 'RUB' });
    http.expectOne('/api/v1/funds/summary').flush({
      funds: [
        {
          id: 'fund-1',
          name: 'Reserve',
          description: null,
          allocation_percentage: '25.0000',
          total_balance: '20.0000',
          archived: false,
          version: 1,
        },
      ],
      positions: [],
      accounts: [
        {
          account_id: 'account-1',
          account_name: 'Main',
          physical_balance: '100.0000',
          reserved_balance: '20.0000',
          free_balance: '80.0000',
          archived: false,
        },
        {
          account_id: 'account-archived',
          account_name: 'Closed',
          physical_balance: '0.0000',
          reserved_balance: '0.0000',
          free_balance: '0.0000',
          archived: true,
        },
      ],
      active_percentage: '25.0000',
      total_reserved: '20.0000',
      total_free: '80.0000',
    });
    expectHistory().flush({ items: [], page: 1, page_size: 25, total: 0 });
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('shows physical coverage and permits editing a fund definition', () => {
    expect(fixture.nativeElement.textContent).toContain('Физический остаток = в фондах + свободно');
    expect(fixture.nativeElement.textContent).toContain('80.00');
    const edit = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent.trim() === 'Изменить',
    ) as HTMLButtonElement;
    edit.click();
    fixture.detectChanges();
    expect((fixture.nativeElement.querySelector('#fund-name') as HTMLInputElement).value).toBe(
      'Reserve',
    );
  });

  it('keeps preview editable and commits exact decimal strings', () => {
    clickButton('Выделить со счёта');
    setValue('#allocation-account', 'account-1');
    setValue('#allocation-amount', '10');
    const previewButton = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent.includes('Рассчитать по процентам'),
    ) as HTMLButtonElement;
    previewButton.click();
    http.expectOne('/api/v1/funds/allocation-preview').flush({
      account_id: 'account-1',
      amount: '10',
      allocations: [{ fund_id: 'fund-1', amount: '2.5000' }],
      allocated_amount: '2.5000',
      unallocated_amount: '7.5000',
      free_before: '80.0000',
      free_after: '77.5000',
    });
    fixture.detectChanges();
    setValue('#allocation-0', '3.1250');
    const form = fixture.nativeElement.querySelector('.modal-card form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/funds/allocations');
    expect(request.request.body.allocations[0].amount).toBe('3.1250');
    request.flush({});
    http.expectOne('/api/v1/funds/summary').flush({
      funds: [],
      positions: [],
      accounts: [],
      active_percentage: '0',
      total_reserved: '0',
      total_free: '0',
    });
    expectHistory().flush({ items: [], page: 1, page_size: 25, total: 0 });
  });

  it('blocks percentage overflow and invalidates a stale allocation preview', () => {
    clickButton('Создать фонд');
    setValue('#fund-percentage', '80');
    const fundSubmit = fixture.nativeElement.querySelector(
      '.modal-card button[type="submit"]',
    ) as HTMLButtonElement;
    expect(fundSubmit.disabled).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Доступно: 75.0000%');

    clickButton('Закрыть');
    clickButton('Выделить со счёта');

    setValue('#allocation-account', 'account-1');
    setValue('#allocation-amount', '10');
    const previewButton = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent.includes('Рассчитать по процентам'),
    ) as HTMLButtonElement;
    previewButton.click();
    const staleRequest = http.expectOne('/api/v1/funds/allocation-preview');
    setValue('#allocation-amount', '11');
    staleRequest.flush({
      account_id: 'account-1',
      amount: '10',
      allocations: [{ fund_id: 'fund-1', amount: '2.5000' }],
      allocated_amount: '2.5000',
      unallocated_amount: '7.5000',
      free_before: '80.0000',
      free_after: '77.5000',
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('Будет распределено:');
  });

  function expectHistory() {
    return http.expectOne(
      (request) =>
        request.url === '/api/v1/funds/history' &&
        request.params.get('page') === '1' &&
        request.params.get('page_size') === '25',
    );
  }

  function setValue(selector: string, value: string): void {
    const control = fixture.nativeElement.querySelector(selector) as HTMLInputElement;
    control.value = value;
    control.dispatchEvent(new Event('input'));
    control.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  function clickButton(label: string): void {
    const button = [...fixture.nativeElement.querySelectorAll('button')].find(
      (item: HTMLButtonElement) =>
        item.textContent.trim() === label || item.getAttribute('aria-label') === label,
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();
  }
});
