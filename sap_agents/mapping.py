from __future__ import annotations

from typing import Any

from sap_agents.llm import AnthropicJsonFallback
from sap_agents.models import AgentResult


FIELD_MAP = {
    "vendor_name": "NAME1",
    "country": "LAND1",
    "company_code": "BUKRS",
    "currency": "WAERS",
    "payment_terms": "ZTERM",
    "tax_code": "MWSKZ",
    "tax_id": "STCD1",
    "email": "SMTP_ADDR",
    "address": "STRAS",
    "phone": "TELF1",
    "bank_key": "BANKL",
    "bank_account": "BANKN",
    "iban": "IBAN",
    "swift_bic": "SWIFT",
}

PAYMENT_TERMS = {
    "net 30": "NET30",
    "net30": "NET30",
    "30 days": "NET30",
    "due immediately": "0001",
    "immediate": "0001",
}

TAX_CODES = {
    "standard": "A1",
    "standard vat": "A1",
    "zero": "A0",
    "zero rated": "A0",
    "exempt": "E0",
}


class MappingAgent:
    """Lookup-table mapping agent with optional Anthropic fallback for unknown codes."""

    name = "mapping"

    def __init__(self, llm: AnthropicJsonFallback | None = None) -> None:
        self.llm = llm or AnthropicJsonFallback()

    def run(self, payload: dict[str, Any]) -> AgentResult:
        data = dict(payload)
        warnings: list[str] = []

        if data.get("payment_terms"):
            data["payment_terms"] = self._map_payment_terms(str(data["payment_terms"]))
        if data.get("tax_code"):
            data["tax_code"] = self._map_tax_code(str(data["tax_code"]))

        sap_data = {
            sap_field: data[source_field]
            for source_field, sap_field in FIELD_MAP.items()
            if data.get(source_field) not in (None, "")
        }

        unresolved = [
            field
            for field in ("payment_terms", "tax_code")
            if payload.get(field) and data.get(field) == payload.get(field)
        ]
        if unresolved:
            fallback = self._llm_map(data, unresolved)
            if fallback:
                sap_data.update(fallback)
            else:
                warnings.append(f"Unmapped SAP values: {', '.join(unresolved)}")

        data["sap"] = sap_data
        return AgentResult(ok=True, data=data, warnings=warnings, agent=self.name)

    def _map_payment_terms(self, value: str) -> str:
        return PAYMENT_TERMS.get(value.strip().casefold(), value.strip().upper())

    def _map_tax_code(self, value: str) -> str:
        return TAX_CODES.get(value.strip().casefold(), value.strip().upper())

    def _llm_map(self, data: dict[str, Any], unresolved: list[str]) -> dict[str, Any] | None:
        return self.llm.complete_json(
            "Map only the requested unresolved vendor values to SAP field names. "
            "Return only JSON using SAP keys such as ZTERM or MWSKZ.",
            {"data": data, "unresolved": unresolved},
        )
