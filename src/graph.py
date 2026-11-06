"""
Graph representation, Road Network modeling, and Dijkstra's Shortest Path algorithm.
"""

from typing import Dict, List, Tuple, Optional, Set, Any
import heapq
import json
import math
from .models import DeliveryPoint, RoadEdge


class Graph:
    """
    Weighted graph representation using an adjacency list.
    Supports cartesian vertex coordinates for spatial layout and Euclidean validation.
    """

    def __init__(self, directed: bool = False):
        self.directed = directed
        self.adjacency: Dict[str, List[Tuple[str, float]]] = {}
        self.nodes: Dict[str, DeliveryPoint] = {}

    def add_node(self, node_id: str, name: str = "", x: float = 0.0, y: float = 0.0, is_depot: bool = False) -> None:
        """Adds a vertex/delivery location to the graph."""
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []
        self.nodes[node_id] = DeliveryPoint(
            node_id=node_id,
            name=name or node_id,
            x=x,
            y=y,
            is_depot=is_depot
        )

    def add_edge(self, source: str, target: str, weight: float, bidirectional: Optional[bool] = None) -> None:
        """
        Adds a weighted road connection between source and target.
        If bidirectional is not specified, defaults to not self.directed.
        """
        if weight < 0:
            raise ValueError(f"Edge weight cannot be negative: {weight}")

        if source not in self.adjacency:
            self.add_node(source)
        if target not in self.adjacency:
            self.add_node(target)

        self.adjacency[source].append((target, float(weight)))

        is_bi = (not self.directed) if (bidirectional is None) else bidirectional
        if is_bi and source != target:
            self.adjacency[target].append((source, float(weight)))

    def get_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        """Returns adjacent nodes and their edge weights."""
        return self.adjacency.get(node_id, [])

    def get_nodes(self) -> List[str]:
        """Returns list of all node IDs."""
        return list(self.adjacency.keys())

    def get_edges(self) -> List[RoadEdge]:
        """Returns list of all unique road edges."""
        edges = []
        seen = set()
        for u, neighbors in self.adjacency.items():
            for v, w in neighbors:
                edge_id = tuple(sorted([u, v])) if not self.directed else (u, v)
                if edge_id not in seen:
                    seen.add(edge_id)
                    edges.append(RoadEdge(source=u, target=v, weight=w))
        return edges

    def to_dict(self) -> Dict[str, Any]:
        """Serializes graph to a dictionary format."""
        return {
            "directed": self.directed,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [
                {"source": e.source, "target": e.target, "weight": e.weight}
                for e in self.get_edges()
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        """Constructs graph from serialized dictionary."""
        g = cls(directed=data.get("directed", False))
        for n in data.get("nodes", []):
            g.add_node(
                node_id=n["node_id"],
                name=n.get("name", ""),
                x=n.get("x", 0.0),
                y=n.get("y", 0.0),
                is_depot=n.get("is_depot", False)
            )
        for e in data.get("edges", []):
            g.add_edge(e["source"], e["target"], e["weight"], bidirectional=not g.directed)
        return g

    def save_json(self, file_path: str) -> None:
        """Saves graph to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, file_path: str) -> "Graph":
        """Loads graph from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


def dijkstra(graph: Graph, source: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Computes single-source shortest paths from source to all reachable vertices
    using Dijkstra's algorithm with a binary min-heap priority queue.
    
    Time Complexity:  O((|V| + |E|) * log |V|)
    Space Complexity: O(|V|)
    
    Args:
        graph: The road network graph.
        source: Starting vertex identifier.
        
    Returns:
        Tuple of (distances_dict, predecessors_dict)
    """
    if source not in graph.adjacency:
        raise ValueError(f"Source vertex '{source}' does not exist in graph.")

    distances: Dict[str, float] = {node: float("inf") for node in graph.adjacency}
    predecessors: Dict[str, Optional[str]] = {node: None for node in graph.adjacency}

    distances[source] = 0.0
    # Priority queue stores tuples of (current_shortest_dist, node_id)
    pq: List[Tuple[float, str]] = [(0.0, source)]

    visited: Set[str] = set()

    while pq:
        curr_dist, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        # Relax all outgoing edges from u
        for v, weight in graph.get_neighbors(u):
            if v in visited:
                continue
            new_dist = curr_dist + weight
            if new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    return distances, predecessors


def reconstruct_path(
    predecessors: Dict[str, Optional[str]],
    target: str,
    source: Optional[str] = None
) -> List[str]:
    """
    Reconstructs the shortest path from the source node to the specified target.
    
    Args:
        predecessors: Predecessor dictionary mapping node -> previous node on shortest path.
        target: Target destination vertex ID.
        source: Optional source vertex ID. If provided, ensures the path begins at source.
        
    Returns:
        List of vertex IDs representing the sequential route [source, ..., target],
        or [] if target is unreachable or does not connect back to source.
    """
    if target not in predecessors:
        return []

    # If target is identical to source, path is trivial
    if source is not None and target == source:
        return [source]

    # If target has no predecessor and isn't the source, it is unreachable
    if predecessors.get(target) is None and (source is None or target != source):
        return []

    path = []
    curr: Optional[str] = target
    visited: Set[str] = set()

    while curr is not None:
        if curr in visited:
            # Cycle detected in predecessor chain; invalid path
            return []
        visited.add(curr)
        path.append(curr)
        curr = predecessors.get(curr)

    path.reverse()

    # If source was specified, verify the reconstructed path begins at source
    if source is not None and (not path or path[0] != source):
        return []

    return path


def compute_distance_matrix(
    graph: Graph,
    nodes_subset: List[str]
) -> Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], List[str]]]:
    """
    Calculates the all-pairs shortest distances and reconstructed paths
    between all nodes in the requested subset using repeated Dijkstra executions.
    
    Complexity: O(|K| * (|V| + |E|) * log |V|) where K = len(nodes_subset).
    """
    dist_matrix: Dict[Tuple[str, str], float] = {}
    path_matrix: Dict[Tuple[str, str], List[str]] = {}

    for u in nodes_subset:
        distances, predecessors = dijkstra(graph, u)
        for v in nodes_subset:
            dist = distances.get(v, float("inf"))
            dist_matrix[(u, v)] = dist
            if dist < float("inf"):
                path_matrix[(u, v)] = reconstruct_path(predecessors, v, source=u)
            else:
                path_matrix[(u, v)] = []

    return dist_matrix, path_matrix
