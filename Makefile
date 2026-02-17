.PHONY: dev lint test clean

dev:
	MEMBRIDGE_DEV=1 MEMBRIDGE_AGENT_DRYRUN=1 python -m uvicorn run:app --host 0.0.0.0 --port 5000 --reload

server:
	python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

agent:
	python -m uvicorn agent.main:app --host 0.0.0.0 --port 8001

lint:
	python -m ruff check server/ agent/ run.py sqlite_minio_sync.py tests/

test:
	MEMBRIDGE_DEV=1 MEMBRIDGE_AGENT_DRYRUN=1 python -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf server/data/jobs.db 2>/dev/null || true
