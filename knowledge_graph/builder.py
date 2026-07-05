"""
Knowledge Graph - build graph from relationships.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Union

import networkx as nx

from .models import Concept, Edge

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """A knowledge graph built on NetworkX with concept nodes and relationship edges."""

    def __init__(self, name: str = "knowledge_graph"):
        self.name = name
        self.graph = nx.DiGraph()
        self.concepts: dict[str, Concept] = {}
        self.edges: list[Edge] = []

    def add_concept(self, concept: Concept) -> None:
        """Add a concept node to the graph."""
        self.concepts[concept.name] = concept
        self.graph.add_node(
            concept.name,
            category=concept.category,
            definition=concept.definition,
            **concept.properties,
        )

    def add_edge(self, edge: Edge) -> None:
        """Add a relationship edge to the graph."""
        # Ensure both nodes exist
        if edge.source not in self.concepts:
            self.add_concept(Concept(name=edge.source))
        if edge.target not in self.concepts:
            self.add_concept(Concept(name=edge.target))

        self.edges.append(edge)
        self.graph.add_edge(
            edge.source,
            edge.target,
            relation=edge.relation,
            weight=edge.weight,
            description=edge.description,
        )

    def from_relationships(self, relationships: list[dict]) -> None:
        """
        Build graph from a list of relationship dicts.

        Compatible with knowledge_base.Relationship.to_dict() output.
        """
        for rel in relationships:
            edge = Edge(
                source=rel["source"],
                target=rel["target"],
                relation=rel["relation_type"],
                description=rel.get("description", ""),
            )
            self.add_edge(edge)

        logger.info(f"Built graph: {len(self.concepts)} concepts, {len(self.edges)} edges")

    def from_knowledge_base(self, kb_dict: dict) -> None:
        """
        Build graph from a knowledge_base.KnowledgeBase.to_dict() output.

        Adds terms as concepts with definitions, and relationships as edges.
        Also infers implicit relationships when one term's definition mentions another.
        """
        # Add terms as concepts
        for term in kb_dict.get("terms", []):
            concept = Concept(
                name=term["term"],
                definition=term.get("definition", ""),
                category=term.get("category", ""),
            )
            self.add_concept(concept)

        # Add explicit relationships as edges
        self.from_relationships(kb_dict.get("relationships", []))

        # Infer implicit relationships: if term A's definition mentions term B
        self._infer_relationships(kb_dict.get("terms", []))

        logger.info(f"Built graph: {len(self.concepts)} concepts, {len(self.edges)} edges")

    def _infer_relationships(self, terms: list[dict]) -> None:
        """
        Infer relationships from term definitions.

        If term A's definition mentions term B, create a "related_to" edge.
        """
        term_names = {t["term"] for t in terms}

        for term in terms:
            name = term["term"]
            definition = term.get("definition", "")
            context = term.get("context", "")
            text = definition + " " + context

            for other_name in term_names:
                if other_name == name:
                    continue
                if other_name in text:
                    edge = Edge(
                        source=name,
                        target=other_name,
                        relation="related_to",
                        description=f"'{other_name}' mentioned in definition of '{name}'",
                    )
                    self.add_edge(edge)

    def save(self, output_dir: Union[str, Path]) -> None:
        """Save graph to disk as JSON."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "name": self.name,
            "concepts": {k: v.to_dict() for k, v in self.concepts.items()},
            "edges": [e.to_dict() for e in self.edges],
        }

        with open(output_dir / "graph.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Also save as GraphML for external tools
        nx.write_graphml(self.graph, str(output_dir / "graph.graphml"))

        logger.info(f"Saved graph → {output_dir}")

    @classmethod
    def load(cls, graph_path: Union[str, Path]) -> "KnowledgeGraph":
        """Load a graph from a saved graph.json file."""
        graph_path = Path(graph_path)

        if graph_path.is_dir():
            graph_path = graph_path / "graph.json"

        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        kg = cls(name=data.get("name", "knowledge_graph"))

        for name, concept_data in data.get("concepts", {}).items():
            kg.add_concept(Concept(
                name=name,
                category=concept_data.get("category", ""),
                definition=concept_data.get("definition", ""),
                properties=concept_data.get("properties", {}),
            ))

        for edge_data in data.get("edges", []):
            kg.add_edge(Edge(
                source=edge_data["source"],
                target=edge_data["target"],
                relation=edge_data["relation"],
                weight=edge_data.get("weight", 1.0),
                description=edge_data.get("description", ""),
            ))

        return kg

    @property
    def node_count(self) -> int:
        return len(self.concepts)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
