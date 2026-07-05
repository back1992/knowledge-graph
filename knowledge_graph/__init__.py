"""
Knowledge Graph - build, query, and visualize knowledge graphs.

Usage:
    from knowledge_graph import KnowledgeGraph, GraphQuery

    kg = KnowledgeGraph()
    kg.from_knowledge_base(kb_dict)

    query = GraphQuery(kg)
    path = query.find_path("编码", "译码")
    central = query.centrality(top_k=5)
"""

from .models import Concept, Edge, Path
from .builder import KnowledgeGraph
from .query import GraphQuery
from .visualizer import to_mermaid, to_dot, to_json

__all__ = [
    "Concept",
    "Edge",
    "Path",
    "KnowledgeGraph",
    "GraphQuery",
    "to_mermaid",
    "to_dot",
    "to_json",
]

__version__ = "1.0.0"
