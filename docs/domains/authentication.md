# Authentication

## Owner-confirmed rules

- There is exactly one local owner. Registration, multiple users, roles,
  permissions, organizations, invitations and tenants are out of scope.
- On first run the owner creates a password; store only an Argon2id hash.
- Authentication uses server-side sessions. The browser carries only a session
  identifier in an HttpOnly cookie, and sessions can be terminated.
- The API requires authentication except owner setup, login and health check.
- JWT is not required.

## Terms and boundary

**Uninitialized instance** has no owner credential. **Setup** is the one-time
transition that creates it. **Session** is revocable server-owned authentication
state, distinct from the owner password hash. The auth module owns these states
and the HTTP authentication dependency; it owns no financial records.

## Initialization status

Authentication is intentionally not implemented in the foundation. Argon2 and
session dependencies will be added with the first designed auth slice, avoiding
unused security packages and fake tables now.

## Assumptions requiring confirmation

- Setup should become permanently unavailable after the first credential is
  committed, except through an explicit recovery procedure.
- State-changing cookie-authenticated requests require CSRF protection or an
  equivalent same-origin design.
- Session identifiers must be random, opaque, rotated after login and stored
  hashed if persisted.

## Open questions

- Session storage schema, idle/absolute expiry and cleanup policy.
- Cookie `SameSite`, `Secure`, domain and reverse-proxy behavior.
- Password reset and owner recovery without an email or cloud dependency.
- Brute-force throttling appropriate to a single-node trusted deployment.
