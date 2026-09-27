from typing import List, Dict, Any

from app.models.entities import Entity
from app.models.relationships import Relationship


def build_graph(
    entities: List[Entity],
    relationships: List[Relationship],
) -> Dict[str, Any]:
    nodes = []
    edges = []

    # Convert entities into graph nodes
    for entity in entities:
        nodes.append(
            {
                "id": entity.id,
                "label": entity.name,
                "type": entity.type,
                "metadata": entity.metadata,
            }
        )

    # Convert relationships into graph edges
    for relationship in relationships:
        edge: Dict[str, Any] = {
            "source": relationship.source,
            "target": relationship.target,
            "type": relationship.type,
        }

        if relationship.amount is not None:
            edge["amount"] = relationship.amount

        if relationship.timestamp is not None:
            edge["timestamp"] = relationship.timestamp

        edges.append(edge)

    return {
        "nodes": nodes,
        "edges": edges,
    }