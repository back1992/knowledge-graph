"""
Knowledge Graph - data models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Concept:
    """A concept node in the knowledge graph."""

    name: str
    category: str = ""
    definition: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "definition": self.definition,
            "properties": self.properties,
        }


@dataclass
class Edge:
    """A relationship edge between two concepts."""

    source: str
    target: str
    relation: str
    weight: float = 1.0
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
            "description": self.description,
        }


@dataclass
class Path:
    """A path between two concepts in the graph."""

    nodes: list[str]
    edges: list[Edge]
    length: int = 0

    def to_dict(self) -> dict:
        return {
            "nodes": self.nodes,
            "edges": [e.to_dict() for e in self.edges],
            "length": self.length,
        }
