from __future__ import annotations
import heapq
from dataclasses import dataclass
from typing import Optional
from astar_city.grid import Grid, Coord
from astar_city.path import reconstruct_path
from astar_city.search_result import SearchResult

def dijkstra_find_path(
    grid: Grid,
    start: Coord,
    goal: Coord,
    allow_diagonal: bool = True,
    prevent_corner_cutting: bool = True,
) -> Optional[SearchResult]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return None
    if not grid.is_walkable(start) or not grid.is_walkable(goal):
        return None

    open_heap: list[tuple[float, int, Coord]] = []
    tie = 0

    came_from: dict[Coord, Coord] = {}
    dist: dict[Coord, float] = {start: 0.0}

    heapq.heappush(open_heap, (0.0, tie, start))
    closed_set: set[Coord] = set()
    expanded = 0

    while open_heap:
        current_dist, _, current = heapq.heappop(open_heap)

        if current in closed_set:
            continue

        expanded += 1

        if current == goal:
            path = reconstruct_path(came_from, current)
            return SearchResult(path=path, expanded_nodes=expanded, total_cost=current_dist)

        closed_set.add(current)

        for neighbor, base_move_cost in grid.neighbors(
            current,
            allow_diagonal=allow_diagonal,
            prevent_corner_cutting=prevent_corner_cutting,
        ):
            if neighbor in closed_set:
                continue

            step_cost = base_move_cost * grid.weight(neighbor)
            nd = current_dist + step_cost

            if (neighbor not in dist) or (nd < dist[neighbor]):
                dist[neighbor] = nd
                came_from[neighbor] = current
                tie += 1
                heapq.heappush(open_heap, (nd, tie, neighbor))

    return None