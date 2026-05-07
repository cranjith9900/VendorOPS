from __future__ import annotations

import re
from typing import Any

from sap_agents.models import AgentError, AgentResult


SWIFT_BIC_PATTERN = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")
US_ROUTING_PATTERN = re.compile(r"^\d{9}$")
SORT_CODE_PATTERN = re.compile(r"^\d{6}$")


class BankIntelligenceAgent:
    """Rules-only bank validation and SAP bank state enrichment."""

    name = "bank_intelligence"

    def run(self, payload: dict[str, Any]) -> AgentResult:
        data = dict(payload)
        errors: list[AgentError] = []

        country = str(data.get("country", "")).upper()
        iban = self._compact(data.get("iban"))
        swift_bic = self._compact(data.get("swift_bic"))
        routing_number = self._compact(data.get("routing_number"))
        sort_code = self._compact(data.get("sort_code"))
        bank_account = self._compact(data.get("bank_account"))

        if iban:
            data["iban"] = iban
            if not self._valid_iban(iban):
                errors.append(AgentError(field="iban", message="Invalid IBAN", code="bank.invalid_iban"))

        if swift_bic:
            data["swift_bic"] = swift_bic
            if not SWIFT_BIC_PATTERN.match(swift_bic):
                errors.append(
                    AgentError(field="swift_bic", message="Invalid SWIFT/BIC", code="bank.invalid_swift")
                )

        if country == "US":
            if not routing_number or not bank_account:
                errors.append(
                    AgentError(
                        field="routing_number",
                        message="US bank details require routing_number and bank_account",
                        code="bank.missing_us_details",
                    )
                )
            elif not US_ROUTING_PATTERN.match(routing_number):
                errors.append(
                    AgentError(
                        field="routing_number",
                        message="routing_number must be 9 digits",
                        code="bank.invalid_us_routing",
                    )
                )
        elif country == "DE" and not iban:
            errors.append(
                AgentError(field="iban", message="DE bank details require IBAN", code="bank.missing_iban")
            )
        elif country == "GB":
            if iban:
                pass
            elif not sort_code:
                errors.append(
                    AgentError(
                        field="sort_code",
                        message="GB bank details require sort_code when IBAN is absent",
                        code="bank.missing_sort_code",
                    )
                )
            elif not SORT_CODE_PATTERN.match(sort_code):
                errors.append(
                    AgentError(
                        field="sort_code",
                        message="sort_code must be 6 digits",
                        code="bank.invalid_sort_code",
                    )
                )

        if bank_account:
            data["bank_account"] = bank_account
        if routing_number:
            data["routing_number"] = routing_number
        if sort_code:
            data["sort_code"] = sort_code

        sap = dict(data.get("sap") or {})
        if iban:
            sap["IBAN"] = iban
        if swift_bic:
            sap["SWIFT"] = swift_bic
        if routing_number:
            sap["BANKL"] = routing_number
        if bank_account:
            sap["BANKN"] = bank_account
        data["sap"] = sap

        return AgentResult(ok=not errors, data=data, errors=errors, agent=self.name)

    def _compact(self, value: Any) -> str:
        return re.sub(r"[\s\-]", "", str(value or "")).upper()

    def _valid_iban(self, value: str) -> bool:
        try:
            from schwifty import IBAN

            IBAN(value)
            return True
        except ImportError:
            return self._valid_iban_checksum(value)
        except ValueError:
            return False

    def _valid_iban_checksum(self, value: str) -> bool:
        if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", value):
            return False
        rearranged = value[4:] + value[:4]
        numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
        return int(numeric) % 97 == 1
