# Accounts

Owns cash, debit and savings account identity. Balances are derived from money
movements, never stored as freely editable account fields.

Release `0.1.0-alpha.2` exposes authenticated account CRUD/lifecycle API and UI.
An `app.application` use case locks the base currency and atomically coordinates
account creation with the public operations command for a non-zero initial
balance. Accounts remains independent from Operations. Accounts with movements
cannot be deleted; archival preserves them and their history.
