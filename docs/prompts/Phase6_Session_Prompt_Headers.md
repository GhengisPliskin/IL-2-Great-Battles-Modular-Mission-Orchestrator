# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 6 — Distribution + Community
### Session Prompt Headers
*Standalone executable, documentation, community onboarding*

**3 AI Sessions | 1 Human Gate | Task IDs 6.1 – 6.4**

---

## Phase 6 Overview

Phase 6 packages the complete MMF stack into a standalone Windows executable, writes end-user and contributor documentation, and releases to the IL-2 community for real-world multiplayer testing. This phase produces no new engine-facing logic — it wraps, documents, and validates everything built in Phases 0–5.

No FMEA constraints introduce new failure modes at this layer. However, the packaging task (6.1) must ensure that every FMEA-constrained module from the compiler, orchestrator, and map database is correctly bundled. A missing hidden import or data file in the PyInstaller build silently degrades the executable — the user gets a stack trace instead of a mission. The documentation tasks (6.2, 6.3) must accurately describe the constraint-driven behavior that end users and contributors will encounter (e.g., the ~100 AI unit cap, wave cycling, initialization delays).

All three AI sessions are Tier 2 (Sonnet 4.6 / Gemini 3 Flash) — standard packaging and technical writing with well-defined inputs. No cross-constraint reasoning is required.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 6.1 | Package with PyInstaller: standalone .exe for Windows | Distribution | AI | Tier 2: Sonnet 4.6 |
| 6.2 | Write user documentation: getting started, module reference, scenario descriptions, DServer guide | Docs | AI | Tier 2: Sonnet 4.6 |
| 6.3 | Write contributor documentation: architecture overview, adding modules, adding maps, extending type catalog | Docs | AI | Tier 2: Sonnet 4.6 |
| 6.4 | Community beta: release to IL-2 server operators and mission designers for real-world testing | Testing | HUMAN | N/A |

**Dependency order:** 6.1, 6.2, and 6.3 all depend on Phase 5.5 (complete Orchestrator GUI) and can run in parallel. 6.4 depends on 6.1 (executable exists) and 6.2 (user documentation exists).

```
Phase 5 (5.5 Orchestrator GUI — complete, tested)
    ↓
    ├──→ 6.1 (PyInstaller Packaging)
    │        ↓
    ├──→ 6.2 (User Documentation) ──→ 6.4 (HUMAN: Community Beta)
    │                                    ↑
    └──→ 6.3 (Contributor Documentation) (6.4 also requires 6.1)
```

---

## Session 6.1 — PyInstaller Packaging

| | |
|---|---|
| **Task ID** | 6.1 |
| **Component** | Distribution (`build/pyinstaller/`, `build/dist/`) |
| **Model Tier** | Tier 2 |
| **Assigned Model** | Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 5.5 (complete Orchestrator GUI — the application entry point being packaged) |
| **Delivers To** | 6.4 (community beta — the executable users will download and test) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `build/pyinstaller/`, `build/dist/`, `data/`, `config/` |

### Role

You are a Senior Python Developer specializing in application packaging and deployment. You are creating a standalone Windows executable from the complete MMF application using PyInstaller, ensuring all runtime dependencies, data files, and configuration are correctly bundled.

### Context

The MMF application is a PyQt6 GUI backed by the compiler, orchestrator, map databases, and module templates built across Phases 0–5. End users are IL-2 server operators and mission designers — they do not have Python installed. The packaged executable must include the entire `src/` tree (parser, schema, compiler, validation, backend orchestrator, UI), all SQLite map databases from Phase 4, all module template JSON files from Phases 2–3, the JSON schema, and default configuration files.

PyInstaller's hidden import detection frequently misses dynamically loaded modules. The MMF codebase uses several patterns that are known to cause hidden import failures: Pydantic model loading (`src/mmf/schema/v2_0.py`), PyQt6 plugin loading, and SQLite database driver imports. These must be explicitly declared in the `.spec` file or a custom hook.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 1: Project Objective — Python UI and Logic Matrix Generator; the packaged executable is the end-user delivery of this objective
> - Section 2: Architectural Design Principles — three-layer architecture; all three layers must be present in the bundle
> - All FMEA constraints (PI-001 through EC-004) are embedded in the bundled compiler code; no constraints require runtime modification, but all constrained modules must be importable from the frozen executable
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Complete `src/` tree: `mmf/` (parser, schema, compiler, validation, utils), `backend/` (mre, map_extractor, orchestrator), `ui/` (gui, cli)
- `data/map_databases/maps.sqlite3` — Phase 4 map database
- `data/module_templates/*.json` — Phase 2/3 module templates (static_cap.json, scramble.json, bomber_escort.json, etc.)
- `data/schemas/mmf-module-schema-v2_0.json` — JSON schema contract
- `config/compiler_defaults.yaml`, `config/logging.yaml` — default configuration
- `requirements.txt` — Python dependency list
- Application entry point: `src/ui/gui/main_window.py` or `src/ui/cli/main.py` (package both GUI and CLI entry points)

### Requirements

**R1 — PyInstaller Spec File**

Create `build/pyinstaller/mmf.spec` with:
- Entry point: GUI application (`src/ui/gui/main_window.py`) as the primary executable
- CLI entry point (`src/ui/cli/main.py`) as a secondary console executable
- `--onedir` mode (not `--onefile`) — allows faster startup and easier debugging of missing files
- Windows-specific: set `console=False` for the GUI entry point, `console=True` for CLI

**R2 — Hidden Import Hook**

Create `build/pyinstaller/hook-mmf.py` that explicitly declares:
- All `src/mmf/compiler/` submodules (id_generator, spatial_offset, reserved_filter, proxy_builder, command_buffer, magazine_array, entity_proxy, garbage_collection, dependency_stubs, compiler)
- All `src/mmf/schema/` submodules (v2_0, validator)
- All `src/mmf/validation/` submodules (fmea, checkers)
- All `src/backend/` submodules (orchestrator, map_extractor, mre)
- PyQt6 plugins: `PyQt6.QtWidgets`, `PyQt6.QtCore`, `PyQt6.QtGui`
- `sqlite3`, `jsonschema`, `pydantic` if used
- Any other imports detected during test builds

**R3 — Data File Bundling**

Bundle non-Python files as PyInstaller `datas`:
- `data/map_databases/` → `data/map_databases/`
- `data/module_templates/` → `data/module_templates/`
- `data/schemas/` → `data/schemas/`
- `config/compiler_defaults.yaml` → `config/`
- `config/logging.yaml` → `config/`

Implement a `runtime_paths.py` utility that resolves data file paths correctly in both development mode (`sys.path`-based) and frozen mode (`sys._MEIPASS`-based):

```python
def get_data_path(relative_path: str) -> Path:
    """Resolve data file path for both dev and frozen execution."""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent.parent
    return base / relative_path
```

**R4 — Build Script**

Create `scripts/build_exe.py` that:
- Runs PyInstaller with the `.spec` file
- Copies the output from `build/dist/` to a release directory
- Prints the final executable size and file count
- Validates that the executable starts without immediate crash (subprocess launch with timeout)

**R5 — Smoke Test**

The build script must include a post-build smoke test:
- Launch the executable with a `--version` flag (add this flag to the CLI entry point if not present)
- Launch the executable with a `--generate-test` flag that compiles a single Static CAP module from a bundled template and writes the .Group output to a temp directory
- Both commands must exit 0 with correct output

> **EXIT CONDITION — Acceptance Criteria**
> - User downloads the `build/dist/mmf/` directory, runs `mmf.exe` on a Windows machine without Python installed
> - GUI launches without import errors or missing file exceptions
> - User generates a mission using the Orchestrator GUI — the .Mission file is written to disk
> - CLI entry point (`mmf-cli.exe --version`) prints version and exits 0
> - CLI entry point (`mmf-cli.exe --generate-test`) compiles a Static CAP module and writes valid .Group output
> - All map databases, module templates, and default configs are accessible from the frozen executable
> - Executable size is documented in the build output

### Ground Rule Compliance

- **Issue Binding:** This task is bound to Issue #[TBD].
- **Decision Logging:** Update `CODE_DECISION_LOG.md` with any structural code decisions made during this session.
- **State Sync:** Move Kanban card from Ready → In Progress at start; In Progress → In Review at completion.

### Execution Sequence & Two-Phase Commit

**PHASE 1: Execution**
1. Generate or modify the required code files per the Requirements above.
2. Output the exact string: `[AWAITING_HUMAN_APPROVAL: Code generation complete. Please test and verify.]`
3. HALT completely. Do not proceed to Phase 2.

**PHASE 2: Documentation (Execute ONLY after human replies "Approved")**
1. Audit the final, approved code against the current FMEA constraints.
2. Generate the required `CODE_DECISION_LOG.md` entry.
3. Generate an `ARCHITECTURE_PATCH.md` if structural drift occurred.
4. Output the final Kanban board state change.

---

## Session 6.2 — User Documentation

| | |
|---|---|
| **Task ID** | 6.2 |
| **Component** | Documentation (`docs/USER_GUIDE.md`) |
| **Model Tier** | Tier 2 |
| **Assigned Model** | Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 5.5 (complete Orchestrator GUI — must document the final interface, not a prototype) |
| **Delivers To** | 6.4 (community beta — this is the document users follow during testing) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `docs/USER_GUIDE.md` |

### Role

You are a Technical Writer producing end-user documentation for a specialized simulation tool. Your audience is IL-2 Great Battles server operators and mission designers — technically proficient with the IL-2 Mission Editor, but not programmers. They need to go from download to first flyable mission within 10 minutes.

### Context

The MMF Orchestrator generates .Mission files for IL-2 Great Battles multiplayer DServer sessions. Users interact through either the PyQt6 GUI or the command-line interface. They need to understand: how to install and launch the tool, how to generate their first mission, what each scenario type does, how module parameters affect gameplay, how to configure DServer rotation, and how to troubleshoot common issues.

The documentation must accurately describe constraint-driven behavior that affects the user experience without exposing internal implementation details. Users will notice: the ~3 second initialization delay before AI units activate (EC-001), the wave cycling behavior when AI units are destroyed or RTB (EL-001, SM-002), and the ~100 AI unit cap that limits simultaneous active flights (EC-004). These are features, not bugs — the documentation must explain them as intentional design.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 1: Project Objective — describes the end-user value proposition (bypass Mission Editor limitations, automated DServer cycling)
> - Section 3: Module Architecture — describes the module types users will select (Static CAP, Scramble, Bomber Escort, etc.)
> - Section 5: Garbage Collection — describes the wave cycling behavior users will observe in-game
> - Section 6: Initialization — describes the startup delay users will observe
> - FMEA constraints EC-001 (init delay), EC-004 (AI cap), EL-001 (wave cycling) — these manifest as user-visible behavior
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Complete, working MMF application (Phase 5.5 output)
- All module template JSON files (Phase 2/3 output) — these define the parameter space users configure
- Map database (Phase 4 output) — these define the available maps and locations
- Scenario templates (Phase 5.3 output) — these define the mission types users select
- DServer rotation config (Phase 5.6 output) — this defines the server operator workflow

### Requirements

**R1 — Getting Started Guide**

Write a quickstart section that takes the user from download to first flyable mission:
- System requirements (Windows, IL-2 Great Battles installed)
- Installation: extract the packaged directory, no Python required
- First launch: open `mmf.exe`, select a map, choose a scenario type, click Generate
- First flight: copy the generated .Mission to the IL-2 data directory, load in Mission Editor or DServer
- Expected result: describe what the user will see in-game (AI flights spawning, waypoint patterns, wave cycling)

**R2 — Module Reference**

Document each available module type with:
- Purpose and behavior description (what this module does in the mission)
- Configurable parameters with valid ranges and defaults
- In-game behavior: what the user will observe (flight paths, engagement patterns, cycling)
- Interaction with other modules: which combinations are recommended, which conflict

At minimum, document: Static CAP, Scramble, Bomber Escort, Ground Attack, and any additional module types from Phase 3.

**R3 — Scenario Guide**

Document each scenario template from Phase 5.3:
- Scenario description: high-level narrative (Intercept, Patrol, Ground Attack, Escort, Free Hunt)
- Map compatibility: which maps support each scenario
- Difficulty scaling: how the difficulty parameter affects AI count, skill, and routing
- Weather and time-of-day effects: how environmental parameters change the mission
- Expected session length and AI cycling behavior

**R4 — DServer Operator Guide**

Document the multiplayer server workflow:
- Batch generation: how to generate a rotation of missions
- SDS configuration: how to configure DServer to cycle through generated missions
- Rotation scheduling: how to set time-based or player-count-based rotation
- Log monitoring: what the DServer logs show during MMF-generated missions
- Inter-mission state: how mission outcomes affect the next generated mission (Phase 5.7)

**R5 — Troubleshooting**

Document the most likely failure modes a user will encounter:
- "No AI spawned" — likely initialization delay (EC-001); wait 3+ seconds after mission start
- "AI stopped spawning" — AI cap reached (EC-004); waves will resume as earlier flights RTB or are destroyed
- "Mission won't load in DServer" — possible file path issue or corrupt .Mission; regenerate
- GUI won't launch — missing Visual C++ redistributable or other Windows dependency
- How to report bugs: what information to include (MMF version, map, scenario type, log files)

> **EXIT CONDITION — Acceptance Criteria**
> - A new user with no prior MMF exposure follows the Getting Started guide and generates a flyable mission within 10 minutes
> - Every configurable parameter in the GUI is documented with its valid range and default value
> - Every scenario type has a description and map compatibility table
> - DServer operators can configure a rotation from documentation alone
> - Troubleshooting section covers the top 5 user-reported issues from Phase 5 testing (5.2h, 5.5h, 5.6h)
> - Document is written in Markdown, stored at `docs/USER_GUIDE.md`

### Ground Rule Compliance

- **Issue Binding:** This task is bound to Issue #[TBD].
- **Decision Logging:** Update `CODE_DECISION_LOG.md` with any structural code decisions made during this session.
- **State Sync:** Move Kanban card from Ready → In Progress at start; In Progress → In Review at completion.

### Execution Sequence & Two-Phase Commit

**PHASE 1: Execution**
1. Generate or modify the required code files per the Requirements above.
2. Output the exact string: `[AWAITING_HUMAN_APPROVAL: Code generation complete. Please test and verify.]`
3. HALT completely. Do not proceed to Phase 2.

**PHASE 2: Documentation (Execute ONLY after human replies "Approved")**
1. Audit the final, approved code against the current FMEA constraints.
2. Generate the required `CODE_DECISION_LOG.md` entry.
3. Generate an `ARCHITECTURE_PATCH.md` if structural drift occurred.
4. Output the final Kanban board state change.

---

## Session 6.3 — Contributor Documentation

| | |
|---|---|
| **Task ID** | 6.3 |
| **Component** | Documentation (`docs/CONTRIBUTOR_GUIDE.md`, `docs/API_REFERENCE.md`) |
| **Model Tier** | Tier 2 |
| **Assigned Model** | Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 5.5 (complete Orchestrator — the full codebase must be stable before documenting its extension points) |
| **Delivers To** | 6.4 (community beta — contributors during beta need this to add modules and maps) |
| **Reference** | See `ARCHITECTURE.md` — this document is the authoritative architecture reference; the contributor guide extends it for external developers |

### Role

You are a Technical Writer producing developer-facing documentation for an open-source Python project. Your audience is IL-2 community developers who want to add new module types, new maps, or extend the type catalog — without modifying core compiler or orchestrator code. They are comfortable with Python and JSON but have no prior exposure to the MMF architecture or FMEA constraint set.

### Context

The MMF architecture is designed for extensibility through composition: new module types are JSON templates consumed by existing compiler primitives, new maps are SQLite database entries consumed by the existing map extractor, and new MCU types are catalog entries consumed by the existing required-field validator. A contributor should never need to modify `src/mmf/compiler/` or `src/backend/orchestrator/` to add content.

However, contributors must understand the FMEA constraints that govern what the compiler can and cannot do. A contributor who designs a module type that requires more than ~100 simultaneous AI units will hit the engine cap (EC-004). A contributor who omits garbage collection from a module design will leak AI slots (SM-002). The contributor guide must make these constraints discoverable without requiring the contributor to read the full FMEA report.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2: Architectural Design Principles — three-layer architecture; contributors work at the top layer
> - Section 2.1: JSON Intermediary — new modules are JSON documents; contributors author JSON, not IL-2 ASCII
> - Section 3: Module Architecture — the template structure contributors will extend
> - All FMEA constraints (PI-001 through EC-004) — contributors must understand the constraints their modules inherit
> - `ARCHITECTURE.md` — the directory structure and import conventions contributors must follow
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Complete `src/` tree with all modules implemented and tested
- `ARCHITECTURE.md` — authoritative directory structure and phase mapping
- `CONSTRAINTS.md` (or equivalent FMEA traceability document) — constraint IDs, severities, and descriptions
- `data/schemas/mmf-module-schema-v2_0.json` — the JSON schema that governs all module definitions
- Existing module templates as examples (`data/module_templates/`)
- Map database schema (`data/map_databases/`)
- MCU type catalog (`src/mmf/parser/` or `data/`)

### Requirements

**R1 — Architecture Overview**

Write a developer-oriented architecture summary:
- Three-layer diagram: shared foundation → backend tool suite → user-facing applications
- Data flow: JSON module → compiler → .Group → orchestrator → .Mission
- Import conventions: how to import from `mmf.*`, prohibition on relative imports
- Testing conventions: unit tests colocated in `src/*/tests/`, integration tests in `tests/integration/`
- Reference `ARCHITECTURE.md` as the authoritative source; the contributor guide supplements, not replaces it

**R2 — Adding a New Module Type**

Write a step-by-step tutorial:
1. Define the module's behavior in plain English (what it does in-game)
2. Create a JSON template in `data/module_templates/` conforming to the schema
3. Add the module type string to the schema's `module_type` enum (non-breaking extension)
4. Add any module-specific conditional validation via `if/then/else` in the schema
5. Verify: the compiler accepts the new template and produces a valid .Group file
6. Test: load the .Group in IL-2 Mission Editor, verify MCU structure
7. Register: add the module type to the GUI's scenario selector

Include a worked example: walk through creating a hypothetical "Ferry Flight" module (non-combat transport) from scratch.

**R3 — Adding a New Map**

Write a step-by-step tutorial:
1. Obtain the map's `.mission` template file (empty mission on the target map)
2. Run the Map Data Extractor (Phase 4 tool) to populate the SQLite database
3. Validate extracted coordinates against known landmarks
4. Register the map in the orchestrator's map selector
5. Test: generate a mission on the new map, verify coordinate placement

**R4 — Extending the Type Catalog**

Document how to add new MCU types to the required-field validator:
- Where the catalog lives (`src/mmf/` or `data/`)
- Required fields per MCU type (from IL-2 engine requirements)
- How to determine required fields for an undocumented MCU type (reverse engineer from reference files)
- How to test: create a .Group with the new MCU type, validate with the compiler, load in IL-2

**R5 — FMEA Constraint Quick Reference**

Create a contributor-facing constraint summary table:
- Each constraint ID, severity, one-line description, and "what this means for module authors"
- Group by impact: "Constraints you will hit" (EC-004 AI cap, EC-001 init delay, SM-002 GC requirement) vs. "Constraints the compiler handles" (PI-003 ID generation, EL-001 magazine counter, SM-001 serialization timers)
- Link to the full FMEA report for detailed rationale

**R6 — API Reference**

Generate or write `docs/API_REFERENCE.md` covering the public interfaces a contributor may call:
- `mmf.parser`: `parse_file()`, `parse_string()`, `serialize()`, `write_file()`
- `mmf.schema`: `validate()`, schema loading
- `mmf.compiler`: `compile_module()`, `IDGenerator`, `SpatialOffset`
- `mmf.validation`: `check_fmea_constraints()`
- `backend.orchestrator`: `build_mission()`, scenario template API
- `backend.map_extractor`: `extract_map_data()`, coordinate database API

> **EXIT CONDITION — Acceptance Criteria**
> - An external contributor with Python experience follows the "Adding a New Module Type" tutorial and successfully adds a module type. No modifications to `src/mmf/compiler/` or `src/backend/orchestrator/` are required.
> - An external contributor follows the "Adding a New Map" tutorial and successfully adds a map to the database. Generated missions place units at correct coordinates.
> - The FMEA constraint quick reference accurately summarizes all 14 constraints with correct severity ratings
> - The API reference documents every public function a contributor would call
> - Documents are written in Markdown: `docs/CONTRIBUTOR_GUIDE.md` and `docs/API_REFERENCE.md`

### Ground Rule Compliance

- **Issue Binding:** This task is bound to Issue #[TBD].
- **Decision Logging:** Update `CODE_DECISION_LOG.md` with any structural code decisions made during this session.
- **State Sync:** Move Kanban card from Ready → In Progress at start; In Progress → In Review at completion.

### Execution Sequence & Two-Phase Commit

**PHASE 1: Execution**
1. Generate or modify the required code files per the Requirements above.
2. Output the exact string: `[AWAITING_HUMAN_APPROVAL: Code generation complete. Please test and verify.]`
3. HALT completely. Do not proceed to Phase 2.

**PHASE 2: Documentation (Execute ONLY after human replies "Approved")**
1. Audit the final, approved code against the current FMEA constraints.
2. Generate the required `CODE_DECISION_LOG.md` entry.
3. Generate an `ARCHITECTURE_PATCH.md` if structural drift occurred.
4. Output the final Kanban board state change.

---

## Human Gate — Action Required

Phase 6 contains one human gate. AI sessions 6.1–6.3 must complete before this gate can begin.

### Gate 6.4 — Community Beta

| | |
|---|---|
| **Gate ID** | 6.4 |
| **Component** | Testing |
| **Depends On** | 6.1 (packaged executable exists), 6.2 (user documentation exists) |
| **Actor** | HUMAN — project owner + invited community testers |

### Required Actions

1. **Recruit beta testers:** Identify 3–5 IL-2 server operators and/or mission designers willing to test the MMF Orchestrator on their live or staging DServer instances.

2. **Distribute the package:** Provide testers with the `build/dist/mmf/` directory and the `docs/USER_GUIDE.md`. Optionally provide `docs/CONTRIBUTOR_GUIDE.md` to testers interested in adding content.

3. **Define test protocol:** Each tester should:
   - Install and launch the executable (no Python)
   - Generate at least 3 missions across different maps and scenario types
   - Run at least one mission on a DServer with 2+ connected clients
   - Run at least one automated rotation session (3+ missions, 1+ hour)
   - Document any crashes, unexpected behavior, or usability issues

4. **Collect and triage feedback:** Categorize issues as:
   - **Blocker:** crash, data loss, mission won't load
   - **Major:** incorrect behavior (AI not spawning, wrong coordinates, broken wave cycling)
   - **Minor:** usability (confusing UI, unclear documentation, cosmetic)
   - **Enhancement:** feature requests for future phases

5. **Incorporate feedback:** Address all Blocker and Major issues. Update documentation for Minor issues related to unclear instructions. Log Enhancements for future consideration.

### Exit Condition

> - 10+ hours of cumulative multiplayer DServer server time across all testers
> - Zero unresolved Blocker issues
> - All Major issues resolved or documented with known workarounds
> - User documentation updated to reflect any changes made during beta
> - Feedback log archived for future development reference

---

## Recommended Execution Sequence

1. **Parallel start:** Begin sessions 6.1, 6.2, and 6.3 simultaneously — they share the same dependency (5.5) and have no interdependencies.
2. **Gate readiness:** Gate 6.4 requires both 6.1 (executable) and 6.2 (user docs). Session 6.3 (contributor docs) is useful for beta but not blocking.
3. **Iterate:** If the 6.1 smoke test fails, fix and rebuild before distributing to beta testers. If 6.2 feedback from internal review suggests gaps, revise before community distribution.
