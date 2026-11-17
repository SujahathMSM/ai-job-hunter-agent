# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| 1.x     | :x:                |

## Security Architecture & Controls

NexusHunt AI incorporates security and isolation guardrails:

1. **Authentication & Multi-Tenant Isolation**:
   - Accounts require cryptographically salted password hashes.
   - Every API endpoint except health, login/registration and the Google client-id lookup requires a signed session token (JWT). Identity is never taken from a request header, query parameter or request body.
   - Single-user local mode (`ALLOW_DEV_AUTH=true`, set by `start.bat`) lets requests from the same machine (loopback only) use the app without signing in. It is off by default and always off when `APP_ENV=production`.
   - No signing secret is embedded in the source: production requires `JWT_SECRET`; local installs generate a random one in `data/.jwt_secret`.
   - SMTP passwords are encrypted at rest (Fernet). Production requires `DATA_ENCRYPTION_KEY`; local installs generate a key in `data/.data_key`. Keep that key out of backups of the database, or the encryption adds nothing.
   - Files are served or attached only from the requesting user's own folder, or from shared folders when the file name starts with a known prefix followed by exactly that user's id.
2. **Outbound requests**:
   - URLs supplied by users (portfolio websites) or scraped from job boards are fetched only if every address the host resolves to is public, on ports 80/443, with each redirect re-checked. Loopback, private, link-local (including cloud metadata) and other internal addresses are refused. A DNS answer can change between the check and the connection, so run behind an egress firewall if that matters to you.
   - LLM API keys are sent in request headers, never in URLs.
   - User data, uploaded documents, resumes, and profiles are partitioned per user ID in isolated directories (`data/uploads/<user_id>/`).
   - Cross-user file access and path traversal attempts (`..`, `.env`, database files) are strictly blocked with `403 Forbidden`.

3. **Zero Arbitrary Environment Manipulation**:
   - Configuration settings and environment variables cannot be modified by unauthenticated public web clients.
   - Sensitive environment files (`.env`) are never served or exposed via document preview or outreach endpoints.

4. **Outreach & Communication Safety**:
   - Outbound emails strictly enforce `SAFE_MODE=true` server-side by default, ensuring all generated applications are saved locally as RFC822 `.eml` drafts for manual review rather than sent live over SMTP.
   - Live email sending requires explicit user credentials and confirmation.

5. **Strict Geographic Exclusions**:
   - The job matching engine enforces a zero-tolerance exclusion filter on job postings located in or affiliated with prohibited regions.

## Reporting a Vulnerability

If you discover a potential security vulnerability, please report it responsibly by contacting the maintainers or opening a private security advisory on GitHub. Please do not publish security issues publicly until they have been addressed.
