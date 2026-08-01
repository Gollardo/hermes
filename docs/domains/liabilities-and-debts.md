# Liabilities and debts

## Owner-confirmed simplified liability model

A loan or installment plan needs original amount, current outstanding amount,
start date, expected end date, regular payment, next-payment date, recurrence,
creditor, description and status.

The first implementation does not calculate annuity or differentiated payment
schedules, complex interest, rate changes, bank fees or complex early repayment.
Those values are recorded as user-known facts rather than recreated bank math.

Debts have direction `i_owe` or `owed_to_me`.

## Boundary

Liabilities owns loans/installments; debts owns interpersonal or other two-way
obligations. Scheduling may represent planned payments. Actual disbursement and
repayment effects are posted by operations using `loan_disbursement`,
`loan_payment`, `debt_issuance` and `debt_repayment`.

The stored “current outstanding amount” must not drift from repayments. Whether
it is derived from original amount and posted repayments or maintained as a
strict transactional projection is an open design choice.

## Open questions

- Status sets and lifecycle transitions.
- Exact meaning of debt issuance for each direction and resulting account
  movements.
- Manual correction of outstanding amounts.
- Partial payments, missed payments and changing next-payment dates.
- Whether liabilities and debts should share a common read contract while
  retaining separate ownership.
