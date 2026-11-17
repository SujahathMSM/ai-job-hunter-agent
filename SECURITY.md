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
   - User data, uploaded documents, resumes, and profiles are partitioned per user ID in isolated directories (`data/uploads/<user_id>/`).
   - Cross-user file access and path traversal attempts (`..`, `.env`, database files) are strictly blocked with `403 Forbidden`.

2. **Zero Arbitrary Environment Manipulation**:
   - Configuration settings and environment variables cannot be modified by unauthenticated public web clients.
   - Sensitive environment files (`.env`) are never served or exposed via document preview or outreach endpoints.

3. **Outreach & Communication Safety**:
   - Outbound emails strictly enforce `SAFE_MODE=true` server-side by default, ensuring all generated applications are saved locally as RFC822 `.eml` drafts for manual review rather than sent live over SMTP.
   - Live email sending requires explicit user credentials and confirmation.

4. **Strict Geographic Exclusions**:
   - The job matching engine enforces a zero-tolerance exclusion filter on job postings located in or affiliated with prohibited regions.

## Reporting a Vulnerability

If you discover a potential security vulnerability, please report it responsibly by contacting the maintainers or opening a private security advisory on GitHub. Please do not publish security issues publicly until they have been addressed.
