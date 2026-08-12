# Backup

Owns versioned full JSON export and transactional restore orchestration. It may
coordinate modules without taking ownership of their domain rules.

Schema 1 exports all persistent application settings, financial ledgers, fund
ledgers and scheduling state through module public contracts. Authentication
credentials, throttles and sessions are excluded. Export uses shared table
locks; restore requires owner re-authentication, CSRF, an exact confirmation
phrase, shared password throttle and exclusive table locks inside the request
transaction. Success preserves the current destination session and revokes the others.
The 50 MiB request limit is enforced before JSON parsing. The SHA-256 digest is
an accidental-corruption check, not proof of backup authorship.
