# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 0 — Foundation
### Session Prompt Headers
*Shared Parser Library + JSON Schema Contract*

**5 AI Sessions | 2 Human Gates | Task IDs 0.2 – 0.6**

---

## Phase 0 Overview

Phase 0 produces the two shared foundations that every subsequent phase imports: the IL-2 ASCII parser/writer library and the JSON schema contract. No phase can begin until Phase 0 is complete.

Task 0.2 (parser) and 0.5 (JSON schema) are Tier 1 (Opus 4.6) — the parser must handle an undocumented proprietary format with no room for silent misparses, and the schema defines the project's central integration contract whose correctness determines all downstream phase alignment. Task 0.3 (writer) and 0.4 (MCU catalog) are Tier 2 (Sonnet 4.6) — both have well-defined input structures (the parser's dictionary output and the reference corpus respectively). Task 0.6 (scaffolding) is Tier 3 (Haiku 4.5) — pure boilerplate with no behavioral logic.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 0.1 | Collect 10+ reference .Group/.Mission files | Data | HUMAN | N/A |
| 0.2 | Build IL-2 ASCII parser (read → Python dict) | Parser lib | AI | Tier 1: Opus 4.6 |
| 0.3 | Build ASCII writer (Python dict → IL-2 syntax) | Parser lib | AI | Tier 2: Sonnet 4.6 |
| 0.4 | Build MCU type catalog (required fields + constraints) | Parser lib | AI | Tier 2: Sonnet 4.6 |
| 0.5 | Define JSON schema contract | Schema | AI | Tier 1: Opus 4.6 |
| 0.5h | REVIEW: Approve JSON schema contract | Schema | HUMAN | N/A |
| 0.6 | Create Python project structure + packaging | Project | AI | Tier 3: Haiku 4.5 |

**Dependency order:** Gate 0.1 must complete first (file collection). 0.2 depends on 0.1. 0.3 and 0.4 both depend on 0.2. 0.5 is independent (defines the interface). 0.6 is independent (can run in parallel with 0.5). 0.5h gates Phase 1 entry.

```
Gate 0.1 (HUMAN: Collect reference files)
    ↓
    0.2 (Parser) ──┬──→ 0.3 (Writer)
                   │
                   └──→ 0.4 (MCU Catalog)

    0.5 (JSON Schema) ──→ 0.5h (HUMAN: Schema Approval) ──→ Phase 1
                                                               ↑
    0.6 (Project Structure) ───────────────────────────────────┘
```

---

## Human Gate 0.1 — Reference File Collection

| | |
|---|---|
| **Gate ID** | 0.1 |
| **Depends On** | None |
| **Actor** | Project Owner |
| **Blocks** | 0.2 (parser requires reference files as input corpus) |

### Required Actions

Collect 10+ .Group and .Mission files from your IL-2 installation (`data/Missions/`, stock campaigns, community libraries). Place in the working directory.

### File Requirements

The corpus must include diversity across:
- **Formation hierarchies:** At least one file with leader + wingmen Target Link structures
- **Complex trigger chains:** At least one file with MCU_Timer, MCU_Counter, or MCU_TR_ComplexTrigger chains
- **Multiplayer templates:** At least one MP-formatted file with coalition and spawn infrastructure
- **Varied MCU types:** Broad coverage of MCU_CMD_AttackArea, MCU_CMD_Waypoint, MCU_Activate, MCU_Deactivate, MCU_CMD_Despawn, MCU_TR_Entity, MCU_Counter, MCU_Timer

> **EXIT CONDITION**
> - 10+ files accessible in working directory
> - Diverse MCU types represented across the corpus
> - Formation hierarchies, trigger chains, and multiplayer templates all present

---

## Session 0.2 — IL-2 ASCII Parser

| | |
|---|---|
| **Task ID** | 0.2 |
| **Component** | Parser library (`src/mmf/parser/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 0.1 (reference file corpus in working directory) |
| **Delivers To** | 0.3 (writer), 0.4 (catalog), 1.x (all compiler tasks) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/mmf/parser/`, Phase Mapping, FMEA Constraints |

### Role

You are a Principal Python Systems Developer specializing in text parsing and abstract syntax tree construction. You have deep familiarity with custom ASCII domain-specific languages and the production of round-trip-stable serialization libraries.

### Context

IL-2 Great Battles .Mission and .Group files are structured in a proprietary ASCII format. The format uses nested brace-delimited blocks, key-value pairs separated by `=`, array values delimited by `[]`, and quoted strings. Every subsequent MMF component — the compiler, the Module Reverse Engineer, and the Map Data Extractor — depends on this parser as a shared import. Parser correctness is not negotiable: a silent parse error propagates to every component downstream.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2: Architectural Design Principles — the parser is the base layer of the three-tier architecture
> - Section 2.1: JSON Intermediary — parser output feeds the intermediate JSON representation
> - Section 2.2: Syntax Agnosticism — parser must isolate the IL-2 format so changes require only compiler updates
> - Appendix / MCU block syntax examples in any attached .Group reference files

### Inputs

Provided in the working directory:
- 10+ .Group and .Mission reference files collected in task 0.1
- Files include formation hierarchies, complex trigger chains, and multiplayer templates
- Diverse MCU types are represented across the corpus

### Requirements

**R1 — Block Parser**

Parse any .Mission or .Group file into a Python dictionary. The data model must represent:
- Named blocks: e.g., `MCU_Timer { ... }` → `{ 'type': 'MCU_Timer', 'fields': {...} }`
- Key-value pairs: `Index = 5;` → `{'Index': 5}`
- Arrays: `Targets = [1, 2, 3];` → `{'Targets': [1, 2, 3]}`
- Quoted strings: `Name = "Alpha Flight";` → `{'Name': 'Alpha Flight'}`
- Nested blocks: any block may contain child blocks
- Numeric type inference: integers and floats parsed as Python numerics, not strings

**R2 — Error Handling**

Parser must not silently skip malformed tokens. Any unrecognized syntax must raise a `ParseError` with the line number and offending token. Do not attempt partial recovery.

**R3 — Public API**

```python
parse_file(path: str) -> dict
parse_string(content: str) -> dict
```

Both functions return the same structure. `parse_file` reads and delegates to `parse_string`.

**R4 — Round-Trip Stability**

Compose with the writer (task 0.3) to verify: parse → serialize → parse produces an identical dictionary. Whitespace and comment stripping is acceptable; no data loss is not.

**R5 — Module and Test File Naming**

The parser module SHALL be named `deserializer.py` within `src/mmf/parser/`, matching the `ARCHITECTURE.md` directory specification. The unit test file SHALL be named `test_parser.py` within `src/mmf/parser/tests/`. These names are pinned — downstream sessions (0.3, 0.6, 1.x) import from `mmf.parser.deserializer` and the test runner expects `test_parser.py` at the specified path.

> **EXIT CONDITION — Acceptance Criteria**
> - `parse_file()` runs on every file in the 0.1 corpus without exception
> - Re-serialized output (via 0.3 writer) diffs clean against the original (whitespace-normalized)
> - All MCU types in corpus are represented in the output dictionary
> - Unit tests pass for: nested blocks, array fields, quoted strings, numeric inference
> - `ParseError` raised on injected malformed input with correct line number
> - Parser module exists at `src/mmf/parser/deserializer.py`
> - Unit tests exist at `src/mmf/parser/tests/test_parser.py`

---

## Session 0.3 — ASCII Writer

| | |
|---|---|
| **Task ID** | 0.3 |
| **Component** | Parser library (`src/mmf/parser/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 0.2 (parser — defines the dictionary structure to serialize) |
| **Delivers To** | All compiler tasks (1.x) that write .Group files to disk |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/mmf/parser/`, Phase Mapping |

### Role

You are a Senior Python Developer. You are extending the parser library with its serialization counterpart. The writer must reproduce valid IL-2 ASCII syntax from the Python dictionary structure defined by the task 0.2 parser.

### Context

The parser (0.2) defines the canonical Python dictionary representation of IL-2 files. The writer is its inverse: it serializes that dictionary back into the proprietary ASCII format. Correct writer output is the primary acceptance gate for the parser — a round-trip diff is the proof. The writer is also the output channel for every compiler primitive in Phase 1.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.1: JSON Intermediary — final output is IL-2 ASCII, not JSON; the writer is what produces it
> - Section 2.2: Syntax Agnosticism — only the compiler mapping (which calls the writer) changes on IL-2 updates
> - IL-2 .Group/.Mission file syntax: brace-delimited blocks, `=` assignment, semicolon terminators, bracket arrays

### Inputs

- Task 0.2 parser source code and the dictionary schema it produces
- Reference .Group files from 0.1 corpus for output comparison

### Requirements

**R1 — Serialization Rules**

The writer must reproduce the IL-2 format precisely:
- Block header: `BlockType {`
- Key-value pair: `Key = Value;`
- Array: `Key = [1, 2, 3];`
- Quoted string: `Key = "Value";`
- Nested blocks indented by 2 spaces per level
- Closing brace on its own line: `}`

**R2 — Type Dispatch**

Serialization behavior by Python type:
- `int` / `float` → bare numeric (no quotes)
- `str` → quoted string
- `list` → bracket array
- `dict` with `'type'` key → nested block

**R3 — Public API**

```python
serialize(data: dict) -> str
write_file(data: dict, path: str) -> None
```

**R4 — Reserved Character Filter**

Implements constraint PI-002: strip reserved characters `{}[];="` from all string-type field values before serialization. This is a second-pass filter, independent of any GUI sanitization.

> **EXIT CONDITION — Acceptance Criteria**
> - Written output loads without error in the IL-2 Mission Editor (human gate test)
> - Round-trip test: parse every 0.1 corpus file, write, re-parse, diff — zero data loss
> - PI-002 filter: string containing reserved chars is serialized with those chars stripped
> - Indentation is consistent across all nesting levels

---

## Session 0.4 — MCU Type Catalog

| | |
|---|---|
| **Task ID** | 0.4 |
| **Component** | Parser library (`src/mmf/parser/`), `data/mcu_catalog.json` |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 0.1 (corpus), 0.2 (parser to enumerate all MCU types) |
| **Delivers To** | 1.8 (schema validator PI-001), 2.x (MRE), all compiler field validation |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/mmf/parser/`, FMEA Constraints table |

### Role

You are a Senior Python Developer and data modeler. Your task is to analyze the reference corpus and produce a machine-readable catalog of every MCU type that appears in IL-2 .Group and .Mission files.

### Context

The IL-2 engine uses Mission Control Units (MCUs) as the node primitives for all mission logic — timers, counters, entity proxies, waypoints, commands, and triggers. The compiler must know, for each MCU type, which fields are required versus optional, what value types are expected, and what constraints apply. This catalog is the source of truth for compiler field validation (PI-001) and the Module Reverse Engineer.

> **Relevant MMF Spec Rev 2 Sections**
> - Section PI-001: Required Field Schema Validator — catalog is the schema source
> - Section 3 (MCU types and field definitions) — cross-reference against the corpus
> - FMEA constraints EL-001, EL-002, EL-003 — these reference specific MCU fields (Counter Reset, Entity binding)

### Inputs

- 0.1 reference corpus (10+ .Group/.Mission files)
- 0.2 parser — use it to enumerate all MCU types programmatically across the corpus

### Requirements

**R1 — Catalog Coverage**

Every MCU type appearing in the 0.1 corpus must have a catalog entry. Missing entries are a catalog failure, not a corpus gap.

**R2 — Entry Schema**

Each catalog entry must specify:
- `type`: string MCU type name (e.g., `'MCU_Timer'`)
- `required_fields`: list of field names that must be present
- `optional_fields`: list of field names that may appear
- `field_types`: dict mapping field name → expected Python type
- `constraints`: list of constraint notes (e.g., `'Reset must be 1 when used in Magazine Array'`)

**R3 — Output Format**

Catalog is saved as `data/mcu_catalog.json`. Must be loadable by the compiler's PI-001 validator without preprocessing.

**R4 — FMEA-Aware Annotations**

Flag the following with their FMEA constraint IDs in the `constraints` field:
- `MCU_Counter`: EL-001 (Reset=TRUE required in Magazine Array context)
- `MCU_TR_Entity`: EL-003 (two-way binding fields MisObjID and LinkTrId)
- `MCU_Timer`: SM-003 (timer pauses when owning object is inactive — document this behavior)

> **EXIT CONDITION — Acceptance Criteria**
> - Catalog covers 100% of MCU types observed in the 0.1 corpus
> - Each entry specifies required fields, field types, and constraints
> - EL-001, EL-003, SM-003 constraints are annotated on the relevant entries
> - Catalog loads as valid JSON and passes jsonschema validation against a provided meta-schema
> - A script enumerating corpus MCU types produces zero types missing from catalog

---

## Session 0.5 — JSON Schema Contract

| | |
|---|---|
| **Task ID** | 0.5 |
| **Component** | Schema (`src/mmf/schema/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | None (independent — defines the interface) |
| **Delivers To** | 0.5h (human approval gate), then all Phase 1+ compiler and GUI tasks |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/mmf/schema/`, FMEA Constraints table |

### Role

You are a Principal Python Systems Developer and API contract designer. Your task is to define the authoritative JSON schema that governs the interface between the MMF frontend (GUI) and backend (compiler). This schema is the project's central integration contract — changes after approval require coordinated rewrites of both sides.

### Context

The MMF architecture uses a JSON intermediary between the GUI and the compiler (Spec Section 2.1). Every module the GUI produces is a JSON document. The compiler consumes that document and emits IL-2 ASCII. The schema defined here is the contract that guarantees they stay aligned — regardless of which model tier implements each component or which session produces them.

The sample payload file (`mmf-sample-static-cap.json`) is the reference instantiation. The schema must validate that file and all future module types without breaking changes.

The existing `mmf-module-schema-v2_0.json` is provided as a starting point. Review it, identify gaps or inconsistencies against the spec and sample payload, and produce the authoritative version.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.1: JSON Intermediary — schema is the contract between UI output and compiler input
> - Section 2.2: Syntax Agnosticism — schema must be stable; compiler mapping absorbs IL-2 format changes
> - Section PI-002: Reserved-character filter applies at compiler side, not schema side
> - Section PI-001: Required Field validator — schema is the source of required field definitions
> - FMEA constraints referenced by module types: EL-001, EL-002, EL-003, SM-001–004, PI-001–004

### Inputs

- `mmf-module-schema-v2_0.json` — existing schema draft (review and improve)
- `mmf-sample-static-cap.json` — reference payload that the final schema must validate
- `MMF_Specification_V2.docx` — full FMEA-annotated architecture spec
- `ARCHITECTURE.md` — authoritative directory structure and phase mapping; schema output belongs at `src/mmf/schema/mmf-module-schema-v2_0.json`

### Requirements

**R1 — Top-Level Structure**

Schema must define and enforce:
- `mmf_version`: string, required, semver format
- `output_mode`: enum `['group', 'mission']`, required
- `compiler_options`: object, required — `id_counter_start` (int|null), `initialization_delay_seconds` (int), `session_duration_minutes` (int), `target_mission_file` (string|null)
- `mission_properties`: object|null — null for group mode, required fields for mission mode
- `modules[]`: array, min 1 item, required — each item is a module object

**R2 — Module Object Schema**

Each module must define:
- `module_id`: string, required, no reserved chars `{}[];="`
- `module_type`: enum of valid types (at minimum: `'static_cap'`), extensible
- `coalition`: enum `['axis', 'allied']`, required
- `flight`: object — aircraft_type, ai_skill, country, flight_size, payload_id, fuel (0.1–1.0), skin, starting_location, spawn_altitude
- `magazine`: object — wave_count (int, 1–50), time_on_station_minutes (int), gc_despawn_delay_seconds (int)
- `waypoints`: object — loop (bool), priority, points array (each with x, z, altitude, speed, area)
- `attack`: object|null, `proxy_coordinates`: object, `wiring`: object|null, `scramble`: object|null, `escort`: object|null

**R3 — Extensibility**

New module types must be addable without breaking changes. Use `additionalProperties: false` only at the top level, not on module subobjects. Module type-specific fields use `oneOf` or `if/then/else` discriminated on `module_type`.

**R4 — Draft 7 Compliance**

Schema must validate against JSON Schema Draft 7. Use `$schema: http://json-schema.org/draft-07/schema#` at the root.

> **EXIT CONDITION — Acceptance Criteria**
> - Schema validates against JSON Schema Draft 7 (`jsonschema` Python library, no errors)
> - `mmf-sample-static-cap.json` validates successfully against the schema
> - A deliberately invalid payload (null Targets, out-of-range fuel, missing module_id) fails validation with descriptive errors
> - Schema is approved by project owner (human gate 0.5h) before Phase 1 begins
> - New module type can be added via a non-breaking schema extension (additive only)

---

## Human Gate 0.5h — JSON Schema Approval

| | |
|---|---|
| **Gate ID** | 0.5h |
| **Depends On** | 0.5 (JSON schema definition complete) |
| **Actor** | Project Owner |
| **Blocks** | Phase 1 cannot begin until this gate is passed |

### Required Actions

Review the generated JSON schema. Confirm the top-level structure, module type list, and extensibility approach. This is the interface between frontend and backend — changes after sign-off require coordinated rewrites of both sides.

### Verification Checklist

- **Top-level structure:** `mmf_version`, `output_mode`, `compiler_options`, `mission_properties`, `modules[]` all present and correctly typed
- **Module object:** All required fields present (`module_id`, `module_type`, `coalition`, `flight`, `magazine`, `waypoints`, `proxy_coordinates`)
- **Extensibility:** New module types addable via `oneOf` or `if/then/else` discriminated on `module_type` — no breaking changes required
- **Sample validation:** `mmf-sample-static-cap.json` validates successfully against the schema
- **Negative validation:** At least one deliberately invalid payload fails with a descriptive error
- **Draft 7 compliance:** Schema root declares `$schema: http://json-schema.org/draft-07/schema#`

### Report Requirements

Record approval date before Phase 1 begins. If the schema requires changes, return to session 0.5 with specific revision requests. Changes after this gate are expensive — they propagate to every compiler and GUI task.

> **EXIT CONDITION**
> - Project owner sign-off on the JSON schema contract
> - Approval date recorded
> - Any requested revisions completed and re-reviewed before Phase 1 begins

---

## Session 0.6 — Python Project Structure

| | |
|---|---|
| **Task ID** | 0.6 |
| **Component** | Project scaffolding (`src/` root package) |
| **Model Tier** | Tier 3 — Haiku 4.5 / Gemini 3.1 Flash-Lite |
| **Depends On** | None (can run in parallel with 0.5) |
| **Delivers To** | All sessions — provides the importable package structure every component uses |
| **Reference** | See `ARCHITECTURE.md` — this is the authoritative directory specification; scaffold exactly what it defines |

### Role

You are a Python packaging and project structure specialist. Your task is to scaffold the MMF project directory so every subsequent session can immediately import its component package without configuration.

### Context

The entire MMF project is Python. All components share the `mmf/` root namespace under `src/`. The project structure must be set up once, correctly, so that Phase 1 sessions can write compiler code and immediately run pytest without import errors.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2: Architectural Design Principles — three-layer architecture: parser base, tool suite middle, applications top
> - Section 1: Project Objective — Python UI and Logic Matrix Generator; no language migration

### Required Directory Structure

**Use `ARCHITECTURE.md` as the authoritative directory specification.** It defines the complete `src/`, `tests/`, `docs/`, `data/`, `config/`, `scripts/`, and `build/` layout for this project. Scaffold exactly what `ARCHITECTURE.md` specifies, including all `__init__.py` files, stub test files, and placeholder data files.

Key structural points from `ARCHITECTURE.md`:
- Source root is `src/` (not a flat `mmf/` at project root)
- Shared framework lives at `src/mmf/` (parser, schema, compiler, validation, utils)
- Backend tools live at `src/backend/` (mre, map_extractor, orchestrator)
- UI lives at `src/ui/` (gui, cli)
- Unit tests colocated at `src/*/tests/`; integration tests at `tests/integration/`

### Requirements

**R1 — Packaging**

Use `pyproject.toml` (PEP 517/518). Package name: `mmf`. Minimum Python: 3.10. Dependencies: `jsonschema>=4.0`, `pytest>=7.0`.

**R2 — Test Stubs**

Each test file must contain at minimum one passing stub test (`def test_placeholder(): pass`) so pytest exits 0 before any implementation is written.

**R3 — Import Verification**

Each package `__init__.py` must be importable with no side effects. Verify with:

```bash
python -c "from mmf.parser import deserializer; from mmf.compiler import compiler"
```

**R4 — README**

`README.md` must contain: project name, one-sentence description, install instructions (`pip install -e .`), and run instructions (`pytest`).

> **EXIT CONDITION — Acceptance Criteria**
> - `pytest` exits 0 with all stub tests passing
> - `from mmf.parser import deserializer` succeeds from the project root
> - All sub-packages defined in `ARCHITECTURE.md` import cleanly
> - `src/mmf/schema/` directory exists with placeholder for `mmf-module-schema-v2_0.json`
> - `data/` directory exists with placeholder for `mcu_catalog.json`
> - `pyproject.toml` present with correct package metadata

---

## Recommended Execution Sequence

```
Gate 0.1 (HUMAN: Collect reference files)
    ↓
    ├──→ 0.2 (Parser) ──┬──→ 0.3 (Writer)
    │                    │
    │                    └──→ 0.4 (MCU Catalog)
    │
    ├──→ 0.5 (JSON Schema) ──→ Gate 0.5h (HUMAN: Schema Approval)
    │
    └──→ 0.6 (Project Structure)
                                        ↓
                                   Phase 1 begins
                              (requires 0.5h PASSED + 0.6 complete)
```

- **Complete first:** Gate 0.1 (file collection — blocks all AI sessions except 0.5 and 0.6)
- **Start immediately after 0.1 (parallel):** Session 0.2 (parser)
- **Start immediately (no dependency on 0.1):** Session 0.5 (JSON schema), Session 0.6 (project structure)
- **After 0.2 completes (parallel):** Session 0.3 (writer), Session 0.4 (MCU catalog)
- **After 0.5 completes:** Gate 0.5h (schema approval)
- **Phase 1 begins after:** Gate 0.5h PASSED, Session 0.6 complete, and Sessions 0.2–0.4 complete
