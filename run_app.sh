#!/usr/bin/env bash
echo "========================================================"
echo "   Dreams2Reality: Two-Electrode BCI Neural Cockpit"
echo "========================================================"
cd "$(dirname "$0")"
python3 -m uvicorn api.server:app --app-dir bci-service --host 0.0.0.0 --port 8000 --reload
