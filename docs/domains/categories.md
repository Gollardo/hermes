# Categories

## Owner-confirmed rules

Categories may contain subcategories. Release `0.1.0-alpha.2` supports exactly
two levels in both API and UI: `category → subcategory`. Arbitrary depth is not
claimed and can be reconsidered only with a UI and migration strategy.

Every new `income` and `expense` operation requires an active category of the
matching type.

## Boundary and invariants

Categories owns tree structure and category lifecycle. Operations may reference
a category through a public identifier and validation contract. The tree must
not contain cycles, and a node cannot be its own ancestor; these are necessary
technical invariants implied by any tree model.

## Assumptions

- A pure transfer is normally uncategorized.
- Deleting a category with historical operations should not silently erase
  classification history.

These behaviours have not been confirmed by the owner.

## Release 0.1.0-alpha.2 decisions

- Income and expense categories are separate typed trees.
- A parent must be active and have the same type as its child.
- A parent must be a root; creating a third level is rejected.
- Changing a category cannot introduce a cycle or make existing children type-incompatible.
- A category with active children cannot be archived; archive children first.
- A child cannot be restored while its parent remains archived.
- Archived categories remain readable. The public operations validation contract rejects them
  for new postings but can explicitly allow them while resolving historical operations.
- Category deletion, merge and reassignment are outside this release; lifecycle is archival.
- Tree mutations and new-operation reference validation share a PostgreSQL
  transaction-level advisory lock, preventing concurrent cycle/archive races.

## Open questions

- Merge and reassignment behavior.
- Category ordering, icons and colors; these are presentation concerns and not
  part of the current foundation.
