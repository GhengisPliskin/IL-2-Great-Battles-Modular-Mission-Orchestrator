# Scope Change Proposal — SCP-001

## Post-V1 Architecture Expansions

**Date:** March 20, 2026
**Author:** Claude Opus 4.6 (Architecture Review role), initiated by GhengisPliskin
**Status:** Proposed — Awaiting Review
**Tracking Issue:** TBD (create in Triage with label `scope-proposal`, `phase:4`)

---

## Purpose

This document proposes four scope expansions identified during an ideal-state analysis of the MMO project. Each item is architecturally compatible with the current plan and introduces no new external dependencies beyond what the plan already uses. Items are scoped as additions or modifications to existing phases, not as new phases.

The proposals are ordered by decision deadline — earliest-required first.

---

## Prerequisite: Resolve C-004 / SQLite Conflict

**This must be resolved before SCP-01 or SCP-02 can be accepted.**

`CONSTRAINTS.md` C-004 states: *"No external database dependency — All data is file-based (.json, .Group, .Mission). No PostgreSQL, SQLite, or other DB required at runtime."*

Phase 4 already specifies SQLite at `data/map_databases/maps.sqlite3` as the geographic database. This is a standing constraint conflict in the current plan. The expanded Phase 4 work in SCP-01 compounds it.

**Recommended resolution:** Amend C-004 to read: *"No external database server dependency. Embedded file-based databases (SQLite) are permitted. No PostgreSQL, MySQL, or other client-server DB required at runtime."* This preserves the intent (standalone .exe, no server process) while reflecting what the plan already requires.

**If accepted:** Generate KEY_DECISION_LOG entry #6 and update `CONSTRAINTS.md` C-004.

---

## SCP-01 — Expanded Phase 4 Strategic Target Database

### Decision Deadline

Before Phase 4.2 (Primary Map Database Population) begins.

### What It Is

Extend the Phase 4 map extraction pipeline to capture strategic ground targets — bridges, factories, rail junctions, ports, supply depots — from stock multiplayer template `.Mission` files. These targets are placed as ground objects in the templates and are extractable using the same parser pipeline that extracts airfields and front-line data.

### Why It Matters

Without strategic target data, the Phase 5.3 Ground Attack scenario template must use arbitrary coordinates or hardcoded target positions. With this data, the scenario engine can select contextually appropriate targets based on map, coalition, and front-line proximity — producing missions where bombers attack actual landmarks rather than empty fields.

### What Changes in the Current Plan

| Document | Change |
|---|---|
| `Phase4_Session_Prompt_Headers.md` | Add requirements R6–R8 to Session 4.2: extract ground target objects, store in new `strategic_targets` SQLite table, expose via `MapDatabase.get_targets()` API. Add target types to Session 4.2h validation checklist. |
| `MMO_Master_Project_Plan.md` | Task 4.2 acceptance criteria: add "Strategic targets extracted for 3+ maps." No new task row — this extends 4.2, not a new task. |
| `ARCHITECTURE.md` | Add `strategic_targets` table to the database schema reference. Add `get_targets()` to the `MapDatabase` API listing. |
| `Phase5_Session_Prompt_Headers.md` | Session 5.3 (Scenario Templates): Ground Attack template references `get_targets()` instead of hardcoded coordinates. Session 5.4 (Ambient AI): artillery module references target proximity for barrage placement. |

### New Tasks Introduced

None. This is a scope expansion of existing task 4.2.

### FMEA Impact

None. Strategic targets are data inputs to the scenario engine. They do not introduce new runtime failure modes — a missing target defaults to coordinate-based placement (current behavior).

### Dependencies on Other Proposals

Independent. Can be accepted or rejected without affecting SCP-02, SCP-03, or SCP-04.

### Disposition

| Decision | Rationale |
|---|---|
| ☐ Accept | |
| ☐ Reject | |
| ☐ Defer | |
| ☐ Modify | |

---

## SCP-02 — Shared Constraint Validation Layer for Scenario Engine

### Decision Deadline

Before Phase 5.3 (Scenario Templates) begins.

### What It Is

Factor the FMEA constraint enforcement logic out of individual scenario templates into a shared validation layer. Instead of each template (Intercept, Patrol, Ground Attack, Escort, Free Hunt) independently checking AI cap compliance, wave count sufficiency, spatial offset uniqueness, and initialization delay scaling, a single `ConstraintValidator` class performs all checks against a declarative constraint registry.

### Why It Matters

Without this, each of the five scenario templates in 5.3 duplicates the same constraint checks. Duplication introduces two risks: (1) a constraint check is implemented slightly differently across templates, producing inconsistent enforcement; (2) when a constraint is amended (FMEA Amendment Protocol, Ground Rule 9), every template must be patched individually. A shared layer means one implementation, one patch surface, and a clear extension point if the constraint set grows or a solver replaces the templates in a future version.

### What Changes in the Current Plan

| Document | Change |
|---|---|
| `Phase5_Session_Prompt_Headers.md` | Add Session 5.0 (or prepend to 5.1): implement `ConstraintValidator` class at `src/backend/orchestrator/constraint_validator.py`. Define constraint registry as a data structure (not hardcoded `if` branches). Sessions 5.1 and 5.3 import and call the validator rather than inline constraint logic. |
| `MMO_Master_Project_Plan.md` | Add task row 5.0 or expand 5.1 scope. If new task: Tier 1, depends on Phase 3 completion (needs full FMEA constraint set proven in implementation), delivers to 5.1 and 5.3. |
| `ARCHITECTURE.md` | Add `constraint_validator.py` to directory structure. Add `ConstraintValidator` to the Orchestrator's public API. |
| `CONSTRAINTS.md` | No change — constraints are consumed by the validator, not modified. |

### New Tasks Introduced

One new task (5.0) or expansion of 5.1 scope. Tier 1 — requires cross-constraint reasoning to design the registry schema. Estimated scope: moderate (the constraints already exist in FMEA; the work is structuring them as machine-readable validation rules).

### FMEA Impact

Reduces occurrence scores for constraint enforcement inconsistency across templates. Does not introduce new failure modes. Existing FMEA IDs (EC-004, EL-001, EC-001, PI-004) are enforced by the validator — their constraint text becomes the validator's rule definitions.

### Dependencies on Other Proposals

Independent of SCP-01 and SCP-04. Enhances the value of SCP-03: if a declarative module schema is adopted, the constraint validator becomes the shared enforcement mechanism for both hand-coded and declaratively-defined modules.

### Disposition

| Decision | Rationale |
|---|---|
| ☐ Accept | |
| ☐ Reject | |
| ☐ Defer | |
| ☐ Modify | |

---

## SCP-03 — Declarative Module Template Schema

### Decision Deadline

After Phase 3 completes (contingent on pattern analysis). Must be resolved before Phase 6.3 (Contributor Documentation), which describes how external contributors add module types.

### What It Is

Replace the current pattern — where each module type is a Python function calling compiler primitives — with a declarative graph template schema. A module type would be defined entirely in JSON/YAML: nodes are MCU types, edges are trigger links, parameters are placeholders that the compiler fills at instantiation. The compiler treats all modules generically: read template, instantiate with fresh IDs and spatial offsets, validate bindings.

### Why It Matters

The current plan's Success Criterion 5 states: *"An external contributor can add a new module type using only the documentation — no core code changes needed."* With Python-class module definitions, "no core code changes" means the contributor must write Python that follows the existing pattern — this is achievable but has a learning curve. With declarative templates, the contributor writes JSON describing MCU graph topology and the compiler handles everything else. This lowers the barrier from "can write Python" to "understands IL-2 MCU logic."

### What Changes in the Current Plan

| Document | Change |
|---|---|
| `Phase6_Session_Prompt_Headers.md` | Session 6.3 (Contributor Documentation) R2 ("Adding a New Module Type") changes from "write a Python class" to "write a JSON template." The worked example ("Ferry Flight" module) becomes a JSON authoring walkthrough. |
| `MMO_Master_Project_Plan.md` | Add task 6.1a or similar: design and implement declarative module template schema + generic compiler instantiation. Tier 1. Depends on Phase 3 completion (pattern analysis required). |
| `ARCHITECTURE.md` | Add module template schema reference. Add `data/module_templates/` directory. Update compiler section to describe generic template instantiation. |
| `MMF_Specification_V2.md` | Section 3 (Module Architecture) updated to describe declarative module definitions. |
| `data/schemas/` | New schema file: `mmf-module-template-schema.json` defining the graph template format. |

### New Tasks Introduced

One new task in Phase 6 (or late Phase 5). Tier 1 — requires analyzing the Phase 3 module implementations to extract the common graph topology pattern and designing a schema expressive enough to capture all proven module behaviors.

### Contingency

**This proposal cannot be accepted until Phase 3 completes.** If Phase 3 reveals that module behavioral patterns are too divergent to generalize (e.g., Scramble's takeoff sequence and Bomber Escort's Cover/Attack toggle share no common graph structure), then the declarative schema is not viable and the Python-class pattern is the ceiling. In that case, reject this proposal and update Phase 6.3's contributor tutorial to document the Python-class extension pattern instead.

**Decision gate:** After Phase 3, before Phase 6 planning begins, review the four implemented module types (Intercept, Scramble, Ground Attack, Bomber Escort). If 3 of 4 share a common graph skeleton that differs only in parameterization, accept. If fewer than 3 share a skeleton, reject.

### FMEA Impact

Introduces a new potential failure mode: a declaratively-defined module template could specify an invalid MCU graph (dangling trigger links, missing required fields, cyclic dependencies). Mitigation: the compiler's existing PI-001 (required field validator) and the constraint validator (SCP-02, if accepted) catch these at compile time. If SCP-02 is rejected, compile-time validation must be added as part of this task's scope.

### Dependencies on Other Proposals

- **SCP-02 (constraint validator):** Enhances this proposal. If both are accepted, the constraint validator enforces FMEA compliance for declaratively-defined modules automatically. If SCP-02 is rejected, compile-time FMEA validation must be scoped into this task directly.
- Independent of SCP-01 and SCP-04.

### Disposition

| Decision | Rationale |
|---|---|
| ☐ Accept | |
| ☐ Reject | |
| ☐ Defer to post-Phase 3 review | |
| ☐ Modify | |

---

## SCP-04 — Read-Only Mission Preview Map in GUI

### Decision Deadline

Before Phase 5.5 (Orchestrator GUI) begins. Can be deferred to a post-5.5 task without blocking other work.

### What It Is

Add a read-only 2D map panel to the Orchestrator GUI that renders a top-down view of a generated mission: module placements, waypoint chains, front-line position, airfield locations, engagement zones, and AI patrol areas. The panel updates after each generation to show what the mission contains spatially. No editing capability — display only.

### Why It Matters

The current GUI (Phase 5.5) presents mission generation as a form: select map, scenario type, difficulty, weather, click Generate. The operator has no spatial feedback — they must load the `.Mission` file into BOSEditor to see where anything is placed. A preview map gives immediate visual confirmation that the scenario engine placed modules sensibly: intercept routes cross the front line, ground attack targets are behind enemy lines, patrol zones are in the right sector. This catches spatial errors before the in-game test cycle.

### What Changes in the Current Plan

| Document | Change |
|---|---|
| `Phase5_Session_Prompt_Headers.md` | Add task 5.5a (or expand 5.5): implement `MissionPreviewWidget` in `src/ui/gui/`. Renders map outline, airfield icons, front-line polyline, waypoint paths, and module placement zones. Input: the `MissionConfig` object produced by the scenario engine (5.3). No new data dependencies — all coordinates are already computed by the generation pipeline. |
| `MMO_Master_Project_Plan.md` | Add task row 5.5a. Tier 2 — standard PyQt6 widget implementation. Depends on 5.3 (needs `MissionConfig` with coordinates) and 4.2 (needs map boundary data for the canvas). |
| `ARCHITECTURE.md` | Add `MissionPreviewWidget` to GUI component listing. |

### New Tasks Introduced

One new task (5.5a). Tier 2 — PyQt6 2D rendering with coordinate transformation. No FMEA constraint reasoning required. Moderate scope: the widget renders existing data, does not generate new data.

### FMEA Impact

None. The preview is read-only and does not affect mission compilation or output. A rendering bug in the preview does not produce a bad mission file — it only misleads the operator's spatial understanding. This is low-severity and self-correcting (the operator discovers the discrepancy in BOSEditor or in-game).

### Dependencies on Other Proposals

- **SCP-01 (strategic targets):** If accepted, the preview map can render strategic target icons. Nice-to-have, not a dependency.
- Independent of SCP-02 and SCP-03.

### Disposition

| Decision | Rationale |
|---|---|
| ☐ Accept | |
| ☐ Reject | |
| ☐ Defer to post-5.5 | |
| ☐ Modify | |

---

## Proposal Dependency Map

```
SCP-01 (Phase 4 targets)      — Independent
SCP-02 (Constraint validator)  — Independent, but enhances SCP-03
SCP-03 (Module templates)      — Contingent on Phase 3 results; enhanced by SCP-02
SCP-04 (Preview map)           — Independent; enhanced by SCP-01

Prerequisite (C-004 amendment)  — Required by SCP-01; relevant to SCP-02 if validator
                                  reads constraint definitions from the database
```

No circular dependencies. SCP-01, SCP-02, and SCP-04 can each be accepted or rejected independently. SCP-03 has a hard dependency on Phase 3 completion and a soft dependency on SCP-02.

---

## Decision Timeline

| Proposal | Decide By | Rationale |
|---|---|---|
| **Prerequisite (C-004)** | Before Phase 4 begins | Standing conflict in current plan; blocking SCP-01 |
| **SCP-01** | Before Task 4.2 | Modifies extraction scope of an existing task |
| **SCP-02** | Before Task 5.3 | Shapes the scenario template architecture |
| **SCP-03** | After Phase 3 completes, before Phase 6 planning | Contingent on Phase 3 pattern analysis |
| **SCP-04** | Before Task 5.5 (or defer to post-5.5) | Modifies or extends the GUI task |

---

## Post-Acceptance Workflow

For each accepted proposal:

1. Generate a KEY_DECISION_LOG entry (next available number, currently #6+)
2. Update the affected documents listed in the proposal's change table
3. If the proposal introduces a new task: add a row to the Master Project Plan task registry, create a GitHub Issue with appropriate labels and milestone, and generate a session prompt header
4. If the proposal modifies an existing task: update the relevant session prompt header and task registry row
5. Move the proposal's disposition from "Proposed" to the selected option with rationale
6. When all four proposals have a disposition, close the tracking issue

---

## Revision History

| Date | Change | Author |
|---|---|---|
| March 20, 2026 | Initial proposal | Claude Opus 4.6 + GhengisPliskin |
