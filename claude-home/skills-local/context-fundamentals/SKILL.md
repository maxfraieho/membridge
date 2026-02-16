# Context Engineering Fundamentals

## Description
Foundational context engineering for AI agent systems in ADR-driven, verification-first development.

## When to Use
- Managing long-running PCMS development sessions
- Investigating context degradation in multi-agent workflows
- Optimizing token usage for extended ADR documentation
- Evaluating context-related architectural decisions

## Prerequisites
Understanding of:
- Language model attention mechanisms
- Agent system architecture basics
- PCMS project constraints (offline-first, privacy-first)

## Core Principles for PCMS

### 1. Context as Finite Resource
- Attention budget depletes with context length
- Tool outputs consume 83.9% of context in typical agent systems
- PCMS constraint: Must maintain ADR trail + session history

### 2. Quality Over Quantity
- Curate smallest high-signal token set
- ADR-first: Load only relevant ADRs for current work
- Progressive disclosure: Reference → Full content only when needed

### 3. Attention-Aware Placement
- Critical info at beginning/end (attention-favored positions)
- PCMS pattern: ADR constraints at start, verification at end
- Middle section: Implementation details, research notes

## Main Components

### System Prompts
- Core identity: PCMS privacy-first, verification-first agent
- Behavioral guidelines: ADR-first, no autonomous refactoring
- Balances specificity (Berkeley Protocol compliance) with flexibility

### Tool Definitions
- Quality descriptions reduce agent guessing
- PCMS tools: ADR lookup, verification, context snapshot

### Retrieved Documents
- ADR documents (004, 005, 006, 007)
- Phase roadmap
- Session history
- Load dynamically via filesystem operations

### Message History
- Conversation tracking across Claude ↔ ChatGPT ↔ Lovable
- Task state management (Phase 0 → 0.1 → 1)
- Handoff protocol compliance

### Tool Outputs
- Verification results (hash chain validation, export tests)
- Build/test outputs
- Git operations logs

## Implementation Patterns

### Pre-load Critical Context
```
- ADR constraints (loaded at session start)
- Phase status (context/meta/summary.md)
- Handoff protocol (context/meta/handoff-protocol.md)
```

### Defer Non-Critical Context
```
- Full ADR text (load on reference)
- Historical session logs (load on request)
- Detailed architecture docs (load when modifying)
```

### Compaction Triggers
- Monitor at 70-80% context utilization (~140K/200K tokens)
- Compress: Replace full ADR text with summaries + references
- Archive: Move completed task logs to external files
- Snapshot: Save context state to timeline.md

### Degradation Assumption
- Design assuming context WILL degrade
- Explicit re-derivation checkpoints every ~10 actions
- Session handoff protocol for clean context transitions

## PCMS-Specific Patterns

### ADR-First Loading
```
1. Load ADR index (lightweight references)
2. Identify relevant ADRs for current task
3. Load full ADR text only for those
4. Unload after decision verified
```

### Verification-First Context
```
Session Start:
  → Load: Phase status, ADR constraints, verification rules

During Work:
  → Defer: Full implementation history
  → Focus: Current change + verification criteria

Before Completion:
  → Re-load: All verification requirements
  → Run: Complete verification suite
  → Log: Results to timeline
```

### Multi-Agent Context Handoff
```
Claude → ChatGPT:
  → Package: Current state, open questions, recommendations
  → Format: context/agents/chatgpt/goal.md
  → Verify: Handoff protocol compliance

ChatGPT → Lovable:
  → Package: ADR constraints, implementation spec
  → Format: Lovable prompt with context references
  → Verify: No context loss
```

## Related Skills
- context-degradation (failure patterns, recovery)
- context-compression (long-running sessions)
- memory-systems (multi-agent state management)
- multi-agent-patterns (Claude ↔ ChatGPT ↔ Lovable)
- evaluation (verification-before-completion)

## Metrics

### Context Health Indicators
- Token usage < 140K/200K (70% threshold)
- ADR references < 5 simultaneously loaded
- Session duration < 4 days without handoff
- Verification pass rate 100% (no degraded decisions)

### Warning Signs
- Forgetting ADR constraints mid-session
- Repeating work already completed
- Uncertain about current phase/goals
- Reasoning feels fuzzy or contradictory

### Recovery Actions
1. Explicit checkpoint: "I'm losing the thread"
2. Re-read context/meta/summary.md
3. Verify current goals from session log
4. Create investigation/ document if confusion persists
5. Handoff to fresh session if degradation severe
