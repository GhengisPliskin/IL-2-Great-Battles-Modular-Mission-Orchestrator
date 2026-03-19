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

## DECISION 6 — Corpus Path in test_parser.py and test_serializer.py

**Status:** RESOLVED — Fix deferred to Phase 0.6

**Resolution:** `test_parser.py` (line 514) and `test_serializer.py` (line 589) both reference `'Group and Mission Examples'` as the local corpus directory — a stale pre-repo folder name. The correct path per `ARCHITECTURE.md` is `tests/fixtures/il2_files/`. The fix is a one-line `os.path.join` update in each file.

**Rationale:** The corpus directory was renamed when the project was structured into a proper repo. The test files predate that decision and were not updated. Deferring to Phase 0.6 (project scaffolding) where all path wiring is verified end-to-end.

**FMEA Impact:** None directly. However a broken corpus path silently returns an empty fixture set, which would cause corpus-dependent tests (0.2 round-trip, 0.4 catalog coverage) to pass vacuously. Fix must land before Phase 0.2 test suite is run against the corpus.

**Documents updated:**
- `KEY_DECISION_LOG.md` — this entry

**Downstream impact:**
- Phase 0.6 session must update `_get_corpus_files()` in both test files to reference `tests/fixtures/il2_files/`
- `.gitignore` already excludes `tests/fixtures/il2_files/` — corpus files must be added manually by the project owner after cloning
