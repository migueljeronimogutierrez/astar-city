from __future__ import annotations # Con esto accedemos a funcionalidades de versiones futuras de Python
from dataclasses import dataclass
from enum import Enum              # Los enums garantizan la consitencia, sobre todo con los errores en los nombres

class TerrainType(Enum):
    ROAD_FREE = "road_free"
    ROAD_TRAFFIC = "road_traffic"
    ROAD_JAM = "road_jam"
    BUILDING = "building"


@dataclass(frozen=True)
class TerrainSpec:
    label: str                      # El nombre que le demos
    walkable: bool                  # Si es True, se puede pisar
    weight: float                   # Atravesar esta celda costará "weight" veces más
    color_rgb: tuple[int, int, int] # El código RGB

# Configuración del terreno (Le daré unos pesos por defecto de 1, 3 y 7):
TERRAIN_SPECS: dict[TerrainType, TerrainSpec] = {
    TerrainType.ROAD_FREE: TerrainSpec(
        label="Clear road",
        walkable=True,
        weight=1.0,
        color_rgb=(240, 240, 240),
    ),
    TerrainType.ROAD_TRAFFIC: TerrainSpec(
        label="Medium traffic",
        walkable=True,
        weight=3.0,
        color_rgb=(200, 200, 255),
    ),
    TerrainType.ROAD_JAM: TerrainSpec(
        label="Traffic jam",
        walkable=True,
        weight=7.0,
        color_rgb=(255, 200, 200),
    ),
    TerrainType.BUILDING: TerrainSpec(
        label="Building",
        walkable=False,
        weight=0.0,  # No se usa ya que walkable=False
        color_rgb=(60, 60, 60),
    ),
}

# Función de ayuda
def min_walkable_weight() -> float:
    return min(spec.weight for spec in TERRAIN_SPECS.values() if spec.walkable)