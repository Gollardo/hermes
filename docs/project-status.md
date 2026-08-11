# Project Status

Этот документ содержит фактический снимок реализованных и проверенных
возможностей. Стратегическая последовательность находится в
[roadmap.md](./roadmap.md), карта документации — в [index.md](./index.md).

## Last updated

2026-08-11

## Current phase

**0.1.0-alpha.4 — виртуальные фонды реализованы и проверены.**

Следующий запланированный этап: **0.1.0-beta.1 — регулярные операции и
календарь**. Alpha-политики ADR 0001 и ADR 0002 требуют owner review после
реального использования.

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

- Владелец может просматривать и менять timezone.
- Основную валюту можно менять до первого счёта или денежной операции.
- `settings.lock_base_currency()` является публичным транзакционным контрактом
  будущих финансовых модулей; после lock смена валюты запрещена, timezone остаётся
  изменяемым.
- Currency update и lock сериализуются row-level lock на singleton settings,
  включая конкурентные транзакции.
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

## Verification snapshot

- Backend suite: 47 тестов: 21 unit/non-PostgreSQL и 26 PostgreSQL-dependent
  scenarios; integration target выполняет 27 сценариев вместе с health-check.
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
  timezone-boundary upgrade и data-bearing downgrade alpha.3.
- Frontend Vitest: 22 теста для access shell, session expiry, setup, settings,
  health UI, счетов, категорий и журнала, включая timezone default, expected-balance
  adjustment, archived edit reference, transfer direction, loading continuity,
  точный manual allocation preview, invalidation устаревшего preview, процентный
  лимит и выбор позиции фонда на физическом счёте.
- Предыдущий alpha.3 frontend проверен в браузере на desktop и mobile: clean setup,
  счета, категории, расход, единый перевод и его два движения; console без ошибок.
- Ruff, Ruff format, strict mypy, ESLint, Prettier, strict TypeScript и docs check.
- Production Angular alpha.4 build проходит. Повторная Docker image build была
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

## Outside current scope

- Поиск, saved filters, running balance, bulk actions и immutable audit trail.
- Account-specific overdraft, pending bank transactions, полноценный
  reconciliation workflow и currency-specific precision/rounding.
- Автоматическое/мультисчётное распределение, несколько фондов на одну операцию,
  fund goals и immutable audit trail.
- Расписания, календарь, прогнозы, liabilities и debts.
- Импорт CSV/Excel, versioned JSON backup/restore и password recovery.
- Несколько пользователей, роли, permissions, organizations и tenants.
- Внешняя инфраструктура, Redis, broker, background workers и cloud identity.

## Recommended next action

Провести owner review ADR 0001/0002 на реальных сценариях, затем отдельно
спроектировать materialization и lifecycle ожидаемых операций для
`0.1.0-beta.1`, не смешивая планы с фактическими ledger balances.
