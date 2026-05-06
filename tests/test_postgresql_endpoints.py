import os
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import Base, get_db
from main import app


POSTGRES_TEST_DATABASE_URL = os.getenv("POSTGRES_TEST_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not POSTGRES_TEST_DATABASE_URL,
    reason="Set POSTGRES_TEST_DATABASE_URL to run PostgreSQL endpoint tests.",
)


def _assert_safe_test_database_url(database_url: str) -> None:
    parsed = urlparse(database_url)

    if parsed.scheme not in {"postgresql", "postgresql+psycopg2"}:
        pytest.fail("POSTGRES_TEST_DATABASE_URL must use a PostgreSQL URL.")

    database_name = parsed.path.lstrip("/")
    if "test" not in database_name.lower() and os.getenv("ALLOW_NON_TEST_POSTGRES") != "1":
        pytest.fail(
            "Refusing to reset a PostgreSQL database whose name does not contain "
            "'test'. Set ALLOW_NON_TEST_POSTGRES=1 only if this is intentional."
        )


if POSTGRES_TEST_DATABASE_URL:
    _assert_safe_test_database_url(POSTGRES_TEST_DATABASE_URL)
    postgres_engine = create_engine(POSTGRES_TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=postgres_engine,
    )
else:
    postgres_engine = None
    TestingSessionLocal = None


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def postgres_test_db():
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=postgres_engine)
    Base.metadata.create_all(bind=postgres_engine)

    yield

    Base.metadata.drop_all(bind=postgres_engine)
    app.dependency_overrides = previous_overrides


@pytest.fixture
def client():
    return TestClient(app)


def seed_reference_tables():
    db = TestingSessionLocal()
    try:
        db.add_all(
            [
                models.T001(bukrs="1000", name="PostgreSQL Test Company"),
                models.T052(zterm="NET30", description="Net 30 days"),
                models.T007A(mwskz="A1", rate=18),
                models.BNKA(bankl="BANK01", bank_name="PostgreSQL Test Bank"),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_all_endpoints_with_postgresql_data(client):
    seed_reference_tables()

    root_response = client.get("/")
    token_response = client.post("/oauth/token")
    create_bp_response = client.post(
        "/business_partner/",
        json={"bp_id": "BP001", "name": "Acme PostgreSQL Ltd"},
    )
    get_bp_response = client.get("/business_partner/BP001")
    create_bank_response = client.post(
        "/bank/",
        json={
            "bp_id": "BP001",
            "account_number": "9876543210",
            "bank_code": "BANK01",
        },
    )
    get_banks_response = client.get("/bank/BP001")
    company_response = client.get("/tables/T001/1000")
    payment_term_response = client.get("/tables/T052/NET30")
    tax_response = client.get("/tables/T007A/A1")
    bank_master_response = client.get("/tables/BNKA/BANK01")
    valid_response = client.post(
        "/tables/validate",
        json={"bukrs": "1000", "zterm": "NET30", "mwskz": "A1", "bankl": "BANK01"},
    )
    invalid_response = client.post(
        "/tables/validate",
        json={
            "bukrs": "1000",
            "zterm": "NET30",
            "mwskz": "A1",
            "bankl": "UNKNOWN",
        },
    )

    assert root_response.status_code == 200
    assert root_response.json() == {"status": "SAP adapter API is running"}

    assert token_response.status_code == 200
    assert token_response.json() == {
        "access_token": "dummy-token",
        "token_type": "bearer",
    }

    assert create_bp_response.status_code == 200
    assert create_bp_response.json()["bp_id"] == "BP001"
    assert create_bp_response.json()["name"] == "Acme PostgreSQL Ltd"

    assert get_bp_response.status_code == 200
    assert get_bp_response.json()["bp_id"] == "BP001"
    assert get_bp_response.json()["name"] == "Acme PostgreSQL Ltd"

    assert create_bank_response.status_code == 200
    assert create_bank_response.json()["bp_id"] == "BP001"
    assert create_bank_response.json()["account_number"] == "9876543210"
    assert create_bank_response.json()["bank_code"] == "BANK01"

    assert get_banks_response.status_code == 200
    assert get_banks_response.json() == [
        {
            "id": create_bank_response.json()["id"],
            "bp_id": "BP001",
            "account_number": "9876543210",
            "bank_code": "BANK01",
        }
    ]

    assert company_response.status_code == 200
    assert company_response.json() == {
        "bukrs": "1000",
        "name": "PostgreSQL Test Company",
    }

    assert payment_term_response.status_code == 200
    assert payment_term_response.json() == {
        "zterm": "NET30",
        "description": "Net 30 days",
    }

    assert tax_response.status_code == 200
    assert tax_response.json() == {"mwskz": "A1", "rate": 18}

    assert bank_master_response.status_code == 200
    assert bank_master_response.json() == {
        "bankl": "BANK01",
        "bank_name": "PostgreSQL Test Bank",
    }

    assert valid_response.status_code == 200
    assert valid_response.json() == {"status": "VALID"}

    assert invalid_response.status_code == 200
    assert invalid_response.json() == {"status": "INVALID"}
