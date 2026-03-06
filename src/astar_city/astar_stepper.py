from __future__ import annotations
import heapq
from dataclasses import dataclass
from typing import Generator, Optional
from astar_city.grid import Grid, Coord
from astar_city.heuristics import octile_distance
from astar_city.path import reconstruct_path
from astar_city.search_result import SearchResult
from astar_city.terrain import min_walkable_weight

# Variante del código original, donde se calculan en cada paso más variables:
@dataclass(frozen=True)
class AStarStep:
    current: Coord                        # Nodo expandido en este paso
    open_set: set[Coord]                  # Conjunto de nodos en frontera (Para pintarlos)
    closed_set: set[Coord]                # Conjunto de nodos ya expandidos
    done: bool                            # Si ha terminado
    result: Optional[SearchResult] = None # Guarda los resultados de la ruta 

# Generador de los pasos de A* (Cada yield corresponde a una expansión de un nodo, devolviendo open/closed)
def astar_steps(
    grid: Grid,
    start: Coord,
    goal: Coord,
    allow_diagonal: bool = True,
    prevent_corner_cutting: bool = True,
) -> Generator[AStarStep, None, None]:
    if not grid.in_bounds(start) or not grid.in_bounds(goal):
        return
    if not grid.is_walkable(start) or not grid.is_walkable(goal):
        return

    min_w = min_walkable_weight()

    open_heap: list[tuple[float, int, Coord]] = []
    tie = 0

    came_from: dict[Coord, Coord] = {}
    g_score: dict[Coord, float] = {start: 0.0}

    f_start = octile_distance(start, goal) * min_w
    heapq.heappush(open_heap, (f_start, tie, start))

    open_set: set[Coord] = {start}
    closed_set: set[Coord] = set()

    expanded = 0

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        if current in closed_set:
            continue

        expanded += 1
        open_set.discard(current)

        # Si llega, devuelve un último step con done=True y result:
        if current == goal:
            path = reconstruct_path(came_from, current)
            res = SearchResult(path=path, expanded_nodes=expanded, total_cost=g_score[current])
            yield AStarStep(current=current, open_set=set(open_set), closed_set=set(closed_set), done=True, result=res)
            return

        closed_set.add(current)

        # Yield intermedio (así está el mapa justo después de expandir current):
        yield AStarStep(current=current, open_set=set(open_set), closed_set=set(closed_set), done=False)

        for neighbor, base_move_cost in grid.neighbors(
            current,
            allow_diagonal=allow_diagonal,
            prevent_corner_cutting=prevent_corner_cutting,
        ):
            if neighbor in closed_set:
                continue

            step_cost = base_move_cost * grid.weight(neighbor)
            tentative_g = g_score[current] + step_cost

            if (neighbor not in g_score) or (tentative_g < g_score[neighbor]):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                h = octile_distance(neighbor, goal) * min_w
                f = tentative_g + h

                tie += 1
                heapq.heappush(open_heap, (f, tie, neighbor))
                open_set.add(neighbor)

    # Si se vacía el heap, no hay ruta:
    yield AStarStep(current=start, open_set=set(), closed_set=set(closed_set), done=True, result=None)