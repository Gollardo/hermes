import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormGroup } from '@angular/forms';
import { ActivatedRoute, provideRouter } from '@angular/router';

import { SchedulingPage } from './scheduling';

const OCCURRENCE = {
  id: 'occurrence-1',
  rule_id: 'rule-1',
  scheduled_on: '2026-08-10',
  due_on: '2026-08-10',
  status: 'pending',
  manually_modified: false,
  series_shift_days: 0,
  preserve_from_series_shift: false,
  overdue: true,
  type: 'expense',
  amount: '12.5000',
  description: 'Интернет',
  account_id: 'account-1',
  account_name: 'Основной',
  destination_account_id: null,
  destination_account_name: null,
  category_id: 'category-1',
  category_name: 'Связь',
  allocate_to_funds: false,
  actual_operation_id: null,
  version: 1,
};

const RULE = {
  id: 'rule-1',
  type: 'expense',
  frequency: 'monthly',
  interval: 1,
  weekdays: null,
  start_on: '2026-08-10',
  end_on: null,
  amount: '12.5000',
  description: 'Интернет',
  account_id: 'account-1',
  account_name: 'Основной',
  destination_account_id: null,
  destination_account_name: null,
  category_id: 'category-1',
  category_name: 'Связь',
  allocate_to_funds: false,
  shift_future_on_postpone: true,
  series_shift_days: 0,
  active: true,
  version: 3,
};

interface SchedulingHarness {
  accounts: { set(value: object[]): void };
  categories: { set(value: object[]): void };
  ruleForm: FormGroup;
  canSaveRule(): boolean;
  submitRule(): void;
}

describe('SchedulingPage recurrence editor', () => {
  let http: HttpTestingController;
  let fixture: ComponentFixture<SchedulingPage>;
  let routeParams: Record<string, string>;

  beforeEach(async () => {
    localStorage.setItem('hermes-recent-accounts', JSON.stringify(['account-1']));
    localStorage.setItem('hermes-recent-categories-income', JSON.stringify(['category-income']));
    routeParams = {};
    await TestBed.configureTestingModule({
      imports: [SchedulingPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: { get: (key: string) => routeParams[key] ?? null },
            },
          },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(SchedulingPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('submits selected weekdays, interval and a normalized decimal amount', () => {
    const page = fixture.componentInstance as unknown as SchedulingHarness;
    page.accounts.set([{ id: 'account-1', name: 'Main', archived: false }]);
    page.categories.set([
      {
        id: 'category-1',
        name: 'Salary',
        type: 'income',
        parent_id: null,
        archived: false,
      },
    ]);
    page.ruleForm.setValue({
      type: 'income',
      frequency: 'weekly',
      interval: 2,
      monday: true,
      tuesday: false,
      wednesday: false,
      thursday: false,
      friday: true,
      saturday: false,
      sunday: false,
      startOn: '2026-08-17',
      endOn: '2026-12-31',
      amount: '10,5 + 2.25',
      description: '',
      accountId: 'account-1',
      destinationAccountId: '',
      categoryId: 'category-1',
      allocateToFunds: false,
      shiftFutureOnPostpone: false,
    });
    expect(page.canSaveRule()).toBe(true);

    page.submitRule();
    const request = http.expectOne('/api/v1/scheduling/rules');
    expect(request.request.body.interval).toBe(2);
    expect(request.request.body.weekdays).toEqual([1, 5]);
    expect(request.request.body.amount).toBe('12.75');
    request.flush({});
    http.expectOne('/api/v1/scheduling/rules').flush([]);
  });

  it('rejects a weekly rule without days and a zero amount', () => {
    const page = fixture.componentInstance as unknown as SchedulingHarness;
    page.ruleForm.patchValue({
      type: 'income',
      frequency: 'weekly',
      interval: 1,
      startOn: '2026-08-17',
      amount: '0',
      accountId: 'account-1',
      categoryId: 'category-1',
    });
    expect(page.canSaveRule()).toBe(false);
  });

  it('renders a monthly calendar and marks an overdue occurrence in text', () => {
    flushInitial([OCCURRENCE]);
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('август 2026');
    expect(text).toContain('Интернет');
    expect(text).toContain('Просрочено');
    expect(fixture.nativeElement.querySelector('.upcoming-item.overdue')).not.toBeNull();
  });

  it('blocks a missing monthly date policy and submits an exact rule snapshot', () => {
    flushInitial([]);
    clickButton('Добавить правило');
    setValue('.form-panel select[formControlName="type"]', 'income');
    setValue('.form-panel input[formControlName="startOn"]', '2026-08-29');
    setValue('.form-panel input[formControlName="amount"]', '100.2500');
    setValue('.form-panel app-entity-combobox[formControlName="accountId"]', 'account-1');
    setValue('.form-panel app-entity-combobox[formControlName="categoryId"]', 'category-income');
    const submit = fixture.nativeElement.querySelector(
      '.form-panel button[type="submit"]',
    ) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);

    setValue('.form-panel input[formControlName="startOn"]', '2026-08-28');
    expect(submit.disabled).toBe(false);
    fixture.nativeElement.querySelector('.form-panel form').dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/scheduling/rules');
    expect(request.request.body).toMatchObject({
      type: 'income',
      frequency: 'monthly',
      interval: 1,
      weekdays: null,
      start_on: '2026-08-28',
      amount: '100.2500',
      account_id: 'account-1',
      category_id: 'category-income',
    });
    request.flush({});
    http.expectOne('/api/v1/scheduling/rules').flush([]);
    flushOccurrenceRequests([]);
  });

  it('persists the transfer-only fund allocation choice', () => {
    flushInitial([]);
    clickButton('Добавить правило');
    setValue('.form-panel select[formControlName="type"]', 'transfer');
    setValue('.form-panel input[formControlName="startOn"]', '2026-08-12');
    setValue('.form-panel input[formControlName="amount"]', '100');
    setValue('.form-panel app-entity-combobox[formControlName="accountId"]', 'account-1');
    const destination = fixture.nativeElement.querySelector(
      '.form-panel app-entity-combobox[formControlName="destinationAccountId"]',
    ) as HTMLElement;
    const destinationSearch = destination.querySelector('input') as HTMLInputElement;
    destinationSearch.value = 'Накоп';
    destinationSearch.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    (destination.querySelector('[data-option-id="account-2"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    const allocation = fixture.nativeElement.querySelector(
      '.form-panel input[formControlName="allocateToFunds"]',
    ) as HTMLInputElement;
    allocation.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(
      'Будут использованы проценты активных фондов на момент подтверждения операции.',
    );

    fixture.nativeElement.querySelector('.form-panel form').dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/scheduling/rules');
    expect(request.request.body).toMatchObject({
      type: 'transfer',
      account_id: 'account-1',
      destination_account_id: 'account-2',
      category_id: null,
      allocate_to_funds: true,
    });
    request.flush({});
    http.expectOne('/api/v1/scheduling/rules').flush([]);
    flushOccurrenceRequests([]);
  });

  it('quick confirmation posts the occurrence version and refreshes both views', () => {
    flushInitial([OCCURRENCE]);
    const confirm = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent.trim() === 'Подтвердить',
    ) as HTMLButtonElement;
    confirm.click();
    const request = http.expectOne('/api/v1/scheduling/occurrences/occurrence-1/confirm');
    expect(request.request.body).toEqual({ version: 1, amount: '12.5000' });
    request.flush({ ...OCCURRENCE, status: 'confirmed', actual_operation_id: 'operation-1' });
    flushOccurrenceRequests([]);
  });

  it('allows correcting only the confirmed occurrence amount', () => {
    flushInitial([OCCURRENCE]);
    setValue('#confirm-amount-occurrence-1', '12000 + 345,75');
    const amountInput = fixture.nativeElement.querySelector(
      '#confirm-amount-occurrence-1',
    ) as HTMLInputElement;
    amountInput.dispatchEvent(new Event('blur'));
    fixture.detectChanges();
    expect(amountInput.value).toBe('12 345,75');
    clickButton('Подтвердить');
    const request = http.expectOne('/api/v1/scheduling/occurrences/occurrence-1/confirm');
    expect(request.request.body).toEqual({ version: 1, amount: '12345.75' });
    request.flush({ ...OCCURRENCE, amount: '12345.7500', status: 'confirmed' });
    flushOccurrenceRequests([]);
  });

  it('explains and submits an enabled series shift with the rule version', () => {
    flushInitial([OCCURRENCE], [RULE]);
    setValue('#postpone-occurrence-1', '2026-08-14');
    expect(fixture.nativeElement.textContent).toContain(
      'следующие нетронутые события сдвинутся на +4 дн.',
    );
    clickButton('Перенести серию');
    const request = http.expectOne('/api/v1/scheduling/occurrences/occurrence-1/postpone');
    expect(request.request.body).toEqual({
      version: 1,
      due_on: '2026-08-14',
      rule_version: 3,
    });
    request.flush({
      ...OCCURRENCE,
      due_on: '2026-08-14',
      status: 'postponed',
      manually_modified: true,
      series_shift_days: 4,
      version: 2,
      series_shift_applied: true,
      shift_days: 4,
      shifted_occurrences: 2,
      preserved_occurrences: 1,
      rule_version: 4,
    });
    http
      .expectOne('/api/v1/scheduling/rules')
      .flush([{ ...RULE, series_shift_days: 4, version: 4 }]);
    flushOccurrenceRequests([]);
    expect(fixture.nativeElement.textContent).toContain('Обновлено следующих событий: 2');
    expect(fixture.nativeElement.textContent).toContain('сохранено исключений: 1');
  });

  it('does not couple a single-occurrence postpone to the rule version', () => {
    flushInitial([OCCURRENCE], [{ ...RULE, shift_future_on_postpone: false }]);
    setValue('#postpone-occurrence-1', '2026-08-14');
    clickButton('Перенести');
    const request = http.expectOne('/api/v1/scheduling/occurrences/occurrence-1/postpone');
    expect(request.request.body).toEqual({ version: 1, due_on: '2026-08-14' });
    request.flush({
      ...OCCURRENCE,
      due_on: '2026-08-14',
      status: 'postponed',
      manually_modified: true,
      series_shift_days: 4,
      version: 2,
      series_shift_applied: false,
      shift_days: 4,
      shifted_occurrences: 0,
      preserved_occurrences: 0,
      rule_version: 3,
    });
    http
      .expectOne('/api/v1/scheduling/rules')
      .flush([{ ...RULE, shift_future_on_postpone: false }]);
    flushOccurrenceRequests([]);
  });

  it('labels an automatically cancelled occurrence preserved by a series shift', () => {
    flushInitial([
      {
        ...OCCURRENCE,
        status: 'cancelled',
        overdue: false,
        preserve_from_series_shift: true,
      },
    ]);

    expect(fixture.nativeElement.textContent).toContain('Сохранено при сдвиге серии');
  });

  it('makes automatic fund allocation explicit at confirmation', () => {
    flushInitial([
      {
        ...OCCURRENCE,
        type: 'transfer',
        category_id: null,
        category_name: null,
        destination_account_id: 'account-2',
        destination_account_name: 'Накопительный',
        allocate_to_funds: true,
      },
    ]);

    expect(fixture.nativeElement.textContent).toContain(
      'После перевода сумма распределится по процентам активных фондов.',
    );
    const action = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent.trim() === 'Перевести и распределить',
    );
    expect(action).toBeDefined();
  });

  it('loads every calendar page and reports the limited upcoming total honestly', () => {
    fixture.detectChanges();
    flushMaterializationAndReferences();
    const firstPage = http.expectOne(
      (request) =>
        request.url === '/api/v1/scheduling/occurrences' &&
        request.params.has('due_from') &&
        request.params.get('page') === '1',
    );
    firstPage.flush({ items: [OCCURRENCE], page: 1, page_size: 1, total: 2 });
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' &&
          request.params.has('due_from') &&
          request.params.get('page') === '2',
      )
      .flush({
        items: [{ ...OCCURRENCE, id: 'occurrence-2', due_on: '2026-08-12' }],
        page: 2,
        page_size: 1,
        total: 2,
      });
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' &&
          request.params.getAll('status')?.length === 2,
      )
      .flush({ items: [OCCURRENCE], page: 1, page_size: 12, total: 31 });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('.calendar-event')).toHaveLength(2);
    expect(fixture.nativeElement.textContent).toContain('1 из 31');
    expect(fixture.nativeElement.textContent).toContain('Показаны первые 1 событий');
  });

  it('links a confirmed calendar snapshot to its exact actual operation', () => {
    flushInitial([
      { ...OCCURRENCE, status: 'confirmed', overdue: false, actual_operation_id: 'operation-1' },
    ]);
    const link = fixture.nativeElement.querySelector('.confirmed-link') as HTMLAnchorElement;
    expect(link.getAttribute('href')).toContain('/operations?focus=operation-1');
    expect(link.textContent).toContain('Подтверждено');
  });

  it('opens the month and exact occurrence requested by forecast drill-down', () => {
    routeParams = { month: '2026-09', focus: 'occurrence-1' };
    fixture.detectChanges();
    flushMaterializationAndReferences();
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' &&
          request.params.get('due_from') === '2026-08-31' &&
          request.params.get('due_to') === '2026-10-11',
      )
      .flush({
        items: [{ ...OCCURRENCE, due_on: '2026-09-10', overdue: false }],
        page: 1,
        page_size: 367,
        total: 1,
      });
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' &&
          request.params.getAll('status')?.length === 2,
      )
      .flush({ items: [], page: 1, page_size: 12, total: 0 });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('сентябрь 2026');
    expect(fixture.nativeElement.querySelector('#occurrence-occurrence-1')).not.toBeNull();
  });

  it('explains an archived reference and blocks saving an active rule with it', () => {
    fixture.detectChanges();
    http.expectOne('/api/v1/scheduling/materialize').flush({
      horizon_from: '2026-08-11',
      horizon_to: '2027-08-11',
      created: 0,
      updated: 0,
      cancelled: 0,
    });
    http
      .expectOne('/api/v1/accounts')
      .flush([{ id: 'account-1', name: 'Основной', archived: true }]);
    http
      .expectOne('/api/v1/categories')
      .flush([{ id: 'category-1', name: 'Связь', type: 'expense', archived: false }]);
    http.expectOne('/api/v1/settings').flush({ base_currency: 'RUB' });
    http.expectOne('/api/v1/scheduling/rules').flush([
      {
        id: 'rule-1',
        type: 'expense',
        frequency: 'monthly',
        interval: 1,
        weekdays: null,
        start_on: '2026-08-11',
        end_on: null,
        amount: '12.5000',
        description: 'Интернет',
        account_id: 'account-1',
        account_name: 'Основной',
        destination_account_id: null,
        destination_account_name: null,
        category_id: 'category-1',
        category_name: 'Связь',
        active: true,
        version: 1,
      },
    ]);
    flushOccurrenceRequests([]);
    clickButton('Изменить');
    const selectedAccount = fixture.nativeElement.querySelector(
      '.form-panel app-entity-combobox[formControlName="accountId"] input',
    ) as HTMLInputElement;
    const submit = fixture.nativeElement.querySelector(
      '.form-panel button[type="submit"]',
    ) as HTMLButtonElement;
    expect(selectedAccount.value).toBe('Основной');
    selectedAccount.dispatchEvent(new Event('focus'));
    fixture.detectChanges();
    expect(
      (
        fixture.nativeElement.querySelector(
          '.form-panel [data-option-id="account-1"]',
        ) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(submit.disabled).toBe(true);
    expect(fixture.nativeElement.textContent).toContain(
      'Для активного правила выберите действующие счёт и категорию',
    );
  });

  function flushInitial(occurrences: object[], rules: object[] = []): void {
    fixture.detectChanges();
    flushMaterializationAndReferences(rules);
    flushOccurrenceRequests(occurrences);
  }

  function flushMaterializationAndReferences(rules: object[] = []): void {
    http.expectOne('/api/v1/scheduling/materialize').flush({
      horizon_from: '2026-08-11',
      horizon_to: '2027-08-11',
      created: 0,
      updated: 0,
      cancelled: 0,
    });
    http.expectOne('/api/v1/accounts').flush([
      { id: 'account-1', name: 'Основной', archived: false },
      { id: 'account-2', name: 'Накопительный', archived: false },
    ]);
    http.expectOne('/api/v1/categories').flush([
      {
        id: 'category-1',
        name: 'Связь',
        type: 'expense',
        parent_id: null,
        archived: false,
      },
      {
        id: 'category-income',
        name: 'Зарплата',
        type: 'income',
        parent_id: null,
        archived: false,
      },
    ]);
    http.expectOne('/api/v1/settings').flush({ base_currency: 'RUB' });
    http.expectOne('/api/v1/scheduling/rules').flush(rules);
  }

  function flushOccurrenceRequests(occurrences: object[]): void {
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' && request.params.has('due_from'),
      )
      .flush({ items: occurrences, page: 1, page_size: 367, total: occurrences.length });
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' &&
          request.params.getAll('status')?.length === 2,
      )
      .flush({ items: occurrences, page: 1, page_size: 12, total: occurrences.length });
    fixture.detectChanges();
  }

  function setValue(selector: string, value: string): void {
    const control = fixture.nativeElement.querySelector(selector) as HTMLInputElement;
    if (control.tagName === 'APP-ENTITY-COMBOBOX') {
      const input = control.querySelector('input') as HTMLInputElement;
      input.value = '';
      input.dispatchEvent(new Event('input'));
      input.dispatchEvent(new Event('focus'));
      fixture.detectChanges();
      (control.querySelector(`[data-option-id="${value}"]`) as HTMLButtonElement).click();
      fixture.detectChanges();
      return;
    }
    control.value = value;
    control.dispatchEvent(new Event('input'));
    control.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  function clickButton(label: string): void {
    const button = [...fixture.nativeElement.querySelectorAll('button')].find(
      (item: HTMLButtonElement) => item.textContent.trim() === label,
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();
  }
});
