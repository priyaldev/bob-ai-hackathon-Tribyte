from fastapi import APIRouter, HTTPException

from app.models.case import CaseAnalysis, CaseInput
from app.services.ai_service import analyze_text
from app.services.fraud_service import detect_fraud_patterns
from app.services.graph_service import build_graph
from app.services.report_service import generate_report

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.post("/analyze", response_model=CaseAnalysis)
def analyze_case(case_input: CaseInput):
    """
    Analyze unstructured cyber-fraud intelligence text.

    1. Extract entities and relationships via ai_service
       (IBM watsonx.ai when USE_LLM=true, deterministic fallback otherwise).
    2. Detect fraud patterns.
    3. Build a graph payload for the frontend.
    4. Generate a summary report.
    """

    try:
        analysis = analyze_text(case_input.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    entities = analysis.entities
    relationships = analysis.relationships
    case_id = analysis.case_id

    patterns = detect_fraud_patterns(entities, relationships)

    graph = build_graph(entities, relationships)

    report = generate_report(case_id, entities, relationships, patterns)

    return CaseAnalysis(
        case_id=case_id,
        entities=entities,
        relationships=relationships,
        patterns=patterns,
        graph=graph,
        report=report,
    )
