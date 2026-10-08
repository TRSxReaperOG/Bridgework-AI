from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Run(BaseModel):
    """One saved run of the system: where it is (stage) and everything it knows so far (state)."""

    run_id: str
    stage: str
    state: dict[str, Any]
    created_at: datetime
    updated_at: datetime
