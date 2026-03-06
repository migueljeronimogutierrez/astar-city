from pathlib import Path
import sys
import unittest
# Me vuelvo a asegurar de que /src esté en el path de forma consistente:
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from astar_city.grid import Grid
from astar_city.terrain import TerrainType
from astar_city.astar import astar_find_path
from astar_city.dijkstra import dijkstra_find_path

class TestAStarWeighted(unittest.TestCase):
    def test_astar_matches_dijkstra_cost(self):
        g = Grid(rows=5, cols=5)

        start = (0, 2)
        goal = (4, 2)

        # Creo el atasco en la camino recto del medio:
        g.set_terrain((1, 2), TerrainType.ROAD_JAM)
        g.set_terrain((2, 2), TerrainType.ROAD_JAM)
        g.set_terrain((3, 2), TerrainType.ROAD_JAM)

        a = astar_find_path(g, start, goal)
        d = dijkstra_find_path(g, start, goal)

        self.assertIsNotNone(a)
        self.assertIsNotNone(d)
        assert a is not None and d is not None # A partir de aquí, a y d no son None, para segurar que no muestre a a.total_cost como posible None

        self.assertAlmostEqual(a.total_cost, d.total_cost, places=6) # A* y Dijkstra deben coincidir

        cost_recto = 7.0 + 7.0 + 7.0 + 1.0
        self.assertLess(a.total_cost, cost_recto)

if __name__ == "__main__":
    unittest.main()