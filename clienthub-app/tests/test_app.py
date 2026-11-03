import io
import pyotp
import pytest

from app import create_app, db, User, DocumentRequest, Document


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "EMAIL_FOLDER": str(tmp_path / "emails"),
        "RETENTION_DAYS": 2190,
        "RETENTION_MINUTES": 0,
    })
    with app.app_context():
        db.create_all()
        admin = User(name="Admin", email="admin@test.local", company="Hub",
                     role="admin", mfa_secret="JBSWY3DPEHPK3PXP")
        admin.set_password("Password123!")
        alice = User(name="Alice", email="alice@test.local", company="Alice Ltd",
                     role="customer", mfa_secret="KRSXG5DSNFXGOIDB")
        alice.set_password("Password123!")
        ben = User(name="Ben", email="ben@test.local", company="Ben Ltd",
                   role="customer", mfa_secret="MFRGGZDFMZTWQ2LK")
        ben.set_password("Password123!")
        db.session.add_all([admin, alice, ben])
        db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, secret):
    response = client.post("/login", data={"email": email, "password": "Password123!"})
    assert response.status_code == 302
    response = client.post("/verify-mfa", data={"code": pyotp.TOTP(secret).now()})
    assert response.status_code == 302


def test_mfa_is_required_before_authentication(client):
    response = client.post("/login", data={"email": "alice@test.local", "password": "Password123!"})
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 302
    response = client.post("/verify-mfa", data={"code": pyotp.TOTP("KRSXG5DSNFXGOIDB").now()})
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 200


def test_customer_cannot_access_admin_review(client):
    login(client, "alice@test.local", "KRSXG5DSNFXGOIDB")
    assert client.get("/admin/review").status_code == 403


def test_customer_cannot_view_another_customers_request(client, app):
    with app.app_context():
        ben = User.query.filter_by(email="ben@test.local").one()
        item = DocumentRequest(customer_id=ben.id, title="Private docs", description="")
        db.session.add(item)
        db.session.commit()
        request_id = item.id
    login(client, "alice@test.local", "KRSXG5DSNFXGOIDB")
    assert client.get(f"/requests/{request_id}").status_code == 403


def test_multi_file_upload_and_cross_customer_download_protection(client, app):
    login(client, "alice@test.local", "KRSXG5DSNFXGOIDB")
    response = client.post("/documents/upload", data={
        "files": [
            (io.BytesIO(b"first file"), "first.pdf"),
            (io.BytesIO(b"second file"), "second.csv"),
        ]
    }, content_type="multipart/form-data")
    assert response.status_code == 302
    with app.app_context():
        docs = Document.query.all()
        assert len(docs) == 2
        assert all(doc.review_status == "pending" for doc in docs)
        ben = User.query.filter_by(email="ben@test.local").one()
        foreign = Document(
            customer_id=ben.id, original_filename="private.pdf",
            stored_filename="not-present.pdf", review_status="pending",
        )
        db.session.add(foreign)
        db.session.commit()
        foreign_id = foreign.id
    assert client.get(f"/documents/{foreign_id}").status_code == 403
    assert client.get(f"/documents/{foreign_id}/download").status_code == 403


def test_review_requires_reason_for_rejection(client, app):
    with app.app_context():
        alice = User.query.filter_by(email="alice@test.local").one()
        doc = Document(customer_id=alice.id, original_filename="x.pdf",
                       stored_filename="x.pdf", review_status="pending")
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id
    login(client, "admin@test.local", "JBSWY3DPEHPK3PXP")
    response = client.post(f"/admin/documents/{doc_id}/review", data={
        "decision": "rejected", "reason": ""
    })
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Document, doc_id).review_status == "pending"


def test_admin_can_edit_customer(client, app):
    login(client, "admin@test.local", "JBSWY3DPEHPK3PXP")
    with app.app_context():
        alice = User.query.filter_by(email="alice@test.local").one()
        alice_id = alice.id
    response = client.post(f"/admin/customers/{alice_id}/edit", data={
        "name": "Alice Updated", "email": "alice@test.local",
        "company": "Alice Updated Ltd", "password": ""
    })
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(User, alice_id).company == "Alice Updated Ltd"
