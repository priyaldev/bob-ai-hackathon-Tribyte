from pydantic import BaseModel
from typing import Optional


class Relationship(BaseModel):
    source: str
    target: str
    type: str
    amount: Optional[float] = None
    timestamp: Optional[str] = None