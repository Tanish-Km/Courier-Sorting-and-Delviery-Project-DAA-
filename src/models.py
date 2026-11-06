"""
Data models and entities for the Mini-Courier Planner system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any


@dataclass
class Parcel:
    """
    Represents an individual parcel submitted for delivery.
    
    Attributes:
        parcel_id: Unique identifier (e.g. 'P101').
        destination: Destination node ID in the delivery graph (e.g. 'C3').
        weight: Parcel weight in kilograms (integer for discrete 0/1 knapsack).
        priority: Priority tier (1 to 5, where 5 is highest urgency).
        deadline: Delivery deadline in hours from dispatch (e.g. 2.0).
        value: Objective value for knapsack optimization. If None, derived from priority & deadline.
        customer_name: Optional recipient name.
    """
    parcel_id: str
    destination: str
    weight: int
    priority: int = 1
    deadline: float = 24.0
    value: int = 0
    customer_name: str = ""

    def __post_init__(self):
        if self.weight < 0:
            raise ValueError(f"Parcel weight cannot be negative: {self.weight}")
        if self.priority < 1 or self.priority > 5:
            raise ValueError(f"Parcel priority must be between 1 and 5: {self.priority}")
        if self.deadline <= 0:
            raise ValueError(f"Parcel deadline must be strictly positive: {self.deadline}")
        if self.value <= 0:
            # Composite value formulation:
            # Higher priority and tighter deadline (lower deadline hours) yield higher business value.
            urgency_bonus = max(0, int(round((12.0 - min(self.deadline, 12.0)) * 2)))
            self.value = max(1, self.priority * 15 + urgency_bonus)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parcel_id": self.parcel_id,
            "destination": self.destination,
            "weight": self.weight,
            "priority": self.priority,
            "deadline": self.deadline,
            "value": self.value,
            "customer_name": self.customer_name,
        }


@dataclass
class DeliveryPoint:
    """
    Represents a geographical location (Depot or Customer Address) in the road network.
    
    Attributes:
        node_id: Unique vertex identifier (e.g. 'Depot', 'C1', 'C2').
        name: Human-readable location description.
        x: X-coordinate for 2D cartesian mapping / visualization.
        y: Y-coordinate for 2D cartesian mapping / visualization.
        is_depot: Boolean flag indicating if this is the central distribution depot.
    """
    node_id: str
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    is_depot: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "is_depot": self.is_depot,
        }


@dataclass
class RoadEdge:
    """
    Represents a road link between two delivery points.
    
    Attributes:
        source: Starting node ID.
        target: Destination node ID.
        weight: Distance in kilometers or travel time in minutes.
    """
    source: str
    target: str
    weight: float


@dataclass
class PackingResult:
    """
    Encapsulates the output of the 0/1 Knapsack dynamic programming stage.
    """
    selected_parcels: List[Parcel]
    rejected_parcels: List[Parcel]
    total_weight: int
    total_value: int
    capacity: int
    dp_table: List[List[int]]
    runtime_ms: float

    @property
    def capacity_utilization(self) -> float:
        if self.capacity <= 0:
            return 0.0
        return (self.total_weight / self.capacity) * 100.0


@dataclass
class RouteResult:
    """
    Encapsulates the TSP and Dijkstra route generation outcome.
    """
    ordered_stops: List[str]
    total_distance: float
    detailed_path: List[str]
    segment_distances: List[Tuple[str, str, float]]
    runtime_ms: float


@dataclass
class CourierPlanResult:
    """
    Integrated output of the entire Mini-Courier Planner execution.
    """
    initial_parcel_count: int
    prioritized_parcels: List[Parcel]
    packing_result: PackingResult
    route_result: RouteResult
    total_runtime_ms: float
    runtime_breakdown_ms: Dict[str, float]
