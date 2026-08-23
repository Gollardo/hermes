import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';

import { OperationsPage } from './operations';

interface TestOperation {
  id: string;
  type: 'income' | 'expense' | 'transfer' | 'balance_adjustment';
  occurred_on: string;
  amount: string;
  description: string | null;
  reason: string | null;
  category_id: string | null;
  category_name: string | null;
  account_id: string;
  destination_account_id: string | null;
  movements: { account_id: string; account_name: string; amount: string }[];
  fund_id: string | null;
  fund_amount: string | null;
  fund_movements: {
    fund_id: string;
    fund_name: string;
    account_id: string;
    account_name: string;
    amount: string;
  }[];
  version: number;
}

describe('OperationsPage', () => {
  let fixture: ComponentFixture<OperationsPage>;
  let http: HttpTestingController;
  let focusedId: string | null;
  let queryParams: Record<string, string>;

  beforeEach(async () => {
    localStorage.setItem('hermes-recent-accounts', JSON.stringify(['account-1', 'account-2']));
    localStorage.setItem('hermes-recent-categories-expense', JSON.stringify(['category-1']));
    focusedId = null;
    queryParams = {};
    await TestBed.configureTestingModule({
      imports: [OperationsPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useFactory: () => ({
            snapshot: {
              queryParamMap: {
                get: (key: string) => (key === 'focus' ? focusedId : (queryParams[key] ?? null)),
              },
            },
          }),
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(OperationsPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    http
      .match((request) => request.url === '/api/v1/scheduling/occurrences')
      .forEach((request) => request.flush({ items: [], page: 1, page_size: 367, total: 0 }));
    http.verify();
  });

  function flushInitial(options?: {
    accounts?: object[];
    categories?: object[];
    funds?: object[];
    positions?: object[];
    operations?: TestOperation[];
    total?: number;
    totalAmount?: string;
    timezone?: string;
    applicationToday?: string;
    defaultAccountId?: string | null;
    focusedOperation?: TestOperation;
    expectedJournalParams?: Record<string, string>;
    plans?: object[];
  }): void {
    fixture.detectChanges();
    if (focusedId) {
      const focusedOperation = options?.focusedOperation ?? options?.operations?.[0];
      expect(focusedOperation).toBeDefined();
      http.expectOne(`/api/v1/operations/${focusedId}`).flush(focusedOperation!);
    }
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: options?.timezone ?? 'UTC',
      application_today: options?.applicationToday ?? '2026-08-31',
      default_account_id: options?.defaultAccountId ?? null,
    });
    http
      .expectOne('/api/v1/accounts')
      .flush(
        options?.accounts ?? [
          { id: 'account-1', name: 'Main', balance: '100.0000', archived: false },
        ],
      );
    http.expectOne('/api/v1/categories').flush(
      options?.categories ?? [
        {
          id: 'category-1',
          name: 'Food',
          type: 'expense',
          archived: false,
          parent_id: null,
        },
      ],
    );
    http.expectOne('/api/v1/funds/summary').flush({
      funds: options?.funds ?? [],
      positions: options?.positions ?? [],
    });
    const journal = http.expectOne(
      (request) => request.url === '/api/v1/operations' && request.params.get('page') === '1',
    );
    for (const [key, value] of Object.entries(options?.expectedJournalParams ?? {})) {
      expect(journal.request.params.get(key)).toBe(value);
    }
    const operations = options?.operations ?? [];
    journal.flush({
      items: operations,
      page: 1,
      page_size: 25,
      total: options?.total ?? operations.length,
      total_amount: options?.totalAmount ?? '0.0000',
    });
    http
      .expectOne(
        (request) =>
          request.url === '/api/v1/scheduling/occurrences' &&
          request.params.getAll('source_kind')?.includes('one_off') === true,
      )
      .flush({
        items: options?.plans ?? [],
        page: 1,
        page_size: 367,
        total: options?.plans?.length ?? 0,
      });
    fixture.detectChanges();
    const add = fixture.nativeElement.querySelector('.create-menu-trigger') as HTMLButtonElement;
    add.click();
    fixture.detectChanges();
    const expense = fixture.nativeElement.querySelector(
      '[data-operation-type="expense"]',
    ) as HTMLButtonElement;
    expense.click();
    fixture.detectChanges();
  }

  function setValue(selector: string, value: string): void {
    const control = fixture.nativeElement.querySelector(selector) as HTMLInputElement;
    const combobox =
      control.closest('app-entity-combobox') ??
      (control.tagName === 'APP-ENTITY-COMBOBOX' ? control : null);
    if (combobox) {
      const input = combobox.querySelector('input') as HTMLInputElement;
      input.value = '';
      input.dispatchEvent(new Event('input'));
      input.dispatchEvent(new Event('focus'));
      fixture.detectChanges();
      (combobox.querySelector(`[data-option-id="${value}"]`) as HTMLButtonElement).click();
      fixture.detectChanges();
      return;
    }
    control.value = value;
    control.dispatchEvent(new Event('input'));
    control.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  it('starts without an unapproved type default and enables only a complete expense', () => {
    flushInitial();
    const submit = fixture.nativeElement.querySelector('.entry-panel button[type="submit"]');
    expect(submit.disabled).toBe(true);

    setValue('#operation-type', 'expense');
    setValue('#operation-category', 'category-1');
    setValue('#operation-amount', '12.34 + 0,66');
    setValue('#operation-account', 'account-1');
    expect(submit.disabled).toBe(false);
    fixture.nativeElement.querySelector('.entry-panel form').dispatchEvent(new Event('submit'));

    const request = http.expectOne('/api/v1/operations');
    expect(request.request.method).toBe('POST');
    expect(request.request.body.amount).toBe('13.00');
    expect(request.request.body.category_id).toBe('category-1');
    request.flush({});
    http.expectOne('/api/v1/accounts').flush([]);
    http.expectOne('/api/v1/categories').flush([]);
    http.expectOne('/api/v1/funds/summary').flush({ funds: [], positions: [] });
    http
      .expectOne((candidate) => candidate.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
  });

  it('shows editable one-off plans in the journal without including them in the actual total', () => {
    flushInitial({
      plans: [
        {
          id: 'plan-1',
          source_kind: 'one_off',
          scheduled_on: '2026-09-10',
          due_on: '2026-09-10',
          status: 'pending',
          type: 'expense',
          amount: '12.5000',
          description: 'Insurance',
          account_id: 'account-1',
          account_name: 'Main',
          destination_account_id: null,
          destination_account_name: null,
          category_id: 'category-1',
          category_name: 'Food',
          allocate_to_funds: false,
          version: 1,
        },
      ],
    });

    expect(fixture.nativeElement.textContent).toContain('Разовые планы');
    expect(fixture.nativeElement.textContent).toContain('10 сентября 2026');
    const plan = fixture.nativeElement.querySelector(
      '.planned-operation-row .row-main',
    ) as HTMLButtonElement;
    plan.click();
    http.expectOne('/api/v1/scheduling/occurrences/plan-1').flush({
      id: 'plan-1',
      source_kind: 'one_off',
      scheduled_on: '2026-09-10',
      due_on: '2026-09-10',
      status: 'pending',
      type: 'expense',
      amount: '12.5000',
      description: 'Insurance',
      account_id: 'account-1',
      destination_account_id: null,
      category_id: 'category-1',
      allocate_to_funds: false,
      version: 1,
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Редактировать разовый план');
  });

  it('cancels a one-off plan from its editor', () => {
    flushInitial({
      plans: [
        {
          id: 'plan-1',
          source_kind: 'one_off',
          scheduled_on: '2026-09-10',
          due_on: '2026-09-10',
          status: 'pending',
          type: 'expense',
          amount: '12.5000',
          description: 'Insurance',
          account_id: 'account-1',
          account_name: 'Main',
          destination_account_id: null,
          destination_account_name: null,
          category_id: 'category-1',
          category_name: 'Food',
          allocate_to_funds: false,
          version: 3,
        },
      ],
    });
    const plan = fixture.nativeElement.querySelector(
      '.planned-operation-row .row-main',
    ) as HTMLButtonElement;
    plan.click();
    http.expectOne('/api/v1/scheduling/occurrences/plan-1').flush({
      id: 'plan-1',
      source_kind: 'one_off',
      scheduled_on: '2026-09-10',
      due_on: '2026-09-10',
      status: 'pending',
      type: 'expense',
      amount: '12.5000',
      description: 'Insurance',
      account_id: 'account-1',
      destination_account_id: null,
      category_id: 'category-1',
      allocate_to_funds: false,
      version: 3,
    });
    fixture.detectChanges();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    (fixture.nativeElement.querySelector('.planned-operation-cancel') as HTMLButtonElement).click();
    const request = http.expectOne('/api/v1/scheduling/occurrences/plan-1/cancel');
    expect(request.request.body).toEqual({ version: 3 });
    request.flush({});
    http
      .expectOne((candidate) => candidate.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
    http
      .expectOne((candidate) => candidate.url === '/api/v1/scheduling/occurrences')
      .flush({ items: [], page: 1, page_size: 367, total: 0 });
  });

  it('sends a future date to one-off planning and explains the delayed balance effect', () => {
    flushInitial({ applicationToday: '2026-08-31' });
    setValue('#operation-type', 'expense');
    setValue('#operation-category', 'category-1');
    setValue('#operation-amount', '12,50');
    setValue('#operation-account', 'account-1');
    setValue('#operation-date', '2026-09-10');
    expect(fixture.nativeElement.textContent).toContain('Баланс изменится только после применения');
    expect(
      fixture.nativeElement.querySelector('.entry-panel button[type="submit"]').textContent,
    ).toContain('Запланировать');

    fixture.nativeElement.querySelector('.entry-panel form').dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/scheduling/one-off-plans');
    expect(request.request.body).toMatchObject({
      type: 'expense',
      scheduled_on: '2026-09-10',
      amount: '12.50',
      category_id: 'category-1',
    });
    request.flush({ scheduled_on: '2026-09-10' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(
      'Разовая операция запланирована на 10 сентября 2026.',
    );
    http.expectOne('/api/v1/accounts').flush([]);
    http.expectOne('/api/v1/categories').flush([]);
    http.expectOne('/api/v1/funds/summary').flush({ funds: [], positions: [] });
    http
      .expectOne((candidate) => candidate.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
  });

  it('keeps a one-off plan date when the settings response arrives after the plan', () => {
    queryParams = { plan: 'plan-1' };
    fixture.detectChanges();

    http.expectOne('/api/v1/scheduling/occurrences/plan-1').flush({
      id: 'plan-1',
      source_kind: 'one_off',
      rule_id: null,
      scheduled_on: '2026-09-10',
      due_on: '2026-09-10',
      status: 'pending',
      type: 'expense',
      amount: '12.5000',
      description: 'Insurance',
      account_id: 'account-1',
      destination_account_id: null,
      category_id: 'category-1',
      allocate_to_funds: false,
      version: 1,
    });
    http.expectOne('/api/v1/settings').flush({
      base_currency: 'RUB',
      timezone: 'UTC',
      application_today: '2026-08-31',
      default_account_id: null,
    });
    http
      .expectOne('/api/v1/accounts')
      .flush([{ id: 'account-1', name: 'Main', balance: '100.0000', archived: false }]);
    http.expectOne('/api/v1/categories').flush([
      {
        id: 'category-1',
        name: 'Food',
        type: 'expense',
        archived: false,
        parent_id: null,
      },
    ]);
    http.expectOne('/api/v1/funds/summary').flush({ funds: [], positions: [] });
    http
      .expectOne((request) => request.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
    fixture.detectChanges();

    expect((fixture.nativeElement.querySelector('#operation-date') as HTMLInputElement).value).toBe(
      '2026-09-10',
    );
  });

  it('prefills an active default account for a new expense', () => {
    flushInitial({ defaultAccountId: 'account-1' });

    const input = fixture.nativeElement.querySelector('#operation-account') as HTMLInputElement;
    expect(input.value).toBe('Main');
  });

  it('does not carry an automatic default account into a transfer', () => {
    flushInitial({ defaultAccountId: 'account-1' });
    expect(
      (fixture.nativeElement.querySelector('#operation-account') as HTMLInputElement).value,
    ).toBe('Main');

    setValue('#operation-type', 'transfer');

    expect(
      (fixture.nativeElement.querySelector('#operation-account') as HTMLInputElement).value,
    ).toBe('');
  });

  it('keeps filters collapsed by default and applies dashboard drill-down parameters', () => {
    queryParams = {
      occurred_from: '2026-08-01',
      occurred_to: '2026-08-31',
      type: 'expense',
      category_id: 'category-1',
    };
    flushInitial({
      expectedJournalParams: {
        occurred_from: '2026-08-01',
        occurred_to: '2026-08-31',
        type: 'expense',
        category_id: 'category-1',
      },
    });
    expect(fixture.nativeElement.querySelector('#operation-filters')).not.toBeNull();
    const chips = fixture.nativeElement.querySelector('.filter-chips') as HTMLElement;
    expect(chips.textContent).toContain('Food');

    (chips.querySelector('button') as HTMLButtonElement).click();
    const resetRequest = http.expectOne(
      (request) => request.url === '/api/v1/operations' && request.params.get('page') === '1',
    );
    expect(resetRequest.request.params.has('category_id')).toBe(false);
    expect(resetRequest.request.params.has('occurred_from')).toBe(false);
    resetRequest.flush({
      items: [],
      page: 1,
      page_size: 25,
      total: 0,
      total_amount: '0.0000',
    });
  });

  it('keeps filters collapsed when there is no active selection', () => {
    flushInitial();
    expect(fixture.nativeElement.querySelector('#operation-filters')).toBeNull();
  });

  it('opens the exact actual operation linked from the calendar', () => {
    const operation: TestOperation = {
      id: 'operation-1',
      type: 'expense',
      occurred_on: '2026-08-11',
      amount: '12.5000',
      description: 'Интернет',
      reason: null,
      category_id: 'category-1',
      category_name: 'Связь',
      account_id: 'account-1',
      destination_account_id: null,
      movements: [{ account_id: 'account-1', account_name: 'Main', amount: '-12.5000' }],
      fund_id: null,
      fund_amount: null,
      fund_movements: [],
      version: 1,
    };
    focusedId = operation.id;
    flushInitial({ operations: [], focusedOperation: operation });

    const panel = fixture.nativeElement.querySelector('.focused-operation') as HTMLElement;
    expect(panel.textContent).toContain('Связь с календарём');
    expect(panel.textContent).toContain('Интернет');
    expect(panel.textContent).toContain('-12,50 ₽');
  });

  it('posts an expense from the explicitly selected fund', () => {
    flushInitial({
      funds: [
        {
          id: 'fund-1',
          name: 'Reserve',
          total_balance: '30.0000',
          archived: false,
        },
      ],
      positions: [{ fund_id: 'fund-1', account_id: 'account-1', balance: '30.0000' }],
    });
    setValue('#operation-type', 'expense');
    setValue('#operation-category', 'category-1');
    setValue('#operation-amount', '12.0000');
    setValue('#operation-account', 'account-1');
    setValue('#operation-fund', 'fund-1');
    fixture.nativeElement.querySelector('.entry-panel form').dispatchEvent(new Event('submit'));

    const request = http.expectOne('/api/v1/operations');
    expect(request.request.body.fund_id).toBe('fund-1');
    expect(request.request.body.fund_amount).toBeNull();
    request.flush({});
    http.expectOne('/api/v1/accounts').flush([]);
    http.expectOne('/api/v1/categories').flush([]);
    http.expectOne('/api/v1/funds/summary').flush({ funds: [], positions: [] });
    http
      .expectOne((candidate) => candidate.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
  });

  it('offers a fund only when it has a position on the selected source account', () => {
    flushInitial({
      accounts: [
        { id: 'account-1', name: 'Main', balance: '100.0000', archived: false },
        { id: 'account-2', name: 'Savings', balance: '30.0000', archived: false },
      ],
      funds: [
        {
          id: 'fund-1',
          name: 'Reserve',
          total_balance: '30.0000',
          archived: false,
        },
      ],
      positions: [{ fund_id: 'fund-1', account_id: 'account-2', balance: '30.0000' }],
    });
    setValue('#operation-type', 'expense');
    setValue('#operation-account', 'account-1');
    expect(
      (fixture.nativeElement.querySelector('#operation-fund') as HTMLSelectElement).textContent,
    ).not.toContain('Reserve');

    setValue('#operation-account', 'account-2');
    expect(
      (fixture.nativeElement.querySelector('#operation-fund') as HTMLSelectElement).textContent,
    ).toContain('Reserve · доступно 30,00 ₽');
  });

  it('posts an exact adjustment delta from the expected balance', () => {
    flushInitial({
      accounts: [{ id: 'account-1', name: 'Main', balance: '100.2500', archived: false }],
    });
    setValue('#operation-type', 'balance_adjustment');
    setValue('#operation-account', 'account-1');
    setValue('#operation-reason', 'Reconciliation');
    setValue('#operation-amount', '-1');
    expect(
      (
        fixture.nativeElement.querySelector(
          '.entry-panel button[type="submit"]',
        ) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    setValue('#operation-amount', '80');
    fixture.nativeElement.querySelector('.entry-panel form').dispatchEvent(new Event('submit'));

    const request = http.expectOne('/api/v1/operations');
    expect(request.request.body.amount).toBe('-20.2500');
    expect(fixture.nativeElement.textContent).toContain('Изменение журнала: -20,25 ₽');
    request.flush({});
    http.expectOne('/api/v1/accounts').flush([]);
    http.expectOne('/api/v1/categories').flush([]);
    http.expectOne('/api/v1/funds/summary').flush({ funds: [], positions: [] });
    http
      .expectOne((candidate) => candidate.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
  });

  it('keeps the same ledger delta when an adjustment is opened and saved unchanged', () => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    const adjustment: TestOperation = {
      id: 'adjustment-1',
      type: 'balance_adjustment',
      occurred_on: '2026-08-02',
      amount: '20.0000',
      description: null,
      reason: 'Reconciliation',
      category_id: null,
      category_name: null,
      account_id: 'account-1',
      destination_account_id: null,
      movements: [{ account_id: 'account-1', account_name: 'Main', amount: '20.0000' }],
      fund_id: null,
      fund_amount: null,
      fund_movements: [],
      version: 1,
    };
    flushInitial({
      accounts: [{ id: 'account-1', name: 'Main', balance: '120.0000', archived: false }],
      operations: [adjustment],
      totalAmount: '20.0000',
    });
    fixture.nativeElement.querySelector('.row-main').click();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.row-actions .secondary').click();
    fixture.detectChanges();
    expect(
      (fixture.nativeElement.querySelector('#operation-amount') as HTMLInputElement).value,
    ).toBe('120,00');
    fixture.nativeElement.querySelector('.entry-panel form').dispatchEvent(new Event('submit'));
    const request = http.expectOne('/api/v1/operations/adjustment-1');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body.amount).toBe('20.0000');
    request.flush(adjustment);
    http.expectOne('/api/v1/accounts').flush([]);
    http.expectOne('/api/v1/categories').flush([]);
    http.expectOne('/api/v1/funds/summary').flush({ funds: [], positions: [] });
    http
      .expectOne((candidate) => candidate.url === '/api/v1/operations')
      .flush({ items: [], page: 1, page_size: 25, total: 0, total_amount: '0.0000' });
  });

  it('shows transfer direction and retains an archived account while editing', () => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    const transfer: TestOperation = {
      id: 'operation-1',
      type: 'transfer',
      occurred_on: '2026-08-02',
      amount: '25.0000',
      description: 'Reserve',
      reason: null,
      category_id: null,
      category_name: null,
      account_id: 'account-1',
      destination_account_id: 'account-2',
      movements: [
        { account_id: 'account-1', account_name: 'Main', amount: '-25.0000' },
        { account_id: 'account-2', account_name: 'Old savings', amount: '25.0000' },
      ],
      fund_id: null,
      fund_amount: null,
      fund_movements: [],
      version: 1,
    };
    flushInitial({
      accounts: [
        { id: 'account-1', name: 'Main', balance: '75.0000', archived: false },
        { id: 'account-2', name: 'Old savings', balance: '25.0000', archived: true },
      ],
      operations: [transfer],
    });
    expect(fixture.nativeElement.textContent).toContain('Main → Old savings');

    fixture.nativeElement.querySelector('.row-main').click();
    fixture.detectChanges();
    fixture.nativeElement.querySelector('.row-actions .secondary').click();
    fixture.detectChanges();
    const destinationInput = fixture.nativeElement.querySelector(
      '#destination-account',
    ) as HTMLInputElement;
    const destination = destinationInput.closest('app-entity-combobox') as HTMLElement;
    expect(destinationInput.value).toBe('Old savings');
    destinationInput.dispatchEvent(new Event('focus'));
    fixture.detectChanges();
    expect(destination.textContent).toContain('25,00 ₽ · в архиве');
  });

  it('uses application timezone for the default financial date', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-01T22:30:00Z'));
    flushInitial({ timezone: 'Europe/Moscow', applicationToday: '2026-08-02' });
    const date = fixture.nativeElement.querySelector('#operation-date') as HTMLInputElement;
    expect(date.value).toBe('2026-08-02');
  });

  it('shows filter context, full-selection total and keeps rows during pagination', () => {
    const expense: TestOperation = {
      id: 'operation-1',
      type: 'expense',
      occurred_on: '2026-08-02',
      amount: '10.0000',
      description: null,
      reason: null,
      category_id: 'category-1',
      category_name: 'Food',
      account_id: 'account-1',
      destination_account_id: null,
      movements: [{ account_id: 'account-1', account_name: 'Main', amount: '-10.0000' }],
      fund_id: null,
      fund_amount: null,
      fund_movements: [],
      version: 1,
    };
    flushInitial({ operations: [expense], total: 26, totalAmount: '-260.0000' });
    (fixture.nativeElement.querySelector('.filter-toggle') as HTMLButtonElement).click();
    fixture.detectChanges();
    setValue('.filters-panel select[formControlName="type"]', 'expense');
    fixture.nativeElement.querySelector('.filters-panel form').dispatchEvent(new Event('submit'));
    http
      .expectOne(
        (candidate) =>
          candidate.url === '/api/v1/operations' && candidate.params.get('type') === 'expense',
      )
      .flush({
        items: [expense],
        page: 1,
        page_size: 25,
        total: 26,
        total_amount: '-260.0000',
      });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.filter-chips').textContent).toContain('Расход');
    const selectionTotal = fixture.nativeElement.querySelector('.selection-total').textContent;
    expect(selectionTotal).toContain('По всей выборке');
    expect(selectionTotal).toContain('-260,00 ₽');

    const buttons = fixture.nativeElement.querySelectorAll('.pagination button');
    buttons[1].click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Food');
    expect(fixture.nativeElement.textContent).toContain('Обновляем выборку…');
    http
      .expectOne(
        (candidate) =>
          candidate.url === '/api/v1/operations' && candidate.params.get('page') === '2',
      )
      .flush({ items: [], page: 2, page_size: 25, total: 26, total_amount: '-260.0000' });
  });
});
