from typing import Any, Dict
from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str
    name: str
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)