from typing import Any, Dict, List

from pydantic import BaseModel

from .entities import Entity
from .relationships import Relationship


class CaseInput(BaseModel):
    text: str


class CaseAnalysis(BaseModel):
    case_id: str
    entities: List[Entity]
    relationships: List[Relationship]
    patterns: List[Dict[str, Any]] = []
    graph: Dict[str, Any] = {}
    report: Dict[str, Any] = {}