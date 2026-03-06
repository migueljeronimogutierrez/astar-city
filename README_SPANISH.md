# AStar City

Prototipo interactivo en Python/Pygame para visualizar búsqueda de rutas en una ciudad modelada como grid, usando A* y comparándolo con Dijkstra.

## Funcionalidades
- Edición interactiva del mapa
- Calles con distintos costes
- Edificios bloqueados
- Inicio y meta configurables
- Cálculo de ruta con A*
- Comparación con Dijkstra
- Animación del coche
- Generación rápida de edificios

## Controles
- `1` Calle libre
- `2` Tráfico medio
- `3` Atasco
- `4` Edificio
- `S` Colocar inicio
- `G` Colocar meta
- `ESC` Volver a modo normal
- `SPACE` Calcular ruta con A*
- `C` Comparar A* vs Dijkstra
- `P` Pausa/reanuda coche
- `R` Reinicia coche
- `+/-` Cambia velocidad del coche
- `A` Activar animación de búsqueda de ruta
- `[/]` Cambia velocidad de la animación de búsqueda de ruta
- `N` Cambiar tamaño del grid
- `B` Generar edificios
- `X` Limpiar mapa

## Ejecutar desde código fuente
```bash
pip install -r requirements.txt
python run_game.py