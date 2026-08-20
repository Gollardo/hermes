# ADR 0004: Encrypted Hermes backup envelope

- Status: accepted
- Date: 2026-08-20
- Decision owner: project owner

## Context

The portable schema-1 JSON backup contains the owner's complete financial and
planning data. Its SHA-256 digest detects accidental corruption but provides no
confidentiality or authentication. Owners also need an explicit plaintext JSON
option for compatibility and manual inspection.

The stored owner credential is a one-way password hash and cannot safely act as
an encryption key. A backup password must therefore be supplied at export and
processed independently of the stored authentication hash.

## Decision

Hermes supports two explicit export choices:

- `hermes-json-backup` schema 1 remains an unencrypted JSON export and import;
- `hermes` version 1 is a UTF-8 JSON envelope whose financial payload is
  encrypted.

Hermes version 1 generates a random 256-bit data-encryption key (DEK). The
payload is encrypted with the DEK using XChaCha20-Poly1305-IETF from PyNaCl. A
separate Argon2id password-derived key (KEK) encrypts the DEK. The file stores
the random salt, explicit Argon2 parameters, independent random nonces and
Base64 ciphertext, but never stores the password, KEK or plaintext DEK.

The writer uses Argon2 version 19 with `time_cost=3`,
`memory_cost=65536` KiB, `parallelism=4`, a 32-byte result and a 16-byte salt.
The reader validates strict upper and lower KDF bounds, encoded-field sizes and
decoded lengths before invoking Argon2. The outer request limit is 72 MiB so a
50 MiB plaintext payload still fits after authenticated encryption and Base64.
Legacy plaintext JSON remains limited to 50 MiB.

Key and payload encryption use separate deterministic associated-data domains.
Payload AAD does not include KDF or wrapped-key metadata. A future password-
rewrap operation can therefore decrypt and re-encrypt only the DEK without
changing the payload ciphertext.

An initialized restore distinguishes the destination current master password
from the backup password. First-run restore distinguishes the new destination
master password from the backup password. Authentication failures never reveal
whether the password or ciphertext was wrong.

## Alternatives considered

- Encrypting the payload directly with the master-password-derived key would
  prevent cheap future password rewrap and couple payload encryption to KDF
  changes.
- AES-GCM and ordinary ChaCha20-Poly1305 are established AEAD alternatives, but
  PyNaCl provides a maintained XChaCha20-Poly1305 implementation with a large
  random-nonce space in the current Python stack.
- Removing plaintext JSON export would reduce accidental disclosure but would
  violate the owner's explicit compatibility and inspection requirement.
- Custom cryptographic primitives were rejected.

## Consequences

- Protected backups remain portable JSON while their financial data is not
  readable without the backup password.
- Plaintext JSON remains a deliberate high-risk action and must be stored as
  sensitive financial data.
- A forgotten backup password cannot be recovered by Hermes.
- Python and the high-level crypto APIs may retain immutable temporary byte
  copies; Hermes minimizes secret lifetimes and wipes mutable DEK/KEK buffers
  on a best-effort basis but cannot promise complete process-memory erasure.
- Version 1 is a one-shot AEAD format. Very large streaming backups require a
  separately versioned format rather than an incompatible V1 change.

## Deferred work

- A UI and command for password-only DEK rewrap.
- Streaming encryption, compression, multiple recipients and signatures.
- Automatic backup scheduling, rotation and server-side atomic file storage.
