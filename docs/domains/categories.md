# Categories

## Owner-confirmed rules

Categories may contain subcategories. The technical model may support a tree of
arbitrary depth, while the first UI is optimized for two levels:
`category → subcategory`.

## Boundary and invariants

Categories owns tree structure and category lifecycle. Operations may reference
a category through a public identifier and validation contract. The tree must
not contain cycles, and a node cannot be its own ancestor; these are necessary
technical invariants implied by any tree model.

## Assumptions

- Categories classify income/expense-style operations, while a pure transfer is
  normally uncategorized.
- Deleting a category with historical operations should not silently erase
  classification history.

These behaviours have not been confirmed by the owner.

## Open questions

- Separate income and expense category sets or one shared tree.
- Archive, merge and reassignment behavior.
- Category ordering, icons and colors; these are presentation concerns and not
  part of the current foundation.
