# Authentication

Owns first-run owner setup, Argon2id password verification and server-side
sessions. Session and CSRF tokens are random; only SHA-256 digests are stored.
The browser session identifier is an HttpOnly, SameSite cookie. Login failures
are throttled in PostgreSQL so restarts do not reset the limit. No multi-user
registration, roles, password recovery or tenants belong here.

Sessions have a configurable absolute lifetime and a 30-minute idle limit by
default. The browser ends the visible session at the effective deadline and
sends a throttled heartbeat only while the owner interacts with the application.
