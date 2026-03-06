from pathlib import Path
import sys
# Me aseguro de que /src esté en el path de forma consistente:
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from ui.pygame_app import PygameApp

def main() -> None:
    app = PygameApp()
    app.run()

if __name__ == "__main__":
    main()