# ClientHub Accounting Services --- Application Specification

## Purpose

ClientHub is a secure document-exchange portal for a small accounting
firm and its business customers. It replaces email and messaging-based
document collection with one central place to request, upload, review
and track accounting documents.

The proof of concept has one accountant (admin) and two customer firms.
Each customer can access only their own firm's information; the
accountant can manage all customer accounts and review all submitted
documents.

## Users and roles

-   **Admin (accountant):** one demo account. Can create and manage
    customer accounts, create document requests, view all customers'
    documents, and approve or reject submissions.
-   **Customer:** two demo accounts, one for each firm. Can view
    requests and documents belonging to their own firm, upload files,
    and respond to review outcomes.
-   There is no public registration. Customer accounts are created by
    the admin.

## Entities

### User

-   `id` (integer, primary key)
-   `name` (text, required)
-   `email` (text, required, unique)
-   `company` (text, required for customer accounts)
-   `password_hash` (text, required)
-   `role` (text, `admin` or `customer`)
-   `created_at` (timestamp)

### DocumentRequest

-   `id` (integer, primary key)
-   `customer_id` (integer, foreign key to `User`)
-   `title` (text, required; e.g. "October bank statement")
-   `description` (text, optional)
-   `status` (text; e.g. `open` or `complete`)
-   `created_at` (timestamp)

### Document

-   `id` (integer, primary key)
-   `customer_id` (integer, foreign key to `User`)
-   `request_id` (integer, foreign key to `DocumentRequest`, optional
    when uploaded without a request)
-   `original_filename` (text, required)
-   `stored_filename` (text, required; random name used for storage)
-   `review_status` (text; `pending`, `approved`, `rejected` or
    `replacement_requested`)
-   `review_reason` (text, required when rejecting or requesting a
    replacement/more information)
-   `uploaded_at` (timestamp)
-   `reviewed_at` (timestamp, optional)

### Message (planned Phase 4)

-   `id` (integer, primary key)
-   `customer_id` (integer, foreign key to `User`)
-   `sender_id` (integer, foreign key to `User`)
-   `body` (text, required)
-   `created_at` (timestamp)
-   `read_at` (timestamp, optional)

**Relationships:** A customer can have many document requests and
documents. A request can have many uploaded documents. A customer has
one conversation with the accountant in the planned chat extension. The
`Message` entity is not required for the committed base version.

## Routes

The following is the proposed Flask route structure for the committed
base version. All customer-specific routes must enforce ownership checks
on the server.

  --------------------------------------------------------------------------------
  Method                  Path                             Purpose
  ----------------------- -------------------------------- -----------------------
  GET, POST               `/login`                         Display sign-in form
                                                           and authenticate a user

  POST                    `/logout`                        Sign out the current
                                                           user

  GET                     `/`                              Show the appropriate
                                                           dashboard for the
                                                           signed-in role

  GET                     `/admin/customers`               Admin: list customer
                                                           accounts

  GET, POST               `/admin/customers/new`           Admin: create a
                                                           customer account

  GET, POST               `/admin/customers/<id>/edit`     Admin: view or update a
                                                           customer account

  GET                     `/requests`                      List requests visible
                                                           to the signed-in user

  GET, POST               `/admin/requests/new`            Admin: create a
                                                           document request for a
                                                           customer

  GET                     `/requests/<id>`                 Show a request and its
                                                           associated documents

  POST                    `/requests/<id>/complete`        Admin: mark a request
                                                           complete or reopen it

  GET, POST               `/documents/upload`              Customer: upload one or
                                                           more documents,
                                                           optionally linked to a
                                                           request

  GET                     `/documents/<id>`                View document details,
                                                           subject to role and
                                                           ownership checks

  GET                     `/admin/review`                  Admin: show the pending
                                                           document review queue

  POST                    `/admin/documents/<id>/review`   Admin: approve, reject
                                                           or request a
                                                           replacement/more
                                                           information

  GET                     `/account/security/mfa`          Set up or manage
                                                           authenticator-app MFA
  --------------------------------------------------------------------------------

The chat extension may later add customer conversation and message
routes. These are planned, not part of the minimum committed version.

## Document uploads and review

-   Accept JPG, PNG, HEIC, PDF, XLSX, CSV and DOCX files.
-   Allow a customer to upload one or multiple files, with or without an
    existing request.
-   Store uploaded files using randomly generated storage names rather
    than trusting the original filename.
-   New uploads enter the accountant's pending review queue.
-   The accountant can approve a document, reject it, or ask for a
    replacement or more information.
-   A reason is required for every decision other than approval.
-   Record the review decision and its timestamp. Notify the customer
    through simulated email.

## Technical constraints

-   Python 3.12 and Flask 3.
-   HTML and Jinja2 templates, using one shared base template.
-   Tailwind CSS for page styling.
-   Flask-Login for sign-in and session management.
-   Flask-WTF for forms and CSRF protection.
-   SQLite during development; PostgreSQL is planned for the deployment
    phase, using Flask-SQLAlchemy.
-   Local disk or a Docker volume for uploaded files.
-   Simulated email only: save local `.eml` files and use a Mailpit test
    inbox in Docker. Do not send real email.
-   Authenticator-app multi-factor authentication (TOTP) for all three
    demo accounts.
-   Enforce role and record-ownership checks on the server for every
    relevant request; hiding interface controls is not sufficient.
-   A scheduled retention job deletes documents older than the
    configured retention period. Use a short period in demo mode so the
    behaviour can be demonstrated.
-   Use Git/GitHub, Ruff, pytest, Bandit, Semgrep and pip-audit for
    version control, code quality, tests and security checks.
-   Docker Compose, gunicorn and AWS Lightsail/HTTPS are planned
    deployment technologies, not prerequisites for the initial base
    website.

## Automations and security

-   **Scheduled:** a nightly job removes documents older than the
    configured retention period. The real-world retention setting is
    expected to be about six years; demo mode uses a few minutes for a
    live demonstration.
-   **Triggered:** generate simulated notification emails when a
    document request is created, a document is uploaded, or a document
    is reviewed.
-   **Approval:** record the accountant's review decision and time;
    require a reason for rejection or a request for replacement/more
    information.
-   **Access control:** customers can see only their own firm's data.
    The admin can see and manage all customer data.
-   **MFA:** require authenticator-app codes for all three demo
    accounts.

## Out of scope

-   Ledger, invoicing and financial reports.
-   Online payments.
-   AI receipt reading and a public API.
-   Real email delivery; notifications are simulated in a local test
    inbox.
-   Public customer self-registration.
-   More than one accountant account.
-   Multiple conversation threads per customer.
-   Chat in the committed base version (planned Phase 4 extension).
-   PostgreSQL migration, Docker-based deployment and AWS Lightsail
    hosting in the committed base version (planned Phase 5 extension).
-   Kubernetes or multi-server hosting.
-   Real customer data; use fictional demo firms, users and documents
    only.

## Delivery phases

  -----------------------------------------------------------------------
  Phase                   Scope                   Status
  ----------------------- ----------------------- -----------------------
  1\. Base website        Sign-in, three demo     Committed
                          accounts, document      
                          requests, uploads,      
                          accountant review queue 
                          and Tailwind styling    

  2\. Automations and     Retention clean-up,     Committed
  security                triggered notification  
                          emails, approval        
                          workflow, MFA and role  
                          checks                  

  3\. Design and          ERD, role/CRUD table,   Committed
  compliance documents    level-1 data flow       
                          diagram, STRIDE threat  
                          table and GDPR write-up 

  4\. Chat extension      One in-portal           Planned
                          conversation per        
                          customer, unread counts 
                          and new-message         
                          notification email      

  5\. Deployment          PostgreSQL, Docker      Planned
                          Compose, AWS Lightsail  
                          and HTTPS               

  6\. Testing and         Role and automation     Committed
  submission              tests, security scans,  
                          evidence collection and 
                          demo video              
  -----------------------------------------------------------------------

## Assumptions and notes

-   This is a proof of concept, not a live accounting product.
-   All demo firms, users and documents are fictional.
-   The project uses Flask, as taught on the course; AI-assisted code
    must be reviewed and understood.
-   The ERD, data flow diagram, STRIDE analysis and GDPR documentation
    are design deliverables independent of the web framework.
-   The precise retention period and implementation tools for scheduled
    jobs and TOTP are to be confirmed during implementation.
-   The entity fields and route paths above turn the project scope into
    an implementable starting specification; adjust them if the final
    design documents establish different names or fields.
