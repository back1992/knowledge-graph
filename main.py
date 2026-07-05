#!/usr/bin/env python3
"""
Knowledge Graph - standalone demo script.

Builds a knowledge graph from the knowledge-base extraction output,
then runs graph queries and generates visualizations.

Usage:
    python main.py                              # Use existing knowledge.json
    python main.py --extract                    # Extract + build graph from PDF
    python main.py --format mermaid             # Mermaid output (default)
    python main.py --format dot                 # Graphviz DOT output
    python main.py --query "编码" "译码"         # Find path between concepts
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

DEFAULT_PDF = Path(__file__).parent.parent / "data" / "chapter04.pdf"
KB_OUTPUT = Path(__file__).parent.parent / "knowledge-base" / "output" / "knowledge.json"
DEFAULT_OUTPUT = Path(__file__).parent / "output"


def main():
    parser = argparse.ArgumentParser(
        description="Knowledge Graph - build, query, and visualize concept graphs",
    )
    parser.add_argument(
        "--knowledge-json",
        type=Path,
        default=KB_OUTPUT,
        help=f"Path to knowledge.json from knowledge-base (default: {KB_OUTPUT})",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract knowledge from PDF first (requires knowledge-base package)",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help=f"PDF file for extraction (default: {DEFAULT_PDF})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--format",
        choices=["mermaid", "dot", "json"],
        default="mermaid",
        help="Visualization format (default: mermaid)",
    )
    parser.add_argument(
        "--query",
        nargs=2,
        metavar=("SOURCE", "TARGET"),
        help="Find path between two concepts",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top results for centrality/degree (default: 10)",
    )

    args = parser.parse_args()

    # Step 1: Get knowledge data
    kb_data = None

    if args.extract:
        kb_data = _extract_from_pdf(args.pdf)
    elif args.knowledge_json.exists():
        with open(args.knowledge_json, encoding="utf-8") as f:
            kb_data = json.load(f)
    else:
        print(f"Error: {args.knowledge_json} not found.", file=sys.stderr)
        print("Run knowledge-base/main.py first, or use --extract flag.", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("Knowledge Graph Demo")
    print("=" * 70)

    # Step 2: Build graph
    from knowledge_graph import KnowledgeGraph, GraphQuery

    kg = KnowledgeGraph(name=kb_data.get("title", "knowledge_graph"))
    kg.from_knowledge_base(kb_data)

    print(f"\nGraph: {kg.node_count} concepts, {kg.edge_count} edges")

    # Step 3: Graph analysis
    query = GraphQuery(kg)
    stats = query.stats()

    print(f"\n{'─' * 70}")
    print("GRAPH STATS")
    print(f"{'─' * 70}")
    print(f"  Nodes: {stats['nodes']}")
    print(f"  Edges: {stats['edges']}")
    print(f"  Density: {stats['density']:.4f}")
    print(f"  Connected: {stats['is_connected']}")
    print(f"  Components: {stats['components']}")
    print(f"  Avg degree: {stats['avg_degree']:.2f}")

    # Centrality
    central = query.centrality(top_k=args.top_k)
    if central:
        print(f"\n{'─' * 70}")
        print(f"TOP {len(central)} CENTRAL CONCEPTS (betweenness)")
        print(f"{'─' * 70}")
        for i, (name, score) in enumerate(central, 1):
            print(f"  {i}. {name}: {score:.4f}")

    # Degree rank
    ranked = query.degree_rank(top_k=args.top_k)
    if ranked:
        print(f"\n{'─' * 70}")
        print(f"TOP {len(ranked)} MOST CONNECTED CONCEPTS")
        print(f"{'─' * 70}")
        for i, (name, degree) in enumerate(ranked, 1):
            print(f"  {i}. {name}: {degree} connections")

    # Clusters
    clusters = query.clusters()
    if clusters and len(clusters) > 1:
        print(f"\n{'─' * 70}")
        print(f"CLUSTERS ({len(clusters)} groups)")
        print(f"{'─' * 70}")
        for i, cluster in enumerate(clusters[:5], 1):
            members = ", ".join(cluster[:5])
            suffix = f" ... (+{len(cluster) - 5})" if len(cluster) > 5 else ""
            print(f"  Group {i} ({len(cluster)}): {members}{suffix}")

    # Path query
    if args.query:
        source, target = args.query
        print(f"\n{'─' * 70}")
        print(f"PATH: {source} → {target}")
        print(f"{'─' * 70}")

        path = query.find_path(source, target)
        if path:
            print(f"  Length: {path.length}")
            print(f"  Path: {' → '.join(path.nodes)}")
            for edge in path.edges:
                print(f"    {edge.source} --[{edge.relation}]--> {edge.target}")
        else:
            print(f"  No path found between '{source}' and '{target}'")

    # Step 4: Visualize
    from knowledge_graph import to_mermaid, to_dot, to_json

    formatter = {"mermaid": to_mermaid, "dot": to_dot, "json": to_json}[args.format]
    output = formatter(kg)

    print(f"\n{'=' * 70}")
    print(f"VISUALIZATION ({args.format})")
    print(f"{'=' * 70}")
    print(output)

    # Save
    args.output.mkdir(parents=True, exist_ok=True)
    ext = {"mermaid": ".mmd", "dot": ".dot", "json": ".json"}[args.format]
    output_file = args.output / f"graph{ext}"
    output_file.write_text(output, encoding="utf-8")

    # Also save graph data
    kg.save(args.output)

    print(f"\nSaved to: {output_file}")
    print(f"Graph data: {args.output / 'graph.json'}")


def _extract_from_pdf(pdf_path: Path) -> dict:
    """Extract knowledge from PDF using knowledge-base package."""
    print(f"Extracting knowledge from: {pdf_path}")

    try:
        from knowledge_base import KnowledgeExtractor
    except ImportError:
        print("Error: knowledge-base package not installed.", file=sys.stderr)
        print("Run: pip install -e packages/knowledge-base/", file=sys.stderr)
        sys.exit(1)

    extractor = KnowledgeExtractor(max_terms=30, max_flashcards=50)
    kb = extractor.extract_from_pdf(pdf_path)
    return kb.to_dict()


if __name__ == "__main__":
    main()
