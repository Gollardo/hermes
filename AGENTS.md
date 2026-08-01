# Repository guidance

- Start with [docs/index.md](docs/index.md); architecture and domain ownership
  are described under `docs/architecture/` and `docs/domains/`.
- Run locally with `make setup` then `make dev`; production-like Compose uses
  `make up`. Run checks with `make test`, `make lint`, and `make typecheck`.
- Preserve the modular monolith. Do not bypass a module's public boundary to
  import its private internals.
- Never store financial values in `float`; use `Decimal`/`NUMERIC` and precise
  JSON representations.
- Changes to one financial operation must be atomic in one database transaction.
- Cover domain invariants with tests.
- Do not rewrite migrations after they have shipped in a public release.
- Do not add external infrastructure without a recorded justification.
- Mark assumptions explicitly; never present them as owner-approved decisions.
- Never commit secrets.

```text
Update documentation in the same change when modifying architecture,
domain invariants, module ownership, data flows or deployment.
```
