from typing import List

from geometry import SE2, SE2value
from zuper_commons.logs import ZLogger

from duckietown_world import pose_from_friendly
from duckietown_world.utils import SE2_apply_R2
from .collision_protocol import Circle, PlacedPrimitive, Rectangle

logger = ZLogger(__name__)

__all__ = ["plot_geometry"]


# noinspection PyListCreation
def plot_geometry(ax, se0: SE2value, structure: List[PlacedPrimitive], style, zorder: int):
    from matplotlib import pyplot

    ax: pyplot.Axes
    for pp in structure:
        if isinstance(pp.primitive, Circle):
            x, y = pp.pose.x, pp.pose.y
            x, y = SE2_apply_R2(se0, (x, y))
            ax.add_artist(pyplot.Circle((x, y), pp.primitive.radius, fill=True, color=style, zorder=zorder))
        if isinstance(pp.primitive, Rectangle):
            q = SE2.multiply(se0, pose_from_friendly(pp.pose))
            points = []

            points.append(SE2_apply_R2(q, (pp.primitive.xmin, pp.primitive.ymin)))
            points.append(SE2_apply_R2(q, (pp.primitive.xmin, pp.primitive.ymax)))
            points.append(SE2_apply_R2(q, (pp.primitive.xmax, pp.primitive.ymax)))
            points.append(SE2_apply_R2(q, (pp.primitive.xmax, pp.primitive.ymin)))
            points.append(SE2_apply_R2(q, (pp.primitive.xmin, pp.primitive.ymin)))
            xs = [_[0] for _ in points]
            ys = [_[1] for _ in points]

            pyplot.fill(xs, ys, "-", color=style, zorder=zorder)
        # if isinstance(pp.primitive, Rectanlge):
        #     x, y = pp.pose.x, pp.pose.y
        #     ax.add_artist(pyplot.Circle((x, y), pp.primitive.radius, fill=False, color=style))
