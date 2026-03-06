from __future__ import annotations
import math
from typing import Optional # En vez de escribir (... | None), escribo (Optional[...])
from astar_city.terrain import TerrainType, TERRAIN_SPECS

Coord = tuple[int, int]

# La clase grid guardará el terreno de cada celda, el start y goal, y calcula los vecinos con las reglas válidas:
class Grid:

    def __init__(
        self,
        rows: int,
        cols: int,
        default_terrain: TerrainType = TerrainType.ROAD_FREE,
    ) -> None:
        self.rows = rows
        self.cols = cols

        self._cells: list[list[TerrainType]] = [
            [default_terrain for _ in range(cols)] for _ in range(rows) # Hay que tener en cuenta durante todo el proyecto que la matriz es [y][x] y no al revés
        ]

        self.start: Optional[Coord] = None
        self.goal: Optional[Coord] = None

    # ---------------------------
    # Funciones de ayuda
    # ---------------------------

    # Detección de si está fuera del grid:
    def in_bounds(self, pos: Coord) -> bool:
        x, y = pos
        return 0 <= x < self.cols and 0 <= y < self.rows

    def get_terrain(self, pos: Coord) -> TerrainType:
        x, y = pos
        return self._cells[y][x]


    def set_terrain(self, pos: Coord, terrain: TerrainType) -> None:
        if not self.in_bounds(pos):
            return

        x, y = pos
        self._cells[y][x] = terrain

        if not self.is_walkable(pos): # Para asegurar que el start y el goal son alcanzables
            if self.start == pos:
                self.start = None
            if self.goal == pos:
                self.goal = None

    def is_walkable(self, pos: Coord) -> bool:
        terrain = self.get_terrain(pos)
        return TERRAIN_SPECS[terrain].walkable

    def weight(self, pos: Coord) -> float:
        terrain = self.get_terrain(pos)
        return TERRAIN_SPECS[terrain].weight

    # ---------------------------
    # Start / Goal (Devulve que se pueden colocar o no)
    # ---------------------------
    def set_start(self, pos: Coord) -> bool:
        if not self.in_bounds(pos):
            return False
        if not self.is_walkable(pos):
            return False
        self.start = pos
        return True

    def set_goal(self, pos: Coord) -> bool:
        if not self.in_bounds(pos):
            return False
        if not self.is_walkable(pos):
            return False
        self.goal = pos
        return True

    # ---------------------------
    # Vecinos (8 direcciones)
    # ---------------------------

    # Creación de vecinos válidos:
    def neighbors(
        self,
        pos: Coord,
        allow_diagonal: bool = True,
        prevent_corner_cutting: bool = True,
    ) -> list[tuple[Coord, float]]:
        if not self.in_bounds(pos):
            return []

        x, y = pos

        # 4 direcciones base:
        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ]

        # Las diagonales (En caso de que se pueda ir en diagonal):
        if allow_diagonal:
            directions += [
                (1, 1),
                (1, -1),
                (-1, 1),
                (-1, -1),
            ]

        results: list[tuple[Coord, float]] = []

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            npos = (nx, ny)

            if not self.in_bounds(npos):
                continue

            if not self.is_walkable(npos):
                continue

            is_diag = (dx != 0) and (dy != 0)

            if is_diag and prevent_corner_cutting: # Aquí creo la regla de no atravesar esquinas
                adj1 = (x + dx, y)      # Horizontal
                adj2 = (x, y + dy)      # Vertical

                # Por construcción, adj1/adj2 están in_bounds si npos lo está:
                if (not self.is_walkable(adj1)) or (not self.is_walkable(adj2)):
                    continue

            base_cost = math.sqrt(2.0) if is_diag else 1.0 # Aplico más peso al movimiento diagonal
            results.append((npos, base_cost))

        return results

    # ---------------------------
    # Utilidad para render / depuración
    # ---------------------------

    # En vez de limpiar con un bucle, relleno todo el grid con un terreno:
    def fill(self, terrain: TerrainType) -> None:
        # Iterar por todas las celdas:
        for y in range(self.rows):
            for x in range(self.cols):
                self._cells[y][x] = terrain

        # Si el terreno es no-walkable, invalidamos start/goal
        if not TERRAIN_SPECS[terrain].walkable:
            self.start = None
            self.goal = None

    # Pintar un rectángulo (x0, y0) con un tamaño de w x h:
    def set_rect(self, x0: int, y0: int, w: int, h: int, terrain: TerrainType, protect: set[Coord] | None = None) -> None:
        if protect is None:
            protect = set() # Celdas que no se pueden modificar

        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                pos = (x, y)
                if not self.in_bounds(pos):
                    continue
                if pos in protect:
                    continue
                self._cells[y][x] = terrain

    # Iterar todas las celdas:
    def iter_cells(self):
        for y in range(self.rows):
            for x in range(self.cols):
                yield x, y, self._cells[y][x]