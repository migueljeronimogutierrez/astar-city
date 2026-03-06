# Tamaño de cada celda (En píxeles):
CELL_SIZE = 32

# Panel lateral para el HUD:
PANEL_COLS = 12
PANEL_WIDTH = PANEL_COLS * CELL_SIZE # El ancho como múltiplo de CELL_SIZE para mantener la coherencia visual

# Defaults (Solo para el arranque):
DEFAULT_GRID_COLS = 30
DEFAULT_GRID_ROWS = 20

# Límites razonables para evitar ventanas absurdas:
MIN_GRID_COLS = 10
MAX_GRID_COLS = 80
MIN_GRID_ROWS = 10
MAX_GRID_ROWS = 60

# FPS objetivo:
FPS = 60