#!/bin/sh
set -a
. /home/vokov/membridge/.env.agent
set +a
exec /home/vokov/membridge/.venv/bin/python -m uvicorn agent.main:app --host 0.0.0.0 --port 8001
