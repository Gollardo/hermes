import { HttpClient, HttpParams } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormArray, NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/auth.service';

interface Fund {
  id: string;
  name: string;
  description: string | null;
  allocation_percentage: string;
  total_balance: string;
  archived: boolean;
  version: number;
}

interface Position {
  fund_id: string;
  fund_name: string;
  account_id: string;
  account_name: string;
  balance: string;
}

interface Coverage {
  account_id: string;
  account_name: string;
  physical_balance: string;
  reserved_balance: string;
  free_balance: string;
  archived: boolean;
}

interface Summary {
  funds: Fund[];
  positions: Position[];
  accounts: Coverage[];
  active_percentage: string;
  total_reserved: string;
  total_free: string;
}

interface AllocationItem {
  fund_id: string;
  amount: string;
}

interface Preview {
  account_id: string;
  amount: string;
  allocations: AllocationItem[];
  allocated_amount: string;
  unallocated_amount: string;
  free_before: string;
  free_after: string;
}

interface FundMovement {
  fund_id: string;
  fund_name: string;
  account_id: string;
  account_name: string;
  amount: string;
}

interface FundEvent {
  id: string;
  type: 'allocation' | 'redistribution' | 'expense' | 'transfer';
  occurred_on: string;
  description: string | null;
  movements: FundMovement[];
}

interface History {
  items: FundEvent[];
  page: number;
  page_size: number;
  total: number;
}

interface AllocationTotals {
  allocated: string;
  unallocated: string;
  freeAfter: string;
  valid: boolean;
}

@Component({
  selector: 'app-funds-page',
  imports: [ReactiveFormsModule],
  templateUrl: './funds.html',
  styleUrls: ['../directory.css', './funds.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FundsPage implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly builder = inject(NonNullableFormBuilder);
  private previewRequestId = 0;
  private historyRequestId = 0;

  protected readonly summary = signal<Summary | null>(null);
  protected readonly history = signal<FundEvent[]>([]);
  protected readonly historyPage = signal(1);
  protected readonly historyTotal = signal(0);
  protected readonly historyPageSize = 25;
  protected readonly preview = signal<Preview | null>(null);
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly editingId = signal<string | null>(null);
  protected readonly baseCurrency = signal('RUB');
  protected readonly Math = Math;

  protected readonly fundForm = this.builder.group({
    name: ['', [Validators.required, Validators.maxLength(120)]],
    description: ['', Validators.maxLength(2000)],
    percentage: [
      '0',
      [Validators.required, Validators.pattern(/^(?:100(?:\.0{1,4})?|\d{1,2}(?:\.\d{1,4})?)$/)],
    ],
  });
  protected readonly allocationForm = this.builder.group({
    accountId: ['', Validators.required],
    amount: ['', [Validators.required, Validators.pattern(/^\d{1,16}(?:\.\d{1,4})?$/)]],
    occurredOn: ['', Validators.required],
    description: ['', Validators.maxLength(2000)],
    allocations: this.builder.array([]),
  });
  protected readonly redistributionForm = this.builder.group({
    fundId: ['', Validators.required],
    sourceAccountId: ['', Validators.required],
    destinationAccountId: ['', Validators.required],
    amount: ['', [Validators.required, Validators.pattern(/^\d{1,16}(?:\.\d{1,4})?$/)]],
    occurredOn: ['', Validators.required],
    description: ['', Validators.maxLength(2000)],
  });

  protected get allocationControls(): FormArray {
    return this.allocationForm.controls.allocations;
  }

  ngOnInit(): void {
    this.loadDate();
    this.allocationForm.controls.accountId.valueChanges.subscribe(() => this.clearPreview());
    this.allocationForm.controls.amount.valueChanges.subscribe(() => this.clearPreview());
    this.load();
  }

  protected activeFunds(): Fund[] {
    return this.summary()?.funds.filter((fund) => !fund.archived) ?? [];
  }

  protected fundIsEmpty(fund: Fund): boolean {
    return moneyUnits(fund.total_balance) === 0n;
  }

  protected positionsFor(fundId: string): Position[] {
    return this.summary()?.positions.filter((position) => position.fund_id === fundId) ?? [];
  }

  protected positionBalance(fundId: string, accountId: string): string {
    return (
      this.summary()?.positions.find(
        (position) => position.fund_id === fundId && position.account_id === accountId,
      )?.balance ?? '0.0000'
    );
  }

  protected activeAccounts(): Coverage[] {
    return this.summary()?.accounts.filter((account) => !account.archived) ?? [];
  }

  protected sourceAccounts(): Coverage[] {
    const fundId = this.redistributionForm.controls.fundId.value;
    const eligibleIds = new Set(
      this.summary()
        ?.positions.filter(
          (position) => position.fund_id === fundId && (moneyUnits(position.balance) ?? 0n) > 0n,
        )
        .map((position) => position.account_id) ?? [],
    );
    return this.activeAccounts().filter((account) => eligibleIds.has(account.account_id));
  }

  protected remainingPercentage(): string {
    return formatUnits(
      1_000_000n - (percentageUnits(this.summary()?.active_percentage ?? '0') ?? 0n),
    );
  }

  protected availablePercentage(): string {
    const active = percentageUnits(this.summary()?.active_percentage ?? '0') ?? 0n;
    const existing = this.summary()?.funds.find((fund) => fund.id === this.editingId());
    if (existing?.archived) return '100.0000';
    const reusable = existing ? (percentageUnits(existing.allocation_percentage) ?? 0n) : 0n;
    return formatUnits(1_000_000n - active + reusable);
  }

  protected canSaveFund(): boolean {
    const value = percentageUnits(this.fundForm.controls.percentage.value);
    const available = percentageUnits(this.availablePercentage());
    return this.fundForm.valid && value !== null && available !== null && value <= available;
  }

  protected submitFund(): void {
    if (!this.canSaveFund()) {
      this.fundForm.markAllAsTouched();
      return;
    }
    this.error.set(null);
    this.saving.set(true);
    const value = this.fundForm.getRawValue();
    const id = this.editingId();
    const existing = this.summary()?.funds.find((fund) => fund.id === id);
    const body = {
      name: value.name,
      description: value.description || null,
      allocation_percentage: value.percentage,
      ...(existing ? { version: existing.version } : {}),
    };
    const request = id
      ? this.http.put<Fund>(`${environment.apiBaseUrl}/funds/${id}`, body)
      : this.http.post<Fund>(`${environment.apiBaseUrl}/funds`, body);
    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.cancelEdit();
        this.load();
      },
      error: (error: unknown) => this.failed(error, 'Не удалось сохранить фонд.'),
    });
  }

  protected edit(fund: Fund): void {
    this.editingId.set(fund.id);
    this.fundForm.setValue({
      name: fund.name,
      description: fund.description ?? '',
      percentage: fund.allocation_percentage,
    });
  }

  protected cancelEdit(): void {
    this.editingId.set(null);
    this.fundForm.reset({ name: '', description: '', percentage: '0' });
  }

  protected toggleArchive(fund: Fund): void {
    if (
      !fund.archived &&
      !window.confirm(`Архивировать фонд «${fund.name}»? Это возможно только при нулевом остатке.`)
    ) {
      return;
    }
    const action = fund.archived ? 'restore' : 'archive';
    this.http
      .post(`${environment.apiBaseUrl}/funds/${fund.id}/${action}`, { version: fund.version })
      .subscribe({
        next: () => this.load(),
        error: (error: unknown) =>
          this.error.set(apiErrorMessage(error, 'Не удалось изменить состояние фонда.')),
      });
  }

  protected requestPreview(): void {
    const { accountId, amount } = this.allocationForm.getRawValue();
    if (
      !accountId ||
      !amount ||
      this.allocationForm.controls.accountId.invalid ||
      this.allocationForm.controls.amount.invalid
    ) {
      this.allocationForm.controls.accountId.markAsTouched();
      this.allocationForm.controls.amount.markAsTouched();
      return;
    }
    const requestId = ++this.previewRequestId;
    this.http
      .post<Preview>(`${environment.apiBaseUrl}/funds/allocation-preview`, {
        account_id: accountId,
        amount,
      })
      .subscribe({
        next: (preview) => {
          const current = this.allocationForm.getRawValue();
          if (
            requestId !== this.previewRequestId ||
            current.accountId !== preview.account_id ||
            moneyUnits(current.amount) !== moneyUnits(preview.amount)
          ) {
            return;
          }
          this.preview.set(preview);
          this.allocationControls.clear();
          for (const item of preview.allocations) {
            this.allocationControls.push(
              this.builder.group({
                fundId: [item.fund_id, Validators.required],
                amount: [
                  item.amount,
                  [Validators.required, Validators.pattern(/^\d{1,16}(?:\.\d{1,4})?$/)],
                ],
              }),
            );
          }
        },
        error: (error: unknown) => {
          if (requestId !== this.previewRequestId) return;
          this.error.set(apiErrorMessage(error, 'Не удалось рассчитать распределение.'));
        },
      });
  }

  protected saveAllocation(): void {
    if (!this.canSaveAllocation()) {
      this.allocationForm.markAllAsTouched();
      return;
    }
    const value = this.allocationForm.getRawValue();
    this.saving.set(true);
    this.http
      .post(`${environment.apiBaseUrl}/funds/allocations`, {
        account_id: value.accountId,
        amount: value.amount,
        occurred_on: value.occurredOn,
        description: value.description || null,
        allocations: (value.allocations as { fundId: string; amount: string }[]).map((item) => ({
          fund_id: item.fundId,
          amount: item.amount,
        })),
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.preview.set(null);
          this.allocationControls.clear();
          this.allocationForm.patchValue({ amount: '', description: '' });
          this.load();
        },
        error: (error: unknown) => this.failed(error, 'Не удалось сохранить распределение.'),
      });
  }

  protected redistribute(): void {
    if (!this.canRedistribute()) {
      this.redistributionForm.markAllAsTouched();
      return;
    }
    const value = this.redistributionForm.getRawValue();
    if (value.sourceAccountId === value.destinationAccountId) {
      this.error.set('Выберите разные счета.');
      return;
    }
    this.saving.set(true);
    this.http
      .post(`${environment.apiBaseUrl}/funds/redistributions`, {
        fund_id: value.fundId,
        source_account_id: value.sourceAccountId,
        destination_account_id: value.destinationAccountId,
        amount: value.amount,
        occurred_on: value.occurredOn,
        description: value.description || null,
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.redistributionForm.patchValue({ amount: '', description: '' });
          this.load();
        },
        error: (error: unknown) => this.failed(error, 'Не удалось перераспределить фонд.'),
      });
  }

  protected fundName(id: string): string {
    return this.summary()?.funds.find((fund) => fund.id === id)?.name ?? 'Фонд';
  }

  protected allocationTotals(): AllocationTotals | null {
    const preview = this.preview();
    if (!preview) return null;
    const amounts = (
      this.allocationForm.controls.allocations.getRawValue() as {
        fundId: string;
        amount: string;
      }[]
    ).map((item) => moneyUnits(item.amount));
    const amount = moneyUnits(preview.amount);
    const freeBefore = moneyUnits(preview.free_before);
    if (
      amounts.some((value) => value === null || value < 0n) ||
      amount === null ||
      freeBefore === null
    ) {
      return null;
    }
    const allocated = (amounts as bigint[]).reduce((total, value) => total + value, 0n);
    return {
      allocated: formatUnits(allocated),
      unallocated: formatUnits(amount - allocated),
      freeAfter: formatUnits(freeBefore - allocated),
      valid: allocated > 0n && allocated <= amount && allocated <= freeBefore,
    };
  }

  protected canSaveAllocation(): boolean {
    const preview = this.preview();
    const totals = this.allocationTotals();
    const value = this.allocationForm.getRawValue();
    return Boolean(
      preview &&
      totals?.valid &&
      this.allocationForm.valid &&
      preview.account_id === value.accountId &&
      moneyUnits(preview.amount) === moneyUnits(value.amount),
    );
  }

  protected canRedistribute(): boolean {
    const value = this.redistributionForm.getRawValue();
    const amount = moneyUnits(value.amount);
    const position = this.summary()?.positions.find(
      (item) => item.fund_id === value.fundId && item.account_id === value.sourceAccountId,
    );
    const available = moneyUnits(position?.balance ?? '0');
    return Boolean(
      this.redistributionForm.valid &&
      value.sourceAccountId !== value.destinationAccountId &&
      amount !== null &&
      amount > 0n &&
      available !== null &&
      amount <= available,
    );
  }

  protected eventLabel(event: FundEvent): string {
    return {
      allocation: 'Распределение',
      redistribution: 'Перераспределение',
      expense: 'Расход из фонда',
      transfer: 'Перевод с фондом',
    }[event.type];
  }

  protected previousHistoryPage(): void {
    if (this.historyPage() > 1) {
      this.historyPage.update((page) => page - 1);
      this.loadHistory();
    }
  }

  protected nextHistoryPage(): void {
    if (this.historyPage() * this.historyPageSize < this.historyTotal()) {
      this.historyPage.update((page) => page + 1);
      this.loadHistory();
    }
  }

  private load(): void {
    this.loading.set(true);
    this.http.get<Summary>(`${environment.apiBaseUrl}/funds/summary`).subscribe({
      next: (summary) => {
        this.summary.set(summary);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить фонды.'));
      },
    });
    this.loadHistory();
  }

  private loadHistory(): void {
    const page = this.historyPage();
    const requestId = ++this.historyRequestId;
    const params = new HttpParams().set('page', page).set('page_size', this.historyPageSize);
    this.http.get<History>(`${environment.apiBaseUrl}/funds/history`, { params }).subscribe({
      next: (history) => {
        if (requestId !== this.historyRequestId || page !== this.historyPage()) return;
        this.history.set(history.items);
        this.historyTotal.set(history.total);
      },
      error: (error: unknown) => {
        if (requestId !== this.historyRequestId || page !== this.historyPage()) return;
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить историю фондов.'));
      },
    });
  }

  private loadDate(): void {
    this.http
      .get<{ timezone: string; base_currency: string }>(`${environment.apiBaseUrl}/settings`)
      .subscribe(({ timezone, base_currency: baseCurrency }) => {
        this.baseCurrency.set(baseCurrency);
        const parts = new Intl.DateTimeFormat('en-CA', {
          timeZone: timezone,
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
        }).formatToParts(new Date());
        const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
        const today = `${value['year']}-${value['month']}-${value['day']}`;
        this.allocationForm.patchValue({ occurredOn: today });
        this.redistributionForm.patchValue({ occurredOn: today });
      });
  }

  private failed(error: unknown, fallback: string): void {
    this.saving.set(false);
    this.error.set(apiErrorMessage(error, fallback));
  }

  private clearPreview(): void {
    this.previewRequestId += 1;
    if (!this.preview()) return;
    this.preview.set(null);
    this.allocationControls.clear();
  }
}

function moneyUnits(value: string): bigint | null {
  const match = /^(\d{1,16})(?:\.(\d{1,4}))?$/.exec(value.trim());
  if (!match) return null;
  return BigInt(match[1]) * 10_000n + BigInt((match[2] ?? '').padEnd(4, '0'));
}

function percentageUnits(value: string): bigint | null {
  const units = moneyUnits(value);
  return units !== null && units <= 1_000_000n ? units : null;
}

function formatUnits(units: bigint): string {
  const sign = units < 0n ? '-' : '';
  const absolute = units < 0n ? -units : units;
  return `${sign}${absolute / 10_000n}.${String(absolute % 10_000n).padStart(4, '0')}`;
}
