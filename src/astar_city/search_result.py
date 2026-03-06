from __future__ import annotations
from dataclasses import dataclass
from astar_city.grid import Coord

# Guardo las métricas más importantes:
@dataclass(frozen=True)
class SearchResult:
    path: list[Coord]
    expanded_nodes: int
    total_cost: float