# Project Status

Этот документ содержит фактический снимок реализованных и проверенных
возможностей. Стратегическая последовательность находится в
[roadmap.md](./roadmap.md), карта документации — в [index.md](./index.md).

## Last updated

2026-08-17

## Current phase

**0.4.0 — динамическое распределение новых поступлений по фондам.**

Следующий шаг: owner acceptance динамического распределения и последовательного
прогноза версии `0.4.0` на реальных данных.
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
  и прогноз представлены рабочими вертикальными сценариями.
- Owner feedback 2026-08-12 реализован как UX-stabilization: sidebar можно
  скрыть с сохранением выбора, entity composers открываются modal-слоями,
  суммы имеют единый формат с группировкой тысяч, категории разделены на
  доходы/расходы, а обзор показывает фактическую краткую сводку вместо
  onboarding/release-карточек.
- Forecast redesign 2026-08-15 превращает прежний график в decision-making
  экран: единый forecast view-model синхронизирует safe-to-spend, минимум,
  cash-gap, конец периода, график, события, риски и итоговый поток. Desktop и
  mobile состояния сверены с концептуальным референсом; рекомендации без
  доменной модели не добавлялись.
- Визуальная корректировка фондов 2026-08-17 отделяет основные денежные итоги
  от вторичных процентов, раскрывает редкие переносы по запросу и показывает
  фонды плотным сравнительным списком. Существующие расчёты, формы и API не
  изменены; desktop и mobile состояния проверены в браузере.
- Owner feedback 2026-08-14 добавил на обзор три компактные круговые диаграммы:
  расходы и доходы текущего месяца по корневым категориям и доли фондов в общей
  сумме отложенных средств. Категории свёрнуты по умолчанию, одновременно
  раскрывается один родитель каждого типа.
- Owner feedback 2026-08-15 зафиксировал единый текстовый формат дат,
  символы валют, группировку тысяч в отформатированных полях, 30-минутный
  idle-timeout и свободные средства как стартовый режим графика прогноза.
- Для доходов и расходов подтверждены обязательная категория, дата
  финансового факта без времени, серийный ручной ввод и отсутствие отдельного
  payee в MVP. Posting model отдельно проверена и описана в ADR 0001; её
  overdraft и audit-допущения остаются alpha-решениями для owner review.

## Verified capabilities

### First run and access

- Чистый экземпляр определяется через публичный setup-status и показывает
  Angular-мастер первоначальной настройки.
- Первым шагом setup предлагает выбрать JSON-backup прежней версии или чистый
  старт. Для чистого старта владелец может отметить необязательные вопросы о
  расходах: выбранные двухуровневые деревья и пять базовых категорий доходов
  создаются атомарно вместе с владельцем; все вопросы можно пропустить.
- Выбранный при первом запуске backup после создания нового мастер-пароля
  проходит integrity, domain и post-write проверки в одной setup-транзакции;
  при ошибке экземпляр остаётся неинициализированным, credential из backup не
  импортируется.
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
- Browser shell завершается после 30 минут без взаимодействия; клавиатура,
  движение или нажатие указателя, touch и scroll продлевают локальный deadline
  и вызывают редкий CSRF-защищённый heartbeat. Backend независимо отклоняет
  idle-сессию.
- Смена мастер-пароля требует текущий пароль и завершает остальные сессии.
- Persistent login throttle по умолчанию блокирует вход на 15 минут после пяти
  ошибок в 15-минутном окне.
- Public API ограничен health, setup status, двумя setup-командами и login; прикладные роутеры
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
- Настройка «Счёт по умолчанию» принимает только активный счёт и автоматически
  подставляет его только в новые доходы/расходы; выбор остаётся изменяемым, а
  архивирование или удаление счёта очищает настройку атомарно.
- Настройка режима фондов переключает ручные и динамические проценты. Включение
  динамики требует целей у всех неархивных фондов; возврат в ручной режим
  атомарно сохраняет текущие вычисленные проценты.

### Schema and delivery

- Первая публичная миграция `0001_first_run_access` создаёт owner credential,
  sessions, login throttle и application settings; следующая миграция
  `0002_harden_access_invariants` добавляет database checks с сохранением
  инициализированных данных.
- Production image содержит Angular build и FastAPI, запускает Alembic до Uvicorn
  и сохраняет один HTTP entrypoint.
- Миграция `0011_dynamic_fund_allocation` добавляет глобальный режим с безопасным
  backfill `manual`, database check и обратимым downgrade до `0010`.
- Runtime-параметры сессии, throttling и Secure-cookie доступны через
  `HERMES_*`; development Compose явно использует non-Secure cookie только для
  локального HTTP.
- Alembic выполняет исторические ревизии отдельными транзакциями: чистый upgrade
  commit-ит PostgreSQL enum additions до зависящих CHECK constraints.
- Миграция `0008_session_idle_timeout` добавляет activity timestamp с database
  checks и сохраняет существующие сессии при upgrade, инициализируя его временем
  создания сессии.

### Backup and restore

- Settings содержит JSON-export schema 1 с SHA-256 integrity, decimal-строками
  и идентификаторами всех settings, ledger, fund и scheduling записей.
- Проверка checksum сохраняет canonical shape старого schema-1 документа:
  добавленные позднее необязательные поля не ломают импорт ранее созданной копии.
- Preview проверяет формат, версию, checksum и ссылки до записи и показывает сводку.
- Restore требует CSRF, мастер-пароль назначения и точную фразу подтверждения;
  exclusive locks, одна транзакция и post-write checks исключают частичную замену.
- Credential, login throttle и sessions не экспортируются; restore проходит
  через общий throttle, сохраняет текущую сессию и завершает остальные.

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
- Миграция `0007_fund_targets_recurrence` добавляет необязательные цели фондов,
  интервалы/дни недели регулярных правил и тип виртуального перевода между фондами.

### Financial operations and journal

- Владелец может создавать, просматривать, редактировать и удалять доходы,
  расходы, переводы и корректировки до ожидаемого остатка; composer вычисляет
  точный signed delta для журнала.
- Кнопка создания раскрывает четыре типа операции и сразу открывает composer
  выбранного типа, сохраняя единый сценарий ввода и редактирования.

### Reports and fund perspective

- Новый раздел «Отчёты» строит доходы или расходы за календарный месяц либо
  произвольный период, показывает большую диаграмму категорий, точные итоги и
  сгруппированный список операций с переходом в журнал.
- В «Плане» отдельная перспектива фондов показывает диаграмму конечных долей и
  линии остатков на горизонте основного прогноза. Текущие активные проценты
  применяются только к actionable переводам с явным `allocate_to_funds`.
- Оба read model используют публичные контракты модулей-владельцев и точную
  decimal-арифметику; fund perspective не блокирует основной прогноз при своей
  ошибке загрузки.
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
- Выбор счетов и категорий в журнале, регулярных правилах, фондах, прогнозе и
  дереве категорий использует общий searchable combobox: prefix-поиск и до пяти
  последних вариантов при пустом запросе.
- Общий combobox поддерживает выбор клавиатурой и мышью; денежные поля принимают
  точку или запятую и при потере фокуса нормализуются либо показывают ошибку.
- Панель фильтров журнала по умолчанию свёрнута, активные условия остаются
  видимыми chips.
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
- Экран явно различает выделение свободных денег, перенос уже существующего
  назначения без физического движения и атомарный физический перевод с
  последующим процентным распределением на счёте назначения.
- ADR 0002 отдельно фиксирует posting model, lock order, rounding и archive policy.
- Фонд имеет необязательную целевую сумму с точным прогрессом; экран показывает
  прогресс каждого фонда и общий прогресс всех заданных целей.
- Создание фонда может атомарно выделить сумму только ему. Перевод между двумя
  фондами на одном счёте сохраняет физический баланс и общий reserved.
- В динамическом режиме незаполненные неархивные фонды получают гарантированную
  долю до 5% и пропорциональную абсолютному остатку часть. Проценты и денежное
  распределение точно замыкаются на 100%, пересчитываются перед каждым
  пополнением и допускают превышение цели без перераспределения внутри операции.
- Заполненные и архивные фонды получают 0%; расход или восстановление
  автоматически возвращает фонд в следующий расчёт, если он снова ниже цели.
- Перспектива фондов последовательно пересчитывает динамические проценты после
  каждого запланированного пополнения и явно показывает заблокированные события.

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
- Календарь показывает месяц, фильтры по счёту и типу, а также быстрые
  confirm/postpone/cancel действия только для событий текущего дня и overdue.
- Месячная сетка загружает все страницы ограниченного диапазона; список действий
  честно показывает первые 12 и полный размер выборки. Подтверждённый экземпляр
  открывает точную связанную операцию, а mobile сначала показывает action list.
- Rule edit блокирует экземпляры до category/account references; confirmation
  берёт те же reference locks после экземпляра. Гонка сериализуется, а stale
  confirmation получает optimistic conflict вместо проведения старого снимка.
- Monthly правила ограничены днями 1–28, yearly не принимает 29 февраля;
  после первого правила timezone заблокирован, а домен хранит calendar date без
  времени.
- Weekly правила выбирают несколько дней недели и интервал 1–3 недели; monthly
  поддерживает интервал 1–3 месяца.
- Правило без даты окончания продолжает скользящую материализацию на год вперёд,
  а не завершается через год. Подтверждённая история защищена от rule edit.
- При подтверждении можно скорректировать сумму одного экземпляра. Плановый
  перевод может атомарно распределить поступление по активным фондам согласно
  их заблокированному на время confirmation снимку процентов; ошибка
  распределения откатывает перевод и confirmation link.
- ADR 0003 фиксирует recurrence, materialization, synchronization и
  confirmation policies.

## Latest verification

- Backend без PostgreSQL: 61 passed, 50 PostgreSQL-сценариев skipped без opt-in.
- PostgreSQL integration: 51/51 passed, включая миграцию `0010`, изменение
  подтверждаемой суммы, скользящую материализацию и атомарный rollback перевода
  с распределением по фондам, lifecycle счёта по умолчанию и отчётный read model.
- Frontend: 96 passed в 20 test files.
- Пройдены `make lint`, `make typecheck`, docs-check, production Angular build;
  Alembic имеет единственную head-ревизию `0010_default_account`.

### Balance forecasting

- Владелец может открыть общий прогноз или выбрать конкретный, в том числе
  архивный, счёт и горизонт: две недели, месяц, квартал, полгода или год.
- Стартовая точка полностью выводится из фактического ledger. В будущую линию
  входят только `pending` и `postponed` экземпляры с датой от сегодня до
  включительного конца горизонта; confirmed/cancelled исключаются.
- По умолчанию старт равен текущим свободным средствам: Funds одним batch-read
  вычитает резервы по каждому счёту из physical ledger. Переключатель `total`
  возвращает полный физический остаток, включая распределённые средства.
- Будущий расход пока не выбирает фонд, поэтому free-режим применяет его к
  текущей свободной стартовой точке без скрытого предположения об источнике
  резерва. Переводы с явным процентным распределением показаны отдельно в
  перспективе фондов.
- События агрегируются в детерминированные daily closing points с точными
  Decimal-суммами. Ответ содержит конец периода, минимум, первую возможную
  отрицательную дату и точный closing balance этого дня; годовая визуальная
  агрегация поэтому не теряет сумму первого daily cash-gap.
- В общем scope внутренний перевод имеет нулевой net effect, но остаётся в
  explanation. Для одного счёта тот же перевод является исходящим или входящим.
- Просроченные события не сдвигаются молча: их scoped count показан отдельно с
  переходом в календарь.
- Один frontend view-model выводит safe-to-spend как `max(0, minimumBalance)`,
  конец, минимум/дату, первый cash-gap/дату, доходы, расходы и net flow. KPI,
  график, timeline, risk panel и period summary не пересчитывают эти значения
  независимо.
- Экран выделяет нулевую границу, отрицательную зону и risk-отрезок не только
  цветом; Y-axis использует округлённые денежные деления, а tooltip сохраняет
  точную сумму, изменение и число операций.
- Фактический starting balance включён в шкалу и отмечен отдельной точкой
  «Сейчас». Годовой monthly-график добавляет точный risk-marker, если дневной
  cash-gap успел восстановиться к закрытию месяца; marker раскрывает операции
  именно этого дня.
- Single-account summary отдельно показывает ненулевой net effect переводов,
  поэтому его общий поток объясним через доходы, расходы и transfer flow.
- До полугода API и экран дают ежедневные closing points; год агрегируется по
  месячным интервалам без потери исходных событий и точности daily risk checks.
  Каждая точка имеет hover/focus tooltip с точным балансом, клик раскрывает её
  события; timeline и risk items синхронно выбирают ту же дату. Неутверждённые
  regression/recommendation слои в интерфейс не входят.
- Forecasting — read-only модуль без таблиц и фоновой materialization; новая
  миграция для beta.2 не добавлялась.
- Forecast snapshot берёт shared locks на ожидаемые экземпляры и account
  identities в том же порядке Scheduling → Accounts, что и confirmation.
  Free-прогноз выбранного счёта делает один глобальный schedule snapshot и
  фильтрует его в памяти: это сохраняет единую последовательность динамических
  пополнений без повторного захвата occurrence locks.
  Конкурентное подтверждение поэтому не может попасть одновременно в фактический
  starting balance и плановую часть одного ответа.
- Экран перед чтением прогноза синхронизирует rolling one-year materialization,
  поэтому дальняя граница не зависит от того, когда последний раз открывался
  календарь; сам forecast GET остаётся read-only.

## Verification snapshot

- Для `0.4.0` пройдены 70 non-PostgreSQL backend-тестов, 54/54 PostgreSQL
  integration-теста и 100/100 frontend-тестов. Отдельно проверены формула для
  1/20/21/25 фондов, точное замыкание процентов и денег, overshoot, пересчёт
  после одного фонда, archive/restore, отсутствие активных целей, atomic
  rollback, фиксация dynamic → manual, backup round trip и последовательный
  прогноз. Ruff, mypy, Angular lint, Prettier, TypeScript, docs-check,
  production Angular build и production Docker Compose build прошли. Code-review
  hardening отдельно фиксирует единственный глобальный schedule snapshot для
  account free forecast и восстановление dynamic backup, в котором неиспользуемая
  сумма ручных процентов больше 100%.
- На временной чистой PostgreSQL-базе пройдены `upgrade head`, `alembic check`,
  `downgrade 0011 → 0010` и повторный `upgrade 0010 → 0011`; временная база
  после проверки удалена.
- `npm audit --omit=dev` сообщает 0 production vulnerabilities. Полный dev graph
  сообщает high advisory для build-only `nanoid 3.3.17`, зафиксированного
  существующим override; обновление зависимости не включено в функциональный
  scope `0.4.0`.

- `rc.1`: 97 backend-сценариев (52 non-PostgreSQL passed, 45 skipped без opt-in);
  полный PostgreSQL integration snapshot 46/46 passed, включая атомарный
  first-run restore, transfer-and-allocation и их rollback, а также forecasting
  snapshot с обновлённым series contract.
  Frontend: 63/63 теста passed; lint/format/typecheck/docs passed.
- Исторический полный `npm audit` после прежних overrides сообщал 0 advisories;
  актуальный снимок для `0.4.0` приведён выше.
- Поиск `float` в финансовом backend-коде нашёл только входной rejection guard
  и docstring о запрете float arithmetic.
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
  upgrade и beta.1 downgrade; полный backup round trip на clean initialized
  target, rollback invalid restore, rate-limited re-authentication, other-session
  revocation и 50 MiB request limit.
  Setup отдельно проверяет выбранные category templates, отклонение повторных
  групп и атомарный first-run restore: ошибка после создания owner откатывает
  credential и оставляет экземпляр неинициализированным.
- Новые PostgreSQL regression-сценарии проверяют rollback определения фонда при
  недоступной начальной сумме, сохранение physical/reserved при переводе между
  фондами, прогресс выше 100%, агрегацию подкатегории в корень и database checks
  для уникальных weekdays и допустимых recurrence intervals.
- Frontend Vitest: 63 теста для access shell, session expiry, setup, settings,
  health UI, счетов, категорий и журнала, включая timezone default, expected-balance
  adjustment, archived edit reference, transfer direction, loading continuity,
  точный manual allocation preview, invalidation устаревшего preview, процентный
  лимит и выбор позиции фонда на физическом счёте; monthly calendar, overdue
  state, missing-day validation, exact rule payload, quick confirmation, полную
  пагинацию месяца, честный upcoming count, archived-reference edit state и
  exact-operation link; forecast risk/explanation, account/horizon switches,
  stale-loading, event-free state и календарную шкалу X.
  Дополнительно проверены dashboard drill-down и частичная ошибка аналитики,
  exact fund progress, optional decimal normalisation, recurrence weekdays и
  скрытая/resettable панель фильтров журнала.
  Settings дополнительно проверяет preview, полную replacement summary, точную
  destructive phrase, restore payload и очистку пароля после ошибки. Новые
  проверки фиксируют atomic first-run restore, disabled setup action при
  невалидном/несовпадающем пароле, выбор onboarding templates, строго последние
  варианты combobox, emoji-prefix search и устойчивость к повреждённому
  localStorage; также сохранение скрытого sidebar и точный строковый формат денег.

- Beta.1 calendar flow проверен в браузере на desktop и mobile: все пункты
  narrow-навигации видимы, action list предшествует календарной сетке, статусы
  выражены текстом, ограниченный список показывает `12 из 30`, а переход из
  confirmed occurrence открывает точную операцию в начале страницы.
- Ruff, Ruff format, strict mypy, ESLint, Prettier, strict TypeScript и docs check.
- `alembic check` не обнаруживает drift между model metadata и схемой head;
  migration env явно загружает Operations, Funds и Scheduling indexes/constraints.
- Production Angular build и ранее проверенный production Docker image build проходят;
  `npm ci` внутри образа сообщает 0 vulnerabilities. Angular build предупреждает
  о превышении `anyComponentStyle` budget общим `directory.css` (5.34 KiB),
  `app.css` (4.25 KiB), `forecast.css` (5.57 KiB), `forecast-chart.css`
  (5.65 KiB) и `scheduling.css` (4.04 KiB) при пороге 4 KiB; это не блокирует
  сборку, но требует последующей декомпозиции общих стилей.
- Production-like Compose e2e на отдельном clean volume: setup → authenticated
  shell → settings update → logout → login; browser console без ошибок.
- Settings/backup flow повторно проверен screenshot-аудитом на 1440 px и 390 px:
  release label согласован с текущей версией, horizontal overflow отсутствует, destructive
  flow раскрывается только после валидного preview, статусы имеют текст и ARIA role.
- UX-stabilization 2026-08-12 проверена в production-like Compose через браузер:
  setup action действительно заблокирован до совпадения валидных паролей; sidebar
  скрывается и восстанавливается; composers счетов, операций, категорий и фондов
  отсутствуют в исходном layout и открываются dialog-слоем; суммы отображаются как
  `100 000.00`; категории разделены на доходы/расходы; overview показывает
  фактические итоги. Сценарий `4 000.00` между счетами при доле фонда 25% атомарно
  дал `1 000.00` нового назначения. Годовой forecast сохранил layout, показывает
  оси «Сумма · RUB»/«Дата» и не содержит прежней нижней ленты сумм.
- Redesign forecast проверен в браузере на 1440 × 1000 и 390 × 844: free/all
  переключает series и safe-to-spend, клик по риску или событию выбирает точную
  дату, body-level horizontal overflow отсутствует, график и timeline получают
  собственную прокрутку на mobile, а roving tabindex оставляет одну keyboard
  остановку на forecast-point series; browser console без ошибок. Финальное
  сравнение с референсом зафиксировано в `design-qa.md` со статусом `passed`.
- Композиционная итерация forecast убрала левую KPI-колонку: четыре decision KPI
  собраны над рабочей областью, а риски и итоги перенесены под полноширинный
  график. Chart viewport больше не имеет
  собственной прокрутки; adaptive Y-domain исключает далёкий ноль для безопасной
  положительной series и возвращает zero-line/tint при приближении к дефициту.
  Area fill ослаблен, обычные markers скрыты до interaction, tooltip сокращён.
- Free forecast учитывает будущие переводы с процентным распределением как
  уменьшение свободных средств на точную распределяемую сумму; total forecast
  сохраняет физическую нейтральность перевода. Нижняя ось графика не обрезается.
- В обзоре круговая диаграмма показывается и для единственной категории. В
  перспективе фондов удалён неинформативный line chart, а диаграмма структуры
  увеличена и использует более контрастные цвета с точной текстовой легендой.
- Меню добавления операции ограничено доступной шириной на узких экранах.
- Для предыдущего `0.2.0` diff пройдены Ruff, backend format, mypy, Angular lint, Prettier,
  TypeScript typecheck, docs-check, production Angular build,
  61 non-PostgreSQL backend-тест, 96 frontend-тестов и 51/51 PostgreSQL
  integration-сценариев. Интеграционный
  прогон отдельно подтвердил idle-timeout/heartbeat, upgrade существующих сессий
  от `0001`, free/total forecast с реальным резервом, бессрочные шаблоны,
  подтверждение с корректировкой суммы и атомарное распределение перевода по
  фондам вместе с прежними транзакционными сценариями финансовых модулей.
- Для исправлений `0.3.0` пройдены 62 non-PostgreSQL backend-теста, 97 frontend-
  тестов, 51/51 PostgreSQL integration-тест, Ruff, mypy,
  Angular lint, Prettier, TypeScript typecheck, docs-check и production Angular
  build. Сохраняются известные non-blocking предупреждения style budget.

## Release assumptions and technical debt

- Build-only dependency `nanoid 3.3.17` имеет актуальный high advisory; runtime
  production graph чист. Нужен отдельный совместимый dependency update и полный
  повтор проверок, чтобы не расширять функциональный diff этого релиза.
- Style-budget warnings остаются для `funds.css`, `forecast.css`,
  `forecast-chart.css`, `scheduling.css`, `directory.css` и `app.css`; новый UI
  режима увеличил `funds.css` до 6.86 KiB при warning-пороге 4 KiB.

- Срок сессии, password policy и throttle являются документированными alpha
  defaults, а не окончательно утверждённой долгосрочной политикой.
- Password recovery отсутствует; потеря мастер-пароля не должна переоткрывать
  обычный setup.
- Нет «remember me» и фонового cleanup истёкших сессий; absolute и idle cleanup
  выполняется при следующем успешном login, а guard отклоняет их до удаления.
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
- Backup schema 1 имеет строгую совместимость и 50 MiB request limit. SHA-256
  защищает от случайной порчи, но не аутентифицирует источник; шифрование и
  цифровая подпись backup остаются вне MVP.
- Frontend lock временно фиксирует patched `hono` и `nanoid` через `overrides`,
  потому что их уязвимые версии приходят только через Angular build tooling.
  Overrides нужно пересмотреть после обновления Angular toolchain.
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
- Годовой forecast возвращает все explaining events и удерживает shared locks на
  выбранных occurrences/accounts до завершения запроса. При измеренном росте
  правил потребуется консистентная read projection, но молчаливое усечение
  объяснений не допускается.

## Outside current scope

- Поиск, saved filters, running balance, bulk actions и immutable audit trail.
- Account-specific overdraft, pending bank transactions, полноценный
  reconciliation workflow и currency-specific precision/rounding.
- Автоматическое/мультисчётное распределение, несколько фондов на одну операцию,
  target dates и immutable audit trail.
- Liabilities, debts и их будущие платежи в прогнозе.
- Recurrence intervals за пределами 1–3, дни месяца 29–31, leap-day policy,
  drag-and-drop, уведомления и background materialization.
- Импорт CSV/Excel, совместимость backup-схем после schema 1 и password recovery.
- Несколько пользователей, роли, permissions, organizations и tenants.
- Внешняя инфраструктура, Redis, broker, background workers и cloud identity.

## Recommended next action

Провести owner acceptance: восстановить реальный backup на отдельном экземпляре
и начать период ежедневного использования; затем обновить Angular toolchain и
проверить, можно ли удалить временные dependency overrides.
