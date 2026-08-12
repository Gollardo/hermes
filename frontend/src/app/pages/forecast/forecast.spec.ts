import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ForecastPage } from './forecast';

const FORECAST = {
  scope: 'all',
  account_id: null,
  account_name: null,
  horizon: 'month',
  from_on: '2026-08-12',
  through_on: '2026-09-12',
  starting_balance: '100.0000',
  ending_balance: '-20.0000',
  minimum_balance: '-20.0000',
  minimum_on: '2026-08-20',
  first_negative_on: '2026-08-20',
  expected_income: '30.0000',
  expected_expense: '150.0000',
  overdue_excluded_count: 1,
  points: [
    {
      on: '2026-08-12',
      opening_balance: '100.0000',
      change: '0',
      closing_balance: '100.0000',
      events: [],
    },
    {
      on: '2026-08-20',
      opening_balance: '100.0000',
      change: '-120.0000',
      closing_balance: '-20.0000',
      events: [
        {
          occurrence_id: 'occurrence-1',
          due_on: '2026-08-20',
          type: 'expense',
          status: 'pending',
          description: 'Аренда',
          account_name: 'Основной',
          destination_account_name: null,
          amount: '120.0000',
          effect: '-120.0000',
        },
      ],
    },
    {
      on: '2026-09-12',
      opening_balance: '-20.0000',
      change: '0',
      closing_balance: '-20.0000',
      events: [],
    },
  ],
};

describe('ForecastPage', () => {
  let fixture: ComponentFixture<ForecastPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ForecastPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    fixture = TestBed.createComponent(ForecastPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('shows an explicit risk and the events explaining a forecast point', () => {
    flushInitial();
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/forecast' && request.params.get('horizon') === 'month',
      )
      .flush(FORECAST);
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Возможен недостаток средств 2026-08-20');
    expect(fixture.nativeElement.textContent).toContain('1 просроченных событий не включено');
    expect(fixture.nativeElement.textContent).toContain('Аренда');
    expect(fixture.nativeElement.querySelector('.forecast-chart')).not.toBeNull();
    expect(
      fixture.nativeElement.querySelector('.period-switcher button').getAttribute('aria-pressed'),
    ).toBe('false');
    const calendarLink = fixture.nativeElement.querySelector('.event-link') as HTMLAnchorElement;
    expect(calendarLink.getAttribute('href')).toContain('month=2026-08');
    expect(calendarLink.getAttribute('href')).toContain('focus=occurrence-1');
    const xCoordinates = (
      fixture.nativeElement.querySelector('.forecast-line') as SVGPolylineElement
    )
      .getAttribute('points')!
      .split(' ')
      .map((point) => Number(point.split(',')[0]));
    expect(xCoordinates[1]).toBeLessThan(40);
    expect(xCoordinates[2]).toBe(96);
  });

  it('replaces stale data with loading and explains an event-free horizon', () => {
    flushInitial();
    http.expectOne('/api/v1/forecast?horizon=month').flush({
      ...FORECAST,
      ending_balance: '100.0000',
      minimum_balance: '100.0000',
      minimum_on: '2026-08-12',
      first_negative_on: null,
      expected_income: '0',
      expected_expense: '0',
      overdue_excluded_count: 0,
      points: [FORECAST.points[0], { ...FORECAST.points[0], on: '2026-09-12' }],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Нет известных ожидаемых событий');

    const week = [...fixture.nativeElement.querySelectorAll('.period-switcher button')].find(
      (button: HTMLButtonElement) => button.textContent.trim() === 'Неделя',
    ) as HTMLButtonElement;
    week.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Рассчитываем будущие остатки');
    expect(fixture.nativeElement.textContent).not.toContain('Прогноз на 2026-09-12');
    http.expectOne('/api/v1/forecast?horizon=week').flush({ ...FORECAST, horizon: 'week' });
  });

  it('requests a selected account and horizon', () => {
    flushInitial();
    http.expectOne('/api/v1/forecast?horizon=month').flush(FORECAST);
    fixture.detectChanges();

    const account = fixture.nativeElement.querySelector('select') as HTMLSelectElement;
    account.value = 'account-1';
    account.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/forecast' && request.params.get('account_id') === 'account-1',
      )
      .flush({ ...FORECAST, scope: 'account', account_id: 'account-1', account_name: 'Основной' });

    const quarter = [...fixture.nativeElement.querySelectorAll('.period-switcher button')].find(
      (button: HTMLButtonElement) => button.textContent.trim() === 'Квартал',
    ) as HTMLButtonElement;
    quarter.click();
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/forecast' &&
          request.params.get('horizon') === 'quarter' &&
          request.params.get('account_id') === 'account-1',
      )
      .flush({ ...FORECAST, horizon: 'quarter' });
  });

  function flushInitial(): void {
    fixture.detectChanges();
    http.expectOne('/api/v1/scheduling/materialize').flush({
      horizon_from: '2026-08-12',
      horizon_to: '2027-08-12',
      created: 0,
      updated: 0,
      cancelled: 0,
    });
    http
      .expectOne('/api/v1/accounts')
      .flush([{ id: 'account-1', name: 'Основной', archived: false }]);
    http.expectOne('/api/v1/settings').flush({ base_currency: 'RUB' });
  }
});
