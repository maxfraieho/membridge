# Context Degradation: PCMS-Specific Patterns

## Description
Detection and recovery from context degradation in ADR-driven, verification-first development.

## When to Use
- Session duration > 3 days (degradation risk increases)
- Token usage > 140K/200K (70% context capacity)
- Verification failures on previously passing tests
- Uncertain about ADR constraints or phase status
- Multi-agent handoffs (context transition points)

## Core Failure Patterns for PCMS

### 1. Lost-in-Middle Effect
**Pattern:** ADR constraints in middle of context suffer 10-40% lower recall
**Impact:** Agent violates ADR-004 (tamper-evident) or ADR-006 (testing scope) mid-session
**Detection:**
- Agent proposes changes violating established ADR
- Forgets Phase 0.1 QA contract mid-implementation
- Reintroduces rejected patterns

**PCMS Mitigation:**
```
- Place ADR constraints at SESSION START (attention-favored)
- Re-state constraints before major decisions
- Verification hook: Check ADR compliance before execution
```

### 2. Context Poisoning
**Pattern:** False assumptions about PCMS architecture enter context
**Impact:** Incorrect beliefs about encryption (client-side vs backend), IPFS implementation, Berkeley Protocol guarantees
**Sources:**
- Hallucinated "Phase 1 implementation" when only Phase 0.1 exists
- Confusing tamper-evident (✅) with tamper-proof (❌)
- Assuming backend exists when PCMS is offline-first

**PCMS Detection:**
```
Watch for:
- Claims about "server-side" anything (PCMS has no backend in Phase 0.1)
- References to "tamper-proof" (forbidden term per ADR-006)
- Mentions of Phase 2+ features as if implemented
```

**Recovery:**
```
1. STOP immediately on poisoning detection
2. Re-read context/meta/summary.md (authoritative state)
3. Explicit correction: "My belief X was wrong, actual state is Y"
4. Document in timeline.md to prevent reoccurrence
```

### 3. Context Distraction
**Pattern:** Irrelevant context competes for attention
**Impact:** Agent focuses on non-PCMS features, general React patterns instead of privacy-first constraints
**Sources:**
- Generic React/TypeScript documentation
- General privacy guides (not Berkeley Protocol specific)
- Skills not relevant to current phase

**PCMS Mitigation:**
```
- Load ONLY phase-relevant ADRs (not all 7)
- Use skill references, not full skill text
- Defer historical session logs until needed
```

### 4. Context Confusion
**Pattern:** Agent mixes constraints from different phases
**Impact:** Tries to implement Phase 1 IPFS while in Phase 0.1 verification
**Sources:**
- Phase roadmap loaded without phase boundary clarity
- ADR-007 (future) confused with ADR-004 (implemented)

**PCMS Detection:**
```
- Agent mentions "OrbitDB" or "Lit Protocol" in Phase 0.1 work
- Proposes backend features when offline-first required
- References unaccepted ADRs as constraints
```

**Recovery:**
```
1. Re-read context/meta/summary.md (Phase Status section)
2. Verify: What phase are we in? What's implemented vs planned?
3. Isolation: Create phase-specific context boundaries
```

### 5. Context Clash
**Pattern:** Contradictions between valid PCMS sources
**Impact:** ADR-004 (implemented) vs ADR-008 (draft) create conflicting guidance
**Sources:**
- Draft ADRs vs Accepted ADRs
- Phase 0.1 reality vs Phase 1 vision
- Lovable implementation vs Claude review feedback

**PCMS Detection:**
```
- Conflicting guidance on same feature
- "Should I follow ADR-X or ADR-Y?" dilemma
- Implementation contradicts verification requirements
```

**Recovery:**
```
Priority Rules (highest to lowest):
1. Accepted ADRs (004, 005, 006, 007)
2. context/meta/summary.md (current state)
3. Draft ADRs (008+, informational only)
4. Session logs (historical context)
5. General documentation
```

## Detection Mechanisms

### Automated Signals
```
Token Usage Monitor:
  > 140K tokens → WARNING: Compaction needed
  > 160K tokens → CRITICAL: Handoff recommended

Session Duration:
  > 3 days → WARNING: Context degradation risk
  > 5 days → CRITICAL: Mandatory handoff

Verification Failures:
  Previously passing test fails → STOP: Investigate root cause
  ADR violation detected → STOP: Context poisoning likely
```

### Manual Signals
```
Agent should self-report:
  "I'm losing the thread" → Checkpoint immediately
  "Uncertain about X" → Re-derive from source
  "This contradicts Y" → Context clash, apply priority rules
```

### Quality Degradation Indicators
- Outputs getting sloppier
- Uncertain what the goal was
- Repeating work already completed
- Reasoning feels fuzzy or contradictory
- Verification pass rate drops below 100%

## Recovery Strategies

### For Poisoning (False Beliefs)
```
STOP → Re-read → Correct → Document
1. STOP all work immediately
2. Re-read authoritative source (context/meta/summary.md)
3. Explicit correction: State wrong belief + correct state
4. Document in timeline.md
5. Resume with verified context
```

### For Distraction (Irrelevant Context)
```
Curate → Filter → Namespace
1. Audit loaded context: What's actually needed?
2. Unload: Generic docs, non-phase-relevant ADRs
3. Namespace: Separate Phase 0.1 vs Phase 1 context
4. Tool-based access: Load on demand, not pre-load
```

### For Confusion (Mixed Constraints)
```
Segment → Isolate → Transition
1. Create phase-specific context boundaries
2. Isolate: Phase 0.1 work uses ONLY Phase 0.1 ADRs
3. Clear transitions: Handoff protocol between phases
4. Conflict marking: Flag contradictions explicitly
```

### For Clash (Contradictions)
```
Prioritize → Resolve → Document
1. Apply priority rules (Accepted ADRs > summary.md > drafts)
2. Resolve: Choose authoritative source
3. Document decision in timeline.md
4. Update summary.md if systemic conflict
```

## The Four-Bucket Mitigation (PCMS Adaptation)

### 1. Write (External Storage)
```
Store in filesystem:
- context/meta/timeline.md (session history)
- context/decisions/adr/*.md (ADR archive)
- investigations/*.md (deep-dive research)

NOT in active context:
- Historical session logs (load on demand)
- Completed ADR full text (use references)
```

### 2. Select (Relevance Filtering)
```
Load ONLY:
- Current phase ADRs (Phase 0.1 → ADR 004, 005, 006)
- Active session goals
- Immediate verification requirements

Defer:
- Future phase ADRs (ADR-008+ in Phase 0.1)
- Generic React/TS patterns
- Full skill text (use references)
```

### 3. Compress (Summarization)
```
At 70% context (140K tokens):
- Replace full ADR text with: "ADR-004: Tamper-evident audit logging (Accepted). Key constraints: [3 bullets]"
- Archive completed task logs to timeline.md
- Snapshot current state to summary.md
```

### 4. Isolate (Sub-Agent Splitting)
```
Multi-Agent Workflow:
- Claude: Verification, review, context management
- ChatGPT: Architecture, ADR drafting, research
- Lovable: Implementation (isolated context)

Each agent maintains:
- Own context window
- Explicit handoff artifacts
- Clean state boundaries
```

## PCMS-Specific Recovery Checklist

**On Degradation Detection:**
```
[ ] STOP all work immediately
[ ] Identify failure pattern (poisoning/distraction/confusion/clash)
[ ] Re-read context/meta/summary.md (authoritative state)
[ ] Verify phase status (0.1? 1? What's implemented?)
[ ] Check ADR compliance (violating any Accepted ADRs?)
[ ] Document degradation in timeline.md
[ ] Apply recovery strategy (truncate/curate/segment/prioritize)
[ ] Resume with verified, clean context
```

## Related Skills
- context-fundamentals (prevention through proper loading)
- context-compression (mitigation through compaction)
- memory-systems (external state management)
- multi-agent-patterns (isolation through sub-agents)
- evaluation (verification-before-completion detection)

## Metrics

### Context Health Score
```
Healthy Session:
✓ Token usage < 140K/200K
✓ Session duration < 3 days
✓ Verification pass rate 100%
✓ Zero ADR violations
✓ Clear about current phase/goals

Degraded Session:
✗ Token usage > 160K/200K
✗ Session duration > 5 days
✗ Verification failures
✗ ADR violations detected
✗ Uncertainty about state
```

### Recovery Success Criteria
- Agent can state current phase accurately
- Agent can list Accepted ADRs without errors
- Agent can explain why previous decision was made
- Verification passes after recovery
- No repeated mistakes from before recovery
