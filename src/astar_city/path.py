from __future__ import annotations
from astar_city.grid import Coord

def reconstruct_path(came_from: dict[Coord, Coord], current: Coord) -> list[Coord]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path