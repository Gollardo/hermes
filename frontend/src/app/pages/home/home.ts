import { HttpClient, HttpParams } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin, switchMap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/auth.service';
import { MoneyPipe } from '../../shared/money.pipe';

interface Coverage {
  physical_balance: string;
}

interface FundSummary {
  accounts: Coverage[];
  total_reserved: string;
  total_free: string;
}

interface Forecast {
  from_on: string;
  through_on: string;
  starting_balance: string;
  ending_balance: string;
  minimum_balance: string;
  minimum_on: string;
  first_negative_on: string | null;
}

interface Operation {
  id: string;
  type: 'income' | 'expense' | 'transfer' | 'balance_adjustment';
  occurred_on: string;
  amount: string;
  description: string | null;
  reason: string | null;
  category_name: string | null;
}

interface OperationPage {
  items: Operation[];
}

interface Occurrence {
  id: string;
  due_on: string;
  overdue: boolean;
  type: 'income' | 'expense' | 'transfer';
  amount: string;
  description: string | null;
}

interface OccurrencePage {
  items: Occurrence[];
  total: number;
}

interface Materialization {
  horizon_from: string;
}

interface Settings {
  base_currency: string;
}

@Component({
  selector: 'app-home-page',
  imports: [RouterLink, MoneyPipe],
  templateUrl: './home.html',
  styleUrl: './home.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomePage implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly summary = signal<FundSummary | null>(null);
  protected readonly forecast = signal<Forecast | null>(null);
  protected readonly recentOperations = signal<Operation[]>([]);
  protected readonly attention = signal<Occurrence[]>([]);
  protected readonly attentionTotal = signal(0);
  protected readonly baseCurrency = signal('RUB');
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.http
      .post<Materialization>(`${environment.apiBaseUrl}/scheduling/materialize`, {})
      .pipe(
        switchMap((materialization) => {
          const attentionParams = new HttpParams()
            .set('page_size', '6')
            .set('due_to', materialization.horizon_from)
            .append('status', 'pending')
            .append('status', 'postponed');
          return forkJoin({
            summary: this.http.get<FundSummary>(`${environment.apiBaseUrl}/funds/summary`),
            forecast: this.http.get<Forecast>(`${environment.apiBaseUrl}/forecast`, {
              params: new HttpParams().set('horizon', 'month'),
            }),
            operations: this.http.get<OperationPage>(`${environment.apiBaseUrl}/operations`, {
              params: new HttpParams().set('page_size', '5'),
            }),
            attention: this.http.get<OccurrencePage>(
              `${environment.apiBaseUrl}/scheduling/occurrences`,
              { params: attentionParams },
            ),
            settings: this.http.get<Settings>(`${environment.apiBaseUrl}/settings`),
          });
        }),
      )
      .subscribe({
        next: ({ summary, forecast, operations, attention, settings }) => {
          this.summary.set(summary);
          this.forecast.set(forecast);
          this.recentOperations.set(operations.items);
          this.attention.set(attention.items);
          this.attentionTotal.set(attention.total);
          this.baseCurrency.set(settings.base_currency);
          this.loading.set(false);
        },
        error: (error: unknown) => {
          this.loading.set(false);
          this.error.set(apiErrorMessage(error, 'Не удалось собрать обзор.'));
        },
      });
  }

  protected physicalTotal(): string {
    const units = this.summary()?.accounts.reduce(
      (total, account) => total + (moneyUnits(account.physical_balance) ?? 0n),
      0n,
    );
    return formatUnits(units ?? 0n);
  }

  protected operationTitle(operation: Operation): string {
    return (
      operation.description ||
      operation.reason ||
      operation.category_name ||
      this.typeLabel(operation.type)
    );
  }

  protected typeLabel(type: Operation['type'] | Occurrence['type']): string {
    return {
      income: 'Доход',
      expense: 'Расход',
      transfer: 'Перевод',
      balance_adjustment: 'Корректировка',
    }[type];
  }

  protected signedOperation(operation: Operation): string {
    if (operation.type === 'income') return `+${operation.amount}`;
    if (operation.type === 'expense') return `-${operation.amount}`;
    return operation.amount;
  }
}

function moneyUnits(value: string): bigint | null {
  const match = /^(-?)(\d+)(?:\.(\d{1,4}))?$/.exec(value);
  if (!match) return null;
  const units = BigInt(match[2]) * 10_000n + BigInt((match[3] ?? '').padEnd(4, '0'));
  return match[1] ? -units : units;
}

function formatUnits(units: bigint): string {
  const sign = units < 0n ? '-' : '';
  const absolute = units < 0n ? -units : units;
  return `${sign}${absolute / 10_000n}.${String(absolute % 10_000n).padStart(4, '0')}`;
}
