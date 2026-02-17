# Memory Systems: PCMS Multi-Agent State Management

## Description
External state management for multi-agent workflow (Claude ↔ ChatGPT ↔ Lovable).

## When to Use
- Multi-agent handoffs requiring state persistence
- Session > 3 days (exceeds single context window)
- Phase transitions (0 → 0.1 → 1)
- Verification state tracking across agents

## PCMS Memory Architecture

### Short-Term Memory (Context Window)
```
Scope: Current session only
Storage: Active context (200K tokens max)
Lifespan: Until compression or handoff
Contents:
- Current task state
- Last 10 actions
- Active ADR constraints
- Immediate verification requirements
```

### Long-Term Memory (Filesystem)
```
Scope: Entire project lifespan
Storage: context/ directory structure
Lifespan: Permanent
Contents:
- context/meta/summary.md (authoritative state)
- context/meta/timeline.md (full session history)
- context/decisions/adr/*.md (ADR archive)
- .claude/sessions/*.md (session logs)
```

### Working Memory (Append-Only Logs)
```
Scope: Current phase
Storage: JSONL files
Lifespan: Until phase completion
Format:
{"timestamp": "2026-01-04T01:05Z", "type": "adr_accepted", "adr": "ADR-005", "agent": "claude"}
{"timestamp": "2026-01-04T01:15Z", "type": "verification", "test": "hash-chain", "status": "PASSED"}
{"timestamp": "2026-01-04T01:30Z", "type": "handoff", "from": "claude", "to": "chatgpt", "artifact": "context/agents/chatgpt/goal.md"}
```

### Graph Memory (ADR Relationships)
```
Scope: Project architecture
Storage: context/decisions/decisions-log.md
Lifespan: Permanent
Structure:
ADR-004 (Accepted)
  ├─ supersedes: None
  ├─ superseded_by: None
  └─ blocks: ADR-005 (dependency)

ADR-005 (Accepted)
  ├─ depends_on: ADR-004
  ├─ extends: ADR-004 (verification layer)
  └─ blocks: ADR-008 (Phase 1 needs 0.1 complete)
```

## Memory Operations

### Write (State Persistence)
```
context/meta/timeline.md:
  Append session updates (never overwrite)

.claude/sessions/file-state.json:
  Update file modifications (merge, not replace)

context/decisions/adr/ADR-XXX.md:
  Write once (immutable after Accepted)
```

### Read (State Retrieval)
```
On Session Start:
  Load: context/meta/summary.md (current state)
  Load: context/meta/handoff-protocol.md (multi-agent rules)

On ADR Reference:
  Load: Specific ADR from context/decisions/adr/

On Handoff:
  Load: context/agents/{agent}/goal.md
```

### Query (State Inspection)
```
"Which ADRs apply to Phase 0.1?"
  → Query: context/meta/summary.md (Phase Status → Completed)
  → Result: ADR-004, 005, 006

"What files were modified in current session?"
  → Query: .claude/sessions/file-state.json
  → Result: audit.ts (+319), db.ts (+465)

"Has ADR-008 been accepted?"
  → Query: context/decisions/decisions-log.md
  → Result: No (Status: Draft)
```

### Compress (Memory Consolidation)
```
Trigger: Token usage > 140K
Action:
  1. Append detailed logs to timeline.md
  2. Update summary.md (current state)
  3. Archive file-state.json (snapshot)
  4. Clear context window (keep summary only)
```

## Multi-Agent Memory Sharing

### Claude Memory
```
Owns:
- Verification state (what tests passed/failed)
- Implementation history (what code changed)
- Context health (compression triggers, degradation warnings)

Shares with ChatGPT:
- context/agents/chatgpt/goal.md (handoff artifact)
- context/meta/summary.md (current state)
- Open questions (what needs architecture decision)

Shares with Lovable:
- ADR constraints (implementation requirements)
- Verification requirements (what tests must pass)
```

### ChatGPT Memory
```
Owns:
- ADR drafts (architecture research)
- Design decisions (rationale, alternatives considered)
- Phase planning (roadmap, dependencies)

Shares with Claude:
- Accepted ADRs (implementation guidance)
- Architecture constraints (hard limits)
- Research findings (context for verification)

Shares with Lovable:
- Implementation specs (what to build)
- Technical constraints (offline-first, privacy-first)
```

### Lovable Memory
```
Owns:
- Implementation iterations (code generation history)
- UI/UX decisions (component choices)
- Build/test results (what passed/failed)

Shares with Claude:
- Final code changes (what to review)
- Known issues (Lovable's warnings)
- Test results (verification starting point)
```

## Memory Integrity

### Verification
```
On Write:
  [ ] Schema validation (timeline.md format correct?)
  [ ] No ADR mutation (Accepted ADRs immutable)
  [ ] Append-only compliance (no silent deletions)

On Read:
  [ ] Source priority (summary.md > drafts > logs)
  [ ] Timestamp verification (no future dates)
  [ ] ADR status check (Accepted vs Draft vs Superseded)
```

### Conflict Resolution
```
Priority (highest to lowest):
1. context/meta/summary.md (authoritative state)
2. Accepted ADRs (004, 005, 006, 007)
3. timeline.md (historical record)
4. Session logs (implementation details)
5. Draft ADRs (informational only)
```

## Related Skills
- context-fundamentals (memory loading patterns)
- context-compression (memory consolidation)
- context-degradation (memory corruption recovery)
- multi-agent-patterns (memory sharing protocols)
