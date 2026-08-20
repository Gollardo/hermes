import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { AuthService, apiErrorMessage } from '../../core/auth.service';

const CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP', 'CNY', 'JPY', 'KZT', 'TRY', 'AED', 'CHF'];
type SetupMode = 'fresh' | 'restore';

interface OnboardingQuestion {
  key: string;
  title: string;
  question: string;
}

const QUESTIONS: OnboardingQuestion[] = [
  {
    key: 'housing',
    title: '🏠 Жильё',
    question:
      'Хотите учитывать расходы на квартиру или дом: аренду, ипотеку, коммунальные услуги и ремонт?',
  },
  {
    key: 'car',
    title: '🚗 Автомобиль',
    question: 'Есть ли у вас автомобиль, расходы на который вы хотите учитывать?',
  },
  {
    key: 'transport',
    title: '🚌 Транспорт',
    question:
      'Пользуетесь ли вы общественным транспортом, такси, каршерингом или другими видами транспорта?',
  },
  {
    key: 'children',
    title: '👶 Дети',
    question: 'Есть ли у вас дети, расходы на которых вы хотите учитывать отдельно?',
  },
  {
    key: 'family',
    title: '👨‍👩‍👧 Семья и близкие',
    question: 'Хотите ли вы отдельно учитывать расходы на семью, родственников и подарки близким?',
  },
  {
    key: 'pets',
    title: '🐕 Домашние животные',
    question: 'Есть ли у вас домашние животные?',
  },
  {
    key: 'health',
    title: '❤️ Здоровье',
    question:
      'Хотите отдельно учитывать расходы на врачей, лекарства, стоматологию и другие медицинские услуги?',
  },
  {
    key: 'sport',
    title: '🏃 Спорт и активность',
    question: 'Занимаетесь ли вы спортом или регулярно тратите деньги на фитнес и активный отдых?',
  },
  {
    key: 'education',
    title: '🎓 Учёба и развитие',
    question: 'Тратите ли вы деньги на образование, курсы, книги или профессиональное развитие?',
  },
  {
    key: 'work',
    title: '💼 Работа и карьера',
    question: 'Есть ли у вас личные расходы, связанные с работой или профессией?',
  },
  {
    key: 'business',
    title: '🧑‍💻 Бизнес и самозанятость',
    question: 'Ведёте ли вы бизнес, работаете на себя или получаете доход от частной деятельности?',
  },
  {
    key: 'travel',
    title: '✈️ Путешествия',
    question: 'Хотите отдельно учитывать расходы на поездки, отпуск и путешествия?',
  },
  {
    key: 'entertainment',
    title: '🎬 Отдых и развлечения',
    question: 'Хотите отдельно учитывать кафе, рестораны, развлечения, мероприятия и хобби?',
  },
  {
    key: 'shopping',
    title: '🛍️ Покупки и личные вещи',
    question: 'Хотите отдельно учитывать покупки одежды, техники, косметики и других личных вещей?',
  },
];

@Component({
  selector: 'app-setup-page',
  imports: [ReactiveFormsModule],
  templateUrl: './setup.html',
  styleUrl: './setup.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SetupPage {
  private readonly auth = inject(AuthService);
  private readonly formBuilder = inject(NonNullableFormBuilder);

  protected readonly currencies = CURRENCIES;
  protected readonly timezones = supportedTimezones();
  protected readonly questions = QUESTIONS;
  protected readonly step = signal(1);
  protected readonly mode = signal<SetupMode | null>(null);
  protected readonly selectedGroups = signal(new Set<string>());
  protected readonly backupName = signal<string | null>(null);
  protected readonly backupRequiresPassword = signal(false);
  protected readonly readingBackup = signal(false);
  protected readonly submitting = signal(false);
  protected readonly error = signal<string | null>(null);
  private backupDocument: unknown | null = null;
  private backupSequence = 0;

  protected readonly form = this.formBuilder.group({
    password: ['', [Validators.required, Validators.minLength(12), Validators.maxLength(1024)]],
    passwordConfirmation: ['', Validators.required],
    baseCurrency: ['RUB', [Validators.required, Validators.pattern(/^[A-Za-z]{3}$/)]],
    timezone: [detectedTimezone(), Validators.required],
    backupPassword: ['', Validators.maxLength(1024)],
  });

  protected startFresh(): void {
    this.backupSequence += 1;
    this.mode.set('fresh');
    this.backupDocument = null;
    this.backupName.set(null);
    this.backupRequiresPassword.set(false);
    this.readingBackup.set(false);
    this.error.set(null);
    this.step.set(2);
  }

  protected chooseBackup(event: Event): void {
    const sequence = ++this.backupSequence;
    const file = (event.target as HTMLInputElement).files?.[0];
    this.backupDocument = null;
    this.backupName.set(null);
    this.backupRequiresPassword.set(false);
    this.mode.set(null);
    this.readingBackup.set(false);
    this.error.set(null);
    if (!file) return;
    if (file.size > 72 * 1024 * 1024) {
      this.error.set('Файл больше допустимых 72 МБ.');
      return;
    }
    this.readingBackup.set(true);
    file
      .text()
      .then((text) => {
        if (sequence !== this.backupSequence) return;
        try {
          this.backupDocument = JSON.parse(text);
          const format = this.backupFormat(this.backupDocument);
          if (format === 'hermes-json-backup' && file.size > 50 * 1024 * 1024) {
            this.backupDocument = null;
            this.error.set('Открытый JSON-backup больше допустимых 50 МБ.');
            return;
          }
          this.backupRequiresPassword.set(format === 'hermes');
          this.backupName.set(file.name);
          this.mode.set('restore');
          this.step.set(2);
        } catch {
          this.error.set('Файл не является корректным JSON.');
        } finally {
          this.readingBackup.set(false);
        }
      })
      .catch(() => {
        if (sequence !== this.backupSequence) return;
        this.readingBackup.set(false);
        this.error.set('Не удалось прочитать выбранный файл.');
      });
  }

  protected back(): void {
    this.error.set(null);
    if (this.step() === 3) {
      this.step.set(2);
      return;
    }
    this.backupSequence += 1;
    this.mode.set(null);
    this.backupDocument = null;
    this.backupName.set(null);
    this.backupRequiresPassword.set(false);
    this.readingBackup.set(false);
    this.step.set(1);
  }

  protected continueToCategories(): void {
    if (!this.credentialsValid()) return;
    if (this.mode() === 'restore') {
      this.submit();
      return;
    }
    this.step.set(3);
  }

  protected toggleGroup(key: string, checked: boolean): void {
    const next = new Set(this.selectedGroups());
    if (checked) next.add(key);
    else next.delete(key);
    this.selectedGroups.set(next);
  }

  protected submit(): void {
    if (!this.credentialsValid() || this.submitting()) return;
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.error.set(null);

    if (this.mode() === 'restore' && this.backupDocument) {
      this.auth
        .restoreSetup({
          master_password: value.password,
          backup: this.backupDocument,
          backup_password: this.backupRequiresPassword() ? value.backupPassword : null,
        })
        .subscribe({
          next: () => this.submitting.set(false),
          error: (error: unknown) => {
            this.submitting.set(false);
            this.error.set(
              apiErrorMessage(error, 'Backup не прошёл проверку. Выберите другой файл.'),
            );
          },
        });
      return;
    }

    this.auth
      .setup({
        master_password: value.password,
        base_currency: value.baseCurrency,
        timezone: value.timezone,
        create_default_categories: this.mode() === 'fresh',
        onboarding_expense_groups: this.mode() === 'fresh' ? [...this.selectedGroups()] : [],
      })
      .subscribe({
        next: () => {
          this.submitting.set(false);
        },
        error: (error: unknown) => {
          this.submitting.set(false);
          this.error.set(apiErrorMessage(error, 'Не удалось завершить первоначальную настройку.'));
        },
      });
  }

  private credentialsValid(): boolean {
    const value = this.form.getRawValue();
    if (
      this.form.invalid ||
      value.password !== value.passwordConfirmation ||
      (this.mode() === 'restore' && this.backupRequiresPassword() && !value.backupPassword)
    ) {
      this.form.markAllAsTouched();
      if (this.form.valid && value.password !== value.passwordConfirmation) {
        this.error.set('Пароли не совпадают.');
      }
      return false;
    }
    return true;
  }

  private backupFormat(document: unknown): string | null {
    if (typeof document !== 'object' || document === null || !('format' in document)) return null;
    return typeof document.format === 'string' ? document.format : null;
  }
}

function detectedTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

function supportedTimezones(): string[] {
  const intl = Intl as typeof Intl & { supportedValuesOf?: (key: 'timeZone') => string[] };
  const values = intl.supportedValuesOf?.('timeZone') ?? ['UTC', detectedTimezone()];
  return [...new Set(['UTC', detectedTimezone(), ...values])].sort();
}
