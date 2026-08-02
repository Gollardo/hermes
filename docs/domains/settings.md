# Application settings

## Ownership and current fields

The `settings` module owns persisted owner preferences, currently the base
currency and IANA timezone. Runtime deployment configuration remains in
`app.core.config` and environment variables.

Setup creates exactly one settings row in the same transaction as the owner
credential. Authenticated owners can read settings, change the timezone and
change the base currency only while it is unlocked.

## Invariants

- There is exactly one settings row with singleton identity `1` after setup.
- Currency is normalized to an uppercase, three-letter ISO 4217-style code.
  This release validates code shape, not membership in an external currency
  registry.
- Timezone must resolve through the runtime IANA timezone database.
- The base currency becomes immutable once financial data exists. Because no
  financial domain writes data in this release, the settings module exposes
  `lock_base_currency(session)` as its public contract. The first future
  financial-data write must call it in the same database transaction.
- Locking is idempotent. Changing only the timezone remains valid after the
  currency lock.
- Currency changes and the first financial lock take a row-level lock on the
  singleton settings record, so concurrent transactions cannot change the
  currency after a financial write establishes the lock.

## Explicit assumptions

- A single base currency is sufficient until per-account currency and
  conversion-aware reporting are designed.
- Currency symbols, decimal scales and exchange rates are outside this release.
- Browser timezone suggestions are convenience only; backend validation is
  authoritative.
