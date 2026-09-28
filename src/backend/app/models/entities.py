from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class Entity(BaseModel):
    id: str
    name: str
    type: str
    role: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
