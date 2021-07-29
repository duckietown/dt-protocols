from typing import List, Optional, TYPE_CHECKING, Union

from zuper_typing import dataclass

from aido_schemas import FriendlyPose
from .basics import InteractionProtocol

if TYPE_CHECKING:
    from dataclasses import dataclass

__all__ = [
    "protocol_collision_checking",
    "Circle",
    "Rectangle",
    "Primitive",
    "MapDefinition",
    "CollisionCheckQuery",
    "CollisionCheckResult",
    "PlacedPrimitive",
    "Point",
    "PlanningQuery",
    "PlanningResult",
    "PlanningSetup",
    "protocol_planner",
    "PlanStep",
    "Appearance",
    "Motion",
]


@dataclass
class Circle:
    radius: float


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Rectangle:
    xmin: float
    ymin: float
    xmax: float
    ymax: float


Primitive = Union[Circle, Rectangle]


@dataclass
class Appearance:
    fillcolor: str
    rel_zorder: int = 0


@dataclass
class PlanStep:
    duration: float
    velocity_x_m_s: float
    angular_velocity_deg_s: float


@dataclass
class Motion:
    steps: List[PlanStep]
    periodic: bool


@dataclass
class PlacedPrimitive:
    pose: FriendlyPose
    primitive: Primitive
    motion: Optional[Motion] = None
    appearance: Optional[Appearance] = None


@dataclass
class MapDefinition:
    environment: List[PlacedPrimitive]
    body: List[PlacedPrimitive]


@dataclass
class CollisionCheckQuery:
    pose: FriendlyPose


@dataclass
class CollisionCheckResult:
    collision: bool


protocol_collision_checking = InteractionProtocol(
    description="""Collision checking protocol""",
    inputs={"set_params": MapDefinition, "query": CollisionCheckQuery},
    outputs={"response": CollisionCheckResult},
    language="""
        (in:set_params ; (in:query ; out:response)*)*
        """,
)


@dataclass
class PlanningSetup(MapDefinition):
    bounds: Rectangle
    max_linear_velocity_m_s: float
    min_linear_velocity_m_s: float
    max_angular_velocity_deg_s: float
    max_curvature: float
    tolerance_xy_m: float
    tolerance_theta_deg: float


@dataclass
class PlanningQuery:
    start: FriendlyPose
    target: FriendlyPose


@dataclass
class PlanningResult:
    feasible: bool
    plan: Optional[List[PlanStep]]


protocol_planner = InteractionProtocol(
    description="""Planning protocol""",
    inputs={"set_params": PlanningSetup, "query": PlanningQuery},
    outputs={"response": PlanningResult},
    language="""
        (in:set_params ; (in:query ; out:response)*)*
        """,
)
