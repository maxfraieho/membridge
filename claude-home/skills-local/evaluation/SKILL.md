# Evaluation: Verification-Before-Completion for PCMS

## Description
Verification frameworks for ADR-driven, verification-first development.

## When to Use
- Before marking any task complete
- Before git commit
- Before multi-agent handoff
- Before phase transition

## PCMS Verification Levels

### Level 1: Syntax Verification
```
TypeScript Compilation:
  npx tsc --noEmit
  → MUST: Zero errors

Linting:
  npm run lint
  → MUST: Zero errors

Format:
  npm run format:check
  → MUST: Zero errors
```

### Level 2: Functional Verification
```
Unit Tests:
  npm run test
  → MUST: 100% pass rate
  → MUST: Coverage > baseline

Integration Tests:
  npm run test:integration
  → MUST: 100% pass rate

E2E Tests (if applicable):
  npm run test:e2e
  → MUST: 100% pass rate
```

### Level 3: ADR Compliance Verification
```
For each Accepted ADR:
  [ ] ADR-004: Tamper-evident audit logging
      → Verify: Hash chain test passes
      → Verify: Deterministic stringify test passes
      → Verify: Redaction test passes

  [ ] ADR-005: Verification & Export
      → Verify: Startup verification runs
      → Verify: Pre-export verification mandatory
      → Verify: Force export shows disclaimer

  [ ] ADR-006: Testing Scope
      → Verify: No "tamper-proof" language
      → Verify: Tests document guarantees accurately
      → Verify: QA contract compliance
```

### Level 4: Behavioral Verification
```
Manual Testing:
  [ ] Feature works as specified
  [ ] Edge cases handled
  [ ] Error messages clear and actionable
  [ ] UX matches design

Privacy Verification:
  [ ] No plaintext sensitive data
  [ ] Encryption keys not logged
  [ ] Client-side only (no backend leaks)
```

### Level 5: Documentation Verification
```
Code Comments:
  [ ] Complex logic explained
  [ ] NOT obvious code (no comment noise)

ADR Updates:
  [ ] If architecture changed, ADR updated or new ADR drafted

Timeline Updates:
  [ ] Session logged in timeline.md
  [ ] State changes documented
```

## Verification Checklist (MANDATORY)

**Before Task Completion:**
```
[ ] Level 1: Syntax (tsc, lint, format) - PASS
[ ] Level 2: Functional (all tests) - PASS
[ ] Level 3: ADR compliance - VERIFIED
[ ] Level 4: Behavioral (manual test) - CONFIRMED
[ ] Level 5: Documentation - UPDATED
[ ] Git: Changes committed with clear message
[ ] Timeline: Session logged
[ ] Handoff: If applicable, artifact created
```

## Verification Anti-Patterns (FORBIDDEN)

### ❌ "Works on My Machine"
```
Bad: Manual test only, no automated verification
Good: Automated tests + manual confirmation
```

### ❌ "Tests Passing" (but wrong tests)
```
Bad: Old tests pass, new feature untested
Good: New tests written for new feature
```

### ❌ "Verified" (but not documented)
```
Bad: Ran tests, didn't log results
Good: Verification results in timeline.md
```

### ❌ Silent Failures
```
Bad: Test fails, skip it, move on
Good: STOP, fix test, verify again
```

## Verification Failure Response

**On ANY Verification Failure:**
```
1. STOP immediately (no proceeding)
2. Identify failure cause (what, why)
3. Document in timeline.md
4. Fix root cause (not just symptom)
5. Re-run FULL verification (not just failed test)
6. Verify fix didn't break other things
7. Document resolution in timeline.md
8. Resume work
```

## Related Skills
- context-fundamentals (verification context loading)
- context-degradation (verification as degradation detection)
