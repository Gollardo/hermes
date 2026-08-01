# Domain modules

Each directory is an ownership boundary inside the modular monolith. A module
may expose a small public Python API when implementation starts; callers must
not import its private persistence or application internals. See
[`docs/architecture/module-boundaries.md`](../../../docs/architecture/module-boundaries.md).
