# Key Decisions — Resolution Log

**Status:** All decisions RESOLVED

---

## DECISION 1 — Phase 3 Human Gates for Ground Attack and Bomber Escort

**Status:** RESOLVED — Option C selected

**Resolution:** Add both 3.3h (Ground Attack in-game test) and 3.4h (Bomber Escort in-game test). Every module type gets an individual in-game flight test before cross-module integration at Gate 3.5. Phase 3 total: 4 AI sessions, 5 human gates.

**Rationale:** Consistent verification policy — each module is individually proven in-game before integration testing. Isolates failures to the specific module session rather than requiring debugging during multi-module 3.5 integration. Higher human time cost is justified by reduced debugging cost if any module has defects.

**FMEA Impact:** None

**Documents updated:**
- `Phase3_Session_Prompt_Headers.md` — header count, task table, dependency text, ASCII diagram, 3.3h section added, 3.4h section added, Gate 3.5 depends-on updated, execution sequence updated, Session 3.3 and 3.4 Delivers To updated

**Downstream impact:**
- Master Project Plan Phase 3 description says "4 human gates" — now correct (was previously inconsistent with 3-gate headers)
- Master Project Plan total: 37 AI + 17 human = 54 total tasks (was 52 — increase of 2 human gates)
- ARCHITECTURE_patches.md: no change needed (ARCHITECTURE.md does not enumerate human gates)

---

## DECISION 2 — Parser Module Name Coupling (0.2 ↔ 0.6)

**Status:** RESOLVED — Option A selected, expanded to include test file

**Resolution:** Added R5 (Module and Test File Naming) to Session 0.2 in Phase 0 headers. The parser module SHALL be named `deserializer.py` at `src/mmf/parser/deserializer.py`. The unit test file SHALL be named `test_parser.py` at `src/mmf/parser/tests/test_parser.py`. Both names are pinned to match `ARCHITECTURE.md` and prevent drift from Session 0.6's hardcoded import verification.

**Rationale:** Prevents name coupling drift between the parser implementation (0.2) and the scaffolding verification (0.6). Pinning both names in the earliest session ensures all downstream consumers reference the same module path.

**FMEA Impact:** None

**Documents updated:**
- `Phase0_Session_Prompt_Headers.md` — Session 0.2: R5 added, two acceptance criteria added to Exit Condition

**Downstream impact:**
- ARCHITECTURE_patches.md: no change needed (ARCHITECTURE.md already names `deserializer.py`; `test_parser.py` is additive alongside the existing `test_roundtrip.py`)
- Session 0.6 import verification command (`from mmf.parser import deserializer`) is now explicitly backed by Session 0.2 R5

---

## DECISION 3 — Phase 2 MRE Override Note Removal

**Status:** RESOLVED — Note removed

**Resolution:** Removed the `> **Note:**` block from the Phase 2 Overview (Session 2.1 area) that flagged the ARCHITECTURE.md MRE tier discrepancy. This note becomes stale once ARCHITECTURE.md Patch 6 is applied (correcting MRE from Tier 2 to Tier 1).

**Rationale:** Stale notes in prompt headers introduce conflicting guidance. The note was a temporary flag; once the underlying issue (ARCHITECTURE.md Patch 6) is resolved, the flag must be removed to prevent confusion.

**FMEA Impact:** None

**Documents updated:**
- `Phase2_Session_Prompt_Headers.md` — Overview section: removed the `> **Note:**` callout block

**Downstream impact:**
- Contingent on ARCHITECTURE.md Patch 6 being applied in the separate ARCHITECTURE.md session. If Patch 6 is not applied, the note removal is premature. The note has been removed on the assumption that Patch 6 will be applied.

---

## DECISION 4 — Master Project Plan Total Task Count

**Status:** RESOLVED — Counts updated below for reference

**Resolution:** Corrected counts (post-Decision 1):
- Phase 3: 4 AI sessions, 5 human gates, 9 total tasks
- Project total: 37 AI sessions, 17 human gates, 54 total tasks

The Master Project Plan document (`MMO_Master_Project_Plan.docx`) states "37 AI tasks, 15 human gates, 52 total tasks." This should be corrected to 37 AI + 17 human = 54 total if the Plan is republished. The per-phase description for Phase 3 ("Contains 4 human gates") is now correct and matches the updated headers.

**Rationale:** Accurate task counts are required for project tracking and resource planning. The discrepancy arose from Decision 1 adding two human gates.

**FMEA Impact:** None

**Documents updated:**
- None (informational — Master Project Plan is a .docx managed separately)

**Downstream impact:**
- Master Project Plan total task count must be updated from 52 to 54 when republished

---

## DECISION 5 — `data/mcu_catalog.json` Location

**Status:** RESOLVED — No action required

**Resolution:** Confirmed consistent. `data/mcu_catalog.json` is at the `data/` root per both ARCHITECTURE.md and Session 0.4. The JSON schema is under `data/schemas/` — different subdirectory, no conflict. Noted for Session 0.6 scaffolding: the catalog is NOT under a subdirectory.

**Rationale:** Location consistency check prevents Session 0.6 scaffolding from creating the catalog in the wrong directory. Confirmed no conflict between `data/mcu_catalog.json` and `data/schemas/mmf-module-schema-v2_0.json`.

**FMEA Impact:** None

**Documents updated:**
- None

**Downstream impact:**
- Session 0.6 scaffolding must place `mcu_catalog.json` at `data/mcu_catalog.json`, not under `data/schemas/`

---

## DECISION 6 — Code Comment Standard Adopted (Ground Rule 11)

**Status:** RESOLVED — Standard adopted, constraints registered, all scaffold documents updated

**Resolution:** A binding code comment standard is established for all AI sessions and all code produced in this project. The standard requires four comment types in every `.py` file: a module-level docstring (MODULE / PURPOSE / FMEA / PHASE), a function docstring on every public function (WHAT / WHY / ARGS / RETURNS / FMEA), a plain-English block comment above every non-trivial logic block, and a Why-Not comment wherever a constraint forces a non-obvious implementation choice. Silent removal of existing comments is prohibited in all task types including refactoring, reformatting, and test writing. Comment presence and preservation are standing acceptance criteria on every session prompt header — they do not require individual negotiation per task.

**Rationale:** AI coding sessions optimize for clean output and will strip or thin comments unless explicitly prohibited. The IL-2 engine has non-obvious runtime behaviors (timer pause semantics, counter non-reset, entity binding races) that must be explained at the point of implementation. A reader — human or AI — arriving in a new session without project history must be able to understand what a block does, why it was written that way, and which engine constraint it is protecting against. Self-documenting code is insufficient for this project's constraint density.

**FMEA Impact:** None to existing constraints. Four new code quality constraints registered: C-019 (module docstrings), C-020 (function docstrings), C-021 (block comments), C-022 (comment preservation). These compound with all existing FMEA constraints — any file that implements an FMEA constraint must also satisfy C-019 through C-022.

**Documents updated:**
- `ARCHITECTURE.md` — New "Code Comment Standard" section added with full format specification, four comment type templates, and five preservation rules. Glossary and "What This Architecture Solves" intro paragraphs added. `CLAUDE.md` and `CONTRIBUTING.md` added to root directory structure.
- `CONSTRAINTS.md` — C-002 updated to reflect GUI framework as pending decision (not locked to PyQt6). New Section 5 added with C-019 through C-022.
- `CONTRIBUTING.md` — New file created at repo root. Contains full comment standard, contribution workflow for AI and human sessions, and ground rules reference table.
- `CLAUDE.md` — New file created at repo root. Ground Rule 11 added to ground rules table. Comment standard summary and templates included.
- `SKILL.md` — Ground Rule 11 added to operational ground rules table. Phase 3 documentation audit step expanded to include comment presence and preservation checks. `CLAUDE.md` and `CONTRIBUTING.md` added to scaffolding file inventory.
- `docs/templates/GitHub_Project_Planner_Templates.md` — SESSION_PROMPT_HEADER acceptance criteria block updated with four standing comment criteria. README skeleton updated to include `CLAUDE.md` and `CONTRIBUTING.md`, ground rules count corrected to 11.
- `docs/templates/GitHub_Project_Planner_Master_Plan_Template.md` — NFR-002 row added for code quality. `CLAUDE.md` and `CONTRIBUTING.md` added to directory structure template.
- `README.md` — "What This Is" and "Project Status" sections added for readers unfamiliar with the project. Documentation table updated with `CONTRIBUTING.md` and improved FMEA description. Ground Rules blurb updated to 11 rules.

**Downstream impact:**
- All future session prompt headers generated from the SESSION_PROMPT_HEADER template will automatically include the four standing comment acceptance criteria.
- All future projects scaffolded from the GitHub Project Planner skill will generate `CLAUDE.md` and `CONTRIBUTING.md` as standard scaffold files.
- A compliance audit prompt system has been designed but deferred. Implementation trigger: Phase 0.3 HUMAN gate review reveals comment compliance gaps despite Ground Rule 11 being present. See `working/DEFERRED_compliance_audit_prompt.md` for full design specification.
- GUI framework decision (C-002) remains open. Formal KEY_DECISION_LOG entry required when framework is confirmed before Phase 2.
