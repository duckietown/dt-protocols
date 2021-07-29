import os
from typing import Tuple

import numpy as np
import yaml
from duckietown_challenges.constants import ENV_CHALLENGE_NAME, ENV_SUBMISSION_ID, ENV_SUBMITTER_NAME
from geometry import SE2
from matplotlib import pyplot, pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation
from progressbar import ProgressBar
from zuper_commons.fs import write_ustring_to_utf8_file
from zuper_ipce import IESO, ipce_from_object

from .constants import COLOR_BG
from dt_protocols import (
    PlanningQuery,
    PlanningResult,
    PlanningSetup,
    plot_geometry,
)
from duckietown_world import pose_from_friendly
from . import logger
from .statistics import SolutionStats

__all__ = ["make_video"]


def make_video(ps: PlanningSetup, pq: PlanningQuery, pr: PlanningResult, s: SolutionStats, fn: str):
    all_stationary = all(_.motion is None for _ in ps.environment)
    if False:
        ipce = ipce_from_object(s, ieso=IESO(with_schema=False))
        write_ustring_to_utf8_file(yaml.dump(ipce), fn + "-stats.yaml")

    if True:
        try:
            ipce = ipce_from_object(pr, ieso=IESO(with_schema=False))
        except:
            pass
        else:
            write_ustring_to_utf8_file(yaml.dump(ipce), fn + "-plan.yaml")
    fig = plt.figure(constrained_layout=True)
    dpi = 100
    H = 1080
    grid = 4, 8
    wmain = 4
    W = int((H / grid[0]) * grid[1])
    fig.set_size_inches(W / dpi, H / dpi, True)

    gs = fig.add_gridspec(grid[0], grid[1])

    ax = fig.add_subplot(gs[:wmain, :wmain])
    ax2 = fig.add_subplot(gs[0:1, wmain:])
    ax3 = fig.add_subplot(gs[1:2, wmain:])
    ax_distance = fig.add_subplot(gs[2:3, wmain:])
    ax_curvature = fig.add_subplot(gs[3:4, wmain:])
    if ENV_SUBMISSION_ID in os.environ:
        submitter_name = os.environ[ENV_SUBMITTER_NAME]
        submission_id = os.environ[ENV_SUBMISSION_ID]
        challenge_name = os.environ[ENV_CHALLENGE_NAME]
        title = f"{submitter_name} - challenge {challenge_name} - submission {submission_id}"
        ax.set_title(title)
    plot_axes = [ax2, ax3, ax_curvature, ax_distance, ax_curvature]
    for _ in plot_axes:
        _.set_xlim(0.0, s.ts[-1])
    for _ in plot_axes[:-1]:
        _.get_xaxis().set_visible(False)

    # frames = len(s.actual_path)
    frames = list(range(len(s.actual_path)))
    logger.info(f=len(s.actual_path), ts=len(s.ts))

    ax3.plot(s.ts, s.ws, ".")
    ax3.set_title("angular velocity (deg/s)")

    ax2.plot(s.ts, s.vs, ".", label="v")

    ax2.set_title("linear velocity (m/s)")
    mk = 1.0

    def c_from_k(x):

        # return  np.arctan(x) / (np.pi/2)
        return 1.0 - np.exp(-x)

    kvalues = np.array([0, 0.1, 1, np.inf])
    ticks = list(c_from_k(kvalues))
    labels = [str(_) for _ in kvalues[:-1]] + ["+inf"]
    ax_curvature.set_yticks(ticks)
    ax_curvature.set_yticklabels(labels)
    ax_curvature.plot(s.ts, c_from_k(np.array(s.curvature)), ".", label="v")

    ax_curvature.set_title("curvature (1/m)")
    ax_distance.plot(s.ts, s.distance, ".", label="v")
    ax_distance.set_title("distance from obstacles (m)")

    def enlarge(v1, v2) -> Tuple[float, float]:
        m = (v2 - v1) * 0.1
        return v1 - m, v2 + m

    v_bounds = enlarge(ps.min_linear_velocity_m_s, ps.max_linear_velocity_m_s)

    ax2.set_ylim(*v_bounds)
    (line_v,) = ax2.plot([0, 0], v_bounds, "-", color="gray", zorder=10)

    for i in s.errors_linear_velocity:
        ax2.plot([s.ts[i], s.ts[i]], v_bounds, "-", color="red", zorder=-2)

    w_bounds = enlarge(-ps.max_angular_velocity_deg_s, +ps.max_angular_velocity_deg_s)

    ax3.set_ylim(*w_bounds)
    (line_w,) = ax3.plot([0, 0], w_bounds, "-", color="gray", zorder=-10)
    for i in s.errors_angular_velocity:
        ax3.plot([s.ts[i], s.ts[i]], w_bounds, "-", color="red", zorder=-2)

    c_bounds = enlarge(0, mk)
    ax_curvature.set_ylim(*c_bounds)
    (line_curvature,) = ax_curvature.plot([0, 0], c_bounds, "-", color="gray", zorder=-10)
    for i in s.errors_curvature:
        ax_curvature.plot([s.ts[i], s.ts[i]], c_bounds, "-", color="red", zorder=-2)

    d_bounds = enlarge(0, max(s.distance))
    ax_distance.set_ylim(*d_bounds)

    (line_distance,) = ax_distance.plot([0, 0], d_bounds, "-", color="gray", zorder=-10)
    for i in s.errors_distance:
        ax_distance.plot([s.ts[i], s.ts[i]], d_bounds, "-", color="red", zorder=-2)

    ax.set_aspect("equal")
    ax.axis((ps.bounds.xmin, ps.bounds.xmax, ps.bounds.ymin, ps.bounds.ymax))
    ax.axis("off")
    a = pyplot.Rectangle(
        (ps.bounds.xmin, ps.bounds.ymin),
        width=(ps.bounds.xmax - ps.bounds.xmin),
        height=(ps.bounds.ymax - ps.bounds.ymin),
        color=COLOR_BG,
        zorder=-10,
    )
    ax.add_artist(a)
    if all_stationary:
        plot_geometry(ax, SE2.identity(), ps.environment, None, 0)

    plot_geometry(ax, pose_from_friendly(pq.start), ps.body, "gray", 2)
    plot_geometry(ax, pose_from_friendly(pq.target), ps.body, "gray", 2)

    last = []

    lines = [line_w, line_v, line_curvature, line_distance]

    bar = ProgressBar(len(frames))
    bar.start()

    def animate(k):
        bar.update(k)
        f = frames[k]
        # logger.info(f'/{frames}')
        nonlocal last
        for artist in last:
            artist.remove()
        last.clear()
        fp = s.actual_path[f]
        s0 = pose_from_friendly(fp)
        last.extend(plot_geometry(ax, s0, ps.body, None, 10))

        if not all_stationary:
            environment = s.obstacles[f]
            last.extend(plot_geometry(ax, SE2.identity(), environment, None, 0))

        ti = s.ts[f]
        x = np.array([ti, ti])
        for _ in lines:
            _.set_xdata(x)

        changed = last + lines
        # logger.info(changed=changed, nchanged=len(changed))
        return changed

    # noinspection PyTypeChecker
    anim = FuncAnimation(fig, animate, frames=len(frames), interval=20, blit=True)

    FFwriter = FFMpegWriter(fps=10, extra_args=["-vcodec", "libx264"])
    d = os.path.dirname(fn)
    if not os.path.exists(d):
        os.makedirs(d)
    fn_video = fn + ".mp4"
    anim.save(fn_video, writer=FFwriter, dpi=dpi)
    pyplot.close(fig)
    bar.finish()
    logger.info(f"Written to {fn_video}")
