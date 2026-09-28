from collections import Counter
from typing import List, Dict, Any

from app.models.entities import Entity
from app.models.relationships import Relationship


def detect_fraud_patterns(
    entities: List[Entity],
    relationships: List[Relationship],
) -> List[Dict[str, Any]]:
    patterns = []

    # Count how many incoming transfers each entity receives
    incoming_transfers = Counter()

    # Count how many accounts a device is connected to
    device_accounts = {}

    for relationship in relationships:
        relationship_type = relationship.type.upper()

        if relationship_type in {"TRANSFERRED_TO", "TRANSFER"}:
            incoming_transfers[relationship.target] += 1

        if relationship_type in {"ACCESSES", "USES"}:
            source_entity = next(
                (e for e in entities if e.id == relationship.source),
                None,
            )

            target_entity = next(
                (e for e in entities if e.id == relationship.target),
                None,
            )

            if source_entity and target_entity:
                if source_entity.type.upper() == "DEVICE":
                    device_accounts.setdefault(
                        source_entity.id, set()
                    ).add(target_entity.id)

    # Pattern 1: One account receives money from multiple sources
    for entity_id, count in incoming_transfers.items():
        if count >= 2:
            entity = next(
                (e for e in entities if e.id == entity_id),
                None,
            )

            if entity:
                patterns.append(
                    {
                        "type": "MULTIPLE_SOURCE_TRANSACTIONS",
                        "description": (
                            f"{entity.name} receives transfers from "
                            f"{count} different relationship sources."
                        ),
                        "severity": "MEDIUM",
                        "evidence": {
                            "entity_id": entity.id,
                            "incoming_transfer_count": count,
                        },
                    }
                )

    # Pattern 2: One device is connected to multiple accounts
    for device_id, account_ids in device_accounts.items():
        if len(account_ids) >= 2:
            device = next(
                (e for e in entities if e.id == device_id),
                None,
            )

            if device:
                patterns.append(
                    {
                        "type": "SHARED_DEVICE",
                        "description": (
                            f"Device {device.name} is associated with "
                            f"{len(account_ids)} different accounts."
                        ),
                        "severity": "MEDIUM",
                        "evidence": {
                            "device_id": device.id,
                            "account_ids": list(account_ids),
                        },
                    }
                )

    # Pattern 3: Multi-hop money movement
    transfer_graph = {}

    for relationship in relationships:
        if relationship.type.upper() in {
            "TRANSFERRED_TO",
            "TRANSFER",
        }:
            transfer_graph.setdefault(
                relationship.source, []
            ).append(relationship.target)

    def _entity_name(entity_id: str) -> str:
        entity = next(
            (e for e in entities if e.id == entity_id),
            None,
        )
        return entity.name if entity else entity_id

    for source, targets in transfer_graph.items():
        for target in targets:
            if target in transfer_graph:
                for destination in transfer_graph[target]:
                    patterns.append(
                        {
                            "type": "MULTI_HOP_TRANSACTION",
                            "description": (
                                f"Funds may move through multiple accounts: "
                                f"{_entity_name(source)} → "
                                f"{_entity_name(target)} → "
                                f"{_entity_name(destination)}."
                            ),
                            "severity": "HIGH",
                            "evidence": {
                                "source": source,
                                "intermediate": target,
                                "destination": destination,
                            },
                        }
                    )

    return patterns