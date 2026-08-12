import { HttpClient, HttpParams } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/auth.service';
import { MoneyPipe } from '../../shared/money.pipe';

type Horizon = 'week' | 'month' | 'quarter' | 'half_year' | 'year';
type OperationType = 'income' | 'expense' | 'transfer';

interface HorizonOption {
  value: Horizon;
  label: string;
}

interface Account {
  id: string;
  name: string;
  archived: boolean;
}

interface ForecastEvent {
  occurrence_id: string;
  due_on: string;
  type: OperationType;
  status: 'pending' | 'postponed';
  description: string | null;
  account_name: string;
  destination_account_name: string | null;
  amount: string;
  effect: string;
}

interface ForecastPoint {
  on: string;
  opening_balance: string;
  change: string;
  closing_balance: string;
  events: ForecastEvent[];
}

interface Forecast {
  scope: 'all' | 'account';
  account_id: string | null;
  account_name: string | null;
  horizon: Horizon;
  from_on: string;
  through_on: string;
  starting_balance: string;
  ending_balance: string;
  minimum_balance: string;
  minimum_on: string;
  first_negative_on: string | null;
  expected_income: string;
  expected_expense: string;
  overdue_excluded_count: number;
  points: ForecastPoint[];
}

interface Settings {
  base_currency: string;
}

interface PlotPoint extends ForecastPoint {
  x: number;
  y: number;
}

@Component({
  selector: 'app-forecast-page',
  imports: [FormsModule, RouterLink, MoneyPipe],
  templateUrl: './forecast.html',
  styleUrl: './forecast.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ForecastPage implements OnInit {
  private readonly http = inject(HttpClient);
  private requestId = 0;

  protected readonly accounts = signal<Account[]>([]);
  protected readonly horizons: readonly HorizonOption[] = [
    { value: 'week', label: 'Неделя' },
    { value: 'month', label: 'Месяц' },
    { value: 'quarter', label: 'Квартал' },
    { value: 'half_year', label: 'Полгода' },
    { value: 'year', label: 'Год' },
  ];
  protected readonly baseCurrency = signal('RUB');
  protected readonly forecast = signal<Forecast | null>(null);
  protected readonly selectedAccountId = signal('');
  protected readonly selectedHorizon = signal<Horizon>('month');
  protected readonly selectedPointIndex = signal(0);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly hasFutureEvents = computed(
    () => this.forecast()?.points.some((point) => point.events.length > 0) ?? false,
  );

  protected readonly selectedPoint = computed(() => {
    const value = this.forecast();
    if (!value) return null;
    return value.points[this.selectedPointIndex()] ?? value.points[0];
  });

  protected readonly plot = computed<PlotPoint[]>(() => {
    const points = this.forecast()?.points ?? [];
    if (!points.length) return [];
    const values = points.map((point) => Number(point.closing_balance));
    const low = Math.min(...values, 0);
    const high = Math.max(...values, 0);
    const span = high - low || 1;
    const from = isoDayNumber(this.forecast()!.from_on);
    const through = isoDayNumber(this.forecast()!.through_on);
    const days = through - from || 1;
    return points.map((point) => ({
      ...point,
      x: points.length === 1 ? 54 : 14 + ((isoDayNumber(point.on) - from) / days) * 82,
      y: 8 + ((high - Number(point.closing_balance)) / span) * 70,
    }));
  });

  protected readonly plotLine = computed(() =>
    this.plot()
      .map((point) => `${point.x},${point.y}`)
      .join(' '),
  );

  protected readonly zeroY = computed(() => {
    const values = (this.forecast()?.points ?? []).map((point) => Number(point.closing_balance));
    if (!values.length) return null;
    const low = Math.min(...values, 0);
    const high = Math.max(...values, 0);
    if (low === high) return null;
    return 8 + (high / (high - low)) * 70;
  });

  protected readonly chartMaximum = computed(() => this.chartExtreme('maximum'));
  protected readonly chartMinimum = computed(() => this.chartExtreme('minimum'));

  ngOnInit(): void {
    forkJoin({
      materialization: this.http.post<unknown>(
        `${environment.apiBaseUrl}/scheduling/materialize`,
        {},
      ),
      accounts: this.http.get<Account[]>(`${environment.apiBaseUrl}/accounts`),
      settings: this.http.get<Settings>(`${environment.apiBaseUrl}/settings`),
    }).subscribe({
      next: ({ accounts, settings }) => {
        this.accounts.set(accounts);
        this.baseCurrency.set(settings.base_currency);
        this.loadForecast();
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось подготовить прогноз.'));
      },
    });
  }

  protected changeAccount(value: string): void {
    this.selectedAccountId.set(value);
    this.loadForecast();
  }

  protected changeHorizon(value: Horizon): void {
    this.selectedHorizon.set(value);
    this.loadForecast();
  }

  protected selectPoint(index: number): void {
    this.selectedPointIndex.set(index);
  }

  protected accountLabel(account: Account): string {
    return `${account.name}${account.archived ? ' · в архиве' : ''}`;
  }

  protected typeLabel(type: OperationType): string {
    return { income: 'Доход', expense: 'Расход', transfer: 'Перевод' }[type];
  }

  protected eventTitle(event: ForecastEvent): string {
    return event.description?.trim() || this.typeLabel(event.type);
  }

  protected eventDirection(event: ForecastEvent): string {
    return event.destination_account_name
      ? `${event.account_name} → ${event.destination_account_name}`
      : event.account_name;
  }

  protected calendarQuery(event: ForecastEvent): { month: string; focus: string } {
    return { month: event.due_on.slice(0, 7), focus: event.occurrence_id };
  }

  protected signed(value: string): string {
    return !value.startsWith('-') && value !== '0' && !/^0(?:\.0+)?$/.test(value)
      ? `+${value}`
      : value;
  }

  protected isNegative(value: string): boolean {
    return value.startsWith('-') && !/^-0(?:\.0+)?$/.test(value);
  }

  private chartExtreme(kind: 'minimum' | 'maximum'): string {
    const values = this.forecast()?.points.map((point) => point.closing_balance) ?? [];
    if (!values.length) return '0';
    return values.reduce((selected, value) => {
      const comparison = Number(value) - Number(selected);
      return kind === 'minimum'
        ? comparison < 0
          ? value
          : selected
        : comparison > 0
          ? value
          : selected;
    });
  }

  private loadForecast(): void {
    const requestId = ++this.requestId;
    this.loading.set(true);
    this.error.set(null);
    this.forecast.set(null);
    this.selectedPointIndex.set(0);
    let params = new HttpParams().set('horizon', this.selectedHorizon());
    if (this.selectedAccountId()) params = params.set('account_id', this.selectedAccountId());
    this.http.get<Forecast>(`${environment.apiBaseUrl}/forecast`, { params }).subscribe({
      next: (value) => {
        if (requestId !== this.requestId) return;
        this.forecast.set(value);
        const firstEventIndex = value.points.findIndex((point) => point.events.length);
        this.selectedPointIndex.set(firstEventIndex >= 0 ? firstEventIndex : 0);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        if (requestId !== this.requestId) return;
        this.loading.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось рассчитать прогноз.'));
      },
    });
  }
}

function isoDayNumber(value: string): number {
  const [year, month, day] = value.split('-').map(Number);
  return Date.UTC(year, month - 1, day) / 86_400_000;
}
