from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AgentName = Literal[
    "validator",
    "enrichment",
    "mapping",
    "bank_intelligence",
]


class AgentError(BaseModel):
    field: str
    message: str
    code: str


class AgentResult(BaseModel):
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[AgentError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    agent: AgentName


class PipelineState(BaseModel):
    input_data: dict[str, Any]
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[AgentError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    halted: bool = False
    completed_agents: list[AgentName] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PipelineState":
        return cls(input_data=payload, data=dict(payload))

    def apply_result(self, result: AgentResult, halt_on_error: bool = True) -> "PipelineState":
        data = dict(self.data)
        data.update(result.data)
        errors = [*self.errors, *result.errors]
        warnings = [*self.warnings, *result.warnings]
        completed_agents = [*self.completed_agents, result.agent]
        return self.model_copy(
            update={
                "data": data,
                "errors": errors,
                "warnings": warnings,
                "halted": self.halted or (halt_on_error and not result.ok),
                "completed_agents": completed_agents,
            }
        )
