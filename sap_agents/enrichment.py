from __future__ import annotations

import re
from typing import Any

from sap_agents.llm import AnthropicJsonFallback
from sap_agents.models import AgentResult


COUNTRY_ALIASES = {
    "usa": "US",
    "u.s.a.": "US",
    "united states": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "germany": "DE",
    "india": "IN",
}

CURRENCY_BY_COUNTRY = {
    "DE": "EUR",
    "GB": "GBP",
    "IN": "INR",
    "US": "USD",
}

VENDOR_SUFFIX_PATTERN = re.compile(
    r"\s+(limited|ltd\.?|inc\.?|llc|gmbh|corp\.?|corporation|private limited|pvt\.?\s+ltd\.?)$",
    re.IGNORECASE,
)


class EnrichmentAgent:
    """Rules-first enrichment agent with optional Anthropic fallback."""

    name = "enrichment"

    def __init__(self, llm: AnthropicJsonFallback | None = None) -> None:
        self.llm = llm or AnthropicJsonFallback()

    def run(self, payload: dict[str, Any]) -> AgentResult:
        data = dict(payload)
        warnings: list[str] = []

        if "vendor_name" in data:
            data["vendor_name"] = self._normalize_vendor_name(str(data["vendor_name"]))

        country_code = self._normalize_country(data.get("country"))
        if country_code:
            data["country"] = country_code
        elif data.get("country"):
            warnings.append(f"Unknown country value: {data['country']}")

        if not data.get("currency") and country_code in CURRENCY_BY_COUNTRY:
            data["currency"] = CURRENCY_BY_COUNTRY[country_code]
        elif data.get("currency"):
            data["currency"] = str(data["currency"]).upper()

        if data.get("phone"):
            phone = self._normalize_phone(str(data["phone"]), country_code)
            if phone:
                data["phone"] = phone
            else:
                warnings.append("Phone number could not be normalized")

        if not data.get("tax_type") or self._address_is_ambiguous(data.get("address")):
            fallback = self._llm_enrich(data)
            if fallback:
                data.update({key: value for key, value in fallback.items() if value})
            elif not data.get("tax_type"):
                warnings.append("tax_type missing and LLM fallback is unavailable")

        return AgentResult(ok=True, data=data, warnings=warnings, agent=self.name)

    def _normalize_country(self, value: Any) -> str | None:
        if not value:
            return None
        raw = str(value).strip()
        if len(raw) == 2:
            return raw.upper()
        alias = COUNTRY_ALIASES.get(raw.casefold())
        if alias:
            return alias

        try:
            import pycountry
        except ImportError:
            return None

        country = pycountry.countries.get(name=raw)
        if not country:
            try:
                country = pycountry.countries.search_fuzzy(raw)[0]
            except LookupError:
                return None
        return country.alpha_2

    def _normalize_phone(self, value: str, country_code: str | None) -> str | None:
        try:
            import phonenumbers
        except ImportError:
            digits = re.sub(r"\D", "", value)
            return digits or None

        try:
            number = phonenumbers.parse(value, country_code)
        except phonenumbers.NumberParseException:
            return None
        if not phonenumbers.is_valid_number(number):
            return None
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)

    def _normalize_vendor_name(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value).strip()
        return VENDOR_SUFFIX_PATTERN.sub("", cleaned).strip()

    def _address_is_ambiguous(self, value: Any) -> bool:
        if not value:
            return False
        return len(str(value).split()) < 3

    def _llm_enrich(self, data: dict[str, Any]) -> dict[str, Any] | None:
        return self.llm.complete_json(
            "Infer missing vendor tax_type or clarify ambiguous address fields. "
            "Return only a compact JSON object with fields to merge.",
            data,
        )
