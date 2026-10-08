from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentStatus(StrEnum):
    OK = "ok"
    NO_EVIDENCE = "no_evidence"
    ERROR = "error"


class AgentResult(BaseModel):
    """The one shape every agent returns, so the Supervisor never special-cases an agent."""

    model_config = ConfigDict(extra="forbid")

    status: AgentStatus = AgentStatus.OK
    result: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_status_consistency(self) -> Self:
        if self.status is AgentStatus.ERROR and not self.errors:
            raise ValueError("status 'error' requires at least one message in errors")
        if self.status is AgentStatus.NO_EVIDENCE and self.sources:
            raise ValueError("status 'no_evidence' cannot have sources")
        return self
