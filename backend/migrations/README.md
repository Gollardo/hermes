# Database migrations

Alembic owns schema evolution. Revision `0001_first_run_access` creates the
single-owner credential, server sessions, persistent login throttle and base
application settings used by release `0.1.0-alpha.1`. Revision
`0002_harden_access_invariants` adds database checks for session lifetime,
throttle counters and normalized currency while preserving initialized data.
Revision `0003_accounts_categories` adds accounts, typed category trees and the
minimal operation/movement ledger needed for initial balance adjustments.
Later revisions extend the same linear history:

- `0004_financial_operations` completes ordinary operation posting;
- `0005_virtual_funds` adds the virtual-fund ledger;
- `0006_recurring_operations` adds rules and expected occurrences;
- `0007_fund_targets_recurrence` adds fund targets and flexible recurrence;
- `0008_session_idle_timeout` adds server-enforced session activity tracking;
- `0009_scheduled_fund_allocation` records the transfer-allocation choice;
- `0010_default_account` adds the optional default account;
- `0011_dynamic_fund_allocation` adds the global manual/dynamic fund mode;
- `0012_recurring_series_shift` adds the opt-in postpone propagation policy and
  persisted day offsets for rules and occurrences, plus an explicit marker for
  automatically cancelled occurrences preserved from later series shifts. Its
  partial candidate index supports narrow deterministic locking during a shift.

`0012_recurring_series_shift` is the current single head. Revision identifiers,
rather than migration filenames, are the stable Alembic chain.

Release `0.4.6` adds no revision: its dynamic fund percentages are derived from
the existing target and movement ledger, and its Scheduling change is CSS-only.
Creating an empty marker migration would not represent schema evolution.

Downgrading below `0012_recurring_series_shift` removes the rule policy, stored
offsets and cancelled-occurrence preservation markers. Untouched occurrence
dates are normalized back to their source dates; take a backup before rollback
because the accumulated series shift and explicit preservation decisions cannot
be reconstructed afterward.
