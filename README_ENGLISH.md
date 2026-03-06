# AStar City

Interactive Python/Pygame prototype for visualizing route searching in a grid-modeled city, using A* and comparing it to Dijkstra's method.

## Features
- Interactive map editing
- Streets with varying costs
- Blocked buildings
- Configurable start and finish lines
- Route calculation with A*
- Comparison with Dijkstra
- Car animation
- Fast building generation

## Controls
- `1` Clear road
- `2` Medium traffic
- `3` Traffic jam
- `4` Building
- `S` Set start
- `G` Set finish
- `ESC` Return to normal mode
- `SPACE` Calculate route with A*
- `C` Compare A* vs. Dijkstra
- `P` Pause/resume car
- `R` Restart car
- `+/-` Change car speed
- `A` Activate route search animation
- `[/]` Change the speed of the route search animation
- `N` Change grid size
- `B` Generate buildings
- `X` Clear map

## Run from source code
```bash
pip install -r requirements.txt
python run_game.py