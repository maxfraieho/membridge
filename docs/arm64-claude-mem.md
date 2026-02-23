# ARM64 claude-mem: Known Issues & Fixes

Reference for deploying `claude-mem` on ARM64 Linux (Orange Pi, Raspberry Pi,
Ampere, etc.).  All issues here are non-fatal from the membridge-agent
perspective — agent heartbeats and project sync continue to work — but they
produce noisy errors in Claude Code CLI Stop hooks.

> **Quick check:** run `scripts/verify_claude_mem.sh` to detect all three
> issues automatically.

---

## Symptom A: "bun-runner.js not found" at Stop hook

### What you see

```
error: non-blocking stop hook failed
  command: node "…/scripts/bun-runner.js" "…/worker-service.cjs" start
  error: No such file or directory
```

### Root cause

`~/.claude/plugins/installed_plugins.json` contains a stale `installPath` or
`version` that no longer matches what is actually present in the plugin cache.

Example of a broken state:

```json
// installed_plugins.json says:
"installPath": "~/.claude/plugins/cache/thedotmack/claude-mem/9.0.5"

// But on disk only this exists:
~/.claude/plugins/cache/thedotmack/claude-mem/10.0.7/
```

Claude Code expands `${CLAUDE_PLUGIN_ROOT}` from `installPath`, so the hook
command resolves to a non-existent path.

### How to verify

```bash
# 1. What does the registry say?
grep -A4 '"version"' ~/.claude/plugins/installed_plugins.json

# 2. What is actually on disk?
ls ~/.claude/plugins/cache/thedotmack/claude-mem/

# 3. Does bun-runner.js exist at the path from the registry?
INSTALL_PATH=$(python3 -c "
import json, os
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
entries = d['plugins'].get('claude-mem@thedotmack', [])
if entries: print(entries[0]['installPath'])
" 2>/dev/null)
ls "${INSTALL_PATH}/scripts/bun-runner.js" 2>/dev/null || echo "NOT FOUND at $INSTALL_PATH"
```

### How to fix

**Option 1 — Reinstall via CLI (recommended)**

```
/plugin install claude-mem
```

This updates `installed_plugins.json` to match the downloaded cache.

**Option 2 — Manual correction (no internet required)**

```bash
# Back up first
cp ~/.claude/plugins/installed_plugins.json \
   ~/.claude/plugins/installed_plugins.json.bak.$(date +%Y%m%d-%H%M%S)

# Find the real version on disk
REAL_VER=$(ls ~/.claude/plugins/cache/thedotmack/claude-mem/ | sort -V | tail -1)
REAL_PATH="$HOME/.claude/plugins/cache/thedotmack/claude-mem/$REAL_VER"

# Edit installed_plugins.json: set installPath → $REAL_PATH and version → $REAL_VER
# (use your preferred editor — jq in-place, sed, or a text editor)
```

After either fix, restart Claude Code CLI and the Stop hook errors will stop.

---

## Symptom B: bun crashes with "Illegal instruction" or "Exec format error"

### What you see

```
/home/user/.bun/bin/bun: Exec format error
# or
bun: Illegal instruction
# or (from bun-runner.js logs)
Failed to start: Process died during startup
```

### Root cause

`~/.bun/bin/bun` is the wrong binary for the current CPU:

| Scenario | What happened |
|---|---|
| Installed `bun` npm package on Windows, then rsynced home dir to ARM64 | `~/.bun/bin/bun` → `…/bun.exe` (Windows PE) |
| Installed bun on x86_64, then migrated to ARM64 host | `~/.bun/bin/bun` is an ELF x86_64 binary |
| Installed bun via npm on Linux | npm only ships the native CLI shim; actual bun runtime is absent |

### How to verify

```bash
# Check what the binary actually is
ls -la ~/.bun/bin/bun            # symlink target?
readelf -h ~/.bun/bin/bun 2>/dev/null | grep -E 'Class|Machine'
# ARM64 correct output:  Machine: AArch64
# x86_64 output:         Machine: Advanced Micro Devices X86-64
# Windows PE: readelf will report "not an ELF file"

# Quick smoke test
~/.bun/bin/bun --version 2>&1   # "1.x.y" is good, error is bad
~/.bun/bin/bun --print "process.arch" 2>&1  # should print "arm64"
```

### How to fix

**Option 1 — Official installer (recommended)**

Requires `unzip` (`apt install unzip` / `apk add unzip`):

```bash
curl -fsSL https://bun.sh/install | bash
```

**Option 2 — Download binary directly (no unzip needed)**

```bash
# Uses Python's built-in zipfile module — no extra tools required
python3 - <<'EOF'
import urllib.request, zipfile, io, os, stat

url = "https://github.com/oven-sh/bun/releases/latest/download/bun-linux-aarch64.zip"
print(f"Downloading {url} ...")
with urllib.request.urlopen(url, timeout=60) as resp:
    data = resp.read()

z = zipfile.ZipFile(io.BytesIO(data))
bun_entry = next(n for n in z.namelist() if n.endswith("/bun") or n == "bun")
dest = os.path.expanduser("~/.bun/bin/bun")
os.makedirs(os.path.dirname(dest), exist_ok=True)
with open(dest, "wb") as f:
    f.write(z.read(bun_entry))
os.chmod(dest, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
print(f"Installed to {dest}")
EOF

~/.bun/bin/bun --version  # verify
```

> **Note for x86_64 ARM emulation users:** replace `bun-linux-aarch64.zip`
> with `bun-linux-x64.zip` if running under QEMU x86_64 emulation.

---

## Quick verification checklist

Run these five commands to confirm a healthy setup:

```bash
# 1. Plugin metadata points to a real directory
python3 -c "
import json, os, sys
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
p = d['plugins'].get('claude-mem@thedotmack', [{}])[0].get('installPath', '')
ok = os.path.isdir(p)
print(('OK' if ok else 'FAIL'), 'installPath:', p)
sys.exit(0 if ok else 1)
"

# 2. bun-runner.js exists at that path
PLUGIN_ROOT=$(python3 -c "
import json, os
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
print(d['plugins'].get('claude-mem@thedotmack', [{}])[0].get('installPath', ''))
" 2>/dev/null)
ls "${PLUGIN_ROOT}/scripts/bun-runner.js" && echo "OK bun-runner.js" || echo "FAIL bun-runner.js missing"

# 3. bun binary is present
BUN=$(command -v bun || echo "$HOME/.bun/bin/bun")
test -x "$BUN" && echo "OK bun found: $BUN" || echo "FAIL bun not found"

# 4. bun is the right architecture
"$BUN" --print "process.arch + ' ' + process.platform" 2>&1

# 5. Worker starts cleanly
node "${PLUGIN_ROOT}/scripts/bun-runner.js" "${PLUGIN_ROOT}/scripts/worker-service.cjs" start 2>&1
```

All five should succeed with no errors. Or just run:

```bash
bash scripts/verify_claude_mem.sh
```

---

## Safety notes

- **Never commit `~/.claude/` contents** — they contain plugin keys and session data.
- **`verify_claude_mem.sh` is read-only** — it only reads and reports, never
  modifies `~/.claude/` or `~/.bun/`.
- Fix scripts above do write to `~/.bun/bin/bun` and
  `~/.claude/plugins/installed_plugins.json` — always back up first.
- Do not include bun binary paths or plugin keys in bug reports or log pastes.
