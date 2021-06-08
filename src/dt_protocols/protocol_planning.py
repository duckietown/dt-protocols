from dataclasses import dataclass
from typing import List, Optional, Union

from typing_extensions import Literal

from aido_schemas import FriendlyPose
from .basics import InteractionProtocol

__all__ = ["protocol_collision_checking", "Circle", 'Rectangle', 'Primitive', 'MapDefinition',
           'CollisionCheckQuery', 'CollisionCheckResult']


@dataclass
class Circle:
    primitive: Literal['circle']
    x: float
    y: float
    radius: float


@dataclass
class Rectangle:
    primitive: Literal['rectangle']
    xmin: float
    ymin: float
    xmax: float
    ymax: float


Primitive = Union[Circle, Rectangle]


@dataclass
class MapDefinition:
    environment: List[Primitive]
    body: Primitive


@dataclass
class CollisionCheckQuery:
    pose: FriendlyPose


@dataclass
class CollisionCheckResult:
    collision: bool
    distance: Optional[float]


protocol_collision_checking = InteractionProtocol(
    description="""Collision checking protocol""",
    inputs={"set_map": MapDefinition, "query": CollisionCheckQuery},
    outputs={"response": CollisionCheckResult},
    language="""
        (in:set_map ; (in:query ; out:response)*)*
        """,
)
