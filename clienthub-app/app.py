import os
import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

import click
import pyotp
from apscheduler.schedulers.background import BackgroundScheduler
from flask import (
    Flask, abort, flash, redirect, render_template, request, send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required, login_user, logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "pdf", "xlsx", "csv", "docx"}

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = None


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    company = db.Column(db.String(160), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    mfa_secret = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class DocumentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    customer = db.relationship("User", backref="document_requests")
    documents = db.relationship("Document", backref="document_request", lazy=True)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey("document_request.id"), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    review_status = db.Column(db.String(30), nullable=False, default="pending")
    review_reason = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    customer = db.relationship("User", backref="documents")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{BASE_DIR / 'clienthub.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
        UPLOAD_FOLDER=str(BASE_DIR / "uploads"),
        EMAIL_FOLDER=str(BASE_DIR / "emails"),
        RETENTION_DAYS=int(os.environ.get("RETENTION_DAYS", "2190")),
        RETENTION_MINUTES=int(os.environ.get("RETENTION_MINUTES", "0")),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["EMAIL_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def admin_required():
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)

    def customer_required():
        if not current_user.is_authenticated or current_user.role != "customer":
            abort(403)

    def can_access_document(document):
        return current_user.role == "admin" or document.customer_id == current_user.id

    def send_simulated_email(to_address, subject, body):
        """Save an email message locally; no email is sent."""
        message = EmailMessage()
        message["To"] = to_address
        message["From"] = "no-reply@clienthub.local"
        message["Subject"] = subject
        message.set_content(body)
        filename = f"{datetime.utcnow():%Y%m%d%H%M%S}_{secrets.token_hex(6)}.eml"
        (Path(app.config["EMAIL_FOLDER"]) / filename).write_bytes(message.as_bytes())

    def notify_admin(subject, body):
        admins = User.query.filter_by(role="admin").all()
        for admin in admins:
            send_simulated_email(admin.email, subject, body)

    def notify_customer(customer, subject, body):
        send_simulated_email(customer.email, subject, body)

    def is_allowed(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.get("/")
    @login_required
    def index():
        return redirect(url_for("dashboard"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        if current_user.role == "admin":
            pending = Document.query.filter_by(review_status="pending").order_by(
                Document.uploaded_at.asc()
            ).all()
            customers = User.query.filter_by(role="customer").order_by(User.name).all()
            return render_template(
                "admin_dashboard.html", pending=pending, customers=customers
            )

        requests_list = DocumentRequest.query.filter_by(
            customer_id=current_user.id
        ).order_by(DocumentRequest.created_at.desc()).all()

        documents = Document.query.filter_by(
            customer_id=current_user.id
        ).order_by(Document.uploaded_at.desc()).all()

        return render_template(
            "customer_dashboard.html",
            requests_list=requests_list,
            documents=documents,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                # Authentication is completed only after MFA verification.
                from flask import session
                session["mfa_user_id"] = user.id
                return redirect(url_for("verify_mfa"))

            flash("Invalid email address or password.", "error")

        return render_template("login.html")

    @app.route("/verify-mfa", methods=["GET", "POST"])
    def verify_mfa():
        from flask import session

        user_id = session.get("mfa_user_id")
        user = db.session.get(User, user_id) if user_id else None

        if not user:
            flash("Please sign in first.", "error")
            return redirect(url_for("login"))

        if request.method == "POST":
            code = request.form.get("code", "").strip()

            if pyotp.TOTP(user.mfa_secret).verify(code, valid_window=1):
                session.pop("mfa_user_id", None)
                login_user(user)
                return redirect(url_for("dashboard"))

            flash("Invalid authentication code.", "error")

        return render_template("verify_mfa.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "success")
        return redirect(url_for("login"))

    @app.get("/admin/customers")
    @login_required
    def customers():
        admin_required()
        customers_list = User.query.filter_by(role="customer").order_by(
            User.name
        ).all()
        return render_template("customers.html", customers=customers_list)

    @app.route("/admin/customers/new", methods=["GET", "POST"])
    @login_required
    def customer_new():
        admin_required()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            company = request.form.get("company", "").strip()
            password = request.form.get("password", "")

            if not all([name, email, company, password]):
                flash(
                    "Name, email, company and temporary password are required.",
                    "error",
                )
            elif len(name) > 120:
                flash("Name must be 120 characters or fewer.", "error")
            elif len(email) > 255:
                flash("Email must be 255 characters or fewer.", "error")
            elif len(company) > 160:
                flash("Company name must be 160 characters or fewer.", "error")
            elif User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
            else:
                user = User(
                    name=name,
                    email=email,
                    company=company,
                    role="customer",
                    mfa_secret=pyotp.random_base32(),
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                flash(
                    "Customer account created. Set up their authenticator "
                    "using the MFA page.",
                    "success",
                )
                return redirect(url_for("customers"))

        return render_template("customer_form.html", customer=None)

    @app.route("/admin/customers/<int:customer_id>/edit", methods=["GET", "POST"])
    @login_required
    def customer_edit(customer_id):
        admin_required()
        customer = db.get_or_404(User, customer_id)

        if customer.role != "customer":
            abort(404)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            company = request.form.get("company", "").strip()

            duplicate = User.query.filter(
                User.email == email,
                User.id != customer.id,
            ).first()

            if not all([name, email, company]):
                flash("Name, email and company are required.", "error")
            elif len(name) > 120:
                flash("Name must be 120 characters or fewer.", "error")
            elif len(email) > 255:
                flash("Email must be 255 characters or fewer.", "error")
            elif len(company) > 160:
                flash("Company name must be 160 characters or fewer.", "error")
            elif duplicate:
                flash("Another account already uses that email.", "error")
            else:
                customer.name = name
                customer.email = email
                customer.company = company

                new_password = request.form.get("password", "")
                if new_password:
                    customer.set_password(new_password)

                db.session.commit()
                flash("Customer account updated.", "success")
                return redirect(url_for("customers"))

        return render_template("customer_form.html", customer=customer)

    @app.get("/requests")
    @login_required
    def requests_list():
        if current_user.role == "admin":
            items = DocumentRequest.query.order_by(
                DocumentRequest.created_at.desc()
            ).all()
        else:
            items = DocumentRequest.query.filter_by(
                customer_id=current_user.id
            ).order_by(DocumentRequest.created_at.desc()).all()

        return render_template("requests.html", requests_list=items)

    @app.route("/admin/requests/new", methods=["GET", "POST"])
    @login_required
    def request_new():
        admin_required()

        customers_list = User.query.filter_by(role="customer").order_by(
            User.name
        ).all()

        if request.method == "POST":
            customer_id = request.form.get("customer_id", type=int)
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()

            customer = db.session.get(User, customer_id) if customer_id else None

            if not customer or customer.role != "customer" or not title:
                flash("Choose a customer and enter a request title.", "error")
            elif len(title) > 160:
                flash(
                    "Request title must be 160 characters or fewer.",
                    "error",
                )
            else:
                item = DocumentRequest(
                    customer_id=customer.id,
                    title=title,
                    description=description,
                )
                db.session.add(item)
                db.session.commit()

                notify_customer(
                    customer,
                    "New document request",
                    f"A new request was created: {title}",
                )
                flash(
                    "Document request created and simulated email saved.",
                    "success",
                )
                return redirect(url_for("requests_list"))

        return render_template("request_form.html", customers=customers_list)

    @app.get("/requests/<int:request_id>")
    @login_required
    def request_detail(request_id):
        item = db.get_or_404(DocumentRequest, request_id)

        if current_user.role != "admin" and item.customer_id != current_user.id:
            abort(403)

        return render_template("request_detail.html", item=item)

    @app.post("/requests/<int:request_id>/complete")
    @login_required
    def request_complete(request_id):
        item = db.get_or_404(DocumentRequest, request_id)

        if current_user.role != "admin":
            abort(403)

        item.status = "complete" if item.status == "open" else "open"
        db.session.commit()

        flash(f"Request marked {item.status}.", "success")
        return redirect(url_for("request_detail", request_id=item.id))

    @app.route("/documents/upload", methods=["GET", "POST"])
    @login_required
    def document_upload():
        customer_required()

        requests_for_customer = DocumentRequest.query.filter_by(
            customer_id=current_user.id,
            status="open",
        ).order_by(DocumentRequest.created_at.desc()).all()

        if request.method == "POST":
            files = [
                f for f in request.files.getlist("files")
                if f and f.filename
            ]

            request_id = request.form.get("request_id", type=int)
            linked_request = None

            if request_id:
                linked_request = db.session.get(DocumentRequest, request_id)

                if (
                    not linked_request
                    or linked_request.customer_id != current_user.id
                ):
                    abort(403)

            # Clean filenames before checking their length or extension.
            cleaned_files = [
                (file, secure_filename(file.filename) or "uploaded-file")
                for file in files
            ]

            if not files:
                flash("Choose at least one file.", "error")

            elif any(
                len(original) > 255
                for file, original in cleaned_files
            ):
                flash(
                    "Filename must be 255 characters or fewer.",
                    "error",
                )

            elif any(
                not is_allowed(original)
                for file, original in cleaned_files
            ):
                flash(
                    "One or more files have an unsupported type.",
                    "error",
                )

            else:
                saved = []

                for file, original in cleaned_files:
                    extension = original.rsplit(".", 1)[1].lower()
                    stored = f"{secrets.token_hex(16)}.{extension}"

                    file.save(Path(app.config["UPLOAD_FOLDER"]) / stored)

                    document = Document(
                        customer_id=current_user.id,
                        request_id=(
                            linked_request.id if linked_request else None
                        ),
                        original_filename=original,
                        stored_filename=stored,
                        review_status="pending",
                    )

                    db.session.add(document)
                    saved.append(original)

                db.session.commit()

                notify_admin(
                    "New documents uploaded",
                    f"{current_user.company} uploaded {len(saved)} "
                    f"document(s): {', '.join(saved)}",
                )

                flash(
                    f"{len(saved)} document(s) uploaded and sent for review.",
                    "success",
                )
                return redirect(url_for("dashboard"))

        return render_template(
            "upload.html",
            requests_for_customer=requests_for_customer,
        )

    @app.get("/documents/<int:document_id>")
    @login_required
    def document_detail(document_id):
        document = db.get_or_404(Document, document_id)

        if not can_access_document(document):
            abort(403)

        return render_template("document_detail.html", document=document)

    @app.get("/documents/<int:document_id>/download")
    @login_required
    def document_download(document_id):
        document = db.get_or_404(Document, document_id)

        if not can_access_document(document):
            abort(403)

        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            document.stored_filename,
            as_attachment=True,
            download_name=document.original_filename,
        )

    @app.get("/admin/review")
    @login_required
    def review_queue():
        admin_required()

        pending = Document.query.filter_by(
            review_status="pending"
        ).order_by(Document.uploaded_at.asc()).all()

        return render_template("review_queue.html", pending=pending)

    @app.post("/admin/documents/<int:document_id>/review")
    @login_required
    def review_document(document_id):
        admin_required()
        document = db.get_or_404(Document, document_id)

        decision = request.form.get("decision", "")
        reason = request.form.get("reason", "").strip()

        if decision not in {"approved", "rejected", "replacement_requested"}:
            abort(400)

        if decision != "approved" and not reason:
            flash(
                "A reason is required when rejecting or requesting a replacement.",
                "error",
            )
            return redirect(url_for("review_queue"))

        document.review_status = decision
        document.review_reason = reason or None
        document.reviewed_at = datetime.utcnow()
        db.session.commit()

        label = decision.replace("_", " ")

        notify_customer(
            document.customer,
            f"Document {label}",
            f"Your document '{document.original_filename}' was {label}. "
            f"Reason: {reason or 'No reason supplied.'}",
        )

        flash("Review saved and simulated email created.", "success")
        return redirect(url_for("review_queue"))

    @app.get("/account/security/mfa")
    @login_required
    def mfa_security():
        totp = pyotp.TOTP(current_user.mfa_secret)

        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name="ClientHub",
        )

        return render_template(
            "mfa_security.html",
            secret=current_user.mfa_secret,
            provisioning_uri=provisioning_uri,
            current_code=totp.now(),
        )

    def cleanup_old_documents():
        now = datetime.utcnow()
        minutes = app.config["RETENTION_MINUTES"]

        cutoff = now - (
            timedelta(minutes=minutes)
            if minutes > 0
            else timedelta(days=app.config["RETENTION_DAYS"])
        )

        old_documents = Document.query.filter(
            Document.uploaded_at < cutoff
        ).all()

        for document in old_documents:
            path = Path(app.config["UPLOAD_FOLDER"]) / document.stored_filename
            path.unlink(missing_ok=True)
            db.session.delete(document)

        db.session.commit()
        return len(old_documents)

    @app.cli.command("init-db")
    def init_db():
        """Create tables and seed the three demonstration accounts."""
        db.create_all()

        if not User.query.filter_by(
            email="admin@clienthub.local"
        ).first():
            demo_users = [
                (
                    "ClientHub Accountant",
                    "admin@clienthub.local",
                    "ClientHub Accounting Services",
                    "admin",
                    "AdminDemo!2026",
                    "JBSWY3DPEHPK3PXP",
                ),
                (
                    "Alice Customer",
                    "alice@example.local",
                    "Alice Design Studio Ltd",
                    "customer",
                    "AliceDemo!2026",
                    "KRSXG5DSNFXGOIDB",
                ),
                (
                    "Ben Customer",
                    "ben@example.local",
                    "Ben Services Ltd",
                    "customer",
                    "BenDemo!2026",
                    "MFRGGZDFMZTWQ2LK",
                ),
            ]

            for name, email, company, role, password, secret in demo_users:
                user = User(
                    name=name,
                    email=email,
                    company=company,
                    role=role,
                    mfa_secret=secret,
                )
                user.set_password(password)
                db.session.add(user)

            db.session.commit()

        click.echo(
            "Database ready. Use 'flask --app app show-demo-codes' for MFA codes."
        )

    @app.cli.command("show-demo-codes")
    def show_demo_codes():
        for user in User.query.order_by(User.id).all():
            click.echo(
                f"{user.email}: {pyotp.TOTP(user.mfa_secret).now()}"
            )

    @app.cli.command("cleanup-documents")
    def cleanup_command():
        count = cleanup_old_documents()
        click.echo(f"Deleted {count} expired document(s).")

    @app.cli.command("run-retention-scheduler")
    def run_retention_scheduler():
        """Run the nightly retention job as a separate process."""
        from time import sleep

        local_scheduler = BackgroundScheduler(daemon=True)
        local_scheduler.add_job(
            cleanup_old_documents,
            "cron",
            hour=2,
            minute=0,
        )
        local_scheduler.start()

        click.echo("Retention scheduler running. Press Ctrl+C to stop.")

        try:
            while True:
                sleep(60)
        except KeyboardInterrupt:
            local_scheduler.shutdown()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
