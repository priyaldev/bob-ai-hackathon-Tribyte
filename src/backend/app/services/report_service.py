from typing import List, Dict, Any

from app.models.entities import Entity
from app.models.relationships import Relationship


def generate_report(
    case_id: str,
    entities: List[Entity],
    relationships: List[Relationship],
    patterns: List[Dict[str, Any]],
) -> Dict[str, Any]:

    # Count entity types
    entity_counts = {}

    for entity in entities:
        entity_type = entity.type.upper()
        entity_counts[entity_type] = (
            entity_counts.get(entity_type, 0) + 1
        )

    # Calculate total transaction amount
    total_transaction_amount = sum(
        relationship.amount
        for relationship in relationships
        if relationship.amount is not None
    )

    # Identify entities involved in suspicious patterns
    key_entities = []

    for pattern in patterns:
        evidence = pattern.get("evidence", {})

        entity_id = evidence.get("entity_id")

        if entity_id:
            entity = next(
                (e for e in entities if e.id == entity_id),
                None,
            )

            if entity and entity.id not in key_entities:
                key_entities.append(entity.id)

    # Convert IDs to useful entity information
    key_entity_details = []

    for entity_id in key_entities:
        entity = next(
            (e for e in entities if e.id == entity_id),
            None,
        )

        if entity:
            key_entity_details.append(
                {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type,
                }
            )

    # Generate investigation actions
    recommended_actions = []

    if patterns:
        recommended_actions.append(
            "Review the identified transaction and relationship patterns."
        )

    if entity_counts.get("BANK_ACCOUNT", 0) > 0:
        recommended_actions.append(
            "Review bank account ownership and transaction history."
        )

    if entity_counts.get("DEVICE", 0) > 0:
        recommended_actions.append(
            "Review device-to-account associations and device activity."
        )

    if entity_counts.get("PHONE", 0) > 0:
        recommended_actions.append(
            "Review phone number ownership and associated communication records."
        )

    return {
        "case_id": case_id,
        "summary": (
            f"Case {case_id} contains "
            f"{len(entities)} identified entities and "
            f"{len(relationships)} relationships. "
            f"{len(patterns)} potentially suspicious network patterns "
            f"were identified for investigation."
        ),
        "entity_counts": entity_counts,
        "total_transaction_amount": total_transaction_amount,
        "pattern_count": len(patterns),
        "key_entities": key_entity_details,
        "recommended_actions": recommended_actions,
    }