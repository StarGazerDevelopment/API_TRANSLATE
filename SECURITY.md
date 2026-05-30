# Security Policy

## Supported Versions
The latest `main` branch is the supported version for security updates.

## Reporting A Vulnerability
- Do not open public issues for sensitive vulnerabilities
- Report the issue privately to the maintainers
- Include reproduction steps, impact, and any known affected routes or providers

## Security Design Notes
- Provider secrets are written to backend `.env` and masked in UI responses
- Dashboard passwords are hashed with bcrypt through `passlib`
- Session state uses cookies and CSRF token checks
- Secure headers are enabled by default
- CORS is configurable from the settings API
- Logs are intended for observability and should not contain secrets
