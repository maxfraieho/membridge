---
tags:
  - domain:meta
  - status:canonical
  - format:audit
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Audit: BLOOM Documentation Rebranding"
dg-publish: true
---

# Audit: BLOOM Documentation Rebranding

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Language: Ukrainian (canonical)

---

## 0. Context

Garden Bloom underwent a rebranding to establish **BLOOM** (Behavioral Logic Orchestration for Order-Made Systems) as the canonical name for the execution runtime. This audit documents the terminology alignment process, identifies remaining inconsistencies, and confirms that all canonical documents use standardized terminology.

---

## 1. Audit Methodology

1. Inventory all documentation files across `docs/` hierarchy
2. Identify legacy terminology (pre-BLOOM naming)
3. Map legacy terms to canonical BLOOM equivalents (see [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]])
4. Verify each Tier-1 document uses canonical terms
5. Flag Tier-2 documents that require updates
6. Document gaps in coverage (see [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]])

---

## 2. Scope

### 2.1 Documents audited

| Package | Files | Tier |
|---------|-------|------|
| `architecture/foundation/` | 2 | Tier 1 |
| `architecture/core/` | 8 | Tier 1 |
| `architecture/features/` | 4 | Tier 1 |
| `architecture/non-functional/` | 6 | Tier 1 |
| `architecture/governance/` | 5 | Tier 1/2 |
| `architecture/runtime/` | 1 | Tier 1 (new) |
| `architecture/historical/` | 2 | Archive |
| `operations/` | 5 | Tier 2 |
| `backend/` | 2 | Tier 1 |
| `frontend/` | 6 | Tier 2 |
| `integration/` | 7 | Tier 1 |
| `manifesto/` | 4 | Tier 1 |
| `product/` | 2 | Tier 1 |
| `memory/` | 6 | Tier 2 |
| `drakon/` | 5 | Tier 2 |
| `notebooklm/` | 7 | Tier 2 |
| Root-level docs | 5 | Mixed |

**Total: ~77 files audited**

### 2.2 Exclusions

- `_quarantine/` directory (archived, non-canonical)
- `architecture/historical/` (retained for provenance, not updated)

---

## 3. Findings

### 3.1 Terminology Alignment Status

| Category | Status | Notes |
|----------|--------|-------|
| System name: "Garden Bloom" | Retained | Garden Bloom is the product; BLOOM is the runtime |
| Runtime name: "BLOOM" | Canonical | Defined in `BLOOM_RUNTIME_IDENTITY.md` |
| Agent execution: "Execution Context" | Canonical | Aligned across all core docs |
| Memory: "claude-mem.db" vs "DiffMem" | Canonical | Two-memory axiom consistently applied |
| Orchestration: "Orchestration Layer" | Canonical | Vendor-agnostic abstraction documented |
| Proxy: "Claude CLI Proxy" | Canonical (new) | Documented in `INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md` |

### 3.2 Legacy Terms Found

See [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]] for the complete mapping. Summary:

- 12 legacy terms identified
- 8 terms already replaced in Tier-1 documents
- 4 terms remain in Tier-2 documents (scheduled for update)

### 3.3 Structural Issues

| Issue | Location | Severity | Resolution |
|-------|----------|----------|------------|
| Runtime layer undocumented | `architecture/runtime/` | High | Created `INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md` |
| No audit documentation | `audit/` | Medium | Created this audit package |
| Missing BLOOM identity link in INDEKS | `ІНДЕКС.md` | Low | Updated with runtime section |
| Broken semantic link to АРХІТЕКТУРНИЙ_КОРІНЬ | `integration/_INDEX.md` | Low | Verified as relative path issue |

### 3.4 Cross-Reference Integrity

All `[[wikilink]]` references in Tier-1 documents verified:
- 94% resolve correctly
- 6% use relative paths that work in Obsidian but not in plain Markdown readers
- No broken references to non-existent documents

---

## 4. Recommendations

### 4.1 Immediate (P0)

1. Ensure all new documents use canonical BLOOM terminology from creation
2. Update `docs/ІНДЕКС.md` to include runtime and audit sections

### 4.2 Short-term (P1)

1. Update remaining Tier-2 documents with canonical terminology
2. Add `architecture/runtime/` to the NotebookLM canonical set
3. Standardize wikilink format across all documents

### 4.3 Long-term (P2)

1. Implement automated terminology linting in CI
2. Generate documentation graph from semantic relations
3. Add changelog tracking for Tier-1 document mutations

---

## 5. Audit Trail

| Date | Action | Actor |
|------|--------|-------|
| 2026-02-24 | Initial audit conducted | architect |
| 2026-02-24 | Terminology matrix created | architect |
| 2026-02-24 | Gaps analysis completed | architect |
| 2026-02-24 | Runtime spec created | architect |

---

## Semantic Relations

**This document is part of:**
- [[_INDEX]] -- Audit Pack index

**Depends on:**
- [[manifesto/ГЛОСАРІЙ.md]] -- Canonical glossary
- [[architecture/foundation/BLOOM_RUNTIME_IDENTITY.md]] -- BLOOM identity definition

**Referenced by:**
- [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]] -- Uses findings from this audit
- [[ІНДЕКС]] -- Master documentation index
