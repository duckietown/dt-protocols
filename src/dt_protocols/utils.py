from dataclasses import dataclass, replace
from typing import List

import math
import numpy as np
from geometry import SE2, se2_from_linear_angular, SE2value
from numpy.testing import assert_allclose, assert_equal
from zuper_commons.types import ZValueError

from aido_schemas import FriendlyPose
from duckietown_world import friendly_from_pose, pose_from_friendly
from . import logger
from .collision_protocol import PlacedPrimitive, PlanningSetup, PlanStep

__all__ = [
    "SimulationResult",
    "pose_diff",
    "simulate",
    "normalize_angle",
    "move_environment",
    "assert_fp_close",
    "move_environment",
    "get_trajectory",
    "realign_plan",
    "more_granular",
]


def assert_fp_close(a: FriendlyPose, b: FriendlyPose, atol=1e-10):
    assert_allclose(a.x, b.x, atol=atol)
    assert_allclose(a.y, b.y, atol=atol)

    t1 = normalize_angle(np.deg2rad(a.theta_deg))
    t2 = normalize_angle(np.deg2rad(b.theta_deg))
    assert_allclose(t1, t2, atol=atol)


def normalize_angle(x: float) -> float:
    c = np.cos(x)
    s = np.sin(x)
    return np.arctan2(s, c)


@dataclass
class SimulationResult:
    poses: List[FriendlyPose]
    ts: List[float]


def simulate(start: FriendlyPose, steps: List[PlanStep]) -> SimulationResult:
    q = pose_from_friendly(start)
    res = [start]
    ts = [0.0]
    t = 0.0
    for step in steps:
        if step.duration < 0:
            logger.error("Invalid duration", step=step)
            duration = 0.0
        else:
            duration = step.duration
        v = step.velocity_x_m_s
        w = np.deg2rad(step.angular_velocity_deg_s)
        V = se2_from_linear_angular([v, 0.0], w)
        dq = SE2.group_from_algebra(V * duration)
        q = q @ dq
        res.append(friendly_from_pose(q))
        t += duration
        ts.append(t)
    return SimulationResult(res, ts)


def pose_diff(q1: SE2value, q2: SE2value):
    d = SE2.multiply(SE2.inverse(q1), q2)
    return d


def move_environment(ps: PlanningSetup, ts: List[float], dt: float) -> List[List[PlacedPrimitive]]:
    nts = len(ts)
    snapshots: List[List[PlacedPrimitive]] = [[] for _ in range(nts)]

    for pp in ps.environment:

        if pp.motion is None:
            for i in range(nts):
                snapshots[i].append(pp)
        else:
            traj = get_trajectory(pp.pose, pp.motion.steps, pp.motion.periodic, ts, dt)
            for i, x in enumerate(traj.poses):
                pp2 = replace(pp, pose=x, motion=None)
                snapshots[i].append(pp2)

    return snapshots


def get_trajectory(fp: FriendlyPose, steps: List[PlanStep], periodic: bool, ts: List[float], dt: float):
    plan_granular = more_granular(steps, dt)
    duration = sum(_.duration for _ in plan_granular)
    duration_robot = ts[-1] - ts[0]
    if duration_robot > duration:
        if periodic:
            n = int(math.ceil(duration_robot / duration))
            plan_granular += plan_granular * (n - 1)
        else:
            rest = duration_robot - duration
            plan_granular.append(GranularPlanStep(rest, 0.0, 0.0, 0))

    tsp = get_ts(0.0, plan_granular)

    allts = sorted(set(ts) | set(tsp))
    allts = [_ for _ in allts if ts[0] <= _ <= ts[-1]]

    realigned = realign_plan(plan_granular, allts)
    simres = simulate(fp, realigned)

    ts_found = []
    poses = []
    errors = []
    for t in ts:
        i = find_nearest(simres.ts, t)

        # i = bisect(simres.ts, t) - 1
        # i = min(i, len(simres.ts)-1)
        errors.append(simres.ts[i] - t)
        ts_found.append(simres.ts[i])
        poses.append(simres.poses[i])

    assert_allclose(errors, 0.0, atol=1e-8)
    return SimulationResult(poses=poses, ts=ts_found)


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


# def over_horizon():


def realign_plan(plan: List[PlanStep], ts: List[float]) -> List[PlanStep]:
    assert_equal(ts[0], 0.0)
    duration = sum(_.duration for _ in plan)
    if duration < ts[-1]:
        msg = "Expect plan larger than sampling interval"
        raise ZValueError(msg, duration=duration, plan=plan, ts=ts)
    # realign plan such that the dts are correct
    rest_plan = list(plan)
    rest_dt = list(ts)
    t = rest_dt.pop(0)

    steps = []
    while True:
        if not rest_dt:
            break

        # if rest_plan:
        plan_dt = rest_plan[0].duration
        # else:
        #     plan_dt = +math.inf
        # if rest_dt:
        external_dt = rest_dt[0] - t
        # logger.info(t=t,
        #             rest_plan=rest_plan,
        #             rest_dt=rest_dt,
        #             plan_dt=plan_dt, external_dt=external_dt, )
        # else:
        #     external_dt = +math.inf
        if np.allclose(plan_dt, external_dt):
            steps.append(rest_plan.pop(0))
            rest_dt.pop(0)
            t += plan_dt
        elif plan_dt < external_dt:
            steps.append(rest_plan.pop(0))

            t += plan_dt
        else:

            if rest_plan:
                first = rest_plan.pop(0)
                s1 = replace(first, duration=external_dt)
                s2 = replace(first, duration=plan_dt - external_dt)
                steps.append(s1)
                rest_plan.insert(0, s2)

            rest_dt.pop(0)
            t += external_dt

    return steps


def get_ts(t0: float, plan: List[PlanStep]) -> List[float]:
    ts = []
    t = t0
    for s in plan:
        ts.append(t)
        t += float(s.duration)
    ts.append(t)
    return ts


@dataclass
class GranularPlanStep(PlanStep):
    subindex: int


def more_granular(plan: List[PlanStep], dt: float) -> List[GranularPlanStep]:
    assert dt > 0, dt
    res = []
    for p in plan:
        res.extend(more_granular_(p, dt))
    return res


def more_granular_(p: PlanStep, dt: float) -> List[GranularPlanStep]:
    dt = float(dt)
    # logger.info(p=p, dt=dt)
    n = int(np.ceil(p.duration * 1.0 / dt))
    ts = [i * dt for i in range(n + 3)]
    ts.append(p.duration)
    ts = [_ for _ in ts if _ <= p.duration]
    ts = sorted(set(ts))

    dts = [float(ts[i + 1] - ts[i]) for i in range(len(ts) - 1)]
    # d2 = sum(dts)
    # logger.info(dts=dts, d2=d2, d=p.duration)

    return [
        GranularPlanStep(
            duration=_,
            angular_velocity_deg_s=p.angular_velocity_deg_s,
            velocity_x_m_s=p.velocity_x_m_s,
            subindex=i,
        )
        for i, _ in enumerate(dts)
    ]
