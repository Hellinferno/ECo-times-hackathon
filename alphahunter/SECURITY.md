# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest (main) | Yes |
| older branches | No |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

To report a security issue, please open a [GitHub Security Advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) on this repository. This keeps the report private until a fix is available.

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

We aim to respond within 48 hours and to release a patch within 7 days for critical issues.

## Security Considerations for Deployers

AlphaHunter is a financial intelligence tool. Please review these before deploying:

**Authentication:**
- `AUTH_JWT_SECRET` must be a strong random value in production (min 32 characters).
  A startup warning is logged if the default demo value is detected.
- `AUTH_DEMO_PASSWORD` should be changed from the default before public deployment.
- The app currently supports single-user demo auth. Multi-user auth is on the roadmap.

**API Keys:**
- `GEMINI_API_KEY` and `MINO_API_KEY` are optional. The app degrades gracefully without them.
- Never commit `.env` files or API keys to version control.
- Use your hosting platform's secret management (Railway Variables, Vercel Environment Variables).

**Network:**
- The CORS configuration (`ALLOWED_ORIGINS`) uses exact-match + single-segment wildcard regex
  to prevent subdomain injection attacks (e.g. `evil.also.vercel.app`).
- Do not set `ALLOWED_ORIGINS=*` in production.

**Financial Disclaimer:**
AlphaHunter provides analysis for educational and informational purposes only. It does not
constitute financial advice. Never make investment decisions based solely on automated signals.
Past performance of backtested patterns does not guarantee future results.
