from typing import Optional
from pydantic import BaseModel


class Relationship(BaseModel):
    source: str
    target: str
    type: str
    amount: Optional[float] = None
    timestamp: Optional[str] = None