from sap_langgraph import run_pipeline


def test_pipeline_maps_valid_us_vendor_to_sap_fields():
    result = run_pipeline(
        {
            "vendor_name": "Acme Ltd",
            "email": "ap@acme.example",
            "tax_id": "us-12345",
            "country": "United States",
            "payment_terms": "net 30",
            "tax_code": "standard",
            "routing_number": "021000021",
            "bank_account": "1234567890",
            "swift_bic": "CHASUS33",
        }
    )

    assert result.halted is False
    assert result.errors == []
    assert result.data["vendor_name"] == "Acme"
    assert result.data["country"] == "US"
    assert result.data["currency"] == "USD"
    assert result.data["sap"]["NAME1"] == "Acme"
    assert result.data["sap"]["LAND1"] == "US"
    assert result.data["sap"]["ZTERM"] == "NET30"
    assert result.data["sap"]["MWSKZ"] == "A1"
    assert result.data["sap"]["BANKL"] == "021000021"


def test_validator_halts_pipeline_with_field_errors():
    result = run_pipeline(
        {
            "vendor_name": "",
            "email": "not-an-email",
            "tax_id": "!",
            "country": "US",
        }
    )

    assert result.halted is True
    assert result.completed_agents == ["validator"]
    assert {error.field for error in result.errors} >= {"vendor_name", "email", "tax_id"}


def test_bank_intelligence_rejects_missing_de_iban():
    result = run_pipeline(
        {
            "vendor_name": "Berlin Supply GmbH",
            "email": "ap@berlin.example",
            "tax_id": "DE12345",
            "country": "DE",
            "currency": "EUR",
        }
    )

    assert result.halted is True
    assert result.completed_agents[-1] == "bank_intelligence"
    assert result.errors[-1].field == "iban"
