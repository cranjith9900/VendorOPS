from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import Base, get_db
from main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_reference_tables():
    db = TestingSessionLocal()
    try:
        db.add_all(
            [
                models.T001(bukrs="1000", name="Test Company"),
                models.T052(zterm="NET30", description="Net 30 days"),
                models.T007A(mwskz="A1", rate=18),
                models.BNKA(bankl="BANK01", bank_name="Test Bank"),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "SAP adapter API is running"}


def test_oauth_token_endpoint():
    response = client.post("/oauth/token")

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "dummy-token",
        "token_type": "bearer",
    }


def test_create_and_get_business_partner():
    create_response = client.post(
        "/business_partner/",
        json={"bp_id": "BP001", "name": "Acme Ltd"},
    )
    get_response = client.get("/business_partner/BP001")

    assert create_response.status_code == 200
    assert create_response.json()["bp_id"] == "BP001"
    assert create_response.json()["name"] == "Acme Ltd"
    assert get_response.status_code == 200
    assert get_response.json()["bp_id"] == "BP001"
    assert get_response.json()["name"] == "Acme Ltd"


def test_get_missing_business_partner_returns_null():
    response = client.get("/business_partner/MISSING")

    assert response.status_code == 200
    assert response.json() is None


def test_add_and_get_bank_accounts():
    create_response = client.post(
        "/bank/",
        json={
            "bp_id": "BP001",
            "account_number": "1234567890",
            "bank_code": "BANK01",
        },
    )
    get_response = client.get("/bank/BP001")

    assert create_response.status_code == 200
    assert create_response.json()["bp_id"] == "BP001"
    assert create_response.json()["account_number"] == "1234567890"
    assert create_response.json()["bank_code"] == "BANK01"
    assert get_response.status_code == 200
    assert get_response.json() == [
        {
            "id": create_response.json()["id"],
            "bp_id": "BP001",
            "account_number": "1234567890",
            "bank_code": "BANK01",
        }
    ]


def test_get_company_code():
    seed_reference_tables()

    response = client.get("/tables/T001/1000")

    assert response.status_code == 200
    assert response.json() == {"bukrs": "1000", "name": "Test Company"}


def test_get_payment_term():
    seed_reference_tables()

    response = client.get("/tables/T052/NET30")

    assert response.status_code == 200
    assert response.json() == {"zterm": "NET30", "description": "Net 30 days"}


def test_get_tax_code():
    seed_reference_tables()

    response = client.get("/tables/T007A/A1")

    assert response.status_code == 200
    assert response.json() == {"mwskz": "A1", "rate": 18}


def test_get_bank_master():
    seed_reference_tables()

    response = client.get("/tables/BNKA/BANK01")

    assert response.status_code == 200
    assert response.json() == {"bankl": "BANK01", "bank_name": "Test Bank"}


def test_validate_reference_data_returns_valid():
    seed_reference_tables()

    response = client.post(
        "/tables/validate",
        json={"bukrs": "1000", "zterm": "NET30", "mwskz": "A1", "bankl": "BANK01"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "VALID"}


def test_validate_reference_data_returns_invalid():
    seed_reference_tables()

    response = client.post(
        "/tables/validate",
        json={
            "bukrs": "1000",
            "zterm": "NET30",
            "mwskz": "A1",
            "bankl": "UNKNOWN",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "INVALID"}
