import { HttpClient, HttpParams } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/auth.service';
import { formatMoney, MoneyPipe } from '../../shared/money.pipe';

type OperationType = 'income' | 'expense' | 'transfer' | 'balance_adjustment';
type CategoryType = 'income' | 'expense';

interface Account {
  id: string;
  name: string;
  balance: string;
  archived: boolean;
}

interface Category {
  id: string;
  name: string;
  type: CategoryType;
  archived: boolean;
  parent_id: string | null;
}

interface Movement {
  account_id: string;
  account_name: string;
  amount: string;
}

interface Fund {
  id: string;
  name: string;
  total_balance: string;
  archived: boolean;
}

interface FundPosition {
  fund_id: string;
  account_id: string;
  balance: string;
}

interface FundSummary {
  funds: Fund[];
  positions: FundPosition[];
}

interface OperationFundMovement {
  fund_id: string;
  fund_name: string;
  account_id: string;
  account_name: string;
  amount: string;
}

interface Operation {
  id: string;
  type: OperationType;
  occurred_on: string;
  amount: string;
  description: string | null;
  reason: string | null;
  category_id: string | null;
  category_name: string | null;
  account_id: string;
  destination_account_id: string | null;
  movements: Movement[];
  fund_id: string | null;
  fund_amount: string | null;
  fund_movements: OperationFundMovement[];
  version: number;
}

interface OperationPage {
  items: Operation[];
  page: number;
  page_size: number;
  total: number;
  total_amount: string;
}

interface ApplicationSettings {
  base_currency: string;
  timezone: string;
}

@Component({
  selector: 'app-operations-page',
  imports: [ReactiveFormsModule, MoneyPipe],
  templateUrl: './operations.html',
  styleUrl: './operations.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OperationsPage implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly builder = inject(NonNullableFormBuilder);
  private readonly route = inject(ActivatedRoute, { optional: true });

  protected readonly operations = signal<Operation[]>([]);
  protected readonly focusedOperation = signal<Operation | null>(null);
  protected readonly Math = Math;
  protected readonly accounts = signal<Account[]>([]);
  protected readonly categories = signal<Category[]>([]);
  protected readonly funds = signal<Fund[]>([]);
  private readonly fundPositions = signal<FundPosition[]>([]);
  protected readonly total = signal(0);
  protected readonly totalAmount = signal('0.0000');
  protected readonly baseCurrency = signal('RUB');
  private readonly timezone = signal('UTC');
  private readonly settingsReady = signal(false);
  protected readonly page = signal(1);
  protected readonly pageSize = 25;
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly editingId = signal<string | null>(null);
  protected readonly expandedId = signal<string | null>(null);
  protected readonly formOpen = signal(false);

  protected readonly form = this.builder.group({
    type: this.builder.control<OperationType | ''>('', Validators.required),
    occurredOn: [this.today(), Validators.required],
    categoryId: [''],
    amount: ['', [Validators.required, Validators.pattern(/^-?\d{1,16}(?:\.\d{1,4})?$/)]],
    accountId: ['', Validators.required],
    destinationAccountId: [''],
    description: ['', Validators.maxLength(2000)],
    reason: ['', Validators.maxLength(2000)],
    fundId: [''],
    fundAmount: ['', Validators.pattern(/^\d{1,16}(?:\.\d{1,4})?$/)],
  });

  protected readonly filters = this.builder.group({
    occurredFrom: [''],
    occurredTo: [''],
    accountId: [''],
    type: this.builder.control<OperationType | ''>(''),
    categoryId: [''],
  });

  ngOnInit(): void {
    const focusedId = this.route?.snapshot.queryParamMap.get('focus');
    if (focusedId) this.loadFocusedOperation(focusedId);
    this.loadSettings();
    this.loadDirectories();
    this.load();
    if (this.route?.snapshot.queryParamMap.get('new') === '1') this.openCreate();
  }

  protected currentOperation(): Operation | undefined {
    return this.operations().find((item) => item.id === this.editingId());
  }

  protected activeAccounts(operation?: Operation): Account[] {
    return this.accounts().filter(
      (account) =>
        !account.archived || operation?.movements.some((m) => m.account_id === account.id),
    );
  }

  protected availableCategories(): Category[] {
    const type = this.form.controls.type.value;
    if (type !== 'income' && type !== 'expense') return [];
    const current = this.currentOperation();
    return this.categories().filter(
      (category) =>
        category.type === type && (!category.archived || category.id === current?.category_id),
    );
  }

  protected availableFunds(): Fund[] {
    const currentFundId = this.currentOperation()?.fund_id;
    const accountId = this.form.controls.accountId.value;
    return this.funds().filter(
      (fund) =>
        fund.id === currentFundId ||
        (!fund.archived && this.fundAvailableOnSource(fund.id, accountId) > 0n),
    );
  }

  protected fundPositionLabel(fund: Fund): string {
    return `${fund.name} · доступно ${formatMoney(
      formatMoneyUnits(this.fundAvailableOnSource(fund.id, this.form.controls.accountId.value)),
    )} ${this.baseCurrency()}${fund.archived ? ' · в архиве' : ''}`;
  }

  protected operationTypeLabel(type: OperationType): string {
    return {
      income: 'Доход',
      expense: 'Расход',
      transfer: 'Перевод',
      balance_adjustment: 'Корректировка',
    }[type];
  }

  protected categoryLabel(category: Category): string {
    const parent = category.parent_id
      ? this.categories().find((item) => item.id === category.parent_id)
      : null;
    const label = parent ? `${parent.name} → ${category.name}` : category.name;
    return category.archived ? `${label} · в архиве` : label;
  }

  protected accountLabel(account: Account): string {
    return `${account.name} · ${formatMoney(account.balance)}${account.archived ? ' · в архиве' : ''}`;
  }

  protected transferDirection(operation: Operation): string {
    if (operation.type !== 'transfer') {
      return operation.category_name || operation.movements[0]?.account_name || '—';
    }
    const source = operation.movements.find((movement) => moneyUnits(movement.amount)! < 0n);
    const destination = operation.movements.find((movement) => moneyUnits(movement.amount)! > 0n);
    return source && destination
      ? `${source.account_name} → ${destination.account_name}`
      : 'Направление недоступно';
  }

  protected signedAmount(operation: Operation): string {
    if (operation.type === 'income') return `+${operation.amount}`;
    if (operation.type === 'expense') return `-${operation.amount}`;
    return operation.amount;
  }

  protected adjustmentBaseBalance(): string | null {
    const accountId = this.form.controls.accountId.value;
    const account = this.accounts().find((item) => item.id === accountId);
    if (!account) return null;
    const existing = this.currentOperation();
    if (existing?.type !== 'balance_adjustment' || existing.account_id !== accountId) {
      return normalizeMoney(account.balance);
    }
    const oldMovement = existing.movements.find((movement) => movement.account_id === accountId);
    return subtractMoney(account.balance, oldMovement?.amount ?? '0');
  }

  protected adjustmentDelta(target = this.form.controls.amount.value): string | null {
    const base = this.adjustmentBaseBalance();
    return base === null ? null : subtractMoney(target, base);
  }

  protected canSubmit(): boolean {
    const value = this.form.getRawValue();
    const postingAmount =
      value.type === 'balance_adjustment' ? this.adjustmentDelta(value.amount) : value.amount;
    const expectedBalance = moneyUnits(value.amount);
    return (
      this.settingsReady() &&
      this.form.valid &&
      postingAmount !== null &&
      (value.type !== 'balance_adjustment' ||
        (expectedBalance !== null && expectedBalance >= 0n)) &&
      this.shapeIsValid(
        value.type,
        postingAmount,
        value.accountId,
        value.categoryId,
        value.destinationAccountId,
        value.reason,
        value.fundId,
        value.fundAmount,
        value.amount,
      ) &&
      this.fundSelectionIsValid(
        value.type,
        value.accountId,
        value.fundId,
        value.amount,
        value.fundAmount,
      )
    );
  }

  protected filterChips(): string[] {
    const value = this.filters.getRawValue();
    const chips: string[] = [];
    if (value.occurredFrom) chips.push(`с ${value.occurredFrom}`);
    if (value.occurredTo) chips.push(`по ${value.occurredTo}`);
    if (value.accountId) {
      chips.push(this.accounts().find((item) => item.id === value.accountId)?.name ?? 'Счёт');
    }
    if (value.type) chips.push(this.operationTypeLabel(value.type));
    if (value.categoryId) {
      const category = this.categories().find((item) => item.id === value.categoryId);
      chips.push(category ? this.categoryLabel(category) : 'Категория');
    }
    return chips;
  }

  protected submit(): void {
    this.error.set(null);
    const value = this.form.getRawValue();
    const postingAmount =
      value.type === 'balance_adjustment' ? this.adjustmentDelta(value.amount) : value.amount;
    if (!this.canSubmit() || postingAmount === null) {
      this.form.markAllAsTouched();
      this.error.set('Заполните обязательные поля выбранного типа операции.');
      return;
    }
    const body: Record<string, unknown> = {
      type: value.type,
      occurred_on: value.occurredOn,
      amount: postingAmount,
      account_id: value.accountId,
      destination_account_id: value.type === 'transfer' ? value.destinationAccountId : null,
      category_id: value.type === 'income' || value.type === 'expense' ? value.categoryId : null,
      description: value.description || null,
      reason: value.type === 'balance_adjustment' ? value.reason : null,
      fund_id: value.type === 'expense' || value.type === 'transfer' ? value.fundId || null : null,
      fund_amount: value.type === 'transfer' && value.fundId ? value.fundAmount || null : null,
    };
    const id = this.editingId();
    const existing = this.operations().find((item) => item.id === id);
    if (existing) body['version'] = existing.version;
    this.saving.set(true);
    const request = id
      ? this.http.put<Operation>(`${environment.apiBaseUrl}/operations/${id}`, body)
      : this.http.post<Operation>(`${environment.apiBaseUrl}/operations`, body);
    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.cancelEdit();
        this.load();
        this.loadDirectories();
      },
      error: (error: unknown) => {
        this.saving.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось сохранить операцию.'));
      },
    });
  }

  protected edit(operation: Operation): void {
    this.editingId.set(operation.id);
    this.form.setValue({
      type: operation.type,
      occurredOn: operation.occurred_on,
      categoryId: operation.category_id ?? '',
      amount:
        operation.type === 'balance_adjustment'
          ? (this.accounts().find((account) => account.id === operation.account_id)?.balance ?? '')
          : operation.amount,
      accountId: operation.account_id,
      destinationAccountId: operation.destination_account_id ?? '',
      description: operation.description ?? '',
      reason: operation.reason ?? '',
      fundId: operation.fund_id ?? '',
      fundAmount: operation.type === 'transfer' ? (operation.fund_amount ?? '') : '',
    });
    this.formOpen.set(true);
  }

  protected openCreate(): void {
    this.cancelEdit();
    this.formOpen.set(true);
  }

  protected cancelEdit(): void {
    this.editingId.set(null);
    this.form.reset({
      type: '',
      occurredOn: this.today(),
      categoryId: '',
      amount: '',
      accountId: '',
      destinationAccountId: '',
      description: '',
      reason: '',
      fundId: '',
      fundAmount: '',
    });
    this.formOpen.set(false);
  }

  protected remove(operation: Operation): void {
    if (
      !window.confirm(
        `Удалить операцию «${this.operationTypeLabel(operation.type)}»? Остатки будут пересчитаны.`,
      )
    )
      return;
    this.http
      .delete<void>(
        `${environment.apiBaseUrl}/operations/${operation.id}?version=${operation.version}`,
      )
      .subscribe({
        next: () => {
          this.load();
          this.loadDirectories();
        },
        error: (error: unknown) =>
          this.error.set(apiErrorMessage(error, 'Не удалось удалить операцию.')),
      });
  }

  protected toggleDetails(operation: Operation): void {
    this.expandedId.set(this.expandedId() === operation.id ? null : operation.id);
  }

  protected applyFilters(): void {
    this.page.set(1);
    this.load();
  }

  protected clearFilters(): void {
    this.filters.reset({
      occurredFrom: '',
      occurredTo: '',
      accountId: '',
      type: '',
      categoryId: '',
    });
    this.applyFilters();
  }

  protected previousPage(): void {
    if (this.page() > 1) {
      this.page.update((value) => value - 1);
      this.load();
    }
  }

  protected nextPage(): void {
    if (this.page() * this.pageSize < this.total()) {
      this.page.update((value) => value + 1);
      this.load();
    }
  }

  private shapeIsValid(
    type: OperationType | '',
    amount: string,
    accountId: string,
    categoryId: string,
    destinationAccountId: string,
    reason: string,
    fundId: string,
    fundAmount: string,
    physicalAmount: string,
  ): boolean {
    if (!type || !accountId) return false;
    if ((type === 'income' || type === 'expense') && !categoryId) return false;
    if (type === 'transfer' && (!destinationAccountId || destinationAccountId === accountId)) {
      return false;
    }
    if (type === 'balance_adjustment' && !reason.trim()) return false;
    if (type === 'transfer' && fundId) {
      const virtualUnits = moneyUnits(fundAmount);
      const physicalUnits = moneyUnits(physicalAmount);
      if (
        virtualUnits === null ||
        physicalUnits === null ||
        virtualUnits <= 0n ||
        virtualUnits > physicalUnits
      ) {
        return false;
      }
    }
    const units = moneyUnits(amount);
    if (units === null) return false;
    return type === 'balance_adjustment' ? units !== 0n : units > 0n;
  }

  private fundSelectionIsValid(
    type: OperationType | '',
    accountId: string,
    fundId: string,
    physicalAmount: string,
    fundAmount: string,
  ): boolean {
    if (!fundId || (type !== 'expense' && type !== 'transfer')) return true;
    const required = moneyUnits(type === 'expense' ? physicalAmount : fundAmount);
    return (
      required !== null &&
      required > 0n &&
      required <= this.fundAvailableOnSource(fundId, accountId)
    );
  }

  private fundAvailableOnSource(fundId: string, accountId: string): bigint {
    const current =
      moneyUnits(
        this.fundPositions().find(
          (position) => position.fund_id === fundId && position.account_id === accountId,
        )?.balance ?? '0',
      ) ?? 0n;
    const oldMovement = this.currentOperation()?.fund_movements.find(
      (movement) => movement.fund_id === fundId && movement.account_id === accountId,
    );
    return current - (moneyUnits(oldMovement?.amount ?? '0') ?? 0n);
  }

  private loadSettings(): void {
    this.http.get<ApplicationSettings>(`${environment.apiBaseUrl}/settings`).subscribe({
      next: (settings) => {
        this.baseCurrency.set(settings.base_currency);
        this.timezone.set(settings.timezone);
        this.settingsReady.set(true);
        if (!this.editingId() && this.form.controls.occurredOn.pristine) {
          this.form.controls.occurredOn.setValue(this.today());
          this.form.controls.occurredOn.markAsPristine();
        }
      },
      error: (error: unknown) =>
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить валюту и часовой пояс.')),
    });
  }

  private loadFocusedOperation(operationId: string): void {
    this.http.get<Operation>(`${environment.apiBaseUrl}/operations/${operationId}`).subscribe({
      next: (operation) => this.focusedOperation.set(operation),
      error: (error: unknown) =>
        this.error.set(apiErrorMessage(error, 'Не удалось открыть связанную операцию.')),
    });
  }

  private loadDirectories(): void {
    this.http.get<Account[]>(`${environment.apiBaseUrl}/accounts`).subscribe({
      next: (accounts) => this.accounts.set(accounts),
      error: (error: unknown) =>
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить счета.')),
    });
    this.http.get<Category[]>(`${environment.apiBaseUrl}/categories`).subscribe({
      next: (categories) => this.categories.set(categories),
      error: (error: unknown) =>
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить категории.')),
    });
    this.http.get<FundSummary>(`${environment.apiBaseUrl}/funds/summary`).subscribe({
      next: (summary) => {
        this.funds.set(summary.funds);
        this.fundPositions.set(summary.positions);
      },
      error: (error: unknown) =>
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить фонды.')),
    });
  }

  private load(): void {
    this.loading.set(true);
    const filter = this.filters.getRawValue();
    let params = new HttpParams().set('page', this.page()).set('page_size', this.pageSize);
    for (const [key, value] of Object.entries({
      occurred_from: filter.occurredFrom,
      occurred_to: filter.occurredTo,
      account_id: filter.accountId,
      type: filter.type,
      category_id: filter.categoryId,
    })) {
      if (value) params = params.set(key, value);
    }
    this.http.get<OperationPage>(`${environment.apiBaseUrl}/operations`, { params }).subscribe({
      next: (result) => {
        this.operations.set(result.items);
        this.total.set(result.total);
        this.totalAmount.set(result.total_amount);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить журнал.'));
      },
    });
  }

  private today(): string {
    return dateInTimezone(new Date(), this.timezone());
  }
}

function moneyUnits(value: string): bigint | null {
  const match = /^(-?)(\d{1,16})(?:\.(\d{1,4}))?$/.exec(value.trim());
  if (!match) return null;
  const fraction = (match[3] ?? '').padEnd(4, '0');
  const units = BigInt(match[2]) * 10_000n + BigInt(fraction || '0');
  return match[1] === '-' ? -units : units;
}

function formatMoneyUnits(units: bigint): string {
  const sign = units < 0n ? '-' : '';
  const absolute = units < 0n ? -units : units;
  const integer = absolute / 10_000n;
  const fraction = String(absolute % 10_000n).padStart(4, '0');
  return `${sign}${integer}.${fraction}`;
}

function normalizeMoney(value: string): string | null {
  const units = moneyUnits(value);
  return units === null ? null : formatMoneyUnits(units);
}

function subtractMoney(minuend: string, subtrahend: string): string | null {
  const left = moneyUnits(minuend);
  const right = moneyUnits(subtrahend);
  return left === null || right === null ? null : formatMoneyUnits(left - right);
}

function dateInTimezone(now: Date, timezone: string): string {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(now);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value['year']}-${value['month']}-${value['day']}`;
}
