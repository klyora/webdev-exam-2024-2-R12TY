from pathlib import Path
from elib import create_app
from config import COVERS_DIR

Path(COVERS_DIR).mkdir(parents=True, exist_ok=True)

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
