"""
Knowledge Graph - graph queries and analysis.
"""

from __future__ import annotations

import logging
from typing import Optional

import networkx as nx

from .builder import KnowledgeGraph
from .models import Edge, Path

logger = logging.getLogger(__name__)


class GraphQuery:
    """Query and analyze a knowledge graph."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.graph = kg.graph

    def find_path(self, source: str, target: str) -> Optional[Path]:
        """
        Find the shortest path between two concepts.

        Returns None if no path exists.
        """
        if source not in self.graph or target not in self.graph:
            return None

        try:
            node_path = nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None

        edges: list[Edge] = []
        for i in range(len(node_path) - 1):
            u, v = node_path[i], node_path[i + 1]
            data = self.graph.edges[u, v]
            edges.append(Edge(
                source=u,
                target=v,
                relation=data.get("relation", ""),
                weight=data.get("weight", 1.0),
                description=data.get("description", ""),
            ))

        return Path(
            nodes=node_path,
            edges=edges,
            length=len(node_path) - 1,
        )

    def find_all_paths(self, source: str, target: str, max_length: int = 5) -> list[Path]:
        """Find all simple paths between two concepts (up to max_length)."""
        if source not in self.graph or target not in self.graph:
            return []

        paths: list[Path] = []
        try:
            for node_path in nx.all_simple_paths(self.graph, source, target, cutoff=max_length):
                edges: list[Edge] = []
                for i in range(len(node_path) - 1):
                    u, v = node_path[i], node_path[i + 1]
                    data = self.graph.edges[u, v]
                    edges.append(Edge(
                        source=u,
                        target=v,
                        relation=data.get("relation", ""),
                    ))
                paths.append(Path(
                    nodes=node_path,
                    edges=edges,
                    length=len(node_path) - 1,
                ))
        except nx.NetworkXError:
            pass

        return sorted(paths, key=lambda p: p.length)

    def centrality(self, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Compute betweenness centrality for all nodes.

        Returns the top_k most central concepts (bridges between clusters).
        """
        if len(self.graph) < 2:
            return []

        centrality = nx.betweenness_centrality(self.graph)
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_k]

    def degree_rank(self, top_k: int = 10) -> list[tuple[str, int]]:
        """
        Rank concepts by degree (number of connections).

        Returns the top_k most connected concepts.
        """
        degrees = dict(self.graph.degree())
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_k]

    def neighbors(self, node: str) -> list[dict]:
        """
        Get all neighbors of a concept with relationship info.
        """
        if node not in self.graph:
            return []

        result: list[dict] = []

        # Outgoing edges
        for _, target, data in self.graph.out_edges(node, data=True):
            result.append({
                "node": target,
                "direction": "outgoing",
                "relation": data.get("relation", ""),
                "description": data.get("description", ""),
            })

        # Incoming edges
        for source, _, data in self.graph.in_edges(node, data=True):
            result.append({
                "node": source,
                "direction": "incoming",
                "relation": data.get("relation", ""),
                "description": data.get("description", ""),
            })

        return result

    def clusters(self) -> list[list[str]]:
        """
        Detect community clusters using weakly connected components.

        Returns groups of concept names.
        """
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        # Sort by size descending
        return sorted([list(c) for c in components], key=len, reverse=True)

    def subgraph(self, nodes: list[str]) -> KnowledgeGraph:
        """Extract a subgraph containing only the specified nodes."""
        sub = self.graph.subgraph(nodes).copy()
        kg = KnowledgeGraph(name=f"{self.kg.name}_sub")

        for node in sub.nodes:
            if node in self.kg.concepts:
                kg.add_concept(self.kg.concepts[node])

        for u, v, data in sub.edges(data=True):
            kg.add_edge(Edge(
                source=u,
                target=v,
                relation=data.get("relation", ""),
                weight=data.get("weight", 1.0),
                description=data.get("description", ""),
            ))

        return kg

    def stats(self) -> dict:
        """Return graph statistics."""
        undirected = self.graph.to_undirected()
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_connected(undirected),
            "components": nx.number_connected_components(undirected),
            "avg_degree": sum(d for _, d in self.graph.degree()) / max(1, self.graph.number_of_nodes()),
        }
