import os
from uuid import uuid4

import httpx


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def assert_response(response, expected_status=200):
    assert response.status_code == expected_status, (
        f"{response.request.method} {response.request.url} returned "
        f"{response.status_code}: {response.text}"
    )
    return response.json()


def main():
    bp_id = f"BP{uuid4().hex[:8].upper()}"

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        root = assert_response(client.get("/"))
        token = assert_response(client.post("/oauth/token"))

        created_bp = assert_response(
            client.post(
                "/business_partner/",
                json={"bp_id": bp_id, "name": "Acme PostgreSQL Ltd"},
            )
        )
        fetched_bp = assert_response(client.get(f"/business_partner/{bp_id}"))

        created_bank = assert_response(
            client.post(
                "/bank/",
                json={
                    "bp_id": bp_id,
                    "account_number": "9876543210",
                    "bank_code": "BANK01",
                },
            )
        )
        fetched_banks = assert_response(client.get(f"/bank/{bp_id}"))

        company = assert_response(client.get("/tables/T001/1000"))
        payment_term = assert_response(client.get("/tables/T052/NET30"))
        tax = assert_response(client.get("/tables/T007A/A1"))
        bank_master = assert_response(client.get("/tables/BNKA/BANK01"))
        valid = assert_response(
            client.post(
                "/tables/validate",
                json={
                    "bukrs": "1000",
                    "zterm": "NET30",
                    "mwskz": "A1",
                    "bankl": "BANK01",
                },
            )
        )
        invalid = assert_response(
            client.post(
                "/tables/validate",
                json={
                    "bukrs": "1000",
                    "zterm": "NET30",
                    "mwskz": "A1",
                    "bankl": "UNKNOWN",
                },
            )
        )

    assert root == {"status": "SAP adapter API is running"}
    assert token == {"access_token": "dummy-token", "token_type": "bearer"}
    assert created_bp["bp_id"] == bp_id
    assert fetched_bp["name"] == "Acme PostgreSQL Ltd"
    assert created_bank["bank_code"] == "BANK01"
    assert fetched_banks[0]["account_number"] == "9876543210"
    assert company["name"] == "PostgreSQL Test Company"
    assert payment_term["description"] == "Net 30 days"
    assert tax["rate"] == 18
    assert bank_master["bank_name"] == "PostgreSQL Test Bank"
    assert valid == {"status": "VALID"}
    assert invalid == {"status": "INVALID"}

    print("All endpoints passed live smoke testing.")


if __name__ == "__main__":
    main()
