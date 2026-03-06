import math
from astar_city.grid import Coord

def octile_distance(a: Coord, b: Coord) -> float:
    ax, ay = a
    bx, by = b

    dx = abs(ax - bx)
    dy = abs(ay - by)

    D = 1.0
    D2 = math.sqrt(2.0)

    return D * (dx + dy) + (D2 - 2.0 * D) * min(dx, dy)