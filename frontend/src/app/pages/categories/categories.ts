import { HttpClient } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { environment } from '../../../environments/environment';
import { apiErrorMessage } from '../../core/auth.service';

type CategoryType = 'income' | 'expense';

interface Category {
  id: string;
  type: CategoryType;
  name: string;
  description: string | null;
  parent_id: string | null;
  archived: boolean;
}

@Component({
  selector: 'app-categories-page',
  imports: [ReactiveFormsModule],
  templateUrl: './categories.html',
  styleUrl: './categories.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategoriesPage implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly builder = inject(NonNullableFormBuilder);

  protected readonly categories = signal<Category[]>([]);
  protected readonly roots = computed(() => this.categories().filter((item) => !item.parent_id));
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly editingId = signal<string | null>(null);
  protected readonly form = this.builder.group({
    name: ['', [Validators.required, Validators.maxLength(120)]],
    type: this.builder.control<CategoryType>('expense', Validators.required),
    description: ['', Validators.maxLength(2000)],
    parentId: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  protected availableParents(): Category[] {
    const type = this.form.controls.type.value;
    return this.categories().filter(
      (item) =>
        !item.archived && !item.parent_id && item.type === type && item.id !== this.editingId(),
    );
  }

  protected children(parentId: string): Category[] {
    return this.categories().filter((item) => item.parent_id === parentId);
  }

  protected submit(): void {
    this.error.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    const body = {
      type: value.type,
      name: value.name,
      description: value.description || null,
      parent_id: value.parentId || null,
    };
    const id = this.editingId();
    this.saving.set(true);
    const request = id
      ? this.http.put<Category>(`${environment.apiBaseUrl}/categories/${id}`, body)
      : this.http.post<Category>(`${environment.apiBaseUrl}/categories`, body);
    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.cancelEdit();
        this.load();
      },
      error: (error: unknown) => {
        this.saving.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось сохранить категорию.'));
      },
    });
  }

  protected edit(category: Category): void {
    this.form.controls.parentId.enable();
    this.editingId.set(category.id);
    this.form.setValue({
      name: category.name,
      type: category.type,
      description: category.description ?? '',
      parentId: category.parent_id ?? '',
    });
    if (this.children(category.id).length > 0) {
      this.form.controls.parentId.disable();
    }
  }

  protected cancelEdit(): void {
    this.editingId.set(null);
    this.form.reset({ name: '', type: 'expense', description: '', parentId: '' });
    this.form.controls.parentId.enable();
  }

  protected toggleArchive(category: Category): void {
    const action = category.archived ? 'restore' : 'archive';
    this.http
      .post<Category>(`${environment.apiBaseUrl}/categories/${category.id}/${action}`, {})
      .subscribe({
        next: () => this.load(),
        error: (error: unknown) =>
          this.error.set(apiErrorMessage(error, 'Не удалось изменить состояние категории.')),
      });
  }

  private load(): void {
    this.loading.set(true);
    this.http.get<Category[]>(`${environment.apiBaseUrl}/categories`).subscribe({
      next: (categories) => {
        this.categories.set(categories);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(apiErrorMessage(error, 'Не удалось загрузить категории.'));
      },
    });
  }
}
