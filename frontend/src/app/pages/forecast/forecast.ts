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
import { DateTextPipe, formatTextDate } from '../../shared/date-text.pipe';
import { currencySymbol } from '../../shared/money.pipe';
import { EntityCombobox, EntityOption } from '../../shared/entity-combobox';

type Horizon = 'week' | 'month' | 'quarter' | 'half_year' | 'year';
type OperationType = 'income' | 'expense' | 'transfer';
const PLOT_TOP = 18;
const PLOT_HEIGHT = 60;
const TOOLTIP_BELOW_THRESHOLD = 30;

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
  period_from: string;
  on: string;
  opening_balance: string;
  change: string;
  closing_balance: string;
  events: ForecastEvent[];
}

interface Forecast {
  balance_mode: 'free' | 'total';
  scope: 'all' | 'account';
  account_id: string | null;
  account_name: string | null;
  horizon: Horizon;
  granularity: 'day' | 'month';
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

interface PlotScale {
  low: number;
  high: number;
}

interface AxisTick {
  y: number;
  value: string;
}

interface DateTick {
  x: number;
  label: string;
}

interface TrendLine {
  points: string;
  changePerPeriod: string;
}

@Component({
  selector: 'app-forecast-page',
  imports: [FormsModule, RouterLink, MoneyPipe, DateTextPipe, EntityCombobox],
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
  protected readonly balanceMode = signal<'free' | 'total'>('free');
  protected readonly selectedPointIndex = signal(0);
  protected readonly hoveredPointIndex = signal<number | null>(null);
  protected readonly trendEnabled = signal(false);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly hasFutureEvents = computed(
    () => this.forecast()?.points.some((point) => point.events.length > 0) ?? false,
  );

  protected accountOptions(): EntityOption[] {
    return this.accounts().map((account) => ({
      id: account.id,
      label: account.name,
      detail: account.archived ? 'В архиве' : undefined,
    }));
  }

  protected readonly selectedPoint = computed(() => {
    const value = this.forecast();
    if (!value) return null;
    return value.points[this.selectedPointIndex()] ?? value.points[0];
  });

  protected readonly hoveredPoint = computed(() => {
    const index = this.hoveredPointIndex();
    return index === null ? null : (this.plot()[index] ?? null);
  });

  protected readonly chartScale = computed<PlotScale>(() => {
    const values = (this.forecast()?.points ?? []).map((point) => Number(point.closing_balance));
    if (!values.length) return { low: 0, high: 1 };
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    if (minimum === maximum) {
      const padding = Math.max(Math.abs(minimum) * 0.05, 1);
      return { low: minimum - padding, high: maximum + padding };
    }
    const padding = (maximum - minimum) * 0.08;
    return { low: minimum - padding, high: maximum + padding };
  });

  protected readonly plot = computed<PlotPoint[]>(() => {
    const points = this.forecast()?.points ?? [];
    if (!points.length) return [];
    const scale = this.chartScale();
    const from = isoDayNumber(this.forecast()!.from_on);
    const through = isoDayNumber(this.forecast()!.through_on);
    const days = through - from || 1;
    return points.map((point) => ({
      ...point,
      x: points.length === 1 ? 54 : 14 + ((isoDayNumber(point.on) - from) / days) * 82,
      y: plotY(Number(point.closing_balance), scale),
    }));
  });

  protected readonly plotLine = computed(() =>
    this.plot()
      .map((point) => `${point.x},${point.y}`)
      .join(' '),
  );

  protected readonly zeroY = computed(() => {
    const scale = this.chartScale();
    return scale.low <= 0 && scale.high >= 0 ? plotY(0, scale) : null;
  });

  protected readonly yTicks = computed<AxisTick[]>(() => {
    const scale = this.chartScale();
    return Array.from({ length: 5 }, (_, index) => {
      const value = scale.high - ((scale.high - scale.low) * index) / 4;
      return { y: plotY(value, scale), value: approximateMoney(value) };
    });
  });

  protected readonly dateTicks = computed<DateTick[]>(() => {
    const points = this.plot();
    if (!points.length) return [];
    const count = Math.min(7, points.length);
    return uniqueIndexes(count, points.length).map((index) => ({
      x: points[index].x,
      label: formatTextDate(points[index].on),
    }));
  });

  protected readonly chartMinWidth = computed(() => {
    const count = this.forecast()?.points.length ?? 0;
    return this.forecast()?.granularity === 'day' ? Math.max(64, count * 0.65) : 64;
  });

  protected readonly trendLine = computed<TrendLine | null>(() => {
    const points = this.plot();
    if (points.length < 2) return null;
    const values = points.map((point) => Number(point.closing_balance));
    const meanIndex = (points.length - 1) / 2;
    const meanValue = values.reduce((total, value) => total + value, 0) / values.length;
    const denominator = values.reduce(
      (total, _value, index) => total + (index - meanIndex) ** 2,
      0,
    );
    const slope =
      values.reduce((total, value, index) => total + (index - meanIndex) * (value - meanValue), 0) /
      denominator;
    const intercept = meanValue - slope * meanIndex;
    const ending = intercept + slope * (points.length - 1);
    return {
      points: `${points[0].x},${plotY(intercept, this.chartScale())} ${points.at(-1)!.x},${plotY(ending, this.chartScale())}`,
      changePerPeriod: approximateMoney(slope),
    };
  });

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
        this.baseCurrency.set(currencySymbol(settings.base_currency));
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

  protected showPoint(index: number): void {
    this.hoveredPointIndex.set(index);
  }

  protected hidePoint(index: number): void {
    if (this.hoveredPointIndex() === index) this.hoveredPointIndex.set(null);
  }

  protected toggleTrend(): void {
    this.trendEnabled.update((enabled) => !enabled);
  }

  protected changeBalanceMode(mode: 'free' | 'total'): void {
    this.balanceMode.set(mode);
    this.loadForecast();
  }

  protected periodLabel(point: ForecastPoint): string {
    return this.forecast()?.granularity === 'month' && point.period_from !== point.on
      ? `${formatTextDate(point.period_from)} — ${formatTextDate(point.on)}`
      : formatTextDate(point.on);
  }

  protected granularityLabel(): string {
    return this.forecast()?.granularity === 'month' ? 'По месяцам' : 'По дням';
  }

  protected trendPeriodLabel(): string {
    return this.forecast()?.granularity === 'month' ? 'месяц' : 'день';
  }

  protected balanceModeLabel(mode: Forecast['balance_mode']): string {
    return mode === 'free' ? 'Свободные средства' : 'Все средства';
  }

  protected tooltipBelow(point: PlotPoint): boolean {
    return point.y < TOOLTIP_BELOW_THRESHOLD;
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

  private loadForecast(): void {
    const requestId = ++this.requestId;
    this.loading.set(true);
    this.error.set(null);
    this.forecast.set(null);
    this.selectedPointIndex.set(0);
    this.hoveredPointIndex.set(null);
    let params = new HttpParams().set('horizon', this.selectedHorizon());
    params = params.set('balance_mode', this.balanceMode());
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

function plotY(value: number, scale: PlotScale): number {
  return PLOT_TOP + ((scale.high - value) / (scale.high - scale.low || 1)) * PLOT_HEIGHT;
}

function approximateMoney(value: number): string {
  const normalized = Math.abs(value) < 0.005 ? 0 : value;
  return normalized.toFixed(2);
}

function uniqueIndexes(count: number, total: number): number[] {
  return [
    ...new Set(
      Array.from({ length: count }, (_, index) =>
        Math.round((index * (total - 1)) / Math.max(count - 1, 1)),
      ),
    ),
  ];
}
