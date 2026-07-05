# Knowledge Graph

Build, query, and visualize knowledge graphs from extracted relationships.

## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
# Build graph from knowledge-base output
python main.py

# Extract from PDF + build graph
python main.py --extract

# Find path between concepts
python main.py --query "编码" "译码"

# Output formats
python main.py --format mermaid
python main.py --format dot
python main.py --format json
```

### Python API

```python
from knowledge_graph import KnowledgeGraph, GraphQuery, to_mermaid

# Build graph
kg = KnowledgeGraph()
kg.from_knowledge_base(kb_dict)

# Query
query = GraphQuery(kg)
path = query.find_path("编码", "译码")
central = query.centrality(top_k=5)
clusters = query.clusters()

# Visualize
print(to_mermaid(kg))
```

## Features

- **Graph construction** from knowledge-base relationships
- **Path finding** between concepts (shortest path, all paths)
- **Centrality analysis** (betweenness centrality)
- **Degree ranking** (most connected concepts)
- **Community detection** (connected component clustering)
- **Subgraph extraction** for focused views
- **Visualization** as Mermaid, Graphviz DOT, or JSON (D3.js)
