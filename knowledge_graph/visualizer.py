"""
Knowledge Graph - visualization output (Mermaid, Graphviz/DOT, JSON).
"""

from __future__ import annotations

import json

from .builder import KnowledgeGraph

# Relation type → Mermaid edge style
_MERMAID_STYLES = {
    "is_a": "-->",
    "part_of": "-->",
    "causes": "==>",
    "related_to": "-.-",
    "used_for": "-->",
}

# Relation type → color
_COLORS = {
    "is_a": "#4A90D9",
    "part_of": "#7B68EE",
    "causes": "#E74C3C",
    "related_to": "#95A5A6",
    "used_for": "#2ECC71",
}


def to_mermaid(kg: KnowledgeGraph, title: str = "") -> str:
    """
    Render the knowledge graph as a Mermaid flowchart.

    Example output:
    ```mermaid
    flowchart LR
        A[编码] -->|is_a| B[传播概念]
        B -->|part_of| C[传播学]
    ```
    """
    lines: list[str] = ["flowchart LR"]

    # Define nodes
    for name, concept in kg.concepts.items():
        node_id = _safe_id(name)
        label = name[:15]
        if concept.category:
            lines.append(f'    {node_id}["{label}<br/><i>{concept.category}</i>"]')
        else:
            lines.append(f'    {node_id}["{label}"]')

    # Define edges
    for edge in kg.edges:
        src = _safe_id(edge.source)
        tgt = _safe_id(edge.target)
        arrow = _MERMAID_STYLES.get(edge.relation, "-->")
        lines.append(f'    {src} {arrow}|"{edge.relation}"| {tgt}')

    # Add styles
    lines.append("")
    for name in kg.concepts:
        node_id = _safe_id(name)
        lines.append(f"    style {node_id} fill:#f9f9f9,stroke:#333")

    return "\n".join(lines)


def to_dot(kg: KnowledgeGraph) -> str:
    """
    Render the knowledge graph as Graphviz DOT format.

    Can be rendered with: dot -Tpng graph.dot -o graph.png
    """
    lines: list[str] = [
        'digraph knowledge_graph {',
        '    rankdir=LR;',
        '    node [shape=box, style="rounded,filled", fillcolor="#f9f9f9"];',
        '    edge [fontsize=10];',
        '',
    ]

    # Nodes
    for name, concept in kg.concepts.items():
        node_id = _safe_id(name)
        label = name.replace('"', '\\"')
        attrs = f'label="{label}"'
        if concept.definition:
            tooltip = concept.definition[:50].replace('"', '\\"')
            attrs += f', tooltip="{tooltip}"'
        lines.append(f'    {node_id} [{attrs}];')

    lines.append("")

    # Edges
    for edge in kg.edges:
        src = _safe_id(edge.source)
        tgt = _safe_id(edge.target)
        color = _COLORS.get(edge.relation, "#333333")
        lines.append(
            f'    {src} -> {tgt} '
            f'[label="{edge.relation}", color="{color}"];'
        )

    lines.append("}")
    return "\n".join(lines)


def to_json(kg: KnowledgeGraph) -> str:
    """Render the knowledge graph as JSON (for D3.js or other tools)."""
    nodes = []
    for name, concept in kg.concepts.items():
        nodes.append({
            "id": name,
            "label": name,
            "category": concept.category,
            "definition": concept.definition[:100] if concept.definition else "",
        })

    edges = []
    for edge in kg.edges:
        edges.append({
            "source": edge.source,
            "target": edge.target,
            "relation": edge.relation,
            "weight": edge.weight,
        })

    data = {
        "name": kg.name,
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }

    return json.dumps(data, indent=2, ensure_ascii=False)


def _safe_id(name: str) -> str:
    """Convert a concept name to a safe node ID."""
    # Use hash for non-ASCII names
    safe = "".join(c if c.isalnum() and c.isascii() else f"_{ord(c):04x}" for c in name)
    return f"n{safe}"
