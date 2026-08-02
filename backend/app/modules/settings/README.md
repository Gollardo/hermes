# Settings

Owns persisted application and owner preferences. Runtime deployment settings
remain in `app.core.config` and environment variables. Financial modules must
import commands and validators from the public `contracts` module and call
`lock_base_currency()` in the same transaction as the first financial-data
write; after that latch is set, changing the currency is rejected. Currency
updates and locking serialize on the singleton settings row.
