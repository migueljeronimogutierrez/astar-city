from __future__ import annotations
import heapq
from dataclasses import dataclass
from typing import Optional
from astar_city.grid import Grid, Coord
from astar_city.heuristics import octile_distance
from astar_city.path import reconstruct_path
from astar_city.terrain import min_walkable_weight
from astar_city.search_result import SearchResult

# El cuerpo principal del algoritmo:
def astar_find_path(
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
    
    # Escalo de manera conservadora h(n):
    min_w = min_walkable_weight()
    
    # Cola de prioridad de candidatos a expandir:
    open_heap: list[tuple[float, int, Coord]] = []
    tie = 0

    came_from: dict[Coord, Coord] = {}

    # g_score: El mejor coste conocido desde start:
    g_score: dict[Coord, float] = {start: 0.0}

    # f_score: g + h:
    f_start = 0.0 + octile_distance(start, goal) * min_w
    heapq.heappush(open_heap, (f_start, tie, start))

    closed_set: set[Coord] = set()

    expanded = 0

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        if current in closed_set: # Si ya se cerró por una ruta mejor, lo salto
            continue

        expanded += 1

        if current == goal:
            path = reconstruct_path(came_from, current)
            return SearchResult(path=path, expanded_nodes=expanded, total_cost=g_score[current])

        closed_set.add(current)

        # Expandir vecinos:
        for neighbor, base_move_cost in grid.neighbors(
            current,
            allow_diagonal=allow_diagonal,
            prevent_corner_cutting=prevent_corner_cutting,
        ):
            if neighbor in closed_set:
                continue

            # Calcular el coste del movimiento según el peso:
            step_cost = base_move_cost * grid.weight(neighbor)
            tentative_g = g_score[current] + step_cost

            # Actualizar el mejor camino si se encuentra uno mejor:
            if (neighbor not in g_score) or (tentative_g < g_score[neighbor]): # En caso de que sea la primera vez que se ve un vecino o se ha mejorado g
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                
                h = octile_distance(neighbor, goal) * min_w
                f = tentative_g + h
                
                tie += 1
                heapq.heappush(open_heap, (f, tie, neighbor))

    return None