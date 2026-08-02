# Project Status

Этот документ содержит фактический снимок реализованных и проверенных
возможностей. Стратегическая последовательность находится в
[roadmap.md](./roadmap.md), карта документации — в [index.md](./index.md).

## Last updated

2026-08-02

## Current phase

**0.1.0-alpha.1 — первый запуск и доступ к приложению завершён.**

Следующий запланированный этап: **0.1.0-alpha.2 — счета и категории**. Его
roadmap описывает границы, но не является утверждённым детальным дизайном.

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
- Основную валюту можно менять до первого финансового объекта.
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

## Verification snapshot

- Backend suite: 14 tests, включая 8 PostgreSQL integration scenarios.
- PostgreSQL scenarios: clean migration/setup, protected API, CSRF/logout/login,
  password/session revocation, expired sessions, sequential and concurrent rate
  limiting, serialized settings currency lock and upgrade initialized data from
  `0001_first_run_access` to `0002_harden_access_invariants`.
- Frontend Vitest: 7 tests для access shell, session expiry, setup, settings и health UI.
- Ruff, Ruff format, strict mypy, ESLint, Prettier, strict TypeScript и docs check.
- Production Angular/backend Docker image build.
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
  внешний реестр. Scale, rounding и exchange rates ещё не спроектированы.
- Currency lock требует вызова публичного settings-контракта в транзакции первого
  будущего financial write; это обязательство следующего финансового среза.
- HTTPS reverse-proxy configurations и CSP не проверены внешним security audit.
- Миграция имеет downgrade для разработки, но production rollback после schema
  upgrade не гарантирован; нужен проверенный backup.

## Outside current scope

- Счета, категории, операции, остатки и любые финансовые API/таблицы.
- Фонды, расписания, календарь, прогнозы, liabilities и debts.
- Импорт CSV/Excel, versioned JSON backup/restore и password recovery.
- Несколько пользователей, роли, permissions, organizations и tenants.
- Внешняя инфраструктура, Redis, broker, background workers и cloud identity.

## Recommended next action

Перед реализацией `0.1.0-alpha.2` спроектировать вертикальный сценарий счетов и
категорий: подтвердить типы/архивирование/удаление, валютную модель счёта и
начальный остаток. Первая запись счёта или другой финансовой сущности должна в
той же транзакции вызвать `settings.lock_base_currency()`; денежные поля должны
использовать `Decimal`/`NUMERIC`, не `float`.
