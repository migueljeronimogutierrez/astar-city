import pygame
import sys
import random
from time import perf_counter
from pathlib import Path
from astar_city.constants import (
    CELL_SIZE,
    PANEL_WIDTH,
    DEFAULT_GRID_COLS,
    DEFAULT_GRID_ROWS,
    MIN_GRID_COLS,
    MAX_GRID_COLS,
    MIN_GRID_ROWS,
    MAX_GRID_ROWS,
    FPS,
)
from astar_city.grid import Grid
from astar_city.terrain import TerrainType, TERRAIN_SPECS
from astar_city.astar import astar_find_path
from astar_city.dijkstra import dijkstra_find_path
from astar_city.constants import PANEL_WIDTH
from astar_city.astar_stepper import astar_steps, AStarStep

# Creo la clase central de la app:
class PygameApp:
    def __init__(self) -> None:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"): # Para poder realizar correctamente el ejecutable
            self.assets_dir = Path(sys._MEIPASS) / "assets"
        else:
            self.assets_dir = Path(__file__).resolve().parents[1] / "assets"

        pygame.init()

        self.clock = pygame.time.Clock()
        self.running = True

        # Grid dinámico (Arranca con los defaults):
        self.grid = Grid(rows=DEFAULT_GRID_ROWS, cols=DEFAULT_GRID_COLS)

        # Dimensiones derivadas del grid actual:
        self._recompute_sizes()

        # Ventana:
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("A* City — Prototype")

        # Modo resize (Mediante una entrada de texto):
        self.resize_mode = False
        self.resize_text = ""

        # Pincel actual para pintar terrenos:
        self.active_brush = TerrainType.ROAD_FREE

        # Modo de colocación especial (None / "start" / "goal"):
        self.place_mode: str | None = None

        # Fuente para mostrar estado en pantalla + Cargar sprites:
        self.font = pygame.font.Font(None, 22)
        self.assets_dir = Path(__file__).resolve().parents[1] / "assets"
        self.sprites = self._load_sprites()

        # Para pintar arrastrando:
        self.is_painting = False

        # Ruta calculada (Lista de celdas):
        self.path: list[tuple[int, int]] | None = None

        # Coste y nodos expandidos:
        self.last_cost: float | None = None
        self.last_expanded: int | None = None
        self.last_status: str = "Press SPACE to calculate route"

        # Resultados de comparación:
        self.astar_cost: float | None = None
        self.astar_expanded: int | None = None
        self.astar_ms: float | None = None

        self.dijkstra_cost: float | None = None
        self.dijkstra_expanded: int | None = None
        self.dijkstra_ms: float | None = None

        # Animación del coche:
        self.car_playing = False
        self.car_progress = 0.0  # Progreso sobre la ruta: 0.0 = start, 1.0 = hacia el siguiente paso, etc.
        self.car_speed_cps = 6.0 # Celdas por segundo (Ajustable)

        # Animación del algoritmo de A*
        self.search_playing = False
        self.search_steps_per_sec = 120.0 # Velocidad
        self.search_accum = 0.0           # Acumulador de dt
        self.search_gen = None            # Generador
        self.search_open: set[tuple[int, int]] = set()
        self.search_closed: set[tuple[int, int]] = set()
        self.search_current: tuple[int, int] | None = None
        self.search_done = False

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Los segundos desde el frame anterior
            self._handle_events()
            self._update(dt)
            self._render()

        pygame.quit()

    # Pasar la información del camino a las variables creadas:
    def _compute_path(self) -> None:
        # Si falta start o goal:
        if self.grid.start is None or self.grid.goal is None:
            self.path = None
            self.last_cost = None
            self.last_expanded = None
            self.last_status = "[NOTICE] START/GOAL missing"
            return

        res = astar_find_path(self.grid, self.grid.start, self.grid.goal)

        if res is None:
            self.path = None
            self.last_cost = None
            self.last_expanded = None
            self.last_status = "No possible route"
            return

        self.path = res.path
        self.last_cost = res.total_cost
        self.last_expanded = res.expanded_nodes
        self.last_status = "Calculated route"
        self.car_progress = 0.0
        self.car_playing = True  # Se puede cambiar a False si no quiero que "arranque" solo

    # Comparo algoritmos:
    def _compare_algorithms(self) -> None:
        # Si falta start o goal, no comparo:
        if self.grid.start is None or self.grid.goal is None:
            self.last_status = "[NOTICE] START/GOAL missing"
            return

        # -------- A* --------
        t0 = perf_counter()
        a = astar_find_path(self.grid, self.grid.start, self.grid.goal)
        t1 = perf_counter()

        if a is None:
            self.last_status = "[NOTICE] A* did not find a route (Cannot be compared)"
            self.path = None
            return

        self.astar_cost = a.total_cost
        self.astar_expanded = a.expanded_nodes
        self.astar_ms = (t1 - t0) * 1000.0 # Se multiplica por 1000 para convertirlo a ms

        # Guardamos la ruta de A* como ruta "principal" (La que se dibuja):
        self.path = a.path

        # Iniciamos la animación del coche:
        self.car_progress = 0.0
        self.car_playing = True

        # -------- Dijkstra --------
        t2 = perf_counter()
        d = dijkstra_find_path(self.grid, self.grid.start, self.grid.goal)
        t3 = perf_counter()

        if d is None:
            self.last_status = "[NOTICE] Dijkstra did not find a route (Cannot be compared)" # Esto casi nunca debería pasar si A* encontró ruta, pero lo dejo por robustez
            return

        self.dijkstra_cost = d.total_cost
        self.dijkstra_expanded = d.expanded_nodes
        self.dijkstra_ms = (t3 - t2) * 1000.0

        # Mensaje de confirmación:
        self.last_status = "Comparison ready (A* vs Dijkstra)"

    # -----------------------
    # Funciones de ayuda
    # -----------------------

    # Centra el sprite del coche en en centro de la celda:
    def _cell_center_px(self, cell: tuple[int, int]) -> tuple[float, float]:
        x, y = cell
        cx = x * CELL_SIZE + CELL_SIZE / 2.0
        cy = y * CELL_SIZE + CELL_SIZE / 2.0
        return cx, cy
    
    # Recalcular el tamaño:
    def _recompute_sizes(self) -> None:
        self.grid_width = self.grid.cols * CELL_SIZE
        self.grid_height = self.grid.rows * CELL_SIZE
        self.window_width = self.grid_width + PANEL_WIDTH
        self.window_height = self.grid_height

    # Aplicar el tamaño:
    def _apply_resize(self, new_cols: int, new_rows: int) -> None:
        # Validación básica:
        if not (MIN_GRID_COLS <= new_cols <= MAX_GRID_COLS):
            self.last_status = f"[NOTICE] cols out of range ({MIN_GRID_COLS}-{MAX_GRID_COLS})"
            return
        if not (MIN_GRID_ROWS <= new_rows <= MAX_GRID_ROWS):
            self.last_status = f"[NOTICE] rows out of range ({MIN_GRID_ROWS}-{MAX_GRID_ROWS})"
            return

        # Nuevo grid: Empieza limpio
        self.grid = Grid(rows=new_rows, cols=new_cols)

        # Recalcular tamaños y recrear ventana:
        self._recompute_sizes()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))

        # Invalida soluciones/metrics/coche:
        self._invalidate_solution(full=True)
        self.last_status = f"New grid: {new_cols}x{new_rows}"

    # Invalidar las respuestas:
    def _invalidate_solution(self, full: bool = False) -> None:
        # Ruta + métricas:
        self.path = None
        self.last_cost = None
        self.last_expanded = None

        # Comparativa:
        self.astar_cost = None
        self.astar_expanded = None
        self.astar_ms = None
        self.dijkstra_cost = None
        self.dijkstra_expanded = None
        self.dijkstra_ms = None

        # Coche:
        self.car_playing = False
        self.car_progress = 0.0

        # Animación de A*:
        self._clear_search_viz()

        if full:
            self.grid.start = None
            self.grid.goal = None
    
    # Parseo del texto:
    def _try_parse_and_resize(self) -> None:
        raw = self.resize_text.strip().lower().replace("x", ",").replace(" ", "")
        if "," not in raw:
            self.last_status = "[NOTICE] Size: cols,rows (Example: 40,25)"
            return

        a, b = raw.split(",", 1)
        if not (a.isdigit() and b.isdigit()):
            self.last_status = "[NOTICE] Only use numbers: cols,rows"
            return

        new_cols = int(a)
        new_rows = int(b)
        self.resize_mode = False
        self.resize_text = ""
        self._apply_resize(new_cols, new_rows)

    # Generar bloques de edificios aleatoriamente:
    def _generate_buildings_blocks(self, density: float = 0.18) -> None: # Density es el porcentaje aproximado de celdas que acaban como edificio
        # Limpio el mapa:
        self.grid.fill(TerrainType.ROAD_FREE)

        protect = set()
        if self.grid.start:
            protect.add(self.grid.start)
        if self.grid.goal:
            protect.add(self.grid.goal)

        area = self.grid.rows * self.grid.cols
        target_buildings = int(area * density)

        placed = 0
        tries = 0

        # Parámetros de bloques ajustables:
        min_w, max_w = 2, 7
        min_h, max_h = 2, 7

        while placed < target_buildings and tries < area * 10:
            tries += 1

            w = random.randint(min_w, max_w)
            h = random.randint(min_h, max_h)

            x0 = random.randint(0, max(0, self.grid.cols - 1))
            y0 = random.randint(0, max(0, self.grid.rows - 1))

            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    pos = (x, y)
                    if not self.grid.in_bounds(pos) or pos in protect:
                        continue
                    # Solo cambio de no-edificio a edificio:
                    if self.grid.get_terrain(pos) != TerrainType.BUILDING:
                        self.grid._cells[y][x] = TerrainType.BUILDING
                        placed += 1
                    if placed >= target_buildings:
                        break
                if placed >= target_buildings:
                    break

        # Por seguridad, si start/goal existen, garantizamos que no queden bloqueados:
        if self.grid.start:
            self.grid.set_terrain(self.grid.start, TerrainType.ROAD_FREE)
        if self.grid.goal:
            self.grid.set_terrain(self.grid.goal, TerrainType.ROAD_FREE)

    # Limpiamos las variables de la animación:
    def _clear_search_viz(self) -> None:
        self.search_open.clear()
        self.search_closed.clear()
        self.search_current = None
        self.search_done = False
        self.search_gen = None
        self.search_playing = False
        self.search_accum = 0.0

    # Interruptor para iniciar/parar la animación
    def _toggle_search_animation(self) -> None:
        # Necesitamos start/goal
        if self.grid.start is None or self.grid.goal is None:
            self.last_status = "[NOTICE] START/GOAL missing"
            return

        # Si no hay generador activo o ya terminó, creamos uno nuevo
        if self.search_gen is None or self.search_done:
            self._clear_search_viz()
            self.search_gen = astar_steps(self.grid, self.grid.start, self.grid.goal)
            self.search_playing = True
            self.last_status = "Animated A*: PLAY (Pause/Resume)"

            # Limpio la ruta anterior para que se vea el proceso desde cero:
            self.path = None
            self.last_cost = None
            self.last_expanded = None
            self.car_progress = 0.0
            self.car_playing = False
            return

        # Si ya existe, toggle play/pause
        self.search_playing = not self.search_playing
        self.last_status = "Animated A*: PLAY" if self.search_playing else "Animated A*: PAUSE"

    # Carga y transforma los sprites para que sean usables:
    def _load_sprite(self, filename: str) -> pygame.Surface | None:
        path = self.assets_dir / filename
        if not path.exists():
            return None

        img = pygame.image.load(str(path)).convert_alpha()
        return pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))

    # Carga los sprites si existen:
    def _load_sprites(self) -> dict[str, pygame.Surface]:
        sprites: dict[str, pygame.Surface] = {}

        # Tiles
        for key, fname in [
            ("road_free", "road_free.png"),
            ("road_traffic", "road_traffic.png"),
            ("road_jam", "road_jam.png"),
            ("building", "building.png"),
            ("goal", "goal.png"),
            ("car", "car.png"),
        ]:
            s = self._load_sprite(fname)
            if s is not None:
                sprites[key] = s
        return sprites

    # -----------------------
    # Estabecer los Inputs
    # -----------------------

    # Gestión de los distintos eventos que pueden generar los inputs:
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Si está en modo resize, la captura de caracteres reales se hace con event.unicode
            if event.type == pygame.KEYDOWN:
                if self.resize_mode:
                    # Se guardan caracteres imprimibles (digits, ',', 'x', espacios):
                    ch = event.unicode
                    if ch and ch in "0123456789, xX":
                        self.resize_text += ch
                    # Luego dejo que _handle_keydown gestione ENTER/BACKSPACE/ESC:
                self._handle_keydown(event.key)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click
                    self.is_painting = True
                    self._handle_left_click(event.pos)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_painting = False

            if event.type == pygame.MOUSEMOTION:
                if self.is_painting:
                    self._handle_left_click(event.pos) # Así consigo que podamos pintar arrastrando

    # Selección de pincel por teclas numéricas:
    def _handle_keydown(self, key: int) -> None:
        # Si estamos en modo resize, solo se procesa texto (Salvo ESC):
        # Se aceptan dígitos, coma, x, espacio (Para teclados distintos)
        if self.resize_mode:
            if key == pygame.K_ESCAPE:
                self.resize_mode = False
                self.resize_text = ""
                self.last_status = "Resize cancelled"
                return

            if key == pygame.K_RETURN:
                self._try_parse_and_resize()
                return

            if key == pygame.K_BACKSPACE:
                self.resize_text = self.resize_text[:-1]
                return
            return
        
        # Elegir generación aleatoria:
        elif key == pygame.K_b:
            self._generate_buildings_blocks(density=0.18)
            self._invalidate_solution()
            self.last_status = "Generated buildings"

        # Limpiar mapa:
        elif key == pygame.K_x:
            self.grid.fill(TerrainType.ROAD_FREE)
            # mantenemos start/goal si ya estaban (siguen siendo walkable)
            self._invalidate_solution()
            self.last_status = "Cleaned map"

        # Cambiar de pinceles:
        if key == pygame.K_1:
            self.active_brush = TerrainType.ROAD_FREE
            self.place_mode = None
        elif key == pygame.K_2:
            self.active_brush = TerrainType.ROAD_TRAFFIC
            self.place_mode = None
        elif key == pygame.K_3:
            self.active_brush = TerrainType.ROAD_JAM
            self.place_mode = None
        elif key == pygame.K_4:
            self.active_brush = TerrainType.BUILDING
            self.place_mode = None

        # Modos especiales para colocar inicio/meta:
        elif key == pygame.K_s:
            self.place_mode = "start"
        elif key == pygame.K_g:
            self.place_mode = "goal"
        elif key == pygame.K_ESCAPE:
            self.place_mode = None

        # Comparar algoritmos:
        elif key == pygame.K_c:
            self._compare_algorithms()

        # Ejecutar el programa:
        elif key == pygame.K_SPACE:
            self._compute_path()

        # Modo resize:
        elif key == pygame.K_n:
            self.resize_mode = not self.resize_mode
            self.resize_text = ""
            self.last_status = "Resize: write cols,rows y press ENTER" if self.resize_mode else "Resize cancelled"

        # Controles de la animación:
        elif key == pygame.K_p:
            # play/pause
            if self.path:
                self.car_playing = not self.car_playing

        # Resetear la aniación:
        elif key == pygame.K_r:
            if self.path:
                self.car_progress = 0.0
                self.car_playing = False

        # Cambiar la velocidad de la animación:
        elif key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS): # + (En muchos teclados, '+' comparte tecla con '=')
            self.car_speed_cps = min(self.car_speed_cps + 1.0, 30.0)

        # Controles de la animación de A*:
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.car_speed_cps = max(self.car_speed_cps - 1.0, 1.0)
        elif key == pygame.K_a:
            self._toggle_search_animation()
        elif key == pygame.K_LEFTBRACKET:
            self.search_steps_per_sec = max(10.0, self.search_steps_per_sec - 30.0)
        elif key == pygame.K_RIGHTBRACKET:
            self.search_steps_per_sec = min(2000.0, self.search_steps_per_sec + 30.0)
        elif key == pygame.K_k:
            self._clear_search_viz()

    def _handle_left_click(self, mouse_pos: tuple[int, int]) -> None:
        x_px, y_px = mouse_pos
        x = x_px // CELL_SIZE # Para covertir los píxeles del ratón, en el tamaño de la celda (32 px)
        y = y_px // CELL_SIZE
        cell = (x, y)

        if not self.grid.in_bounds(cell): # Si hace click fuera del grid, no pasa nada
            return
        
        # Si se modifica mapa o start/goal, se invalida la ruta anterior y la comparación:
        self._invalidate_solution()
        self.last_status = "Changed map"

        # Me aseguro de que no se pueda colocar start/goal en un lugar erróneo:
        if self.place_mode == "start":
            ok = self.grid.set_start(cell)
            if not ok:
                print("[NOTICE] You cannot place START in a building/blocked area.")
            self.place_mode = None
            return

        if self.place_mode == "goal":
            ok = self.grid.set_goal(cell)
            if not ok:
                print("[NOTICE] You cannot place GOAL in a building/blocked area.")
            self.place_mode = None
            return

        # Modo normal (Pintar terreno):
        self.grid.set_terrain(cell, self.active_brush)

    # -----------------------
    # Update
    # -----------------------

    # Actualizar el movimiento cada segundo:
    def _update(self, dt: float) -> None:
        # Actualiza la animación del coche:
        if self.path and self.car_playing:
            # Avanza el progreso cada segundo:
            self.car_progress += self.car_speed_cps * dt

            # Si llega al final, se para en el último nodo:
            last_index = len(self.path) - 1
            if self.car_progress >= last_index:
                self.car_progress = float(last_index)
                self.car_playing = False

        # Actalizar la animación de A*:
        if self.search_playing and self.search_gen is not None and not self.search_done:
            self.search_accum += dt
            step_interval = 1.0 / self.search_steps_per_sec

            # Avanza tantos pasos como “quepan” en este frame:
            while self.search_accum >= step_interval:
                self.search_accum -= step_interval
                try:
                    step: AStarStep = next(self.search_gen)
                except StopIteration:
                    self.search_done = True
                    self.search_playing = False
                    self.last_status = "Animated A*: Finished"
                    break

                self.search_current = step.current
                self.search_open = step.open_set
                self.search_closed = step.closed_set

                if step.done:
                    self.search_done = True
                    self.search_playing = False

                    if step.result is None:
                        self.path = None
                        self.last_cost = None
                        self.last_expanded = None
                        self.last_status = "Animated A*: No route"
                    else:
                        self.path = step.result.path
                        self.last_cost = step.result.total_cost
                        self.last_expanded = step.result.expanded_nodes
                        self.last_status = "Animated A*: Route found"

                        # Reinicio la animación del coche con la nueva ruta:
                        self.car_progress = 0.0
                        self.car_playing = True
                    break

    # -----------------------
    # Render
    # -----------------------

    # Función principal que se ocupa de renderizar visualemente el algoritmo:
    def _render(self) -> None:
        brush_spec = TERRAIN_SPECS[self.active_brush]
        brush_weight = brush_spec.weight if brush_spec.walkable else "X"
        panel_x0 = self.grid_width  # El panel empieza justo donde acaba el grid

        # Fondo neutro:
        self.screen.fill((255, 255, 255))

        # Fondo del panel:
        panel_rect = pygame.Rect(panel_x0, 0, PANEL_WIDTH, self.window_height)
        pygame.draw.rect(self.screen, (250, 250, 250), panel_rect)

        # Línea separadora entre grid y panel:
        pygame.draw.line(self.screen, (180, 180, 180), (panel_x0, 0), (panel_x0, self.window_height), width=2)

        # Dibujo las celdas con sprites:
        for x, y, terrain in self.grid.iter_cells():
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            # Elijo sprite según terreno:
            sprite_key = None
            if terrain == TerrainType.ROAD_FREE:
                sprite_key = "road_free"
            elif terrain == TerrainType.ROAD_TRAFFIC:
                sprite_key = "road_traffic"
            elif terrain == TerrainType.ROAD_JAM:
                sprite_key = "road_jam"
            elif terrain == TerrainType.BUILDING:
                sprite_key = "building"

            if sprite_key and sprite_key in self.sprites:
                self.screen.blit(self.sprites[sprite_key], rect.topleft)
            else:
                spec = TERRAIN_SPECS[terrain]
                pygame.draw.rect(self.screen, spec.color_rgb, rect)

            pygame.draw.rect(self.screen, (220, 220, 220), rect, width=1)

        # Visualización de búsqueda (A* animado):
        if self.search_closed:
            for (x, y) in self.search_closed:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                inner = rect.inflate(-CELL_SIZE * 0.65, -CELL_SIZE * 0.65)
                pygame.draw.rect(self.screen, (190, 190, 190), inner)

        if self.search_open:
            for (x, y) in self.search_open:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                inner = rect.inflate(-CELL_SIZE * 0.65, -CELL_SIZE * 0.65)
                pygame.draw.rect(self.screen, (120, 200, 255), inner)

        if self.search_current is not None:
            x, y = self.search_current
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            inner = rect.inflate(-CELL_SIZE * 0.45, -CELL_SIZE * 0.45)
            pygame.draw.rect(self.screen, (255, 180, 80), inner)

        # Dibujar la ruta final:
        if self.path:
            for (x, y) in self.path:
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                inner = rect.inflate(-CELL_SIZE * 0.4, -CELL_SIZE * 0.4)
                pygame.draw.rect(self.screen, (255, 215, 0), inner)

        # Dibujar el coche animado:
        car_pos = None

        if self.path:
            i = int(self.car_progress)

            if i >= len(self.path) - 1:
                car_pos = self._cell_center_px(self.path[-1])
            else:
                a = self._cell_center_px(self.path[i])
                b = self._cell_center_px(self.path[i + 1])
                t = self.car_progress - i  # 0..1 entre dos celdas

                # Interpolación lineal:
                car_pos = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

        # Si no hay ruta pero sí start, dejo el coche en start:
        elif self.grid.start is not None:
            car_pos = self._cell_center_px(self.grid.start)

        if car_pos is not None:
            if "car" in self.sprites:
                # Centro el sprite en car_pos:
                car_rect = self.sprites["car"].get_rect(center=(int(car_pos[0]), int(car_pos[1])))
                self.screen.blit(self.sprites["car"], car_rect.topleft)
            else:
                pygame.draw.circle(self.screen, (30, 120, 220), (int(car_pos[0]), int(car_pos[1])), CELL_SIZE // 4)

        # Marcadores start por encima del terreno:
        if self.grid.start is not None:
            self._draw_marker(self.grid.start, (0, 180, 0), "S")

        # Sprite del goal:
        if self.grid.goal is not None:
            gx, gy = self.grid.goal
            rect = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            if "goal" in self.sprites:
                self.screen.blit(self.sprites["goal"], rect.topleft)
            else:
                self._draw_marker(self.grid.goal, (180, 0, 0), "G")

        # HUD (Mostrando controles y pincel activo):
        hud_lines = [
            f"Brush: {brush_spec.label} | weight: {brush_weight}",
            f"Mode: {self.place_mode or 'normal'}",
            "S: set START | G: set GOAL | ESC: normal",
            "Click/drag: paint | SPACE: A* path",
            "C: compare A* vs Dijkstra",
            "",
            f"Status: {self.last_status}",
            f"Car: {'PLAY' if self.car_playing else 'PAUSE'} | speed={self.car_speed_cps:.0f} cells/s  (P,R,+,-)",
            f"A*: animate [A]  speed [{self.search_steps_per_sec:.0f} steps/s]  [ / ]  K clear"
        ]

        # Si esta en resize mode:
        if self.resize_mode:
            hud_lines += [
                "",
                "== RESIZE MODE ==",
                "Type: cols,rows  (e.g. 40,25)",
                f"> {self.resize_text}",
                "ENTER apply | ESC cancel",
            ]
        else:
            hud_lines.append("N: resize grid  |  B: gen buildings  |  X: clear")

        # Si hay ruta principal (A*):
        if self.last_cost is not None and self.last_expanded is not None:
            hud_lines.append(f"Cost: {self.last_cost:.3f} | Expanded: {self.last_expanded}")

        # Si hay comparativa:
        if (
            self.astar_cost is not None
            and self.dijkstra_cost is not None
            and self.astar_ms is not None
            and self.dijkstra_ms is not None
        ):
            hud_lines += [
                "",
                "== Compare ==",
                f"A*:      cost={self.astar_cost:.3f}  exp={self.astar_expanded}  ms={self.astar_ms:.2f}",
                f"Dijkstra: cost={self.dijkstra_cost:.3f}  exp={self.dijkstra_expanded}  ms={self.dijkstra_ms:.2f}",
            ]

        # Configuro que la visualización del HUD sea correcta, sin que la líneas se "pisen":
        y_cursor = 10                                         # Empieza en 6 para dejar un pequeño margen arriba
        for line in hud_lines:
            surf = self.font.render(line, True, (20, 20, 20)) # Crea una imagen con el texto
            self.screen.blit(surf, (panel_x0 + 10, y_cursor)) # Se pega esa imagen en pantalla en esa posición
            y_cursor += 20                                    # Baja para la siguiente línea

        pygame.display.flip() # Como Pygame solo dibuja en un buffer, tengo que usar esta función para que el resultado se muestre

    # Dibujo los marcadores de start/goal:
    def _draw_marker(self, cell: tuple[int, int], color: tuple[int, int, int], letter: str) -> None:
        cx, cy = cell
        center_x = cx * CELL_SIZE + CELL_SIZE // 2
        center_y = cy * CELL_SIZE + CELL_SIZE // 2

        # Círculo sólido para que destaque sobre cualquier terreno:
        pygame.draw.circle(self.screen, color, (center_x, center_y), CELL_SIZE // 3)

        # Letra encima (S/G):
        text = self.font.render(letter, True, (255, 255, 255))
        text_rect = text.get_rect(center=(center_x, center_y))
        self.screen.blit(text, text_rect)