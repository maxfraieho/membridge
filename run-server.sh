#!/bin/sh
set -a
. /home/vokov/membridge/.env.server
set +a
exec /home/vokov/membridge/.venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
