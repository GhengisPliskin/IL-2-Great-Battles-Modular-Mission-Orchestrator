# Contributing — IL-2 Great Battles Modular Mission Orchestrator

**Last Updated:** March 19, 2026  
**Status:** Active (stub — extended contributor guide at `docs/CONTRIBUTOR_GUIDE.md` produced in Phase 6)

This file covers the minimum required reading for anyone contributing code to this project, human or AI. The [Master Plan](docs/MMO_Master_Project_Plan.md) and [ARCHITECTURE.md](ARCHITECTURE.md) contain the full operational detail.

---

## Ground Rules

All contributors — human and AI — operate under 11 non-negotiable ground rules. Full definitions are in [`SKILL.md`](SKILL.md) (the GitHub Project Planner skill) and the [Master Plan](docs/MMO_Master_Project_Plan.md).

| # | Rule | Short Form |
|---|---|---|
| 1 | **Issue Binding** | No code without an active, assigned Issue. |
| 2 | **Decision Logging** | Architectural decisions → `KEY_DECISION_LOG.md`. Code decisions → `working/CODE_DECISIONS_PATCH.md` (merged at HUMAN gate). |
| 3 | **State Synchronization** | AI agents announce Kanban state at start and end of every action. |
| 4 | **Source Truth** | `ARCHITECTURE.md` updated concurrently with any structural change. |
| 5 | **Constraint Traceability** | Decisions impacting FMEA constraints cite the FMEA ID. |
| 6 | **Template Adherence** | Read the template file before generating any project document. No reconstruction from memory. |
| 7 | **[SPIKE] Exemption** | Spike issues may not move to Done without a linked formalization issue. |
| 8 | **Execution-Locked FMEA** | FMEA constraints are immutable during execution. Do not relax, alter, or work around them. |
| 9 | **FMEA Amendment Protocol** | If a constraint appears logically impossible, HALT and propose a formal amendment. Do not proceed. |
| 10 | **Codebase State Synchronization** | Ingest a current repo map before any execution session outside an AI-native IDE. |
| 11 | **Code Comment Standard** | All code must meet the comment standard below. Comments are preserved across all revisions. |

---

## Code Comment Standard (Ground Rule 11)

**Authoritative source:** [`ARCHITECTURE.md`](ARCHITECTURE.md) — "Code Comment Standard" section.  
**Constraint IDs:** `CONSTRAINTS.md` C-019 through C-022.

The standard exists so that any reader — unfamiliar with IL-2 internals, this codebase, or both — can understand what each block of code does and why it was written the way it was. The IL-2 engine has non-obvious runtime behaviors (timer pause semantics, counter non-reset, entity binding races) that must be explained at the point of implementation. "Self-documenting code" is not sufficient here.

### Four required comment types

**1. Module docstring — every `.py` file, at the top**

```python
"""
MODULE:  <filename without .py>
PURPOSE: <What this module does. Which layer/component it belongs to. 1–3 sentences.>
FMEA:    <Constraint IDs this module directly implements, e.g. "EL-001, SM-003". "None" if not applicable.>
PHASE:   <Project phase that introduced this module, e.g. "Phase 1.4".>
"""
```

**2. Function/method docstring — every public function or method**

```python
def example_function(arg1, arg2):
    """
    WHAT:    <One sentence: what does this function do?>
    WHY:     <One sentence: why does it exist / what failure does it prevent?>
    ARGS:
        arg1 (type): <Description.>
        arg2 (type): <Description.>
    RETURNS:
        type: <Description. "None" if void.>
    FMEA:    <Constraint ID if directly enforced, else "None".>
    """
```

**3. Block comment — every non-trivial logic block**

```python
# --- WHAT THIS DOES ---
# <2–4 plain sentences. Describe the operation and its purpose. If an FMEA
# constraint drives this logic, cite the ID in brackets: [EL-001]>
```

**4. Why-Not comment — when a constraint forces a non-obvious choice**

```python
# WHY NOT <obvious alternative>: [<FMEA-ID>] — <Plain explanation of why the
# obvious approach fails in the IL-2 engine or violates a project constraint.>
```

### Preservation rules

These apply to every session — no per-task negotiation required:

- **Preserve existing comments verbatim.** Do not remove or truncate docstrings or block comments unless the underlying logic is being replaced in the current task.
- **Refactored functions keep their docstring.** If behavior changes, update the docstring to match — never delete it.
- **New code requires new comments.** A function or block without the required comment type is a failing deliverable.
- **Silent removal is prohibited.** Stripping comments to produce "cleaner" output is a violation. This applies to refactoring, reformatting, and test-writing tasks equally.

---

## Workflow for AI Sessions

1. Read `ARCHITECTURE.md` and `CONSTRAINTS.md` before writing code.
2. For FMEA-constrained tasks: treat every constraint as an immutable physical law. If one appears impossible, HALT and invoke Ground Rule 9.
3. Write code. Add all required comment types as you go — do not defer comments to a cleanup pass.
4. Output `[AWAITING_HUMAN_APPROVAL: Code generation complete. Please test and verify.]` and halt (Tier 1 and Tier 2 tasks).
5. After human approval: write decisions to `working/CODE_DECISIONS_PATCH.md`. Do not write to `CODE_DECISION_LOG.md` directly.
6. At issue close: verify documentation parity — `ARCHITECTURE.md` updated, comments present and preserved, patch file updated.

---

## Workflow for Human Contributors

1. Create a GitHub Issue before touching code (Ground Rule 1).
2. Assign it, move it to "In Progress" on the Kanban board.
3. Follow the code comment standard above.
4. Open a PR. Documentation updates (`ARCHITECTURE.md`, decision log) are prerequisites to merge, not follow-ups.
5. At sign-off: perform the HUMAN gate merge protocol — patch file → `CODE_DECISION_LOG.md`, reset patch, update phase status.

---

## Where to Find Things

| Need | Go To |
|---|---|
| Comment format templates | [`ARCHITECTURE.md`](ARCHITECTURE.md) — Code Comment Standard |
| FMEA constraint details | [`CONSTRAINTS.md`](CONSTRAINTS.md) Section 4 |
| Code quality constraints | [`CONSTRAINTS.md`](CONSTRAINTS.md) Section 5 (C-019–C-022) |
| Decision log templates | [`docs/templates/templates.md`](docs/templates/templates.md) |
| Session prompt header template | [`docs/templates/templates.md`](docs/templates/templates.md) |
| Full ground rule definitions | [`SKILL.md`](SKILL.md) or [Master Plan](docs/MMO_Master_Project_Plan.md) |
| Phase status | [`ARCHITECTURE.md`](ARCHITECTURE.md) — Phase Mapping table |

---

*Extended contributor documentation (module authoring guide, adding map data, architecture deep-dive) will be generated in Phase 6 as `docs/CONTRIBUTOR_GUIDE.md`.*
