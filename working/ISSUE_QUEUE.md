# Issue Queue

**Status:** PROCESSED
**Last processed:** March 20, 2026

---

## QUEUE ENTRY

**Title:** SCP-001: Review Post-V1 Scope Expansions
**Labels:** amendment, phase:4, normal
**Milestone:** Phase 4
**Depends on:** None
**Assignee:** human-gate
**Status:** CREATED — Issue #55

**Body:**

Review and disposition four proposed scope expansions documented in `docs/proposals/SCP-001_Post_V1_Scope_Expansions.md`.

Proposals:
- SCP-01: Expanded Phase 4 strategic target database (decide before task 4.2)
- SCP-02: Shared constraint validation layer (decide before task 5.3)
- SCP-03: Declarative module template schema (decide after Phase 3 completes)
- SCP-04: Read-only mission preview map (decide before task 5.5)

Prerequisite: C-004 SQLite constraint conflict must be resolved first.

Each accepted proposal spawns its own implementation issue(s). This issue closes when all four proposals have a recorded disposition (Accept/Reject/Defer/Modify) in the SCP-001 document.

### Acceptance Criteria
- [ ] All four SCP items have a disposition recorded in the document
- [ ] Accepted items have spawned implementation issues with correct phase labels
- [ ] Rejected items have rationale documented

---

## QUEUE ENTRY

**Title:** Resolve C-002: GUI framework selection (pre-Phase 2)
**Labels:** decision, phase:0, high
**Milestone:** Phase 0
**Depends on:** None
**Assignee:** human-gate
**Status:** CREATED — Issue #56

**Body:**

`CONSTRAINTS.md` C-002 currently reads: "GUI framework TBD (currently PyQt6; replacement under evaluation). Decision required before Phase 2 begins."

This issue tracks the framework decision. Evaluate alternatives and select a framework. The resolution updates:
- `CONSTRAINTS.md` C-002 — lock the framework choice
- `MMO_Master_Project_Plan.md` §3.3 — align with CONSTRAINTS.md
- `ARCHITECTURE.md` — update all PyQt6 references if framework changes
- All session prompt headers referencing PyQt6 (2.3, 2.4, 2.5, 2.6, 3.1–3.4, 5.5)
- `KEY_DECISION_LOG.md` — new entry documenting the decision

### Acceptance Criteria
- [ ] Framework selected and documented in KEY_DECISION_LOG
- [ ] CONSTRAINTS.md C-002 updated to reflect locked decision
- [ ] All downstream documents identified and either updated or logged to DOCUMENT_DRIFT_LOG

---

## QUEUE ENTRY

**Title:** Resolve C-004: Amend no-database constraint for SQLite
**Labels:** amendment, phase:0, high
**Milestone:** Phase 0
**Depends on:** None
**Assignee:** human-gate
**Status:** CREATED — Issue #57

**Body:**

`CONSTRAINTS.md` C-004 states: "No external database dependency — All data is file-based (.json, .Group, .Mission). No PostgreSQL, SQLite, or other DB required at runtime."

Phase 4 already specifies SQLite at `data/map_databases/maps.sqlite3`. This is a standing conflict. SCP-001 (expanded strategic targets) compounds it.

Proposed amendment: Change C-004 to: "No external database server dependency. Embedded file-based databases (SQLite) are permitted. No PostgreSQL, MySQL, or other client-server DB required at runtime."

This preserves the intent (standalone .exe via PyInstaller, no server process) while reflecting what the plan already requires.

Resolution updates:
- `CONSTRAINTS.md` C-004 — amended text
- `MMO_Master_Project_Plan.md` §3.3 — align (see also DOCUMENT_DRIFT_LOG entry 2 re: ID numbering)
- `KEY_DECISION_LOG.md` — new entry
- Unblocks SCP-001 prerequisite

### Acceptance Criteria
- [ ] C-004 amended in CONSTRAINTS.md
- [ ] KEY_DECISION_LOG entry created
- [ ] SCP-001 prerequisite marked as resolved

---

## QUEUE ENTRY

**Title:** Update SKILL.md: add housekeeping session type and queue files to scaffolding
**Labels:** amendment, phase:0, normal
**Milestone:** Phase 0
**Depends on:** None
**Assignee:** ai-with-review
**Status:** CREATED — Issue #58

**Body:**

The GitHub Project Planner skill (`SKILL.md`) scaffolds project infrastructure for future projects. The March 20, 2026 planning session introduced three process mechanisms that should become standard scaffolding:

1. **Housekeeping session type** — `CLAUDE.md` now defines Execution and Housekeeping as distinct session types. The SKILL.md template for `CLAUDE.md` does not include this yet.
2. **`working/ISSUE_QUEUE.md`** — transit queue for issue creation. Not in the SKILL.md scaffolding inventory.
3. **`working/DOCUMENT_DRIFT_LOG.md`** — stale-fact registry. Not in the SKILL.md scaffolding inventory.
4. **Simplified label taxonomy** — `KANBAN_SETUP.md` template still uses the ~40-label taxonomy.

This issue requires an Opus planning session (Tier 1) to design how these project-specific implementations generalize into reusable templates, followed by a Tier 3 session to write the changes.

Do not modify SKILL.md directly from this issue description. The planning session determines the design; this issue holds the slot.

### Acceptance Criteria
- [ ] Opus planning session completed — design decisions documented
- [ ] SKILL.md scaffolding inventory includes ISSUE_QUEUE.md and DOCUMENT_DRIFT_LOG.md
- [ ] SKILL.md CLAUDE.md template includes session type definitions
- [ ] SKILL.md KANBAN_SETUP.md template uses simplified label taxonomy
- [ ] SKILL.md templates reference doc updated if template formats changed

---

## QUEUE ENTRY

**Title:** Document housekeeping session workflow in CONTRIBUTING.md
**Labels:** task, phase:0, normal
**Milestone:** Phase 0
**Depends on:** None
**Assignee:** ai-with-review
**Status:** CREATED — Issue #59

**Body:**

`CONTRIBUTING.md` has no coverage of the housekeeping session type introduced in the March 20, 2026 planning session. A returning human contributor has no documented way to know the mechanism exists or how to invoke it.

Add a "Housekeeping Sessions" section to `CONTRIBUTING.md` covering:
- What a housekeeping session is and when to run one (after a planning session that generated queue entries, or when `working/ISSUE_QUEUE.md` / `working/DOCUMENT_DRIFT_LOG.md` show PENDING ENTRIES)
- How to trigger it: open Claude Code and say "Run a housekeeping session"
- What to expect: Claude Code reads both queue files, creates GitHub Issues via `gh issue create`, patches stale documents, commits with a descriptive message
- What it will not do: no code written, no prompt headers generated, no execution work — queue processing only
- ESCALATE entries: Claude Code skips these; they require a planning session to resolve first

### Acceptance Criteria
- [ ] "Housekeeping Sessions" section added to CONTRIBUTING.md
- [ ] Section covers trigger phrase, expected output, and ESCALATE behavior
- [ ] No changes to CLAUDE.md, ARCHITECTURE.md, or queue files — CONTRIBUTING.md only

---
