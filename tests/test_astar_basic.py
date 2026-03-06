from pathlib import Path
import sys # Librería que da acceso a aspectos del intérprete, lo usaré para meter src/ en el path de ejecución
import unittest
# Me vuelvo a asegurar de que /src esté en el path de forma consistente:
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from astar_city.grid import Grid
from astar_city.terrain import TerrainType
from astar_city.astar import astar_find_path

class TestAStarBasic(unittest.TestCase):
    def test_path_exists_in_empty_grid(self):
        g = Grid(rows=10, cols=10)
        start = (0, 0)
        goal = (9, 9)

        res = astar_find_path(g, start, goal)
        self.assertIsNotNone(res)
        assert res is not None

        # Debe empezar y terminar bien:
        self.assertEqual(res.path[0], start)
        self.assertEqual(res.path[-1], goal)

        # En un grid vacío con diagonales, debería haber ruta relativamente corta:
        self.assertTrue(len(res.path) > 0)

    def test_no_path_when_blocked(self):
        g = Grid(rows=3, cols=3)
        start = (0, 0)
        goal = (2, 2)

        # Bloqueo todo alrededor de start para que no pueda salir:
        g.set_terrain((1, 0), TerrainType.BUILDING)
        g.set_terrain((0, 1), TerrainType.BUILDING)
        g.set_terrain((1, 1), TerrainType.BUILDING)

        res = astar_find_path(g, start, goal)
        self.assertIsNone(res)

if __name__ == "__main__":
    unittest.main()