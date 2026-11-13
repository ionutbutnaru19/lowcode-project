# ClientHub Accounting Services

A Flask proof-of-concept portal for an accountant and two customer firms to exchange accounting documents securely.

## Included functionality

- Admin and customer roles; no public registration.
- Password login followed by TOTP multi-factor authentication.
- Admin can create and edit customer accounts.
- Admin can create document requests for a customer.
- Customers can view their own requests and upload one or multiple files, with or without a request.
- Customers can add an optional description when uploading documents.
- Admin has a separate document review queue and can approve, reject, or request a replacement.
- A reason is required for rejection and replacement requests.
- Customers and admins can view permitted document details, preview supported PDF, JPG, JPEG and PNG files in the browser, and download documents.
- Admins can view all customer documents, including pending, approved, rejected and replacement-requested documents.
- Customer ownership checks are enforced on request and document routes.
- Uploads use random stored filenames and an extension allowlist.
- Notifications are saved as local `.eml` files; no real email is sent.
- Retention cleanup can run manually or as a separate scheduled process.

## Technology

Python 3.12 or newer, Flask 3.x, Flask-SQLAlchemy, Flask-Login, Flask-WTF/CSRF, Jinja2, Tailwind CSS, SQLite, PyOTP and APScheduler.

## Public welcome homepage

The public homepage is available at `/` without signing in. It is branded **ClientHub Accounting Services** and provides two entry points:

- **I am already a customer** opens the existing `/login` route (password and MFA flow unchanged).
- **Submit your details** opens a portal route that redirects to the configured prospective-client Google Form.

The actual Google Form URL is already configured as the application's default, so no additional configuration is required for the current form.

If the Google Form changes, you can override the default URL using the GOOGLE_FORM_URL environment variable.

An accountant reviews submissions separately; this portal does not automatically create customer accounts from the form.

## Setup and installation

### 1. Get the project

Clone the repository using HTTPS:

```bash
git clone https://github.com/ionutbutnaru19/lowcode-project.git
cd lowcode-project/clienthub-app
```

Alternatively, download the repository as a ZIP file from GitHub, extract it, and open a terminal inside the `clienthub-app` folder.

### 2. Create and activate a virtual environment

For Windows Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

For Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

For macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install the application dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Initialise the database

```bash
flask --app app init-db
```

This creates the database tables and initial demonstration accounts.

A fresh clone does not include a database because database files are excluded from Git.

**Important:** This command does not migrate an existing database. If you have an older database from a previous ClientHub version, back it up first. If it contains only disposable demonstration data, stop the application, delete `clienthub.db`, and run the initialisation command again. Do not delete a database containing data you need.

### 5. Start the application

```bash
python app.py
```

Open the following address in your browser:

<http://127.0.0.1:5000>

To stop the application, press `Ctrl+C` in the terminal.

## Demonstration accounts

The following accounts are created during database initialisation:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@clienthub.local` | `AdminDemo!2026` |
| Customer 1 | `alice@example.local` | `AliceDemo!2026` |
| Customer 2 | `ben@example.local` | `BenDemo!2026` |

These credentials are for demonstration purposes only and must not be reused for real accounts.

### Multi-factor authentication

After initialising the database, open a second terminal, navigate to the `clienthub-app` folder, activate the virtual environment, and run:

```bash
flask --app app show-demo-codes
```

Enter the current six-digit code for the relevant account after password login.

Codes change every 30 seconds. For a real account, use the MFA security page to add the displayed secret or provisioning URI to an authenticator app.

## Retention cleanup

The default document retention period is six years (`RETENTION_DAYS=2190`).

For a short demonstration window, you can set `RETENTION_MINUTES` before running the cleanup command.

For Windows Git Bash, macOS or Linux:

```bash
export RETENTION_MINUTES=5
flask --app app cleanup-documents
```

For Windows PowerShell:

```powershell
$env:RETENTION_MINUTES = "5"
flask --app app cleanup-documents
```

This deletes uploaded documents older than five minutes. Use this setting only with disposable demonstration data.

The scheduled process can be run separately in another terminal:

```bash
flask --app app run-retention-scheduler
```

The scheduler runs nightly at 02:00 local server time. It must be started separately and kept running for scheduled cleanup to take place. Run it as a separate process rather than starting multiple schedulers inside web workers.

## Running the tests

Install the development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the automated tests:

```bash
python -m pytest
```

The tests check key application functionality, including authentication, access permissions and document handling.

## Local files and database

The following are created or used locally and are not committed to Git:

- `clienthub.db` – SQLite database.
- `uploads/` – uploaded document files.
- `emails/` – locally generated email notification files.
- `.venv/` – Python virtual environment.

The application creates the upload and email directories when needed. The database must be initialised using the command described above.

## Important limitations

This is coursework/demo software, not a production service.

Before real-world use, it would need additional security and operational improvements, including:

- HTTPS and secure secret management.
- Stronger MFA enrolment and recovery.
- Malware scanning and content-based file validation.
- Rate limiting and audit logging.
- PostgreSQL migrations, object storage and backups.
- Monitoring and a full security review.

The default development secret key must be replaced before deployment. Tailwind CSS is loaded from its CDN. No real emails are sent, and no real customer data should be uploaded.