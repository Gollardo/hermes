# Funds

Owns virtual fund definitions, percentages, allocation/redistribution events and
per-account virtual movements. Balances are reconstructed from the virtual
ledger; funds never replace physical accounts. Cross-ledger writes use the
public contracts in `contracts.py`; composition with Operations reads lives in
`app.application.funds`, keeping the module graph acyclic. See ADR 0002.
