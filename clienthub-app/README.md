# ClientHub Accounting Services

A Flask proof-of-concept portal for an accountant and two customer firms to exchange accounting documents securely.

## Included functionality

- Admin and customer roles; no public registration.
- Password login followed by TOTP multi-factor authentication.
- Admin can create and edit customer accounts.
- Admin can create document requests for a customer.
- Customers can view their own requests and upload one or multiple files, with or without a request.
- Admin has a separate document review queue and can approve, reject, or request a replacement.
- A reason is required for rejection and replacement requests.
- Customers and admins can view permitted document details and download files.
- Customer ownership checks are enforced on request and document routes.
- Uploads use random stored filenames and an extension allowlist.
- Notifications are saved as local `.eml` files; no real email is sent.
- Retention cleanup can run manually or as a separate scheduled process.

## Technology

Python 3.12 recommended, Flask 3.x, Flask-SQLAlchemy, Flask-Login, Flask-WTF/CSRF, Jinja2, Tailwind CSS, SQLite, PyOTP and APScheduler.

## Setup (Git Bash on Windows)

Open Git Bash in the project folder:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
flask --app app init-db
flask --app app run --debug
```

Open <http://127.0.0.1:5000>.

If you have an older database from a previous ClientHub version, back it up first. This updated version changes database column names to match the specification. For a disposable demo database, stop Flask, delete `clienthub.db`, then run `flask --app app init-db` again. Do not delete a database containing data you need.

## Demonstration accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@clienthub.local` | `AdminDemo!2026` |
| Customer 1 | `alice@example.local` | `AliceDemo!2026` |
| Customer 2 | `ben@example.local` | `BenDemo!2026` |

After the database is initialized, run:

```bash
flask --app app show-demo-codes
```

Enter the current six-digit code for the account after password login. Codes change every 30 seconds. For a real account, use the MFA security page to add the displayed secret/provisioning URI to an authenticator app.

## Retention cleanup

Default retention is six years (`RETENTION_DAYS=2190`). For a short demonstration window, set `RETENTION_MINUTES` before starting the app, for example:

```bash
export RETENTION_MINUTES=5
flask --app app cleanup-documents
```

This will delete uploaded documents older than five minutes. Use only with disposable demo data. The scheduled process can be run separately in another terminal:

```bash
flask --app app run-retention-scheduler
```

The scheduler runs nightly at 02:00 local server time. Run it as a separate process rather than starting multiple schedulers inside web workers.

## Tests and code quality

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
bandit -r app.py
pip-audit
```

Semgrep is optional and can be run with:

```bash
semgrep scan --config auto .
```

## Important limitations

This is coursework/demo software, not a production service. Before real use, add HTTPS, secure secret management, stronger MFA enrolment/recovery, malware scanning, content-based file validation, rate limiting, audit logging, PostgreSQL migrations, object storage, backups, monitoring and a security review. The default development secret key must be replaced. Tailwind is loaded from its CDN. No real emails are sent and no customer data should be uploaded.
