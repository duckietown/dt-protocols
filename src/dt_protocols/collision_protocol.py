from typing import List, TYPE_CHECKING, Union

from zuper_typing import dataclass

from aido_schemas import FriendlyPose
from .basics import InteractionProtocol

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
]

if TYPE_CHECKING:
    from dataclasses import dataclass


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
class PlacedPrimitive:
    pose: FriendlyPose
    primitive: Primitive


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
