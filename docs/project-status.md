# Project Status

Этот документ содержит фактический снимок реализованных и проверенных
возможностей. Стратегическая последовательность находится в
[roadmap.md](./roadmap.md), карта документации — в [index.md](./index.md).

## Last updated

2026-08-12

## Current phase

**0.1.0-beta.1 — регулярные операции и календарь реализованы и проверены.**

Следующий запланированный этап: **0.1.0-beta.2 — прогнозирование остатков**.
Политики ADR 0001, ADR 0002 и ADR 0003 требуют owner review после реального
использования.

## Product and UI/UX foundation

- В `docs/ui-ux/` зафиксированы vision, UX-принципы, предварительное визуальное
  направление, information architecture и направления ключевых экранов.
- Владелец подтвердил P0-фокус: dashboard обзорный, свободные деньги являются
  primary, быстрое создание операции остаётся доступным, а аналитика отвечает
  на вопросы о будущем остатке и крупнейших расходах.
- Для первого прототипа подтверждены light neutral premium-minimalism,
  приглушённый зелёный акцент и Quixotic как главный визуальный ориентир;
  тёмная тема отложена.
- Текущий Angular frontend приведён к этому направлению: access/setup,
  адаптивная shell-навигация, обзор, счета, категории, настройки и системные
  состояния и журнал используют общую иерархию поверхностей и действий. Фонды
  и прогноз не имитируются dashboard-заглушками.
- Для доходов и расходов подтверждены обязательная категория, дата
  финансового факта без времени, серийный ручной ввод и отсутствие отдельного
  payee в MVP. Posting model отдельно проверена и описана в ADR 0001; её
  overdraft и audit-допущения остаются alpha-решениями для owner review.

## Verified capabilities

### First run and access

- Чистый экземпляр определяется через публичный setup-status и показывает
  Angular-мастер первоначальной настройки.
- Production-like Compose публикует чистый экземпляр только на loopback;
  владелец завершает setup до намеренного LAN/remote exposure.
- Setup атомарно создаёт единственного владельца, Argon2id-хеш мастер-пароля,
  основную валюту, IANA timezone, throttle и первую сессию.
- Повторный setup получает conflict и не может заменить credential или настройки.
- Инициализированный экземпляр без сессии показывает вход по мастер-паролю.
- Защищённая оболочка и settings API недоступны без действующей серверной сессии.

### Authentication and sessions

- Случайный идентификатор сессии передаётся в HttpOnly, SameSite=Lax cookie;
  PostgreSQL хранит только SHA-256 digest.
- Изменяющие cookie-authenticated запросы дополнительно защищены per-session
  double-submit CSRF token.
- Поддержаны текущая сессия, logout, logout всех сессий и семидневный абсолютный
  срок жизни по умолчанию.
- Смена мастер-пароля требует текущий пароль и завершает остальные сессии.
- Persistent login throttle по умолчанию блокирует вход на 15 минут после пяти
  ошибок в 15-минутном окне.
- Public API ограничен health, setup status, setup и login; прикладные роутеры
  подключены через общий authentication dependency.
- Транзакционная dependency завершается до отправки успешного HTTP-ответа и
  session cookies.

### Settings

- Владелец может просматривать и менять timezone до создания первого
  регулярного правила.
- Основную валюту можно менять до первого счёта или денежной операции.
- `settings.lock_base_currency()` является публичным транзакционным контрактом
  будущих финансовых модулей; после lock смена валюты запрещена. Scheduling
  отдельно блокирует смену timezone после появления первого правила.
- Currency/timezone update и соответствующие locks сериализуются row-level lock
  на singleton settings, включая конкурентные транзакции.
- Backend валидирует трёхбуквенный currency code и IANA timezone независимо от UI.

### Schema and delivery

- Первая публичная миграция `0001_first_run_access` создаёт owner credential,
  sessions, login throttle и application settings; следующая миграция
  `0002_harden_access_invariants` добавляет database checks с сохранением
  инициализированных данных.
- Production image содержит Angular build и FastAPI, запускает Alembic до Uvicorn
  и сохраняет один HTTP entrypoint.
- Runtime-параметры сессии, throttling и Secure-cookie доступны через
  `HERMES_*`; development Compose явно использует non-Secure cookie только для
  локального HTTP.

### Accounts and balances

- Владелец может создавать, просматривать и редактировать счета типов `cash`,
  `debit`, `savings`, архивировать и восстанавливать их.
- Начальный ненулевой остаток атомарно создаёт `balance_adjustment` и движение;
  текущий остаток вычисляется суммой `NUMERIC(20,4)`-движений и возвращается строкой.
- API не принимает `float` для денег и ограничивает alpha-scale четырьмя знаками.
- Счёт без движений можно удалить; наличие истории возвращает conflict и требует архивации.
- Первый account write в той же транзакции фиксирует основную валюту; создание
  currency-independent категории оставляет её изменяемой.

### Categories

- Владелец может создавать и редактировать раздельные деревья категорий доходов
  и расходов; UI оптимизирован под категорию и подкатегорию.
- Родитель обязан быть активным и иметь тот же тип; циклы запрещены.
- API и UI поддерживают ровно два уровня; третий уровень отклоняется.
- Активные дети блокируют архивирование родителя, а архивный родитель — восстановление ребёнка.
- Архивные категории остаются читаемыми для истории; публичный validation-контракт
  запрещает их для новых операций и имеет явный historical-read режим.
- Тип категории неизменяем, пока на неё ссылается финансовая операция;
  application use case проверяет operations-owned history contract.
- Мутации дерева и проверка новой operation reference сериализуются общей
  transaction-level advisory-блокировкой.

### Financial schema

- Миграция `0003_accounts_categories` добавляет `accounts`, `categories`,
  `financial_operations`, `account_movements` и PostgreSQL enum-типы.
- Миграция `0004_financial_operations` добавляет общие типы операций, calendar
  date, category reference, adjustment reason, optimistic version, journal
  indexes и уникальность движения операции по счёту. Старые timestamps
  преобразуются в дату через timezone приложения; downgrade заполняет обязательное
  legacy-описание для записей alpha.3.
- Миграция `0005_virtual_funds` добавляет определения фондов, события,
  виртуальные движения, source checks, внешние ключи и history indexes.
- Миграция `0006_recurring_operations` добавляет регулярные правила, ожидаемые
  экземпляры, recurrence/status enum-типы, уникальный identity правила/даты,
  confirmation link и calendar indexes.

### Financial operations and journal

- Владелец может создавать, просматривать, редактировать и удалять доходы,
  расходы, переводы и корректировки до ожидаемого остатка; composer вычисляет
  точный signed delta для журнала.
- Доход и расход требуют активную категорию соответствующего типа; перевод
  использует два разных активных счёта и остаётся одной операцией с двумя
  противоположными движениями.
- Создание, полная замена движений и удаление выполняются в транзакции запроса.
  Затронутые счета блокируются в UUID-порядке, версия защищает от lost update.
- Консервативная alpha-политика запрещает результат ниже нуля; неуспешная
  проверка не сохраняет заголовок или часть перевода.
- Журнал фильтруется по периоду, счёту, типу и категории, имеет server-side
  пагинацию, стабильный порядок, раскрываемую деталь, transfer direction,
  full-selection net total и локализованные ошибки.
- Удаление счёта блокирует identity до проверки истории, поэтому конкурентное
  проведение не превращается в необработанную FK-ошибку.

### Virtual funds

- Владелец может создавать, редактировать, архивировать и восстанавливать фонды;
  активные проценты атомарно ограничены суммой 100%.
- Остатки восстанавливаются из виртуального журнала и показаны общим итогом, по
  счетам и через равенство physical = reserved + free.
- Preview использует точную decimal-арифметику и округление вниз до четырёх
  знаков; ручная коррекция и свободный remainder видимы до commit.
- Расход может списать выбранный фонд или остаться без фонда. Перевод может
  перенести одну виртуальную часть; перераспределение не меняет физические деньги.
- CRUD fund-linked операции заменяет оба журнала в одной транзакции и повторно
  проверяет coverage и non-negative positions.
- История объединяет allocations, redistributions, expenses и transfers.
- ADR 0002 отдельно фиксирует posting model, lock order, rounding и archive policy.

### Recurring rules and calendar

- Владелец может создавать и редактировать регулярные доходы, расходы и
  переводы с `daily`, `weekly`, `monthly` или `yearly` периодичностью, датой
  начала и необязательной включительной датой окончания.
- Явная materialization-команда синхронизирует экземпляры от текущей даты на
  один календарный год вперёд. Rule lock и unique `(rule_id, scheduled_on)`
  делают повторный и конкурентный запуск идемпотентным.
- Изменение или отключение правила затрагивает только текущие/будущие
  нетронутые экземпляры. Подтверждённые, перенесённые, вручную отменённые и
  просроченные экземпляры не исчезают.
- Подтверждение создаёт ровно одну фактическую операцию и записывает связь в той
  же транзакции. Перенос и отмена не создают физических движений.
- Календарь показывает месяц, ближайшие 30 дней, overdue, фильтры по счёту и
  типу, а также быстрые confirm/postpone/cancel действия.
- Месячная сетка загружает все страницы ограниченного диапазона; список действий
  честно показывает первые 12 и полный размер выборки. Подтверждённый экземпляр
  открывает точную связанную операцию, а mobile сначала показывает action list.
- Rule edit блокирует экземпляры до category/account references; confirmation
  берёт те же reference locks после экземпляра. Гонка сериализуется, а stale
  confirmation получает optimistic conflict вместо проведения старого снимка.
- Monthly правила ограничены днями 1–28, yearly не принимает 29 февраля;
  после первого правила timezone заблокирован, а домен хранит calendar date без
  времени.
- ADR 0003 фиксирует recurrence, materialization, synchronization и
  confirmation policies.

## Verification snapshot

- Backend suite: 64 теста: 33 unit/non-PostgreSQL и 31 PostgreSQL-dependent
  scenario; integration target выполняет 32 сценария вместе с health-check.
- PostgreSQL scenarios: clean migration/setup, protected API, CSRF/logout/login,
  password/session revocation, expired sessions, sequential and concurrent rate
  limiting, serialized settings currency lock and upgrade initialized data from
  `0001_first_run_access` до head и upgrade базы `alpha.2` с начальной
  корректировкой; account lifecycle,
  initial adjustment/history protection, category lifecycle и конкурентные
  reparent/archive-create races; immutable historical category type, operation
  CRUD, filters/totals, version conflict, concurrent expenses, concurrent
  account deletion, insufficient balance и injected rollback после первого
  движения перевода; fund lifecycle, deterministic allocation, manual remainder,
  fund-aware CRUD, redistribution, history, concurrent allocation и concurrent
  fund consumption, serialized concurrent percentage definitions; rollback
  после первого виртуального движения, откат
  физической операции при нарушении coverage, archive-инвариант, upgrade
  существующей alpha.3 базы и downgrade схемы alpha.4. Проверены
  timezone-boundary upgrade и data-bearing downgrade alpha.3; recurrence rule
  lifecycle, exact bounded dates (включая 367-дневное leap-year окно), all
  operation types, no-balance-before-confirm,
  idempotent confirmation, protected manual edits, overdue preservation,
  concurrent materialization, concurrent confirmation/rule edit, duplicate
  confirmation, scheduling auth/CSRF, injected confirmation rollback, alpha.4
  upgrade и beta.1 downgrade.
- Frontend Vitest: 29 тестов для access shell, session expiry, setup, settings,
  health UI, счетов, категорий и журнала, включая timezone default, expected-balance
  adjustment, archived edit reference, transfer direction, loading continuity,
  точный manual allocation preview, invalidation устаревшего preview, процентный
  лимит и выбор позиции фонда на физическом счёте; monthly calendar, overdue
  state, missing-day validation, exact rule payload, quick confirmation, полную
  пагинацию месяца, честный upcoming count, archived-reference edit state и
  exact-operation link.
- Beta.1 calendar flow проверен в браузере на desktop и mobile: все пункты
  narrow-навигации видимы, action list предшествует календарной сетке, статусы
  выражены текстом, ограниченный список показывает `12 из 30`, а переход из
  confirmed occurrence открывает точную операцию в начале страницы.
- Ruff, Ruff format, strict mypy, ESLint, Prettier, strict TypeScript и docs check.
- `alembic check` не обнаруживает drift между model metadata и схемой head;
  migration env явно загружает Operations, Funds и Scheduling indexes/constraints.
- Production Angular beta.1 build проходит; остаётся прежнее warning превышения
  `anyComponentStyle` budget общим `directory.css` (5.27 KiB при пороге 4 KiB).
  Повторная Docker image build была
  запущена, но Docker Hub frontend resolver завершился внешним
  `DeadlineExceeded`; локальная компиляция backend/frontend и тесты проходят.
- Production-like Compose e2e на отдельном clean volume: setup → authenticated
  shell → settings update → logout → login; browser console без ошибок.

## Release assumptions and technical debt

- Срок сессии, password policy и throttle являются документированными alpha
  defaults, а не окончательно утверждённой долгосрочной политикой.
- Password recovery отсутствует; потеря мастер-пароля не должна переоткрывать
  обычный setup.
- Нет idle timeout, «remember me» и фонового cleanup истёкших сессий; cleanup
  выполняется при успешном login.
- Throttle глобален для экземпляра, а не IP: это надёжно за неизвестным proxy,
  но позволяет локальный denial-of-service серией неверных попыток.
- Currency validation проверяет форму ISO 4217-style кода, но не использует
  внешний реестр. Currency-specific scale и exchange rates не спроектированы;
  фонды используют документированный общий alpha-scale 4.
- Currency lock требует вызова публичного settings-контракта в транзакции первого
  monetary/account write; account creation выполняет этот контракт через
  application-layer use case, category creation не блокирует валюту.
- `NUMERIC(20,4)` — единый alpha-envelope, а не утверждённая currency-specific
  политика precision/rounding.
- Список счетов вычисляет остаток отдельным агрегатным запросом на счёт; при
  большом количестве счетов потребуется batch read model.
- Journal response пока разрешает имена отдельными запросами на операцию; перед
  большими объёмами нужен batch read model.
- Fund summary и объединённая history используют несколько агрегатных запросов
  и Python-side pagination; при измеренном росте нужен read projection.
- Alpha.4 поддерживает один фонд на расход/перевод и распределение на одном
  счёте; автоматическое распределение дохода намеренно отсутствует.
- Редактирование заменяет движения и увеличивает version, но immutable audit
  trail отсутствует. Описание обычной операции остаётся опциональным.
- Запрет отрицательного остатка един для всех типов счетов и должен быть
  подтверждён или заменён account-specific overdraft model.
- Advisory lock намеренно сериализует редкие мутации всего category tree; при
  доказанной необходимости высокой write-concurrency потребуется более узкая схема блокировок.
- HTTPS reverse-proxy configurations и CSP не проверены внешним security audit.
- Upgrade существующей `0004 → 0005` и schema downgrade `0005 → 0004` проверены.
  Downgrade удаляет фондовые данные, поэтому production rollback требует backup
  и явного принятия потери alpha.4 ledger.
- Материализация запускается календарём или явным API-вызовом; background worker
  намеренно отсутствует. Если календарь долго не открывать, новый дальний край
  годового окна появится при следующем запуске, а ранее созданные overdue
  экземпляры сохранятся.
- Rule/occurrence responses пока разрешают имена отдельными запросами; перед
  большим числом ежедневных правил потребуется batch calendar read model.
- Архивация счёта или категории не отключает правило автоматически. При
  подтверждении такого экземпляра backend вернёт понятную invalid-reference
  ошибку; автоматическая lifecycle policy отложена.
- Timezone migration расписания не реализована: после первого правила смена
  timezone отклоняется, а явный migration flow отложен.

## Outside current scope

- Поиск, saved filters, running balance, bulk actions и immutable audit trail.
- Account-specific overdraft, pending bank transactions, полноценный
  reconciliation workflow и currency-specific precision/rounding.
- Автоматическое/мультисчётное распределение, несколько фондов на одну операцию,
  fund goals и immutable audit trail.
- Прогнозы, liabilities и debts.
- Custom recurrence intervals, weekdays, дни 29–31, leap-day policy,
  drag-and-drop, уведомления и background materialization.
- Импорт CSV/Excel, versioned JSON backup/restore и password recovery.
- Несколько пользователей, роли, permissions, organizations и tenants.
- Внешняя инфраструктура, Redis, broker, background workers и cloud identity.

## Recommended next action

Провести owner review ADR 0003 на реальном месяце регулярных платежей, затем
спроектировать read-only forecasting engine beta.2 поверх ledger-derived
остатков и ожидаемых экземпляров, не проводя планы автоматически.
