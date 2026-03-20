# Architecture Patch — Phase 0.4

**Patch ID:** ARCH-PATCH-0.4-001
**Date:** 2026-03-19
**Session:** Phase 0.4 — MCU Type Catalog
**Author:** Claude Sonnet 4.6 (build_mcu_catalog.py)

---

## Summary

Phase 0.4 introduces the `logs/` directory at the project root. This directory was not present in the original `ARCHITECTURE.md` directory structure and requires a formal patch to bring the documentation into sync.

---

## Directory Tree Addition

Insert after the `working/` entry in the `ARCHITECTURE.md` Directory Structure section:

```
├── logs/                            # Build-time diagnostic output (not committed to git)
│   └── Corpus_Anomalies.md          # Fields at >90% but <100% occurrence across corpus — human review required [Phase 0.4]
```

**Gitignore status:** `logs/` is added to `.gitignore`. Its contents are regenerated on every run of `scripts/build_mcu_catalog.py` and are developer-local. They must not be version-controlled.

---

## Rationale

The `build_mcu_catalog.py` script (Phase 0.4) uses a strict 100% set intersection to determine required fields, and writes a separate anomaly report for fields at >90% but <100% corpus occurrence. This report surfaces edge cases for human judgment without automating the decision (per D-20). The `logs/` directory provides a stable, documented home for this and any future build-time diagnostic output.

**Decision reference:** D-20 (required/optional split strategy with anomaly logging)

---

## Affected Files

| File | Change |
|---|---|
| `ARCHITECTURE.md` | Add `logs/` entry to Directory Structure section |
| `.gitignore` | Add `logs/` entry (already applied this session) |

---

## No Structural Drift

This patch adds one new directory. It does not:
- Move, rename, or remove existing directories or modules
- Change import paths or module boundaries
- Alter phase dependencies or the compiler pipeline

The three-layer architecture (User-Facing Apps → Backend Tools → Shared Foundation) is unchanged.
