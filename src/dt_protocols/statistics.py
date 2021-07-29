from dataclasses import dataclass, replace
from typing import Callable, Dict, List

import math
import numpy as np
from geometry import translation_angle_from_SE2
from progressbar import ProgressBar

from aido_schemas import FriendlyPose
from duckietown_world import pose_from_friendly
from . import logger
from .collision_protocol import (
    PlacedPrimitive,
    PlanningQuery,
    PlanningResult,
    PlanningSetup,
    PlanStep,
)

__all__ = ["SolutionStats", "get_stats"]


@dataclass
class SolutionStats:
    nerrors: int
    msgs: List[str]
    plan_granular: List[PlanStep]
    actual_path: List[FriendlyPose]
    ts: List[float]
    ws: List[float]
    vs: List[float]
    collided: List[bool]
    distance: List[float]
    curvature: List[float]
    exy: float
    etheta_deg: float
    obstacles: List[List[PlacedPrimitive]]

    errors_linear_velocity: Dict[int, str]
    errors_angular_velocity: Dict[int, str]
    errors_curvature: Dict[int, str]
    errors_distance: Dict[int, str]


from .collision_protocol import CollisionCheckResult, CollisionCheckQuery, MapDefinition
from .utils import more_granular, pose_diff, simulate, move_environment


def get_stats(
    ps: PlanningSetup,
    pq: PlanningQuery,
    pr: PlanningResult,
    dt: float,
    collision_checker: Callable[[MapDefinition, CollisionCheckQuery], CollisionCheckResult],
) -> SolutionStats:
    nerrors: int = 0
    msgs = []
    ts = []
    vs = []
    ws = []
    collided = []
    distance = []

    plan_granular = more_granular(pr.plan, dt)
    actual_path = simulate(pq.start, plan_granular).poses

    t = 0.0
    for s in plan_granular:
        ts.append(t)
        vs.append(float(s.velocity_x_m_s))
        ws.append(float(s.angular_velocity_deg_s))
        t += float(s.duration)
    ts.append(t)
    vs.append(0.0)
    ws.append(0.0)

    obstacles = move_environment(ps, ts, dt)

    def get_curvature(v: float, w: float) -> float:
        v = math.fabs(v)
        w = math.fabs(w)
        if v < 0.00001:
            return np.inf

        # v = omega * R
        # K = 1/R = omega/v

        return w / v

    curvature: List[float] = [get_curvature(a, b) for a, b in zip(vs, ws)]

    bar = ProgressBar(len(actual_path))
    bar.start()

    errors_linear_velocity = {}
    errors_angular_velocity = {}
    errors_curvature = {}
    errors_distance = {}

    for i, pose in enumerate(actual_path):
        bar.update(i)
        psi = replace(ps, environment=obstacles[i])
        r = collision_checker(psi, CollisionCheckQuery(pose))
        collided.append(r.collision)
        if hasattr(r, "distance"):
            d = r.distance if not r.collision else 0.0
        else:
            d = 1.0
        distance.append(d)
        if r.collision:
            msg = f"Robot collides at time {ts[i]}"
            msgs.append(msg)
            errors_distance[i] = msg
            nerrors += 1
    bar.finish()

    for i, plan_step in enumerate(plan_granular):
        if plan_step.subindex != 0:
            continue
        if plan_step.duration < 0:
            msgs.append(f"Invalid negative duration at step #{i}:\n{plan_step}")
            nerrors += 1
        if not ps.min_linear_velocity_m_s <= plan_step.velocity_x_m_s <= ps.max_linear_velocity_m_s:
            msg = f"Invalid linear velocity at step #{i}:\n{plan_step}"
            msgs.append(msg)
            nerrors += 1
            errors_linear_velocity[i] = msg

        if math.fabs(plan_step.angular_velocity_deg_s) > ps.max_angular_velocity_deg_s:
            msg = f"Invalid angular velocity at step #{i}:\n{plan_step}"
            msgs.append(msg)
            nerrors += 1
            errors_angular_velocity[i] = msg
        ki = get_curvature(plan_step.velocity_x_m_s, plan_step.angular_velocity_deg_s)
        if ki > ps.max_curvature:
            msg = f"Invalid curvature {ki} > {ps.max_curvature} at step #{i}:\n{plan_step}"
            msgs.append(msg)
            errors_curvature[i] = msg
            nerrors += 1
        #
        # total_rot_deg = plan_step.duration * math.fabs(plan_step.angular_velocity_deg_s)
        # if total_rot_deg > 180.0:
        #     msgs.append(f"Total rotation {total_rot_deg} at step #{i}:\n{plan_step}")
        #     # nerrors += 1

    dq = pose_diff(pose_from_friendly(actual_path[-1]), pose_from_friendly(pq.target))
    dxy, dt = translation_angle_from_SE2(dq)
    exy = float(np.linalg.norm(dxy))
    etheta_deg = float(np.rad2deg(float(math.fabs(dt))))
    logger.info("Last error", exy=exy, etheta_deg=etheta_deg)
    if exy > ps.tolerance_xy_m:
        nerrors += 1
        msgs.append(f"Too far from final position xy ({exy})")
    if etheta_deg > ps.tolerance_theta_deg:
        nerrors += 1
        msgs.append(f"Too far from final orientation theta ({etheta_deg})")

    return SolutionStats(
        nerrors,
        msgs,
        plan_granular,
        actual_path,
        ts,
        ws,
        vs,
        collided,
        distance,
        curvature,
        exy,
        etheta_deg,
        obstacles,
        errors_linear_velocity=errors_linear_velocity,
        errors_angular_velocity=errors_angular_velocity,
        errors_curvature=errors_curvature,
        errors_distance=errors_distance,
    )
