# Security policy

## Reporting a vulnerability

Please use the repository's private GitHub Security Advisory flow when it is
available. Until a public repository location is configured, report only a
minimal, non-exploitable description in the project issue tracker and ask the
maintainer for a private channel. **No security contact email has been assigned
yet.** Do not publish credentials, personal financial data or working exploits.

## Deployment expectations

Hermes is designed primarily for a trusted, protected network. That assumption
does not remove the need for a strong owner password, secure HttpOnly session
cookies, protected Docker volumes and tested backups.

- Do not expose PostgreSQL to the internet; the production Compose file does not
  publish its port.
- Replace example passwords and keep `.env` out of version control.
- Protect the PostgreSQL volume and backup files as sensitive financial data.
- For remote access, prefer a VPN or a maintained reverse proxy with HTTPS.
- End server-side sessions after suspected compromise and keep the host, images
  and dependencies patched.

The authentication design is documented in
[the authentication domain](docs/domains/authentication.md). Security hardening
must be revisited before the first public release.
