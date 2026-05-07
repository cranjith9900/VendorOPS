from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from sap_agents.models import AgentError, AgentResult


TAX_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-]{4,24}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class VendorPayload(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    vendor_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    tax_id: str = Field(min_length=5, max_length=25)
    country: str = Field(min_length=2, max_length=80)
    currency: str | None = Field(default=None, max_length=3)
    address: str | None = Field(default=None, max_length=240)

    @field_validator("tax_id")
    @classmethod
    def validate_tax_id(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not TAX_ID_PATTERN.match(normalized):
            raise ValueError("tax_id must be 5-25 uppercase letters, numbers, or hyphens")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("email must be a valid address")
        return normalized

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        normalized = value.strip().upper()
        if not re.match(r"^[A-Z]{3}$", normalized):
            raise ValueError("currency must be a three-letter ISO code")
        return normalized


class ValidatorAgent:
    """Rules-only validation agent."""

    name = "validator"

    def run(self, payload: dict[str, Any]) -> AgentResult:
        try:
            parsed = VendorPayload.model_validate(payload)
        except ValidationError as exc:
            return AgentResult(
                ok=False,
                agent=self.name,
                errors=[
                    AgentError(
                        field=".".join(str(part) for part in error["loc"]),
                        message=str(error["msg"]),
                        code=str(error["type"]),
                    )
                    for error in exc.errors()
                ],
            )

        data = parsed.model_dump(exclude_none=True)
        data.update(parsed.model_extra or {})
        return AgentResult(ok=True, data=data, agent=self.name)
