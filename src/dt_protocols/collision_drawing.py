from typing import List

import numpy as np
from duckietown_world import pose_from_friendly
from duckietown_world.utils import SE2_apply_R2
from geometry import SE2, SE2value
from zuper_commons.logs import ZLogger

from .collision_protocol import Appearance, Circle, PlacedPrimitive, Rectangle

logger = ZLogger(__name__)

__all__ = ["plot_geometry"]


# noinspection PyListCreation
def plot_geometry(
    ax, se0: SE2value, structure: List[PlacedPrimitive], style, zorder: int, text: str = None
) -> List:
    from matplotlib import pyplot

    artists = []
    ax: pyplot.Axes
    for pp in structure:
        if pp.appearance is None:
            appearance = Appearance(style, 0)
        else:
            appearance = pp.appearance

        if text is not None:
            x, y = pp.pose.x, pp.pose.y
            x, y = SE2_apply_R2(se0, (x, y))
            a = pyplot.Text(text=text, x=x, y=y, zorder=zorder + 3)
            artists.append(a)
            ax.add_artist(a)
        if isinstance(pp.primitive, Circle):
            x, y = pp.pose.x, pp.pose.y
            x, y = SE2_apply_R2(se0, (x, y))
            zorder_ = zorder + appearance.rel_zorder
            a = pyplot.Circle(
                (x, y), pp.primitive.radius, fill=True, color=appearance.fillcolor, zorder=zorder_
            )
            ax.add_artist(a)
            artists.append(a)
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

            xy = np.array((xs, ys)).T
            zorder_ = zorder + appearance.rel_zorder
            a = pyplot.Polygon(xy, fill=True, edgecolor=None, facecolor=appearance.fillcolor, zorder=zorder_)
            ax.add_artist(a)
            artists.append(a)

    return artists
