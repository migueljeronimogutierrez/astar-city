from pathlib import Path
import sys
# Me vuelvo a asegurar de que /src esté en el path de forma consistente::
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from astar_city.grid import Grid
from astar_city.terrain import TerrainType

def main() -> None:
    g = Grid(rows=3, cols=3)

    # Situación, start en (0,0) -> Bloqueo (1,0) y (0,1) -> La diagonal hacia (1,1) NO debería ser válida si prevenimos corner cutting
    start = (0, 0)
    g.set_start(start)

    g.set_terrain((1, 0), TerrainType.BUILDING)
    g.set_terrain((0, 1), TerrainType.BUILDING)

    n1 = g.neighbors(start, allow_diagonal=True, prevent_corner_cutting=True)
    n2 = g.neighbors(start, allow_diagonal=True, prevent_corner_cutting=False)

    print("Neighbors con prevent_corner_cutting=True:", n1)
    print("Neighbors con prevent_corner_cutting=False:", n2)

if __name__ == "__main__":
    main()