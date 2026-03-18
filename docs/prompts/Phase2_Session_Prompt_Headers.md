# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 2 — GUI + Module Reverse Engineer
### Session Prompt Headers
*User-facing module constructor + validation corpus (parallel tracks)*

**6 AI Sessions | 2 Human Gates | Task IDs 2.1 – 2.6**

---

## Phase 2 Overview

Phase 2 produces the Module Reverse Engineer (MRE) and the PyQt6 GUI in two parallel tracks. Track A (MRE: 2.1 → 2.2) builds the .Group-to-JSON reverse-engineering pipeline and validates compiler output against hand-built reference files. Track B (GUI: 2.3 → 2.4 → 2.5 → 2.6) builds the user-facing module constructor that outputs JSON for the compiler. The tracks converge at task 2.2, which requires both the MRE and the compiler to produce the validation corpus.

Tasks 2.1 and 2.2 are Tier 1 (Opus 4.6) — the MRE must recognize and validate all 14 FMEA constraints in hand-built .Group files, requiring cross-constraint reasoning across the full specification. Tasks 2.3–2.6 are Tier 2 (Sonnet 4.6) — standard PyQt6 GUI implementation with well-defined schemas.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 2.1 | Build Module Reverse Engineer (.Group → MMF JSON + audit) | MRE | AI | Tier 1: Opus 4.6 |
| 2.1h | Provide 5+ hand-built .Group files (validation corpus input) | Data | HUMAN | N/A |
| 2.2 | Build validation corpus: MRE vs. compiler cross-diff | MRE + Compiler | AI | Tier 1: Opus 4.6 |
| 2.3 | Build GUI shell: PyQt6 app with module selection + compile button | GUI | AI | Tier 2: Sonnet 4.6 |
| 2.4 | Implement Static CAP parameter form | GUI | AI | Tier 2: Sonnet 4.6 |
| 2.5 | Implement JSON export with reserved-char sanitization + compile wiring | GUI | AI | Tier 2: Sonnet 4.6 |
| 2.5h | IN-GAME TEST: GUI-compiled module vs. CLI baseline | Testing | HUMAN | N/A |
| 2.6 | Add calculated AI cap display (EC-004) | GUI | AI | Tier 2: Sonnet 4.6 |

**Dependency order:** Track A and Track B are independent until convergence. Track A: 2.1 depends on Phase 0 outputs (0.2, 0.4). 2.1h has no dependency (human provides files). 2.2 requires 2.1, 2.1h, and 1.10 (compiler output for cross-diff). Track B: 2.3 depends on 0.5 (JSON schema). 2.4 depends on 2.3. 2.5 depends on 2.4 and 1.10 (compiler integration). 2.6 depends on 2.4. 2.5 and 2.6 can run in parallel after 2.4 completes.

---

## Session 2.1 — Module Reverse Engineer

| | |
|---|---|
| **Task ID** | 2.1 |
| **Component** | Module Reverse Engineer (`src/backend/mre/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 0.2 (parser library — reads .Group ASCII), 0.4 (MCU type catalog — required field definitions) |
| **Delivers To** | 2.2 (validation corpus — MRE output is one side of the diff) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/mre/`, FMEA Constraints table (all 14 constraints are detection targets) |

### Role

You are a Principal Python Systems Developer specializing in reverse engineering and structural analysis. You are building the MMF Module Reverse Engineer — a tool that reads hand-built IL-2 .Group files, classifies the MCU logic patterns within them, extracts them into the MMF JSON schema, and produces a structured audit report identifying FMEA constraint violations.

### Context

The Module Reverse Engineer (MRE) is the inverse of the compiler. The compiler takes JSON and emits IL-2 ASCII. The MRE takes IL-2 ASCII and infers the JSON representation. Its primary purpose is twofold: (1) it enables the validation corpus (task 2.2) by providing a machine-readable decomposition of hand-built .Group files that can be diffed against compiler output; (2) it gives mission designers a way to import existing work into the MMF ecosystem.

The MRE does not need to handle arbitrary .Group files from the wild. Its scope is .Group files that implement patterns recognized by the MMF architecture: formation flights, Magazine Array wave management, Command Buffers, Entity proxy bindings, GC chains, and I/O proxy nodes. Files that don't map to any recognized pattern should produce a structured "unrecognized" classification, not crash the tool.

The constraint validation capability is the MRE's most architecturally significant feature. The MRE must check every recognized pattern against the 14 FMEA constraints and flag violations. This is what makes it a Tier 1 task — the MRE must hold the full FMEA constraint set in working memory while classifying MCU structures.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All 14 FMEA constraints are detection targets: PI-001 through PI-004, EL-001 through EL-003, SM-001 through SM-004, EC-001 through EC-004
> - Section 2.1: JSON Intermediary — the MRE outputs this schema
> - Section 4.2: Entity proxy binding rules (MRE must detect and validate)
> - Section 5.2: Magazine Array pattern (MRE must recognize Activate/Deactivate vs. Spawn)
> - Section 5.3: GC chain structure (MRE must detect dual-path vs. single-path)

### Inputs

- Phase 0 outputs: parser library (`src/mmf/parser/`), MCU type catalog
- JSON schema (`src/mmf/schema/mmf-module-schema-v2_0.json`) — MRE output must validate against this
- FMEA constraint definitions from `MMF_FMEA_Report_v2.docx` — detection rules
- Hand-built .Group files (provided at 2.1h) for testing once available

### Requirements

**R1 — .Group Parser Integration**

Use the existing parser library (task 0.2) to read .Group files into Python dictionaries. The MRE does not reimplement parsing — it consumes the parser's output and performs semantic analysis on the resulting dictionary.

**R2 — Pattern Classifier**

Classify MCU structures into recognized MMF patterns:
- **Formation flight:** Aircraft blocks with Target Link hierarchies and Enabled state
- **Magazine Array:** MCU_Counter with sequential Activate targets on deactivated flights
- **Command Buffer:** MCU_Deactivate → MCU_Timer → MCU_Activate chains
- **Entity proxy:** MCU_TR_Entity blocks with MisObjID/LinkTrId bindings
- **GC chain:** Despawn chains triggered by OnKilled or ToS timer
- **I/O proxy nodes:** 0-second MCU_Timer blocks at user-visible coordinates (identified by naming convention `[IN]_`, `[OUT]_`, `[CFG]_`)
- **Waypoint loop:** Command:Waypoint chains with terminal-to-initial linking
- **AttackArea:** MCU_CMD_AttackArea with populated Targets array

Patterns that don't match any known classification are tagged `"pattern": "unrecognized"` with the raw MCU type and connection graph preserved.

**R3 — JSON Extraction**

For each recognized module pattern, emit a JSON representation conforming to the MMF schema (`mmf-module-schema-v2_0.json`). The extraction must populate: `module_type`, `coalition`, `flight` parameters, `magazine` parameters, `waypoints`, `attack`, `proxy_coordinates`, and `wiring`.

**R4 — FMEA Constraint Audit**

For each recognized pattern, validate against all applicable FMEA constraints. The audit report must list:
- Constraint ID and severity
- PASS / VIOLATION / NOT_APPLICABLE disposition
- For violations: the specific MCU Index values involved, the expected value, and the actual value
- Summary count: total constraints checked, passed, violated, not applicable

**R5 — Public API**

```python
class ModuleReverseEngineer:
    def __init__(self, schema_path: str)
    def analyze_file(self, group_path: str) -> MREResult
    def analyze_dict(self, parsed_data: dict) -> MREResult

@dataclass
class MREResult:
    modules: list[ExtractedModule]    # Recognized module patterns → JSON
    audit: AuditReport                # FMEA constraint check results
    unrecognized: list[dict]          # MCU structures that didn't classify
    source_file: str
```

**R6 — CLI Entry Point**

Provide a CLI at `src/backend/mre/cli.py`:

```bash
python -m backend.mre.cli analyze path/to/file.group --output report.json
python -m backend.mre.cli audit path/to/file.group   # constraint check only
```

> **[EL-003] — CRITICAL** The MRE must detect Entity proxy binding violations: (1) Entity.MisObjID != Aircraft.Index, (2) Aircraft.LinkTrId != Entity.Index, (3) Entity.MisObjID == Entity.Index (self-reference). Any of these in a hand-built file must appear as a VIOLATION in the audit report.

> **[EL-001] — CRITICAL** The MRE must detect Magazine Array counter misconfiguration: Reset After Operation = FALSE, counter deactivation links present, wave_count insufficient for session duration (wave_count < ceil(180 / ToS)).

> **[EC-003] — HIGH** The MRE must detect use of MCU_CMD_Spawn for formation-based flight activation. If a Spawner trigger targets an aircraft that has Target Link associations, this is a VIOLATION.

> **[SM-002] — HIGH** The MRE must detect RTB/Waypoint commands that Object Link only to the formation leader (not all flight members). Single-target RTB on a multi-aircraft flight is a VIOLATION.

> **EXIT CONDITION — Acceptance Criteria**
> - `analyze_file()` runs on all parser test fixtures without exception
> - Recognized patterns (formation flight, Magazine Array, Command Buffer, Entity proxy, GC chain, I/O proxy) are correctly classified in at least one test file
> - JSON extraction output validates against the MMF schema
> - Constraint audit correctly identifies at least one injected PI-003 violation (duplicate Index), one EL-003 violation (broken Entity binding), and one EC-003 violation (Spawn on formation)
> - Unrecognized MCU structures are preserved in the output (not silently dropped)
> - CLI runs and produces a valid JSON audit report

---

## Session 2.2 — Validation Corpus

| | |
|---|---|
| **Task ID** | 2.2 |
| **Component** | MRE + Compiler (`src/backend/mre/`, `src/mmf/compiler/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 1.10 (compiler — produces .Group from JSON), 2.1 (MRE — produces JSON from .Group), 2.1h (hand-built .Group files — the reference corpus) |
| **Delivers To** | Phase 3 (module types — validated compiler patterns), 2.5 (GUI compile wiring — confidence that compiler is correct) |
| **Reference** | See `ARCHITECTURE.md` — all FMEA Constraints active as detection targets; Phase Mapping → Phase 2; Directory Structure → `src/backend/mre/` and `src/mmf/compiler/` |

### Role

You are a Principal Python Systems Developer and validation engineer. Your task is to build the cross-validation pipeline that proves compiler correctness by diffing compiler output against hand-built reference .Group files. Every discrepancy must be classified as either a compiler bug or a hand-built deviation.

### Context

The validation corpus is the bridge between human-authored mission logic and machine-generated mission logic. The pipeline works in two directions:

1. **Forward path:** Take a hand-built .Group file → reverse-engineer it with the MRE → extract the JSON representation → recompile it with the compiler → diff the compiler's .Group output against the original hand-built file.

2. **Reverse path:** Take the MRE's JSON extraction → validate it against the schema → check that the extraction accurately represents the hand-built file's logic structure.

Every discrepancy in the forward path falls into one of two categories: (a) the compiler emits different IL-2 syntax for equivalent logic — this is a compiler bug that must be fixed; (b) the hand-built file uses a pattern that deviates from the MMF architecture (e.g., uses MCU_CMD_Spawn for formations, reuses timers, omits GC chains) — this is a hand-built deviation that the FMEA audit should have flagged.

The validation corpus is the safety net. A compiler that passes its unit tests but fails the corpus diff has a bug that unit tests didn't cover. This is how implementation errors in Phase 1 get caught before they reach Phase 3 module expansion.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All 14 FMEA constraints are active simultaneously — discrepancies may trace to any constraint
> - Section 6.1: Initial Validation Prototype — Static CAP description (primary comparison target)
> - Section 2.1: JSON Intermediary — the schema is the contract between MRE extraction and compiler input
> - Section 2.2: Syntax Agnosticism — format differences (whitespace, ordering) are not semantic errors

### Inputs

- Task 1.10 output: the working Static CAP compiler and its sample .Group output
- Task 2.1 output: the Module Reverse Engineer
- Task 2.1h output: 5+ hand-built .Group files of varying complexity
- Parser library and JSON schema from Phase 0

### Requirements

**R1 — Corpus Pipeline**

Implement the cross-validation pipeline:

```python
class ValidationCorpus:
    def __init__(self, compiler, mre, schema_path: str)
    def validate_file(self, group_path: str) -> CorpusResult
    def validate_corpus(self, corpus_dir: str) -> list[CorpusResult]
```

For each .Group file:
1. Parse with the IL-2 parser (Phase 0.2)
2. Reverse-engineer with the MRE (Phase 2.1) → extracted JSON
3. Validate extracted JSON against the schema
4. Compile extracted JSON with the compiler (Phase 1.10) → recompiled .Group
5. Diff original .Group against recompiled .Group (structural, not textual)
6. Classify each discrepancy

**R2 — Structural Diff Engine**

The diff must be structural, not textual. Two .Group files that are logically equivalent but differ in:
- Whitespace or indentation
- Block ordering (MCU blocks appear in different sequence)
- Index values (different ID assignments)

...must compare as EQUIVALENT. The diff operates on the parsed dictionary representation, not raw text. ID remapping is required: the diff must detect that original ID 5 maps to recompiled ID 101 and treat all downstream references consistently.

**R3 — Discrepancy Classification**

Each discrepancy must be classified:
- `COMPILER_BUG`: the compiler emits structurally incorrect output for a pattern the MRE correctly extracted. This blocks Phase 3 until fixed.
- `HAND_BUILT_DEVIATION`: the hand-built file uses a pattern that violates an FMEA constraint. The MRE audit should have flagged this. The compiler correctly refuses to reproduce the violation.
- `EXTRACTION_ERROR`: the MRE incorrectly classified or extracted a pattern from the hand-built file. The diff fails because the MRE fed bad JSON to the compiler.
- `EQUIVALENT`: no semantic difference after structural normalization.

**R4 — Report Output**

Generate a JSON report per file and a summary report for the full corpus:

```python
@dataclass
class CorpusResult:
    source_file: str
    mre_audit: AuditReport           # From task 2.1
    schema_valid: bool                # Extracted JSON passes schema check
    discrepancies: list[Discrepancy]  # Structural diff results
    classification_summary: dict      # Count per classification type
```

**R5 — Regression Test Integration**

Generate pytest fixtures from the corpus results. Each hand-built file that produces a `COMPILER_BUG` discrepancy becomes a regression test case in `src/mmf/compiler/tests/`. Each file that produces `EQUIVALENT` becomes a golden-file test case.

> **EXIT CONDITION — Acceptance Criteria**
> - Every hand-built .Group file in the 2.1h corpus is processed without pipeline crash
> - Every discrepancy is classified as COMPILER_BUG, HAND_BUILT_DEVIATION, EXTRACTION_ERROR, or EQUIVALENT
> - At least one hand-built file produces EQUIVALENT result (proves the full forward path works)
> - Any COMPILER_BUG discrepancies are documented with the specific MCU structures involved, the expected output, and the actual output — sufficient for a developer to locate and fix the bug
> - Corpus summary report is generated as JSON
> - Regression test fixtures are generated for all EQUIVALENT and COMPILER_BUG cases

---

## Session 2.3 — GUI Shell

| | |
|---|---|
| **Task ID** | 2.3 |
| **Component** | GUI (`src/ui/gui/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 0.5 (JSON schema — defines the form structure the GUI must produce) |
| **Delivers To** | 2.4 (Static CAP form), 2.5 (compile wiring), 2.6 (AI cap display) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/ui/gui/`, Phase Mapping → Phase 2 |

### Role

You are a Senior Python GUI Developer specializing in PyQt6 desktop applications. You are building the shell application that hosts all module parameter forms and compiler integration for the MMF.

### Context

The GUI is Layer 3 (User-Facing Applications) of the three-layer architecture. It reads the JSON schema to determine available module types and their parameters, renders dynamic forms, collects user input into a JSON payload conforming to the schema, and passes that payload to the compiler for .Group file generation. The GUI does not contain any compiler logic — it is a pure frontend that communicates exclusively through the JSON contract.

Phase 2 builds the shell and the first module form (Static CAP). Phase 3 adds additional module type forms. Phase 5 extends the GUI for orchestrator scenario configuration. The shell must be designed for this incremental growth.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.1: JSON Intermediary — the GUI outputs this; the schema is the interface contract
> - Section 1: Project Objective — "UI-driven generation tool"
> - `ARCHITECTURE.md` → `src/ui/gui/` directory structure: `main_window.py`, `module_editor.py`, `schema_widgets.py`, `compiler_output.py`, `dialogs/`

### Inputs

- JSON schema (`src/mmf/schema/mmf-module-schema-v2_0.json`) — defines all form fields and validation rules
- Sample payload (`data/module_templates/static_cap.json`) — reference output the form must be capable of producing

### Requirements

**R1 — Main Window Layout**

PyQt6 `QMainWindow` with:
- **Left pane:** Module list (tree or list widget). Initially contains only "Static CAP". Extensible — Phase 3 adds module types here.
- **Center pane:** Dynamic parameter form area. Renders the form for the selected module type.
- **Bottom bar:** "Compile" button, "Export JSON" button, status bar.
- **Menu bar:** File (New, Open JSON, Save JSON, Exit), Help (About).

**R2 — Module Type Registry**

A registry pattern that maps `module_type` strings to form builder classes:

```python
MODULE_FORMS: dict[str, type[ModuleFormBase]] = {
    "static_cap": StaticCAPForm,
    # Phase 3 adds: "intercept": InterceptForm, "scramble": ScrambleForm, etc.
}
```

Adding a new module type requires only: (1) subclass `ModuleFormBase`, (2) register in the dictionary. No changes to `main_window.py`.

**R3 — Schema-Driven Validation**

All form field constraints (min/max, enum values, required fields) are read from the JSON schema at startup, not hardcoded. If the schema changes, the form validation updates without code changes. Use `jsonschema` for validation of the assembled payload before compilation.

**R4 — JSON Export**

"Export JSON" serializes the current form state to a `.json` file conforming to the MMF schema. The exported file must pass `jsonschema.validate()` against the schema. If validation fails, display errors in the status bar and do not write the file.

**R5 — Compiler Output Panel**

A dockable output panel (`compiler_output.py`) that displays:
- Compiler stdout/stderr
- Compilation warnings (EC-001 entity count, EL-001 wave count)
- Success/failure status with the output .Group file path

> **EXIT CONDITION — Acceptance Criteria**
> - Application launches without error (`python -m ui.gui`)
> - Module type list displays "Static CAP"
> - Selecting "Static CAP" renders a form in the center pane (field content is task 2.4)
> - "Export JSON" produces a valid JSON file that passes schema validation
> - "Compile" button is present and wired to a placeholder (actual wiring is task 2.5)
> - New module type can be added by subclassing `ModuleFormBase` and registering — no main_window changes

---

## Session 2.4 — Static CAP Parameter Form

| | |
|---|---|
| **Task ID** | 2.4 |
| **Component** | GUI (`src/ui/gui/module_editor.py`, `src/ui/gui/schema_widgets.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 2.3 (GUI shell — provides the form framework and registry) |
| **Delivers To** | 2.5 (compile wiring — the form produces the JSON payload the compiler consumes), 2.6 (AI cap display — reads flight_size and wave_count from this form) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/ui/gui/`; FMEA Constraints → EL-001 (wave count validation), EC-004 (AI cap display) |

### Role

You are a Senior Python GUI Developer. You are implementing the first module parameter form — Static CAP — within the GUI shell built in task 2.3. The form collects all parameters defined in the JSON schema for a `static_cap` module and validates them before export or compilation.

### Context

The Static CAP form is the template for all future module forms. Every field maps to a specific JSON schema property under `modules[].flight`, `modules[].magazine`, `modules[].waypoints`, `modules[].attack`, and `modules[].proxy_coordinates`. The form must enforce the schema's constraints (ranges, enums, required fields) at the widget level so the user gets immediate feedback, not just a schema validation error at export time.

The session formula validation (EL-001) and the AI cap warning (EC-004) are the two FMEA-relevant GUI behaviors in this task. Both are display-only — the GUI warns but does not block compilation.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EL-001] CRITICAL — `wave_count >= ceil(session_duration_minutes / ToS)`. GUI validates this formula and warns if insufficient.
> - [EC-004] HIGH — `max_concurrent_AI = flight_size × max_simultaneous_waves`. GUI warns if > 80. (Display implementation is task 2.6; form must expose the underlying field values.)
> - Section 5.2.2: Counter Behavior & Session Sizing — wave count formula
> - JSON schema `modules[].flight`, `modules[].magazine`, `modules[].waypoints`, `modules[].attack` property definitions

### Inputs

- Task 2.3 output: GUI shell with form framework and `ModuleFormBase`
- JSON schema: field definitions, types, ranges, enums
- Sample payload (`data/module_templates/static_cap.json`): the target output

### Requirements

**R1 — Flight Parameters Group**

Form fields with schema-driven constraints:
- `aircraft_type`: dropdown (enum from schema or type catalog)
- `ai_skill`: dropdown (enum: low, normal, high, ace)
- `country`: dropdown (enum by coalition)
- `flight_size`: spinbox (int, range from schema, typically 1–4)
- `payload_id`: text input (validated against known payload IDs if available, or free-text)
- `fuel`: slider + spinbox (float, 0.1–1.0, step 0.1)
- `skin`: text input or file browser
- `starting_location`: coordinate input (X, Z)
- `spawn_altitude`: spinbox (int, meters)

**R2 — Magazine Parameters Group**

- `wave_count`: spinbox (int, 1–50)
- `time_on_station_minutes`: spinbox (int, min 1)
- `gc_despawn_delay_seconds`: spinbox (int, default 30)

**R3 — Session Formula Validation (EL-001)**

When `wave_count` or `time_on_station_minutes` changes, calculate:

```
required_waves = ceil(session_duration_minutes / time_on_station_minutes)
```

Where `session_duration_minutes` comes from `compiler_options.session_duration_minutes` (default 180). If `wave_count < required_waves`, display a persistent warning label:

> ⚠ Wave count ({wave_count}) is less than ceil({session_duration} / {ToS}) = {required_waves}. Magazine will exhaust before session ends.

**R4 — Waypoint Editor**

A table widget for `waypoints.points[]`:
- Columns: X, Z, Altitude, Speed, Area (optional)
- Add/remove row buttons
- `waypoints.loop`: checkbox (links last waypoint back to first)
- `waypoints.priority`: dropdown (low, medium, high)

**R5 — Attack Parameters**

- `attack.attack_type`: dropdown (enum)
- `attack.area_radius`: spinbox (int, meters)
- `attack.targets`: coordinate table (X, Z — must be non-empty per PI-001)

**R6 — Proxy Coordinates**

- `proxy_coordinates.x`: spinbox (float)
- `proxy_coordinates.z`: spinbox (float)

These are the coordinates where the module's I/O proxy nodes will appear in BOSEditor.

> **[EL-001] — CRITICAL** The wave count session formula warning must be visible immediately on form load when defaults produce an insufficient wave count. The warning updates dynamically as the user adjusts `wave_count` or `time_on_station_minutes`.

> **EXIT CONDITION — Acceptance Criteria**
> - All fields from the JSON schema's `static_cap` module definition are represented in the form
> - Every field enforces its schema-defined range (no out-of-range values accepted)
> - Form state serializes to JSON that validates against the schema
> - Session formula warning triggers when `wave_count < ceil(180 / ToS)` (e.g., wave_count=5 with ToS=10 warns because ceil(180/10) = 18)
> - Session formula warning clears when the user corrects the values
> - Waypoint table supports add/remove and produces a valid `waypoints.points[]` array
> - Empty `attack.targets` triggers a PI-001 validation error on export

---

## Session 2.5 — JSON Export + Compile Wiring

| | |
|---|---|
| **Task ID** | 2.5 |
| **Component** | GUI (`src/ui/gui/main_window.py`, `src/ui/gui/compiler_output.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 2.4 (Static CAP form — produces the JSON payload), 1.10 (compiler — consumes the JSON payload and emits .Group) |
| **Delivers To** | 2.5h (in-game test — the GUI-compiled .Group is what gets flown) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/ui/gui/`, `src/mmf/compiler/`; FMEA Constraints → PI-002 (reserved-char filter at export) |

### Role

You are a Senior Python Developer. You are wiring the GUI's export and compilation pipeline — the last mile that connects the form to the compiler and produces a flyable .Group file.

### Context

The "Compile" button is the user's primary interaction endpoint. It must: (1) assemble the current form state into a valid JSON payload, (2) apply reserved-character sanitization per PI-002, (3) pass the payload to the MMF compiler, (4) capture compiler output (warnings, errors, success), and (5) display results in the compiler output panel. The "Export JSON" button performs steps 1–2 only and writes the sanitized JSON to disk.

The end-to-end workflow is: GUI → JSON → Compiler → .Group → BOSEditor. This session closes the loop. The acceptance gate is that a GUI-compiled .Group file behaves identically to a CLI-compiled .Group file for the same parameters.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [PI-002] HIGH — Reserved-character filter: `{}[];="` stripped from all string fields. The compiler applies its own filter, but the GUI must also sanitize before export to prevent schema validation failures on strings containing reserved characters.
> - Section 2.1: JSON Intermediary — the GUI outputs the JSON contract; the compiler consumes it
> - Section 3.1: Compiler Validation — PI-001 required-field checks happen compiler-side; GUI displays the result

### Inputs

- Task 2.4 output: Static CAP parameter form with complete form state
- Task 1.10 output: working MMF compiler (`src/mmf/compiler/compiler.py`)
- JSON schema for pre-export validation

### Requirements

**R1 — JSON Assembly**

Collect all form widget values into a Python dictionary matching the MMF schema structure. The dictionary must include:
- `mmf_version`: from application config
- `output_mode`: "group" (default for module compilation)
- `compiler_options`: from a separate compiler options dialog or defaults
- `modules[]`: array containing the current module's parameters

**R2 — Reserved-Character Sanitization (PI-002)**

Before schema validation and before passing to the compiler, apply the reserved-character filter to all string-type values in the assembled dictionary:
- Strip characters: `{ } [ ] ; = "`
- Log each stripped character with the field path (e.g., `modules[0].flight.skin: stripped '"' at position 5`)
- Display strip count in the status bar if any characters were removed

**R3 — Schema Validation Gate**

Validate the assembled (and sanitized) JSON against the schema using `jsonschema.validate()`. If validation fails:
- Display all validation errors in the compiler output panel
- Do NOT invoke the compiler
- Highlight the offending form fields if identifiable from the error path

**R4 — Compiler Invocation**

Call the compiler programmatically (not via subprocess):

```python
from mmf.compiler.compiler import compile_module

result = compile_module(payload_dict, output_path=user_selected_path)
```

Capture:
- Compiler warnings (EC-001 entity count, EL-001 wave count, etc.)
- Compiler errors (PI-001 missing fields, EL-003 binding failures, etc.)
- Output .Group file path on success

Display all output in the compiler output panel with severity-appropriate formatting (warnings in amber, errors in red, success in green).

**R5 — Export JSON (No Compile)**

"Export JSON" performs R1 + R2 + R3 only. On success, opens a file save dialog and writes the sanitized, validated JSON to the selected path.

**R6 — Output File Handling**

On successful compilation:
- Display the .Group output file path in the output panel
- Offer a "Open in Explorer" button to navigate to the output directory
- Store the last compilation output path for quick re-access

> **[PI-002] — HIGH** The reserved-character filter is defense-in-depth. The compiler has its own filter (task 1.8), but the GUI must sanitize before export so that: (a) the exported JSON is clean for manual inspection, and (b) string fields don't cause unexpected schema validation failures. Both filters must exist independently.

> **EXIT CONDITION — Acceptance Criteria**
> - "Compile" button produces a .Group file from the GUI form state
> - GUI-compiled .Group file is byte-equivalent (whitespace-normalized) to CLI-compiled .Group file for the same JSON payload
> - Reserved characters in string fields are stripped before export/compile; strip actions are logged
> - Schema validation errors block compilation and display in the output panel
> - Compiler warnings (EC-001, EL-001) display in the output panel
> - "Export JSON" produces a valid, sanitized JSON file
> - End-to-end: GUI → Compile → BOSEditor import succeeds (verified at 2.5h)

---

## Session 2.6 — Calculated AI Cap Display

| | |
|---|---|
| **Task ID** | 2.6 |
| **Component** | GUI (`src/ui/gui/module_editor.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 2.4 (Static CAP form — provides the flight_size and wave_count values) |
| **Delivers To** | Phase 3 (module type forms inherit this display), 2.5h (AI cap warning visible during test configuration) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → EC-004; Directory Structure → `src/ui/gui/` |

### Role

You are a Senior Python GUI Developer. You are implementing the real-time AI cap calculation display — a safety instrument that shows the mission designer how many concurrent AI units their module configuration will produce.

### Context

The IL-2 DServer has an approximately 100-unit active AI cap. Exceeding it causes non-linear tickrate degradation: SPS drops below the physics simulation threshold, producing desync, rubber-banding, and eventual server instability. The GUI must make this invisible ceiling visible. The display is not a hard block — it warns, but the user can override if they know their server can handle it.

The calculation is straightforward: `max_concurrent_AI = flight_size × max_simultaneous_waves`. The challenge is determining `max_simultaneous_waves`, which depends on GC timing. For the Static CAP, the worst case is 2 simultaneous waves (current wave overlapping with the next wave during the GC despawn delay window). The display should show the worst-case calculation.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EC-004] HIGH — GUI SHALL calculate and display: `max_concurrent_AI = flight_size × max_simultaneous_waves`. GUI SHALL warn if this value exceeds 80. GC-gated activation prevents actual cap breach at runtime, but the designer must see the theoretical worst case at design time.
> - Section 5.2.3: GC-Gated Wave Activation — the ~100 AI cap and the reason for the warning threshold

### Inputs

- Task 2.4 output: Static CAP form with `flight_size` and `wave_count` fields
- Module type-specific worst-case overlap factor (Static CAP: 2)

### Requirements

**R1 — AI Cap Calculation Widget**

A persistent display widget (not a dialog) positioned near the Magazine parameters group. Shows:
- `Max Concurrent AI: {value}` — updated dynamically as `flight_size` or overlap factor changes
- Color-coded: green (≤ 60), amber (61–80), red (> 80)
- Formula tooltip: "flight_size × max_simultaneous_waves = {flight_size} × {overlap} = {value}"

**R2 — Worst-Case Overlap Factor**

For the Static CAP module type, `max_simultaneous_waves = 2` (one wave active + one wave in the GC despawn delay window). Future module types may have different overlap factors:
- Intercept: 2 (same as Static CAP)
- Scramble: 3 (takeoff + active + GC window)

The overlap factor is a property of the module form class, not hardcoded in the widget.

**R3 — Warning Threshold**

If `max_concurrent_AI > 80`, display a warning:

> ⚠ AI cap warning: {value} concurrent AI units exceeds the recommended DServer limit of 80. Consider reducing flight size or designing for fewer simultaneous waves.

The warning is informational. It does not block compilation.

**R4 — Multi-Module Awareness (Future-Proofing)**

When Phase 5 adds multi-module composition, the AI cap display must aggregate across all modules in the session. For now, display the single-module value. The widget's `update_cap(modules: list[ModuleConfig])` method should accept a list even though Phase 2 only passes a single-element list.

**R5 — Dynamic Update**

The display must update immediately (no lag, no manual refresh) when:
- `flight_size` spinbox value changes
- Module type changes (different overlap factor)
- Any parameter affecting the overlap calculation changes

> **[EC-004] — HIGH** The ~100 AI cap is a hard performance cliff. The GUI's 80-unit warning threshold provides a 20-unit safety margin. DServer tickrate degradation above ~100 units is non-linear — it does not gracefully degrade; it falls off a cliff.

> **EXIT CONDITION — Acceptance Criteria**
> - AI cap display updates dynamically when `flight_size` changes
> - Display shows correct value: flight_size=4, overlap=2 → shows "8"
> - Green/amber/red color coding at thresholds ≤60 / 61–80 / >80
> - Warning message appears when value exceeds 80
> - Warning message disappears when value drops to ≤80
> - Tooltip shows the formula with current values
> - Widget accepts a list of modules (future multi-module support)

---

## Human Gate 2.1h — Hand-Built .Group Files

| | |
|---|---|
| **Gate ID** | 2.1h |
| **Depends On** | None (can be completed at any time before task 2.2) |
| **Actor** | Project Owner |
| **Blocks** | Task 2.2 (validation corpus requires these files as input) |

### Required Actions

Provide 5+ hand-built .Group files from your IL-2 mission design work or from community sources. These files are the reference corpus that the MRE will reverse-engineer and the validation pipeline will diff against compiler output.

### File Requirements

The corpus must include diversity across:
- **Complexity range:** At least one simple file (single flight, no triggers) and one complex file (multi-flight, trigger chains, timer logic)
- **Formation flights:** At least one file with formation hierarchies (leader + wingmen with Target Links)
- **Trigger chains:** At least one file with MCU_Timer, MCU_Counter, or MCU_TR_ComplexTrigger chains
- **Timer logic:** At least one file with time-based activation patterns
- **Varied MCU types:** Coverage of MCU_CMD_AttackArea, MCU_CMD_Waypoint, MCU_Activate, MCU_Deactivate, MCU_CMD_Despawn

### Ideal Corpus Composition

1. Simple CAP patrol: single flight, waypoint loop, AttackArea
2. Multi-wave CAP: Magazine Array pattern with 3+ waves
3. Scramble or takeoff sequence: taxi → takeoff → altitude gate
4. Complex trigger chain: nested timer/counter logic with branching
5. Known-violation file: a file deliberately containing at least one FMEA-violating pattern (e.g., Spawn on formation, single-leader RTB) for audit validation

### Delivery

Place files in `tests/fixtures/il2_files/hand_built/` and notify that the gate is complete.

> **EXIT CONDITION**
> - 5+ .Group files accessible in `tests/fixtures/il2_files/hand_built/`
> - Files cover diverse MCU patterns as specified above
> - Complexity ranges from simple (single flight) to multi-flight with trigger chains

---

## Human Gate 2.5h — In-Game Test (GUI Compilation)

| | |
|---|---|
| **Gate ID** | 2.5h |
| **Depends On** | 2.5 — GUI-compiled .Group file |
| **Actor** | Project Owner |
| **Blocks** | Phase 3 cannot begin until this gate is passed |

### Required Actions

- Use the GUI (task 2.3–2.5) to configure and compile a Static CAP module
- Import the GUI-compiled .Group file into BOSEditor
- In the same session, import the CLI-compiled .Group file from task 1.10h (or recompile via CLI with identical parameters)
- Fly both modules in a 30-minute test session
- Compare behavior between GUI-compiled and CLI-compiled modules

### Verification Checklist

- **Behavioral equivalence:** GUI-compiled AI behavior matches CLI-compiled AI behavior (patrol, engagement, RTB, despawn, wave activation)
- **AI cap display accuracy:** The GUI's AI cap calculation matches observed in-game concurrent AI count
- **Session formula warning:** If wave count was set below the formula threshold, verify that the Magazine exhausts as warned
- **No regression:** All Phase 1.10h verification items still pass (patrol, engagement, ToS, despawn, leader-kill, slot reclamation, 30-min stability)
- **GUI-specific:** Compiler output panel displays warnings/success correctly; exported JSON re-imports into the GUI and reproduces the same .Group output

### Report Requirements

Document the test results before Phase 3 begins. For each verification item: PASS, FAIL, or NOT OBSERVED.

- If behavioral equivalence is FAIL: this is a GUI export or wiring bug in task 2.5. Return to session 2.5 with the failure evidence.
- If a Phase 1 regression is detected: return to the relevant Phase 1 primitive session.
- If the AI cap display is inaccurate: return to session 2.6.

The Phase 3 module expansion depends on both the compiler and the GUI being correct. Bugs discovered in Phase 3 that trace to Phase 2 GUI issues are significantly more expensive to isolate.

---

## Recommended Execution Sequence

```
                    ┌─── Track A (MRE) ───────────────────────┐
                    │                                         │
Gate 2.1h ──────────┤                                         ├──→ 2.2 (Validation Corpus)
(hand-built files)  │                                         │         ↑
                    └──→ 2.1 (MRE) ──────────────────────────┘         │
                                                                       │
                                                              1.10 ────┘ (compiler output)
                                                                
                    ┌─── Track B (GUI) ───────────────────────────────────────────┐
                    │                                                             │
0.5 (schema) ──────┴──→ 2.3 (Shell) → 2.4 (Form) ──┬──→ 2.5 (Compile) → 2.5h  │
                                                     │                            │
                                                     └──→ 2.6 (AI Cap)           │
                                                                                  │
                                              1.10 (compiler) ──→ 2.5 ───────────┘
```

- **Start immediately (parallel):** Gate 2.1h (file collection), Session 2.1 (MRE), Session 2.3 (GUI shell)
- **After 2.3:** Session 2.4 (form)
- **After 2.4 (parallel):** Session 2.5 (compile wiring — also needs 1.10), Session 2.6 (AI cap display)
- **After 2.1 + 2.1h + 1.10:** Session 2.2 (validation corpus)
- **After 2.5:** Gate 2.5h (in-game test)
- **Phase 3 begins after:** Gate 2.5h PASSED and Session 2.2 complete
