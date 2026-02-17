# Multi-Agent Patterns: Claude ↔ ChatGPT ↔ Lovable

## Description
Coordination patterns for PCMS multi-agent workflow with clean handoffs and zero context loss.

## PCMS Agent Roles

### Claude (Verification Agent)
**Responsibilities:**
- Code review and verification
- ADR compliance checking
- Test execution and validation
- Context degradation monitoring
- Session management

**Outputs:**
- Verification reports
- Context health metrics
- Handoff artifacts (goal.md)

### ChatGPT (Architecture Agent)
**Responsibilities:**
- ADR drafting and research
- Architecture decisions
- Phase planning
- Technical feasibility analysis

**Outputs:**
- Draft ADRs
- Architecture constraints
- Phase roadmaps

### Lovable (Implementation Agent)
**Responsibilities:**
- Code generation
- UI/UX implementation
- Component creation
- Build/test execution

**Outputs:**
- Implementation code
- Build results
- Test outputs

## Coordination Patterns

### Orchestrator Pattern (CURRENT)
```
User (Orchestrator)
  ├─> Claude (verification, review)
  ├─> ChatGPT (architecture, ADRs)
  └─> Lovable (implementation)

Communication: Through user
Handoffs: Manual via user
State: Shared through context/ directory
```

### Peer-to-Peer Pattern (FUTURE - Phase 2+)
```
Claude <─> ChatGPT <─> Lovable
  ↑          ↑          ↑
  └──────────┴──────────┘
       (shared context)

Communication: Direct via MCP
Handoffs: Automated
State: Real-time sync
```

## Handoff Protocol

### Claude → ChatGPT
```
Trigger: Architecture decision needed
Artifact: context/agents/chatgpt/goal.md

Contents:
- Current state (Phase status, ADR constraints)
- Open question (What needs architecture decision?)
- Context (Why this question arose)
- Constraints (Hard limits: offline-first, privacy-first)
- Success criteria (What makes a good ADR?)

Verification:
[ ] goal.md created
[ ] summary.md updated
[ ] timeline.md logged
[ ] No context loss (ChatGPT has full context)
```

### ChatGPT → Claude
```
Trigger: ADR draft complete
Artifact: context/decisions/adr/ADR-XXX.md (Draft)

Contents:
- Draft ADR (full text)
- Research findings (alternatives considered)
- Constraints (technical limits)
- Recommendations (next steps)

Verification:
[ ] ADR follows template
[ ] Research complete
[ ] Claude reviews before accepting
[ ] timeline.md logged
```

### Claude → Lovable
```
Trigger: Implementation work ready
Artifact: Lovable prompt + ADR constraints

Contents:
- Implementation spec (what to build)
- ADR constraints (must-follow rules)
- Verification requirements (what tests must pass)
- Technical constraints (offline-first, privacy-first)

Verification:
[ ] ADR constraints explicit
[ ] Verification criteria clear
[ ] No ambiguity in spec
```

### Lovable → Claude
```
Trigger: Implementation complete
Artifact: Git commit + test results

Contents:
- Code changes (what was built)
- Test results (what passed/failed)
- Known issues (Lovable's warnings)

Verification:
[ ] Code pushed to git
[ ] Tests executed
[ ] Claude reviews before merge
[ ] timeline.md logged
```

## State Synchronization

### Shared State (Read-Only for All Agents)
```
- context/meta/summary.md (authoritative current state)
- Accepted ADRs (004, 005, 006, 007)
- Phase status (0.1 complete, 1 pending)
```

### Agent-Owned State (Write Access)
```
Claude:
- .claude/sessions/*.md (session logs)
- Verification results

ChatGPT:
- context/decisions/adr/*.md (Draft ADRs)
- Research findings

Lovable:
- Implementation code (src/*)
- Build/test results
```

### Conflict Resolution
```
If state conflicts:
1. Halt all agents
2. Identify conflict source
3. Apply priority rules (summary.md > ADRs > agent state)
4. Resolve manually through user
5. Update conflict agent's state
6. Resume work
```

## Anti-Patterns (FORBIDDEN)

### ❌ Silent Handoffs
```
Bad: Agent passes work without logging
Good: Explicit handoff artifact + timeline.md log
```

### ❌ Context Loss
```
Bad: "Implement audit logging" (no constraints)
Good: "Implement audit logging per ADR-004: hash chain, SHA-256, deterministic serialization, redaction rules"
```

### ❌ State Drift
```
Bad: Agents maintain separate "truth" about project state
Good: Single source of truth (summary.md)
```

### ❌ Assumption Propagation
```
Bad: Agent assumes another agent knows X
Good: Explicit in handoff artifact: "You need to know X because Y"
```

## Related Skills
- context-fundamentals (handoff context design)
- memory-systems (shared state management)
- context-degradation (handoff as degradation prevention)
