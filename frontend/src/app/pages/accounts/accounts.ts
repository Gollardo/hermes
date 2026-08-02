import { HttpClient } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/auth.service';

type AccountType = 'cash' | 'debit' | 'savings';

interface Account {
  id: string;
  type: AccountType;
  name: string;
  description: string | null;
  balance: string;
  archived: boolean;
}

@Component({
  selector: 'app-accounts-page',
  imports: [ReactiveFormsModule],
  templateUrl: './accounts.html',
  styleUrl: './accounts.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccountsPage implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly builder = inject(NonNullableFormBuilder);

  protected readonly accounts = signal<Account[]>([]);
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly editingId = signal<string | null>(null);
  protected readonly form = this.builder.group({
    name: ['', [Validators.required, Validators.maxLength(120)]],
    type: this.builder.control<AccountType>('cash', Validators.required),
    description: ['', Validators.maxLength(2000)],
    initialBalance: ['0', [Validators.required, Validators.pattern(/^\d{1,16}(?:\.\d{1,4})?$/)]],
  });

  ngOnInit(): void {
    this.load();
  }

  protected submit(): void {
    this.error.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    const id = this.editingId();
    const body = { type: value.type, name: value.name, description: value.description || null };
    this.saving.set(true);
    const request = id
      ? this.http.put<Account>(`${environment.apiBaseUrl}/accounts/${id}`, body)
      : this.http.post<Account>(`${environment.apiBaseUrl}/accounts`, {
          ...body,
          initial_balance: value.initialBalance,
        });
    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.cancelEdit();
        this.load();
      },
      error: (error: unknown) => {
        this.saving.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось сохранить счёт.'));
      },
    });
  }

  protected edit(account: Account): void {
    this.editingId.set(account.id);
    this.form.setValue({
      name: account.name,
      type: account.type,
      description: account.description ?? '',
      initialBalance: '0',
    });
    this.form.controls.initialBalance.disable();
  }

  protected cancelEdit(): void {
    this.editingId.set(null);
    this.form.reset({ name: '', type: 'cash', description: '', initialBalance: '0' });
    this.form.controls.initialBalance.enable();
  }

  protected toggleArchive(account: Account): void {
    const action = account.archived ? 'restore' : 'archive';
    this.http
      .post<Account>(`${environment.apiBaseUrl}/accounts/${account.id}/${action}`, {})
      .subscribe({
        next: () => this.load(),
        error: (error: unknown) =>
          this.error.set(apiErrorMessage(error, 'Не удалось изменить состояние счёта.')),
      });
  }

  protected remove(account: Account): void {
    this.http.delete<void>(`${environment.apiBaseUrl}/accounts/${account.id}`).subscribe({
      next: () => this.load(),
      error: (error: unknown) => this.error.set(apiErrorMessage(error, 'Не удалось удалить счёт.')),
    });
  }

  private load(): void {
    this.loading.set(true);
    this.http.get<Account[]>(`${environment.apiBaseUrl}/accounts`).subscribe({
      next: (accounts) => {
        this.accounts.set(accounts);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить счета.'));
      },
    });
  }
}
