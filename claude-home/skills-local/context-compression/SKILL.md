# Context Compression: PCMS Long-Running Sessions

## Description
Compression strategies for ADR-driven development with multi-day sessions and extensive verification trails.

## When to Use
- Token usage > 70% (140K/200K tokens)
- Session duration > 2 days (artifact trail accumulation)
- Before multi-agent handoffs (Claude → ChatGPT → Lovable)
- After major phase completion (Phase 0 → 0.1 → 1 transitions)

## Compression Approaches for PCMS

### 1. Anchored Iterative Summarization (RECOMMENDED)
**Why:** Prevents silent information loss in ADR-driven workflow
**How:** Incremental merge with explicit checklists

```
Structure:
┌─ Session Intent
│  └─ Current phase, ADR constraints, verification goals
├─ Files Modified
│  └─ src/lib/audit.ts (+319 lines, hash chain implementation)
│  └─ src/lib/db.ts (+465 lines, audit hooks in CRUD)
├─ Decisions Made
│  └─ ADR-005 accepted (verification & export)
│  └─ Deterministic stringify chosen over JSON.stringify
├─ Current State
│  └─ Phase 0.1 complete, verification passing
│  └─ ADR-008 (Phase 1) pending ChatGPT draft
└─ Next Steps
   └─ Handoff to ChatGPT for ADR-008 architecture
```

**PCMS Template:**
```markdown
## Session Intent
- Phase: [0 / 0.1 / 1]
- Goal: [Primary objective]
- ADR Constraints: [Accepted ADRs applying to this work]
- Verification Requirements: [Must-pass criteria]

## Files Modified
- [path]: [change description, line count, verification status]

## Decisions Made
- [ADR-XXX]: [Status change, key decision, rationale]
- [Technical choice]: [What, why, verification outcome]

## ADR Compliance
- ✓ ADR-004: [How compliance verified]
- ✓ ADR-005: [Verification results]
- ✓ ADR-006: [Testing outcomes]

## Current State
- Implementation: [What's built, what's tested]
- Verification: [Pass/fail status, blockers]
- Context Health: [Token usage, session duration]

## Next Steps
1. [Immediate action]
2. [Pending decision]
3. [Handoff requirements if applicable]
```

**Incremental Merge Process:**
```
New Compression = Previous Summary + New Activity
1. Load previous summary
2. Append new file changes to Files Modified
3. Add new decisions to Decisions Made
4. Update Current State (replace, not append)
5. Refresh Next Steps (replace, not append)
6. Verify: No ADR constraint loss
```

### 2. Opaque Compression (NOT RECOMMENDED)
**Why NOT:** 99% compression but unverifiable
**Risk:** ADR constraints silently lost
**PCMS Position:** Unacceptable for verification-first workflow

### 3. Regenerative Full Summary (FALLBACK)
**Why:** Readable, detailed, but lossy across cycles
**Use Case:** Emergency compression when anchored fails
**Risk:** Details lost in repeated regenerations
**Mitigation:** Verify ADR constraints preserved after each cycle

## Compression Triggers for PCMS

### Fixed Threshold (PRIMARY)
```
Trigger: 70% context utilization (140K/200K tokens)
Action:
1. Create anchored summary
2. Archive detailed logs to timeline.md
3. Replace full ADR text with references
4. Verify: ADR constraints still accessible
```

### Task Boundary (SECONDARY)
```
Trigger: Phase completion (0 → 0.1 → 1)
Action:
1. Full session summary to timeline.md
2. Create handoff artifact for next agent
3. Reset context window
4. Load only next-phase ADRs
```

### Sliding Window (TERTIARY)
```
Trigger: Multi-agent handoff
Maintain:
- Last 10 actions (implementation details)
- Full summary (session state)
- ADR constraints (always loaded)
Discard:
- Historical verification logs
- Superseded decisions
```

### Importance-Based (EXPERIMENTAL)
```
High Priority (NEVER compress):
- Accepted ADR constraints
- Current phase status
- Verification requirements
- Open blockers

Medium Priority (Compress to references):
- Full ADR text (keep summaries)
- Completed verification logs
- Superseded decisions

Low Priority (Archive to files):
- Historical session logs
- Rejected approaches
- General research notes
```

## Critical Metric: Tokens-Per-Task

**NOT:** Tokens-per-compression (misleading optimization)
**YES:** Tokens-per-task (task start → completion)

```
Bad Compression:
- Saves 0.5% tokens
- But causes 20% more re-fetching
- Net: WORSE efficiency

Good Compression:
- Saves 40% tokens
- Zero re-fetching (ADR constraints preserved)
- Net: BETTER efficiency
```

## Artifact Trail Problem (PCMS-Specific)

**Challenge:** File tracking weakest compression dimension (2.2/5.0 score)
**Impact:** Agent forgets which files modified, breaking verification

**PCMS Solution:**
```
Dedicated File State Tracking:
┌─ .claude/sessions/file-state.json
│  {
│    "session": "2026-01-01-2138-case-chronicle-setup",
│    "files": {
│      "src/lib/audit.ts": {
│        "status": "modified",
│        "lines": "+319, -0",
│        "purpose": "Berkeley Protocol audit logging",
│        "verification": "hash-determinism-test PASSED",
│        "adr": "ADR-004, ADR-005"
│      },
│      "src/lib/db.ts": {
│        "status": "modified",
│        "lines": "+465, -0",
│        "purpose": "Audit hooks in CRUD operations",
│        "verification": "cascade-delete-test PASSED",
│        "adr": "ADR-004"
│      }
│    }
│  }
```

**Benefits:**
- Survives compression cycles
- Queryable (which files touch ADR-004?)
- Verification-linked (what passed/failed?)
- Handoff-ready (next agent sees full file history)

## Compression Checklist (MANDATORY)

**Before Compression:**
```
[ ] Token usage > 140K/200K (compression justified?)
[ ] Create anchored summary with full template
[ ] Export file state to .claude/sessions/file-state.json
[ ] Verify: All Accepted ADRs referenced
[ ] Verify: Current phase status accurate
[ ] Verify: Verification requirements preserved
```

**During Compression:**
```
[ ] Archive detailed logs to timeline.md
[ ] Replace full ADR text with summaries + references
[ ] Preserve last 10 actions (implementation context)
[ ] Maintain file modification list (artifact trail)
```

**After Compression:**
```
[ ] Verify: Can state all Accepted ADRs from memory
[ ] Verify: Can explain current phase status
[ ] Verify: Can list modified files + verification status
[ ] Verify: No re-fetching needed for immediate work
[ ] Document compression in timeline.md
```

## Compression Anti-Patterns (FORBIDDEN)

### ❌ Silent Information Loss
```
Bad: Compress without verifying ADR preservation
Good: Explicit checklist, verify after compression
```

### ❌ Premature Compression
```
Bad: Compress at 50% context (unnecessary)
Good: Wait until 70% threshold
```

### ❌ Lossy Re-Regeneration
```
Bad: Regenerate summary from scratch each cycle
Good: Incremental merge (anchored approach)
```

### ❌ Artifact Trail Neglect
```
Bad: Compress file modifications into vague "changes made"
Good: Preserve file-state.json with verification links
```

## Recovery from Bad Compression

**Detection:**
```
Agent shows:
- Uncertain which files modified
- Forgot ADR constraints
- Can't explain previous decisions
- Repeating already-completed work
```

**Recovery:**
```
1. STOP compression cycles
2. Restore from timeline.md (last known good state)
3. Re-derive from file-state.json (file modifications)
4. Re-load ADR constraints explicitly
5. Verify: Context health restored
6. Document failure in timeline.md
```

## Multi-Agent Compression Strategy

### Claude → ChatGPT Handoff
```
Compress:
- Claude's implementation logs (detailed)
- Verification test outputs (verbose)

Preserve:
- Anchored summary (session state)
- File state (modifications + verification)
- ADR constraints (always full text for new agent)
- Open questions (ChatGPT needs context)
```

### ChatGPT → Lovable Handoff
```
Compress:
- ADR research process (ChatGPT's reasoning)
- Rejected architecture alternatives

Preserve:
- Final ADR text (Lovable implementation guide)
- Technical constraints (offline-first, privacy-first)
- Verification requirements (what tests must pass)
```

### Lovable → Claude Review
```
Compress:
- Lovable's iteration history (implementation details)

Preserve:
- Final code changes (what to review)
- Lovable's test results (verification starting point)
- Known issues (Lovable's warnings)
```

## Related Skills
- context-fundamentals (loading patterns, pre-compression design)
- context-degradation (compression as degradation prevention)
- memory-systems (external state for artifact trail)
- multi-agent-patterns (handoff-specific compression)

## Metrics

### Compression Efficiency
```
Good Compression:
✓ Token reduction: 40%+
✓ Re-fetching: 0%
✓ ADR constraints: 100% preserved
✓ File state: Complete artifact trail
✓ Verification: No false negatives post-compression

Bad Compression:
✗ Token reduction: 10% (not worth it)
✗ Re-fetching: 20%+ (defeats purpose)
✗ ADR constraints: Partial loss
✗ File state: Vague "changes made"
✗ Verification: Failures after compression
```

### Context Health Post-Compression
```
[ ] Agent can list all Accepted ADRs
[ ] Agent can state current phase accurately
[ ] Agent can explain last 3 major decisions
[ ] Agent can enumerate modified files + verification status
[ ] Agent knows next steps without re-reading full history
```
