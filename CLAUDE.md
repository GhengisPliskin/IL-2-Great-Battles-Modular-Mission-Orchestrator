# CLAUDE.md — Session Briefing for Claude Code

This file is read automatically by Claude Code at the start of every session.
It is the minimum required orientation for any AI session on this project.
Do not skip or summarize it.
This project has two session types — Execution and Housekeeping — described below. Confirm the session type before proceeding.

---

## Step 1 — Read These Files Before Writing Any Code

Execute these reads in order at session start. Do not proceed to code generation
until all four are ingested.

1. `ARCHITECTURE.md` — Directory structure, component layout, three-layer architecture, glossary, code comment standard
2. `CONSTRAINTS.md` — All engine behavior constraints and code quality constraints (C-001 through C-022)
3. `CODE_DECISION_LOG.md` — Existing code decisions and debugging heuristics
4. `working/CODE_DECISIONS_PATCH.md` — Provisional decisions from the current active phase

Together these four files represent the full project state. Code generated without
reading them will conflict with existing decisions, violate FMEA constraints, or
produce output that cannot be merged.

---

## Step 2 — Ingest a Repository Map (Ground Rule 10)

Before writing code, ingest a current Repomix output or equivalent repository map.
Do not generate code against a stale or assumed mental model of the repository
structure. If no map is provided, request one from the user before proceeding.

---

## Step 3 — Confirm the Active Task

Every session is bound to a specific GitHub Issue and a session prompt header
(Ground Rule 1). Confirm:

- Which Issue number this session addresses
- Which prompt header governs this session (found in `docs/prompts/`)
- Which Kanban column the card should move to at session start

Announce the Kanban state change at session start and again at session end
(Ground Rule 3).

---

---

## Session Types

This project uses two distinct session types. Confirm which type applies before proceeding.

### Execution Session (Default)

For coding, testing, and documentation tasks bound to a GitHub Issue.

Startup: Steps 1–3 above.
Exit responsibility: If this session changed any project-level fact (constraint text, task count, phase status, framework name, file path, directory structure), log all other documents containing the stale version of that fact to `working/DOCUMENT_DRIFT_LOG.md` before ending the session. Use the entry format defined in that file's header.

### Housekeeping Session

For processing accumulated administrative queues. Triggered by the user — not automatic.

Startup sequence:
1. Read `working/ISSUE_QUEUE.md`. If entries exist with status other than CREATED, create each issue via `gh issue create` with the specified title, labels, milestone, and body. Record the created issue number on each entry.
2. Read `working/DOCUMENT_DRIFT_LOG.md`. For each pending entry: open the listed document, verify the stale value is still present, apply the correction, mark the entry as RESOLVED. Skip entries marked ESCALATE.
3. Stage all changes with a descriptive commit message summarizing actions taken (e.g., "Housekeeping: created issues #12–#17, patched 3 drift entries in Master Plan and CONSTRAINTS.md").

Do not combine housekeeping with execution work. Housekeeping sessions process queues and end. They do not write code, generate prompt headers, or perform task execution.

---

## Ground Rules (Summary)

Full definitions are in `SKILL.md` and `docs/MMO_Master_Project_Plan.md`.
These are non-negotiable.

| # | Rule | What It Means in Practice |
|---|---|---|
| 1 | Issue Binding | No code without an active assigned Issue |
| 2 | Decision Logging | Write code decisions to `working/CODE_DECISIONS_PATCH.md` — never directly to `CODE_DECISION_LOG.md` |
| 3 | State Sync | Announce Kanban column changes at start and end of every session |
| 4 | Source Truth | Update `ARCHITECTURE.md` concurrently with any structural change |
| 5 | Constraint Traceability | Cite FMEA constraint IDs in decision log entries and inline comments whenever a constraint governs a decision |
| 6 | Template Adherence | Read the relevant template file before generating any project document — never reconstruct from memory |
| 7 | Spike Exemption | Issues tagged `[SPIKE]` cannot reach Done without a linked formalization issue |
| 8 | Execution-Locked FMEA | FMEA constraints are immutable during execution — do not relax, alter, or work around them |
| 9 | FMEA Amendment Protocol | If a constraint appears logically impossible, HALT and propose a formal amendment — do not proceed |
| 10 | Codebase State Sync | Ingest a current repo map before any execution session |
| 11 | Code Comment Standard | All code must meet the comment standard — see below |

---

## Code Comment Standard (Ground Rule 11)

Full format specification and examples are in `ARCHITECTURE.md` — "Code Comment
Standard" section. Constraints C-019 through C-022 in `CONSTRAINTS.md` define
the enforcement rules.

**Summary of what is required in every `.py` file:**

**Module docstring** — top of every file:
```python
"""
MODULE:  <filename without .py>
PURPOSE: <What this module does. 1–3 sentences.>
FMEA:    <Constraint IDs directly implemented here, or "None".>
PHASE:   <Project phase that introduced this file.>
"""
```

**Function docstring** — every public function or method:
```python
def example(arg1, arg2):
    """
    WHAT:    <What it does.>
    WHY:     <Why it exists / what failure it prevents.>
    ARGS:
        arg1 (type): <Description.>
        arg2 (type): <Description.>
    RETURNS:
        type: <Description. "None" if void.>
    FMEA:    <Constraint ID if directly enforced, else "None".>
    """
```

**Block comment** — above every non-trivial logic block:
```python
# --- WHAT THIS DOES ---
# <2–4 plain sentences. Cite FMEA ID in brackets if applicable: [EL-001]>
```

**Why-Not comment** — when a constraint forces a non-obvious choice:
```python
# WHY NOT <obvious alternative>: [FMEA-ID] — <Plain explanation.>
```

**Preservation rules — no exceptions:**
- Existing comments are preserved verbatim unless the underlying logic is replaced
- New code requires new comments — no deferral to a cleanup pass
- Silent removal of comments is prohibited in all task types including refactoring,
  reformatting, and test writing
- Comment presence and preservation are standing acceptance criteria on every task

---

## Two-Phase Commit (Tier 1 and Tier 2 Tasks)

After code generation is complete:

**PHASE 1 — Execution**
1. Generate the required code
2. Output exactly: `[AWAITING_HUMAN_APPROVAL: Code generation complete. Please test and verify.]`
3. HALT. Do not proceed to documentation.

**PHASE 2 — Documentation (only after human replies "Approved")**
1. Audit final code against FMEA constraints
2. Write decisions to `working/CODE_DECISIONS_PATCH.md` using the patch template
3. Generate an `ARCHITECTURE_PATCH.md` if structural drift occurred
4. Announce final Kanban state change

---

## Decision Logging

Write all code decisions to `working/CODE_DECISIONS_PATCH.md`.
Never write directly to `CODE_DECISION_LOG.md`.

The patch file is provisional. It is merged into `CODE_DECISION_LOG.md` by the
human at the HUMAN gate when the phase passes all tests and receives sign-off.
The patch file is then reset to an empty initialized template.

Template format is in `docs/templates/templates.md`.

---

## FMEA Constraint Handling

Constraints in `CONSTRAINTS.md` Section 4 (PI-*, EL-*, SM-*, EC-*) are the
project's physical laws. During execution:

- Treat every constraint as immutable
- Cite the constraint ID in any inline comment where it governs logic
- If a constraint appears logically impossible to satisfy: HALT, do not work
  around it, invoke Ground Rule 9 and propose a formal FMEA amendment

The FMEA Amendment template is in `docs/templates/templates.md`.

---

## File Write Locations

| Output Type | Write To |
|---|---|
| Source code | `src/` per `ARCHITECTURE.md` directory structure |
| Code decisions | `working/CODE_DECISIONS_PATCH.md` |
| Architecture changes | `ARCHITECTURE_PATCH.md` (propose, do not directly edit) |
| Compliance findings (if audit run) | `working/COMPLIANCE_LOG.md` |
| Issue definitions (from planning sessions) | `working/ISSUE_QUEUE.md` |
| Stale-fact notifications | `working/DOCUMENT_DRIFT_LOG.md` |

Never write directly to `CODE_DECISION_LOG.md`, `KEY_DECISION_LOG.md`, or
`ARCHITECTURE.md` during active development. These are updated only at HUMAN
gates or via the patch/amendment protocol.
