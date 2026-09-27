from uuid import uuid4

from fastapi import APIRouter

from app.models.case import CaseAnalysis, CaseInput
from app.models.entities import Entity
from app.models.relationships import Relationship
from app.services.fraud_service import detect_fraud_patterns
from app.services.graph_service import build_graph
from app.services.report_service import generate_report

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.post("/analyze", response_model=CaseAnalysis)
def analyze_case(case_input: CaseInput):
    case_id = f"CASE-{str(uuid4())[:8].upper()}"

    # Temporary structured data for testing.
    # This will later be replaced by the AI extraction service.
    entities = [
        Entity(
            id="E001",
            name="Rahul",
            type="PERSON",
        ),
        Entity(
            id="E002",
            name="9876543210",
            type="PHONE",
        ),
        Entity(
            id="E003",
            name="DEV101",
            type="DEVICE",
        ),
        Entity(
            id="E004",
            name="ACC100",
            type="BANK_ACCOUNT",
        ),
        Entity(
            id="E005",
            name="ACC200",
            type="BANK_ACCOUNT",
        ),
        Entity(
            id="E006",
            name="V001",
            type="VICTIM",
        ),
        Entity(
            id="E007",
            name="V002",
            type="VICTIM",
        ),
    ]

    relationships = [
        Relationship(
            source="E001",
            target="E002",
            type="USES",
        ),
        Relationship(
            source="E002",
            target="E003",
            type="ASSOCIATED_WITH",
        ),
        Relationship(
            source="E003",
            target="E004",
            type="ACCESSES",
        ),
        Relationship(
            source="E006",
            target="E004",
            type="TRANSFERRED_TO",
            amount=50000,
        ),
        Relationship(
            source="E007",
            target="E004",
            type="TRANSFERRED_TO",
            amount=35000,
        ),
        Relationship(
            source="E004",
            target="E005",
            type="TRANSFERRED_TO",
            amount=70000,
        ),
    ]

    patterns = detect_fraud_patterns(
        entities,
        relationships,
    )

    graph = build_graph(
        entities,
        relationships,
    )

    report = generate_report(
        case_id,
        entities,
        relationships,
        patterns,
    )

    return {
        "case_id": case_id,
        "entities": entities,
        "relationships": relationships,
        "patterns": patterns,
        "graph": graph,
        "report": report,
    }