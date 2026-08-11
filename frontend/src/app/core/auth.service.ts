import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { AccessStateService } from './access-state.service';

export type AccessState =
  'checking' | 'uninitialized' | 'unauthenticated' | 'authenticated' | 'unavailable';

export interface SetupPayload {
  master_password: string;
  base_currency: string;
  timezone: string;
}

interface SetupStatusResponse {
  initialized: boolean;
}

interface SessionResponse {
  authenticated: true;
  expires_at: string;
}

export interface PasswordChangePayload {
  current_password: string;
  new_master_password: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly access = inject(AccessStateService);

  readonly state = this.access.state.asReadonly();
  readonly expiresAt = this.access.expiresAt.asReadonly();

  initialize(): void {
    this.access.checking();
    this.http.get<SetupStatusResponse>(`${environment.apiBaseUrl}/setup/status`).subscribe({
      next: ({ initialized }) => {
        if (!initialized) {
          this.access.uninitialized();
          return;
        }
        this.restoreSession();
      },
      error: () => this.access.unavailable(),
    });
  }

  setup(payload: SetupPayload): Observable<SessionResponse> {
    return this.http
      .post<SessionResponse>(`${environment.apiBaseUrl}/setup`, payload)
      .pipe(tap((session) => this.acceptSession(session)));
  }

  login(masterPassword: string): Observable<SessionResponse> {
    return this.http
      .post<SessionResponse>(`${environment.apiBaseUrl}/auth/login`, {
        master_password: masterPassword,
      })
      .pipe(tap((session) => this.acceptSession(session)));
  }

  logout(): Observable<void> {
    return this.http
      .post<void>(`${environment.apiBaseUrl}/auth/logout`, {})
      .pipe(tap(() => this.clearSession()));
  }

  logoutAll(): Observable<void> {
    return this.http
      .post<void>(`${environment.apiBaseUrl}/auth/logout-all`, {})
      .pipe(tap(() => this.clearSession()));
  }

  changePassword(payload: PasswordChangePayload): Observable<void> {
    return this.http.post<void>(`${environment.apiBaseUrl}/auth/password`, payload);
  }

  private restoreSession(): void {
    this.http.get<SessionResponse>(`${environment.apiBaseUrl}/auth/session`).subscribe({
      next: (session) => this.acceptSession(session),
      error: (error: HttpErrorResponse) => {
        if (error.status === 401) {
          this.access.unauthenticated();
        } else {
          this.access.unavailable();
        }
      },
    });
  }

  private acceptSession(session: SessionResponse): void {
    this.access.authenticated(session.expires_at);
  }

  private clearSession(): void {
    this.access.unauthenticated();
  }
}

export function apiErrorMessage(error: unknown, fallback: string): string {
  if (!(error instanceof HttpErrorResponse)) {
    return fallback;
  }
  const detail: unknown = error.error?.detail;
  if (
    typeof detail === 'object' &&
    detail !== null &&
    'code' in detail &&
    typeof detail.code === 'string'
  ) {
    const localized: Record<string, string> = {
      already_initialized: 'Первоначальная настройка уже завершена.',
      authentication_required: 'Сессия завершена. Войдите снова.',
      base_currency_locked: 'Основную валюту уже нельзя изменить.',
      account_has_history: 'Счёт с историей операций нельзя удалить. Архивируйте его.',
      account_not_found: 'Счёт не найден.',
      archived_fund_balance:
        'Изменение вернуло бы деньги в архивный фонд. Сначала восстановите фонд.',
      category_has_active_children: 'Сначала архивируйте активные подкатегории.',
      category_not_found: 'Категория не найдена.',
      category_type_has_history:
        'Тип категории с финансовой историей изменить нельзя. Создайте новую категорию.',
      csrf_failed: 'Защитный токен устарел. Обновите страницу и повторите действие.',
      current_password_invalid: 'Текущий мастер-пароль указан неверно.',
      invalid_credentials: 'Неверный мастер-пароль.',
      invalid_category_parent: 'Родитель должен быть активной категорией того же типа.',
      invalid_account_reference: 'Выбранный счёт недоступен для новой операции.',
      invalid_category_reference: 'Выбранная категория недоступна или имеет другой тип.',
      insufficient_balance: 'На счёте недостаточно денег. Отрицательный остаток запрещён.',
      fund_not_found: 'Фонд не найден или находится в архиве.',
      invalid_fund_reference: 'Выбранный фонд недоступен для новой операции.',
      fund_conflict: 'Фонд уже изменён в другой вкладке. Обновите страницу.',
      fund_percentage_limit: 'Сумма процентов активных фондов не может превышать 100%.',
      fund_has_balance: 'Фонд можно архивировать только после обнуления остатка.',
      insufficient_fund_balance: 'В выбранном фонде на этом счёте недостаточно денег.',
      insufficient_free_balance: 'На счёте недостаточно свободных денег для резервирования.',
      login_rate_limited: 'Слишком много неудачных попыток. Повторите вход позже.',
      operation_conflict: 'Операция уже изменена в другой вкладке. Обновите журнал.',
      operation_not_found: 'Операция не найдена.',
    };
    return localized[detail.code] ?? fallback;
  }
  return fallback;
}
