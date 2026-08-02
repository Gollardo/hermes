# Categories

Owns the two-level category tree used by the first API and interface.

Release `0.1.0-alpha.2` separates two-level `income` and `expense` trees. Parent
and child must have the same type, active children block parent archival, and a
child cannot be restored below an archived parent. Mutations and new-operation
validation serialize on a transaction-level advisory lock. The public validator
returns an immutable reference, rejects archived categories for new operations
and permits an explicit historical read path.
