# Scheduling

Owns recurrence rules and expected operation occurrences. Only confirmation
materializes a posted financial operation.

Public HTTP capabilities cover rule CRUD-with-disable, bounded idempotent
materialization, calendar reads and occurrence confirmation/postpone/cancel.
Confirmation calls the Operations posting contract in the same transaction;
Scheduling never writes account movements directly.

Account, category and timezone checks also use public module contracts. Rule
replacement locks its occurrences before those references; confirmation locks
one occurrence and follows the same category-before-account posting order.

Public lifecycle-reference reads live in `contracts.py`. Account deletion and
category type changes use them from application coordination without importing
Scheduling's private models.
