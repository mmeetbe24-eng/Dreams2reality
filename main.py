# main.py - 1-Click Entry Point for Dreams2Reality
import os
import sys
from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
BCI_SERVICE_DIR = BASE_DIR / "bci-service"
sys.path.insert(0, str(BCI_SERVICE_DIR))

from api.server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 65)
    print(" 🧠 Starting Dreams2Reality BCI Neurological Platform")
    print(f" 🌐 Open Web UI at: http://localhost:{port}")
    print(f" 📡 WebSocket Telemetry: ws://localhost:{port}/ws/telemetry")
    print(f" 🏥 PhysioNet Dataset Benchmark: Loaded & Ready")
    print("=" * 65)
    uvicorn.run(app, host=host, port=port)
