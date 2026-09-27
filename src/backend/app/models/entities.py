from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class Entity(BaseModel):
    id: str
    name: str
    type: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
