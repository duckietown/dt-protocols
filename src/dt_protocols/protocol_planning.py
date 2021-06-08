from typing import List, Optional, TYPE_CHECKING, Union

from zuper_typing import dataclass

from aido_schemas import FriendlyPose
from .basics import InteractionProtocol

__all__ = ["protocol_collision_checking", "Circle", 'Rectangle', 'Primitive', 'MapDefinition',
           'CollisionCheckQuery', 'CollisionCheckResult']

if TYPE_CHECKING:
    from dataclasses import dataclass


@dataclass
class Circle:
    x: float
    y: float
    radius: float


@dataclass
class Rectangle:
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
    inputs={"set_params": MapDefinition, "query": CollisionCheckQuery},
    outputs={"response": CollisionCheckResult},
    language="""
        (in:set_params ; (in:query ; out:response)*)*
        """,
)
