# Update claude-mem on Orange Pi to fix project identity

## Context

The RPi (source of truth) has pushed commit `3d44f0b` to `main` with these fixes:

1. **`sqlite_minio_sync.py`** — `resolve_canonical_id()` now supports explicit `CLAUDE_CANONICAL_PROJECT_ID` env var override, preventing memory orphaning on project rename. Worker startup fixed to use bun + marketplaces/ path.
2. **`config.env`** — project renamed from `mem` to `garden-seedling` with pinned canonical ID.

You are running on the Orange Pi (hostname: `debian` or similar). The membridge repo lives at the same relative path as on RPi.

---

## Steps

### Step 1 — Find the membridge directory

```bash
MEMBRIDGE_DIR="${MEMBRIDGE_DIR:-$HOME/projects/mem}"
ls "$MEMBRIDGE_DIR/sqlite_minio_sync.py" || echo "NOT FOUND — locate it manually"
```

### Step 2 — Pull latest code

```bash
cd "$MEMBRIDGE_DIR"
git pull origin main
```

Verify commit `3d44f0b` is present:

```bash
git log --oneline -3
```

### Step 3 — Update config.env

Edit `$MEMBRIDGE_DIR/config.env`. Ensure these lines exist:

```
CLAUDE_PROJECT_ID=garden-seedling
CLAUDE_CANONICAL_PROJECT_ID=6fe2e0f6071ac2bb
```

If `CLAUDE_PROJECT_ID` was `mem` or commented out — fix it.
**Do NOT remove or change `CLAUDE_CANONICAL_PROJECT_ID=6fe2e0f6071ac2bb`.**

Also update `~/.claude-mem-minio/config.env` if it exists as a separate copy (not a symlink):

```bash
diff "$MEMBRIDGE_DIR/config.env" ~/.claude-mem-minio/config.env
```

If they differ, copy the project identity lines over.

### Step 4 — Copy enforcement script

```bash
mkdir -p ~/.claude-mem-minio/bin
cat > ~/.claude-mem-minio/bin/enforce-project.sh << 'SCRIPT'
#!/bin/bash
EXPECTED_NAME="garden-seedling"
EXPECTED_CID="6fe2e0f6071ac2bb"
CONFIG="${1:-$HOME/.claude-mem-minio/config.env}"

changed=0

if grep -q "CLAUDE_PROJECT_ID=" "$CONFIG"; then
    CURRENT=$(grep "^CLAUDE_PROJECT_ID=" "$CONFIG" | cut -d= -f2)
    if [ "$CURRENT" != "$EXPECTED_NAME" ]; then
        sed -i "s/^CLAUDE_PROJECT_ID=.*/CLAUDE_PROJECT_ID=$EXPECTED_NAME/" "$CONFIG"
        echo "Fixed project name: $CURRENT -> $EXPECTED_NAME"
        changed=1
    fi
fi

if grep -q "CLAUDE_CANONICAL_PROJECT_ID=" "$CONFIG"; then
    CURRENT_CID=$(grep "^CLAUDE_CANONICAL_PROJECT_ID=" "$CONFIG" | cut -d= -f2)
    if [ "$CURRENT_CID" != "$EXPECTED_CID" ]; then
        sed -i "s/^CLAUDE_CANONICAL_PROJECT_ID=.*/CLAUDE_CANONICAL_PROJECT_ID=$EXPECTED_CID/" "$CONFIG"
        echo "Fixed canonical ID: $CURRENT_CID -> $EXPECTED_CID"
        changed=1
    fi
fi

[ "$changed" -eq 0 ] && echo "OK — identity correct"
SCRIPT
chmod +x ~/.claude-mem-minio/bin/enforce-project.sh
~/.claude-mem-minio/bin/enforce-project.sh
```

### Step 5 — Verify

```bash
set -a && source "$MEMBRIDGE_DIR/config.env" && set +a
source "$MEMBRIDGE_DIR/venv/bin/activate"
export PATH="$HOME/npm-global/bin:$PATH"
python "$MEMBRIDGE_DIR/sqlite_minio_sync.py" print_project
```

Expected:

```
project_name: garden-seedling
canonical_project_id: 6fe2e0f6071ac2bb
```

### Step 6 — Run doctor

```bash
python "$MEMBRIDGE_DIR/sqlite_minio_sync.py" doctor
```

Expected: `STATUS: OK` or `DEGRADED` only due to worker (not identity/MinIO issues).

### Step 7 — Test sync

```bash
python "$MEMBRIDGE_DIR/sqlite_minio_sync.py" pull_sqlite
```

Expected: `already up to date` (same prefix `projects/6fe2e0f6071ac2bb/sqlite/`).

---

## Critical constraint

`canonical_project_id` MUST remain `6fe2e0f6071ac2bb`. If it changes, all existing memory is orphaned.

## Success criteria

- `project_name: garden-seedling`
- `canonical_project_id: 6fe2e0f6071ac2bb`
- MinIO sync works (same prefix as RPi)
- Doctor shows no identity errors
