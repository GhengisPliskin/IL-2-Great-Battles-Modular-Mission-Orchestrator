# Document Drift Log

**Status:** PROCESSED (1 ESCALATED)
**Last processed:** March 20, 2026

---

## DRIFT ENTRY 1

**Discovered:** March 20, 2026
**Discovered during:** SCP-001 planning session — constraint cross-reference audit
**Stale document:** `MMO_Master_Project_Plan.md`
**Section:** §3.3 Constraints table, row C-002
**Stale value:** "C-002 — PyQt6 for GUI — Tech Stack — Framework locked; no web/Electron alternatives"
**Correct value:** "C-002 — GUI framework TBD (currently PyQt6; replacement under evaluation) — Tech Stack — Decision required before Phase 2 begins"
**Source of truth:** `CONSTRAINTS.md` C-002, updated in KEY_DECISION_LOG Decision 6
**Status:** RESOLVED — March 20, 2026

---

## DRIFT ENTRY 2

**Discovered:** March 20, 2026
**Discovered during:** SCP-001 planning session — constraint ID cross-reference
**Stale document:** `MMO_Master_Project_Plan.md`
**Section:** §3.3 Constraints table, constraint ID numbering
**Stale value:** Plan uses C-004 = "IL-2 ASCII format undocumented", C-007 = "No external database". Seven total rows with IDs C-001 through C-007.
**Correct value:** `CONSTRAINTS.md` uses C-004 = "No external database dependency", C-008 = "IL-2 ASCII syntax is undocumented and proprietary". Twenty-two total constraints across five sections with IDs C-001 through C-022.
**Source of truth:** `CONSTRAINTS.md` is the complete constraint register. The Master Plan §3.3 should either reproduce the correct IDs or (preferred) replace the table with a reference: "See `CONSTRAINTS.md` for the complete constraint register including engine runtime constraints, FMEA traceability, and code quality requirements."
**Note:** ESCALATE — this entry has two resolution paths (reproduce vs. reference). A planning session should decide which approach before the housekeeping session patches it.

---

## DRIFT ENTRY 3

**Discovered:** March 20, 2026
**Discovered during:** SCP-001 planning session — documentation framework audit
**Stale document:** `MMO_Master_Project_Plan.md`
**Section:** §9 Documentation Framework table
**Stale value:** Table does not include `docs/proposals/`, `working/ISSUE_QUEUE.md`, or `working/DOCUMENT_DRIFT_LOG.md`
**Correct value:** Add three rows: `docs/proposals/SCP-001_Post_V1_Scope_Expansions.md` (Generated, SCP-001 session), `working/ISSUE_QUEUE.md` (Generated, Housekeeping infrastructure), `working/DOCUMENT_DRIFT_LOG.md` (Generated, Housekeeping infrastructure)
**Source of truth:** This housekeeping spec (source session March 20, 2026)
**Status:** RESOLVED — March 20, 2026

---
