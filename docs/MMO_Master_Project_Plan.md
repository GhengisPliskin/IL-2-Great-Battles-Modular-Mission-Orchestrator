# Master Project Plan — IL-2 Great Battles Modular Mission Orchestrator

**Generated:** March 18, 2026
**Status:** Confirmed
**Version:** 2.1

---

**Table of Contents**

1. [Project Intelligence Roster](#1-project-intelligence-roster)
2. [Project Overview](#2-project-overview)
3. [Requirements](#3-requirements)
4. [Architecture & Directory Structure](#4-architecture--directory-structure)
5. [Risk Register (FMEA)](#5-risk-register-fmea)
6. [Task Registry](#6-task-registry)
7. [Kanban Board Configuration](#7-kanban-board-configuration)
8. [Operational Ground Rules](#8-operational-ground-rules)
9. [Documentation Framework](#9-documentation-framework)
10. [Phase 0 Decisions](#10-phase-0-decisions)

**Appendices**

- [A. Phase Dependency Summary](#appendix-a-phase-dependency-summary)
- [B. AI Module Use Recommendations](#appendix-b-ai-module-use-recommendations)
- [C. Prompt Header Generation Guidance](#appendix-c-prompt-header-generation-guidance)

---

## 1. Project Intelligence Roster

Tasks are assigned to the lowest model tier that can reliably meet the acceptance criteria. Higher-tier models are reserved for tasks where engine-constraint reasoning, complex state management logic, or spatial/architectural planning determines correctness.

| Tier | Role | Assigned Model(s) | Max Context Window | Notes |
|---|---|---|---|---|
| **Tier 1** — Complex Reasoning & Multi-Constraint Logic | Architecture, FMEA analysis, compiler primitives, integration planning, cross-cutting engine-semantic concerns | Claude Opus 4.6 / Gemini 3.1 Pro | 200K tokens | Task acceptance criteria reference FMEA constraints. Logic involves engine-semantic reasoning (timer pause behavior, counter non-reset, Entity binding races, formation hierarchy preservation). Spatial planning for coordinate generation. Architectural decisions with long-term coupling. |
| **Tier 2** — Standard Execution & Coding | Feature implementation, GUI forms, straightforward algorithms, file I/O, test harnesses, PyQt6 widgets, data extraction | Claude Sonnet 4.6 / Gemini 3 Flash | 200K tokens | Standard coding with well-defined specs. The bulk of the project's code volume. |
| **Tier 3** — Boilerplate, Scaffolding, & Formatting | File scaffolding, template population, documentation formatting, config files, repetitive data entry, prompt header generation | Claude Haiku 4.5 / Gemini 3.1 Flash-Lite | 200K tokens | Pure boilerplate with no behavioral logic. |

### Context Window Implications

- The decision rule: if the task's acceptance criteria reference an FMEA constraint ID or require reasoning about engine runtime behavior, use Tier 1. If the criteria are purely structural (does it compile, does the form render, does the file parse), Tier 2 is sufficient. Scaffolding and documentation use Tier 3.
- Prompt headers for Tier 1 tasks must include the full FMEA constraint text and relevant specification sections to avoid requiring the model to retrieve this from memory.
- Repository map configuration must exclude `tests/fixtures/il2_files/` and `docs/IL-2_Sturmovik_Mission_Editor_Manual.pdf` (300+ MB of binary data) to stay within context windows. The PDF is also gitignored.

---

## 2. Project Overview

### 2.1 Purpose

This plan sequences the development of the IL-2 Modular Mission Orchestrator from foundational tooling through to a complete EMG-class mission generator. The architecture is three layers: a shared IL-2 ASCII parser library at the base, a tool suite of three independent backend components in the middle (MMF Compiler, Module Reverse Engineer, Map Data Extractor), and user-facing applications on top (GUI, CLI, and the future Orchestrator). The entire project is Python. No language migration is planned or required.

Each phase produces a usable deliverable. No phase depends on a future phase to be useful. The project can stop at any phase boundary and the completed work has standalone value.

Tasks flagged HUMAN require action from the project owner (file collection, in-game testing, design decisions, hardware access). AI sessions cannot proceed past a HUMAN gate until the required input is provided.

### 2.2 Stakeholders

| Role | Name / Team | Responsibilities |
|---|---|---|
| Owner / Lead | GhengisPliskin | Project direction, in-game testing, human gates, FMEA calibration, DServer operation, design decisions |

### 2.3 Success Criteria

1. Static CAP .Group compiles from JSON and flies correctly in-game (Phase 1 deliverable)
2. 3+ module types proven compositional — modules interoperate when wired together (Phase 3 deliverable)
3. 180-minute DServer session runs stable without AI slot leaks or tickrate degradation (Phase 5 deliverable)
4. Standalone Windows .exe generates flyable missions without requiring a Python installation (Phase 6 deliverable)
5. An external contributor can add a new module type using only the documentation — no core code changes needed (Phase 6 deliverable)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-001 | Parse IL-2 .Mission/.Group ASCII files into Python data structures with round-trip fidelity | Must | Spec §2.1 |
| FR-002 | Serialize Python data structures back into valid IL-2 ASCII syntax loadable in BOSEditor | Must | Spec §2.2 |
| FR-003 | Compile MMF JSON intermediary into .Group ASCII files with correct ID assignment, spatial offsets, and Entity bindings | Must | Spec §2-5 |
| FR-004 | Validate all MCU command nodes against Required Field Schema before emission | Must | Spec §3.1, PI-001 |
| FR-005 | Strip reserved IL-2 syntax characters from user-supplied string fields | Must | Spec §2.1, PI-002 |
| FR-006 | Preserve formation Target Link hierarchies through Magazine Array activation | Must | Spec §5.2.1, EC-003 |
| FR-007 | Implement dual-path garbage collection (OnKilled + Despawn) with next-wave counter advancement | Must | Spec §5.3, SM-004 |
| FR-008 | Implement Command Buffer serialization with staggered timers (50-100ms) | Must | Spec §4.1.1, SM-001 |
| FR-009 | Provide PyQt6 GUI for module configuration, JSON export, and compilation | Should | Phase 2 |
| FR-010 | Extract airfield coordinates, runway headings, and spawn positions from stock .Mission files | Should | Phase 4 |
| FR-011 | Generate complete .Mission files from high-level scenario parameters | Should | Phase 5 |
| FR-012 | Support DServer mission rotation with automated batch generation | Could | Phase 5 |
| FR-013 | Implement inter-mission state feedback from DServer logs | Could | Phase 5 |

### 3.2 Non-Functional Requirements

| ID | Requirement | Category | Threshold |
|---|---|---|---|
| NFR-001 | Active AI units must not exceed ~100 during any server tick | Performance | GUI warns at 80; compiler enforces via GC-gated activation |
| NFR-002 | 180-minute continuous DServer session without tickrate degradation | Performance | SPS remains above physics simulation threshold throughout session |
| NFR-003 | Command Buffer serialization delay must not exceed 200ms | Performance | Prevents AI command-vacuum behavioral drift |
| NFR-004 | Entity proxy binding must include 2-second post-Activate delay | Reliability | Prevents silent binding failure during mass activation |
| NFR-005 | Compiled .Group files must load without error in BOSEditor | Correctness | Zero tolerance — single malformed field causes cascade failure |
| NFR-006 | Standalone .exe generation time under 30 seconds for a complete mission | Usability | Phase 5 GUI target |

### 3.3 Constraints

| ID | Constraint | Type | Impact |
|---|---|---|---|
| C-001 | Python 3.10+ | Tech Stack | Minimum runtime version for all components |
| C-002 | PyQt6 for GUI | Tech Stack | Framework locked; no web/Electron alternatives |
| C-003 | JSON Schema Draft 7 | Tech Stack | Intermediary format validation standard |
| C-004 | IL-2 ASCII format undocumented | Format | Parser must handle syntax empirically; zero official spec |
| C-005 | DServer multiplayer environment | Runtime | Output must run on dedicated server |
| C-006 | Windows primary target | Platform | PyInstaller distribution targets .exe |
| C-007 | No external database | Infrastructure | All data file-based (.json, .Group, .Mission) |

See `CONSTRAINTS.md` for the complete constraint register including engine runtime constraints and FMEA traceability.

---

## 4. Architecture & Directory Structure

### 4.1 High-Level Architecture

The system is organized in three layers. Layer 1 (Shared Foundation) provides the IL-2 ASCII parser library and JSON Schema validation — every other component imports from this layer. Layer 2 (Backend Tool Suite) contains four independent tools: the MMF Compiler (JSON → .Group), the Module Reverse Engineer (.Group → JSON), the Map Data Extractor (.Mission → geographic JSON), and the Mission Orchestrator (scenario → .Mission). Layer 3 (User-Facing Applications) provides the PyQt6 GUI and CLI interfaces.

See `ARCHITECTURE.md` for the full three-layer diagram, detailed directory structure, phase mapping table, FMEA constraints by layer, dependency graph, import structure, and testing strategy.

### 4.2 Directory Structure

```
il2-mmo/
├── src/
│   ├── mmf/                     # Shared framework (Layer 1)
│   │   ├── parser/              # IL-2 ASCII Parser [Phase 0.2 COMPLETE]
│   │   ├── schema/              # JSON Schema Contract [Phase 0.5]
│   │   ├── compiler/            # MMF Compiler [Phase 1]
│   │   ├── validation/          # FMEA Constraint Checking
│   │   └── utils/
│   ├── backend/                 # Backend tools (Layer 2)
│   │   ├── mre/                 # Module Reverse Engineer [Phase 2]
│   │   ├── map_extractor/       # Map Data Extraction [Phase 4]
│   │   └── orchestrator/        # Mission Orchestrator [Phase 5]
│   └── ui/                      # User-facing interfaces (Layer 3)
│       ├── gui/                 # PyQt6 GUI [Phase 2]
│       └── cli/                 # CLI Interface [Phase 5+]
├── tests/
├── data/
├── docs/                        # includes KANBAN_SETUP.md, FMEA.md, prompt headers
├── ARCHITECTURE.md
├── CONSTRAINTS.md
├── KEY_DECISION_LOG.md
├── CODE_DECISION_LOG.md
├── README.md
│
└── working/                     # Ephemeral per-session scratch space
    └── CODE_DECISIONS_PATCH.md  # Provisional decisions — merged into CODE_DECISION_LOG.md at HUMAN gate
```

### 4.3 Component Descriptions

| Component | Responsibility | Interfaces | Key Files |
|---|---|---|---|
| Parser Library | Read/write IL-2 ASCII .Group/.Mission files | Python dict ↔ IL-2 ASCII | `src/mmf/parser/deserializer.py`, `src/mmf/parser/serializer.py` |
| JSON Schema | Define and validate MMF intermediary format | JSON Schema Draft 7 | `src/mmf/schema/v2_0.py`, `data/schemas/mmf-module-schema-v2_0.json` |
| MMF Compiler | Compile MMF JSON into .Group ASCII | JSON input → .Group output | `src/mmf/compiler/compiler.py`, `src/mmf/compiler/modules/` |
| Module Reverse Engineer | Parse hand-built .Group into MMF JSON | .Group input → JSON output | `src/backend/mre/extractor.py` |
| Map Data Extractor | Extract geographic data from stock .Mission files | .Mission input → JSON database | `src/backend/map_extractor/extractor.py` |
| Mission Orchestrator | Generate complete .Mission from scenario parameters | Scenario config → .Mission output | `src/backend/orchestrator/scenario_engine.py` |
| PyQt6 GUI | Module configuration, compilation, export | User input → JSON → Compiler | `src/ui/gui/main_window.py` |

---

## 5. Risk Register (FMEA)

14 failure points identified across four domains: Pipeline Integrity (4), Engine Limitation Compliance (3), State Management (4), and Environmental/Configuration (3). Four are rated CRITICAL, seven HIGH, three MEDIUM, one LOW.

**Action threshold:** RPN ≥ 100 requires a mitigation plan before any dependent task begins.

**Amendment protocol:** Changes to this register during execution require an FMEA Amendment Proposal (Ground Rule 9). See `docs/templates/templates.md` for the template.

| ID | Severity | Failure Mode | RPN | Status |
|---|---|---|---|---|
| PI-001 | CRITICAL | Null Targets[] array crashes DServer | 210 | Open |
| PI-002 | HIGH | Reserved-char injection corrupts MCU blocks | 160 | Open |
| PI-003 | CRITICAL | ID namespace collision on multi-import | 210 | Open |
| PI-004 | MEDIUM | Overlapping remote coordinate zones | 100 | Open |
| EL-001 | CRITICAL | Magazine Array counter state persists through deactivation | 210 | Open |
| EL-002 | HIGH | Entity proxy binds before 3D instantiation | 160 | Open |
| EL-003 | CRITICAL | Entity binding self-reference (swapped values) | 210 | Open |
| SM-001 | HIGH | Same-tick command interleaving race condition | 160 | Open |
| SM-002 | HIGH | Leader-kill orphans wingmen permanently | 160 | Open |
| SM-003 | HIGH | Timer pause semantics cause premature firing | 160 | Open |
| SM-004 | LOW | Early kill stalls Magazine Array permanently | 27 | Open |
| EC-001 | MEDIUM | Init delay insufficient for large entity counts | 100 | Open |
| EC-002 | MEDIUM | Stub timer collides with future real MCUs | 100 | Open |
| EC-003 | HIGH | MCU_CMD_Spawn breaks formation hierarchies | 160 | Open |
| EC-004 | HIGH | Wave activation without GC gate breaches AI cap | 160 | Open |

> S/O/D scores are DRAFT — derived from qualitative severity labels. Awaiting calibration by Project Owner.

See `docs/FMEA.md` for the complete register with S/O/D/RPN values, mitigations, and revision history.
See `docs/MMF_FMEA_Report_v2.md` for the full analytical narrative and amendment review.

---

## 6. Task Registry

### Master Task Table

37 AI tasks, 17 human gates, 54 total tasks across 7 phases.

| Task ID | Task Name | Component | Complexity | Tier | Depends On | Delivers To | FMEA Refs | Boundary | Phase |
|---|---|---|---|---|---|---|---|---|---|
| 0.1 | Collect reference .Group/.Mission files | Data | L | — | None | 0.2 | None | human-only | 0 |
| 0.2 | Build IL-2 ASCII parser | Parser lib | H | 1 | 0.1 | 0.3, 0.4, 1.x | None | ai-with-review | 0 |
| 0.3 | Build ASCII writer | Parser lib | M | 2 | 0.2 | 1.x | None | ai-eligible | 0 |
| 0.4 | Build MCU type catalog | Parser lib | M | 2 | 0.1 | 1.3, 1.8 | None | ai-eligible | 0 |
| 0.5 | Define JSON schema contract | Schema | H | 1 | None | 0.5h, 1.1, 2.3 | None | ai-with-review | 0 |
| 0.5h | Approve JSON schema contract | Schema | L | — | 0.5 | Phase 1 | None | human-only | 0 |
| 0.6 | Create Python project structure | Project | L | 3 | None | Phase 1 | None | ai-eligible | 0 |
| 1.1 | Implement monotonic ID generator | Compiler | M | 2 | 0.5 | 1.2, 1.3, 1.5, 1.7 | PI-003 | ai-with-review | 1 |
| 1.2 | Implement spatial offset engine | Compiler | M | 2 | 1.1 | 1.10 | PI-004 | ai-eligible | 1 |
| 1.3 | Implement flight emitter | Compiler | H | 1 | 0.4, 1.1 | 1.4, 1.6, 1.10 | EL-003 | ai-with-review | 1 |
| 1.4 | Implement Magazine Array activator | Compiler | H | 1 | 1.3 | 1.6, 1.9, 1.10 | EL-001, EL-002, EC-003 | ai-with-review | 1 |
| 1.5 | Implement Command Buffer | Compiler | H | 1 | 1.1 | 1.10 | SM-001, SM-003 | ai-with-review | 1 |
| 1.6 | Implement garbage collection | Compiler | H | 1 | 1.3, 1.4 | 1.10 | SM-002, SM-004 | ai-with-review | 1 |
| 1.7 | Implement dependency stub system | Compiler | M | 2 | 1.1 | 1.10 | EC-002 | ai-eligible | 1 |
| 1.8 | Implement validator + reserved-char filter | Compiler | M | 2 | 0.4 | 1.10 | PI-001, PI-002 | ai-eligible | 1 |
| 1.9 | Implement initialization buffer | Compiler | M | 2 | 1.4 | 1.10 | EC-001 | ai-eligible | 1 |
| 1.10 | Compose Static CAP module | Compiler | H | 1 | 1.1–1.9 | 1.10h, 2.2, 2.5, 3.x | All PI/EL/SM/EC | ai-with-review | 1 |
| 1.10h | In-game test: Static CAP | Testing | M | — | 1.10 | Phase 2 | None | human-only | 1 |
| 2.1 | Build Module Reverse Engineer | MRE | H | 1 | 0.2, 0.4 | 2.2 | None | ai-with-review | 2 |
| 2.1h | Provide hand-built .Group files | Data | L | — | None | 2.2 | None | human-only | 2 |
| 2.2 | Build validation corpus | MRE + Compiler | H | 1 | 1.10, 2.1, 2.1h | Phase 3 | None | ai-with-review | 2 |
| 2.3 | Build GUI shell | GUI | M | 2 | 0.5 | 2.4 | None | ai-eligible | 2 |
| 2.4 | Implement Static CAP parameter form | GUI | M | 2 | 2.3 | 2.5, 2.6 | None | ai-eligible | 2 |
| 2.5 | Implement JSON export + compile wiring | GUI | M | 2 | 2.4, 1.10 | 2.5h, 3.x | PI-002 | ai-eligible | 2 |
| 2.5h | In-game test: GUI-compiled module | Testing | M | — | 2.5 | Phase 3 | None | human-only | 2 |
| 2.6 | Add AI cap display | GUI | L | 2 | 2.4 | None | EC-004 | ai-eligible | 2 |
| 3.1 | Intercept module | Compiler + GUI | M | 2 | 1.10, 2.5 | 3.1h | None | ai-eligible | 3 |
| 3.1h | In-game test: Intercept | Testing | M | — | 3.1 | 3.5 | None | human-only | 3 |
| 3.2 | Scramble module | Compiler + GUI | H | 1 | 3.1 | 3.2h | None | ai-with-review | 3 |
| 3.2h | In-game test: Scramble | Testing | M | — | 3.2 | 3.5 | None | human-only | 3 |
| 3.3 | Ground Attack module | Compiler + GUI | M | 2 | 1.10, 2.5 | 3.3h | None | ai-eligible | 3 |
| 3.3h | In-game test: Ground Attack | Testing | M | — | 3.3 | 3.5 | None | human-only | 3 |
| 3.4 | Bomber Escort module | Compiler + GUI | H | 1 | 3.1 | 3.4h | None | ai-with-review | 3 |
| 3.4h | In-game test: Bomber Escort | Testing | M | — | 3.4 | 3.5 | None | human-only | 3 |
| 3.5 | Cross-module integration test | Testing | H | — | 3.1h–3.4h | Phase 5 | None | human-only | 3 |
| 4.0h | Provide stock .Mission files per map | Data | L | — | None | 4.1 | None | human-only | 4 |
| 4.1 | Build Map Data Extractor | MDE | M | 2 | 0.2, 0.4, 4.0h | 4.2, 4.2h, 4.3 | None | ai-eligible | 4 |
| 4.2h | In-editor validation: airfield coords | Testing | L | — | 4.1 | 4.2 | None | human-only | 4 |
| 4.2 | Extract data for primary maps | MDE + Data | M | 2 | 4.1, 4.2h | 4.4, 4.5, 5.x | None | ai-eligible | 4 |
| 4.3 | Extract front-line reference data | MDE + Data | M | 2 | 4.1 | 5.3 | None | ai-eligible | 4 |
| 4.4 | Build route generation utility | MDE | H | 1 | 4.2 | 5.3 | None | ai-with-review | 4 |
| 4.5 | Add remaining maps | MDE + Data | M | 2 | 4.2 | 5.x | None | ai-eligible | 4 |
| 5.1 | Build mission assembly engine | Orchestrator | H | 1 | 1.10, 4.2 | 5.2 | None | ai-with-review | 5 |
| 5.2 | Implement player spawn management | Orchestrator | H | 1 | 5.1, 4.2 | 5.2h, 5.3 | None | ai-with-review | 5 |
| 5.2h | DServer test: MP connection | Testing | M | — | 5.2 | 5.3 | None | human-only | 5 |
| 5.3 | Implement scenario templates | Orchestrator | H | 1 | 5.1, 5.2, 4.3 | 5.4, 5.5 | None | ai-with-review | 5 |
| 5.4 | Implement ambient AI | Orchestrator | M | 2 | 5.3 | 5.5 | EC-004 | ai-eligible | 5 |
| 5.5 | Build Orchestrator GUI | Orchestrator GUI | M | 2 | 5.3, 2.3 | 5.5h, 5.6 | None | ai-eligible | 5 |
| 5.5h | In-game test: generated missions | Testing | M | — | 5.5 | 5.6 | None | human-only | 5 |
| 5.6 | Implement DServer rotation | Orchestrator | M | 2 | 5.5 | 5.6h, 5.7 | None | ai-eligible | 5 |
| 5.6h | DServer test: 3+ hour rotation | Testing | H | — | 5.6 | 5.7 | None | human-only | 5 |
| 5.7 | Implement inter-mission state feedback | Orchestrator | H | 1 | 5.6 | Phase 6 | None | ai-with-review | 5 |
| 6.1 | Package with PyInstaller | Distribution | M | 2 | 5.5 | 6.4 | None | ai-eligible | 6 |
| 6.2 | Write user documentation | Docs | M | 2 | 5.5 | 6.4 | None | ai-eligible | 6 |
| 6.3 | Write contributor documentation | Docs | M | 2 | 5.5 | 6.4 | None | ai-eligible | 6 |
| 6.4 | Community beta | Testing | H | — | 6.1, 6.2 | None | None | human-only | 6 |

### Two-Phase Commit Applicability

- Tasks marked Tier 1 or Tier 2: Two-Phase Commit is mandatory.
- Tasks marked Tier 3: Two-Phase Commit applies only if FMEA Refs is non-empty.
- Tasks tagged `[SPIKE]`: exempt from Two-Phase Commit (Ground Rule 7).

### Dependency Graph

```
Phase 0 (Parser + Schema)
    ↓
    ├→ Phase 1 (Compiler)
    │   ↓
    │   ├→ Phase 2 (GUI + MRE)
    │   │   ↓
    │   │   └→ Phase 3 (Module Types)
    │   │       ↓
    │   │       └→ Phase 5 (Orchestrator)
    │   │
    │   └→ Phase 5 (Orchestrator)
    │
    └→ Phase 4 (Map Extractor) [Can run parallel with Phases 1-3]
        ↓
        └→ Phase 5 (Orchestrator)

Phase 5 → Phase 6 (Distribution)
```

### Phase Detail Tables

The following subsections preserve the original per-phase task breakdowns with full descriptions and acceptance criteria.

#### Phase 0 — Foundation

**Goal:** Shared parser library + JSON schema contract

Everything depends on this. The parser is the shared foundation that every other component imports. The JSON schema is the contract between frontend and backend.

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **0.1** | Collect 10+ reference .Group and .Mission files from your IL-2 installation (data/Missions/, stock campaigns, community libraries). Must include formation hierarchies, complex trigger chains, and multiplayer templates. | Data | None | **HUMAN** | N/A | Files accessible in working directory. Diverse MCU types represented. |
| **0.2** | Build the IL-2 ASCII parser: read .Mission/.Group files into Python dictionaries. Handle all block types, nested blocks, key-value pairs, arrays, quoted strings. | Parser lib | 0.1 | **AI** | Opus 4.6 / 3.1 Pro | Round-trip: parse every reference file, re-serialize, diff. Output matches input (whitespace-normalized). |
| **0.3** | Build the ASCII writer: serialize Python dictionaries back into valid IL-2 ASCII syntax. | Parser lib | 0.2 | **AI** | Sonnet 4.6 / 3 Flash | Written output loads without error in IL-2 Mission Editor. |
| **0.4** | Build the MCU type catalog: document required vs. optional fields, value types, and valid ranges for every MCU type in the reference corpus. | Parser lib | 0.1 | **AI** | Sonnet 4.6 / 3 Flash | Catalog covers all MCU types in corpus. Each entry specifies required fields, types, constraints. |
| **0.5** | Define the JSON schema contract. Must include: mmf_version, output_mode (group/mission), mission_properties (null for group mode), `modules[]` array. Extensible without breaking changes. | Schema | None | **AI** | Opus 4.6 / 3.1 Pro | Schema validates against JSON Schema Draft 7. Approved by project owner. |
| **0.5h** | REVIEW: Approve the JSON schema contract. This is the interface between frontend and backend — changes after approval require coordinated rewrites. | Schema | 0.5 | **HUMAN** | N/A | Project owner signs off on schema structure and module type list. |
| **0.6** | Create Python project structure: mmf/ with parser/, compiler/, reverse/, extractor/, gui/, orchestrator/, data/ subdirectories. Packaging, imports, test harness. | Project | None | **AI** | Haiku 4.5 / 3.1 Flash-Lite | pytest runs. Each package imports parser/ cleanly. |

#### Phase 1 — Core compiler + first module

**Goal:** Compile a Static CAP .Group that flies correctly in-game

Validates the entire compiler pipeline. All FMEA constraints have explicit acceptance criteria. The Static CAP requires zero dynamic player triggers, making failures attributable to the compiler.

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **1.1** | Implement monotonic ID generator (PI-003). Initializes from max(existing Index) + 1. Global counter, never resets per module. | Compiler | 0.5 | **AI** | Sonnet 4.6 / 3 Flash | Import 10 copies of same module. Zero ID collisions. IDs strictly ascending. |
| **1.2** | Implement spatial offset engine (PI-004). Internal MCUs to remote zone (50km+). 1000m Z-axis increment per module. | Compiler | 1.1 | **AI** | Sonnet 4.6 / 3 Flash | Two modules in same session: non-overlapping remote coordinates. |
| **1.3** | Implement flight emitter: aircraft hierarchy (leader + wingmen), Target Links preserved, Enabled=FALSE, Entity proxy with verified two-way binding (EL-003). | Compiler | 0.4, 1.1 | **AI** | Opus 4.6 / 3.1 Pro | Post-emission assertion passes: Entity.MisObjID == Aircraft.Index, Aircraft.LinkTrId == Entity.Index, no self-reference. |
| **1.4** | Implement Magazine Array activator (EL-001, EC-003): wave_count deactivated flights, MCU_Counter Reset=TRUE, 2s post-Activate Entity delay (EL-002). Spawn prohibited. | Compiler | 1.3 | **AI** | Opus 4.6 / 3.1 Pro | Counter never deactivated. Wave count validated. Activate/Deactivate only. |
| **1.5** | Implement Command Buffer with serialization (SM-001, SM-003): Deactivate → 50–100ms Timer → Activate. Timer pool, no reuse. Staggered per [IN] port. | Compiler | 1.1 | **AI** | Opus 4.6 / 3.1 Pro | Two simultaneous [IN] signals: deterministic, non-interleaved transitions. |
| **1.6** | Implement garbage collection: dual-path (SM-004), leader-kill resilience (SM-002). RTB to all flight members. OnKilled → ForceComplete → 30s Timer → Despawn. | Compiler | 1.3, 1.4 | **AI** | Opus 4.6 / 3.1 Pro | Leader killed: wingmen get ForceComplete + Despawn. Counter advances from both paths. |
| **1.7** | Implement dependency stub system (EC-002): reserved ID range 900000–999999, manifest comment block. | Compiler | 1.1 | **AI** | Sonnet 4.6 / 3 Flash | Stub generated for missing [OUT] target. No ID collision. |
| **1.8** | Implement Required Field Schema validator (PI-001) and reserved-char filter (PI-002). Halt on null Targets/Objects. Strip `{}[];=` from strings. | Compiler | 0.4 | **AI** | Sonnet 4.6 / 3 Flash | Compilation aborts on null Target array. Reserved chars stripped. |
| **1.9** | Implement initialization buffer (EC-001): Master Core, configurable delay (default 3s). Warning if entities > 200 and delay < 5s. | Compiler | 1.4 | **AI** | Sonnet 4.6 / 3 Flash | Warning emitted for 250-entity mission with 3s delay. |
| **1.10** | Compose all primitives into Static CAP module: waypoint loop, AttackArea, Magazine Array, Command Buffer, GC, Entity proxies, I/O proxy nodes. | Compiler | 1.1–1.9 | **AI** | Opus 4.6 / 3.1 Pro | Compiled .Group imports into BOSEditor without errors. |
| **1.10h** | IN-GAME TEST: Import compiled .Group into BOSEditor. Fly 30-minute test session. Verify: AI patrols, engages targets, RTBs on ToS, gets despawned, next wave activates. Report results. | Testing | 1.10 | **HUMAN** | N/A | 30-min session stable. AI behavior matches spec. No AI slot leaks. |

#### Phase 2 — GUI + Module Reverse Engineer

**Goal:** User-facing module constructor + validation corpus (parallel tracks)

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **2.1** | Build Module Reverse Engineer: parse .Group ASCII into MMF JSON. Validate against revised spec constraints. Output structured audit report. | MRE | 0.2, 0.4 | **AI** | Opus 4.6 / 3.1 Pro | Hand-built .Group parses to JSON. Constraint violations detected and reported. |
| **2.1h** | Provide 5+ hand-built .Group files of varying complexity for the validation corpus. Must include formation flights, trigger chains, and timer logic. | Data | None | **HUMAN** | N/A | Files cover diverse MCU patterns. Complexity ranges from simple to multi-flight. |
| **2.2** | Build validation corpus: reverse-engineer hand-built .Groups, diff MRE output against compiler output for equivalent configs. Document discrepancies. | MRE + Compiler | 1.10, 2.1, 2.1h | **AI** | Opus 4.6 / 3.1 Pro | Every discrepancy explained as compiler bug (fixed) or hand-built deviation. |
| **2.3** | Build GUI shell: PyQt6 app with module selection pane, dynamic parameter form, compile button, JSON export. | GUI | 0.5 | **AI** | Sonnet 4.6 / 3 Flash | App launches. Module types listed. Form renders for Static CAP. |
| **2.4** | Implement Static CAP parameter form: aircraft type, AI skill, payload, fuel (0.1–1.0), wave count (1–50), ToS (min), X/Z coords, init delay (3–10s). | GUI | 2.3 | **AI** | Sonnet 4.6 / 3 Flash | All fields validate. Session formula checked. AI cap warning displayed. |
| **2.5** | Implement JSON export with IL-2 reserved-char sanitization. Wire Compile button to MMF Compiler. | GUI | 2.4, 1.10 | **AI** | Sonnet 4.6 / 3 Flash | End-to-end: GUI → compile → import → fly. Works identically to CLI. |
| **2.5h** | IN-GAME TEST: Use GUI to configure and compile a module. Import into BOSEditor, fly the mission. Verify identical behavior to CLI-compiled output. | Testing | 2.5 | **HUMAN** | N/A | GUI-compiled module behavior matches CLI-compiled baseline. |
| **2.6** | Add calculated AI cap display: `max_concurrent_AI = flight_size × max_simultaneous_waves`. Warning if > 80. | GUI | 2.4 | **AI** | Sonnet 4.6 / 3 Flash | Display updates dynamically. Warning triggers at threshold. |

#### Phase 3 — Additional module types

**Goal:** 3+ validated module types proving compositional architecture

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **3.1** | Intercept module: non-looping waypoint chain, AttackArea, Magazine Array, GC. Reuses Phase 1 primitives. | Compiler + GUI | 1.10, 2.5 | **AI** | Sonnet 4.6 / 3 Flash | AI flies to intercept, engages, RTBs or GC'd. No new primitives. |
| **3.1h** | IN-GAME TEST: Fly intercept module. Verify AI intercept behavior, engagement, RTB, GC. | Testing | 3.1 | **HUMAN** | N/A | AI behavior correct. GC functions. Stable 30-min session. |
| **3.2** | Scramble module: takeoff sequence, ComplexTrigger altitude gate, then intercept. New primitive: `emit_takeoff_sequence()`. | Compiler + GUI | 3.1 | **AI** | Opus 4.6 / 3.1 Pro | AI starts parked, taxis, takes off, clears altitude gate, executes intercept. |
| **3.2h** | IN-GAME TEST: Fly scramble module. Verify taxi, takeoff, altitude gate, intercept transition. | Testing | 3.2 | **HUMAN** | N/A | Full scramble sequence executes. No logic gaps at gate transition. |
| **3.3** | Ground Attack module: waypoint chain to target, AttackArea (ground). May need: `emit_attack_ground()`. | Compiler + GUI | 1.10, 2.5 | **AI** | Sonnet 4.6 / 3 Flash | AI attacks ground objects. [OUT]_Success on target destruction. |
| **3.3h** | IN-GAME TEST: Fly ground attack module. Verify ground engagement, destruction detection, [OUT]_Success firing. | Testing | 3.3 | **HUMAN** | N/A | AI attacks ground targets. [OUT]_Success fires on threshold. 30-min session stable. |
| **3.4** | Bomber Escort module: Cover/Attack toggle, proximity logic. New primitive: `emit_cover_attack_toggle()`. | Compiler + GUI | 3.1 | **AI** | Opus 4.6 / 3.1 Pro | Escort covers bomber, engages threats, returns to cover. |
| **3.4h** | IN-GAME TEST: Fly bomber escort module. Verify Cover/Attack cycling, CheckZone management, bomber-lost fallback. | Testing | 3.4 | **HUMAN** | N/A | Multiple Cover/Attack cycles without timer corruption. Bomber-lost triggers fallback. 30-min session stable. |
| **3.5** | Cross-module integration test: import 2+ modules into same .Mission in BOSEditor. Wire [OUT] to [IN]. Verify interop. | Testing | 3.1–3.4h | **HUMAN** | N/A | Modules interoperate. AI cap never exceeded. 60-min session stable. |

#### Phase 4 — Map Data Extractor + geographic databases

**Goal:** Machine-readable map data for orchestrator (can run parallel with Phases 1–3)

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **4.0h** | Provide stock .Mission files from IL-2 installation for each owned map (Stalingrad, Moscow, Kuban, Rhineland, etc.). Include multiplayer templates. | Data | None | **HUMAN** | N/A | Files accessible. At least 5 maps represented. |
| **4.1** | Build Map Data Extractor: parse .Mission files, identify airfield objects, extract coordinates, runway headings, spawn positions. Output JSON per map. | MDE | 0.2, 0.4, 4.0h | **AI** | Sonnet 4.6 / 3 Flash | Processes stock files. Airfield coords match BOSEditor. |
| **4.2h** | IN-EDITOR VALIDATION: Spot-check extracted airfield coordinates against BOSEditor positions for each map. | Testing | 4.1 | **HUMAN** | N/A | Coordinates verified for all extracted airfields. |
| **4.2** | Extract data for primary maps. Cross-reference against community airfield databases. | MDE + Data | 4.1, 4.2h | **AI** | Sonnet 4.6 / 3 Flash | Geo database for 5+ maps. Validated. |
| **4.3** | Extract front-line reference data: icon translator positions from stock multiplayer templates. | MDE + Data | 4.1 | **AI** | Sonnet 4.6 / 3 Flash | Front-line data for 2+ scenarios per map. |
| **4.4** | Build route generation utility: start airfield → target area → return, with plausible altitudes/speeds. | MDE | 4.2 | **AI** | Opus 4.6 / 3.1 Pro | Generated route loads in BOSEditor. Tactically plausible. |
| **4.5** | Add remaining maps. Establish repeatable process for future DLC maps. | MDE + Data | 4.2 | **AI** | Sonnet 4.6 / 3 Flash | Process documented. New map extractable within 1 day. |

#### Phase 5 — Mission Orchestrator

**Goal:** Full .Mission file generation from high-level scenario parameters

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **5.1** | Build mission assembly engine: merge multiple .Group blocks into single .Mission with mission properties, coalitions, mission begin/end translators. | Orchestrator | 1.10, 4.2 | **AI** | Opus 4.6 / 3.1 Pro | Assembled .Mission loads in DServer. All modules activate. |
| **5.2** | Implement player spawn management: airfield objects, plane sets, spawn points, briefing text. SP and MP modes. | Orchestrator | 5.1, 4.2 | **AI** | Opus 4.6 / 3.1 Pro | Player spawns correctly. MP clients can join. |
| **5.2h** | DSERVER TEST: Load assembled .Mission on DServer. Verify MP client connection, spawning, and mission execution. | Testing | 5.2 | **HUMAN** | N/A | MP session functional. Players spawn and fly. |
| **5.3** | Implement scenario templates: Intercept, Patrol, Ground Attack, Escort, Free Hunt. Auto-wire modules, calculate coordinates from front lines. | Orchestrator | 5.1, 5.2, 4.3 | **AI** | Opus 4.6 / 3.1 Pro | Select Intercept on Stalingrad → complete flyable mission. AI correct. |
| **5.4** | Implement ambient AI: background transport, artillery, convoys using lightweight modules. | Orchestrator | 5.3 | **AI** | Sonnet 4.6 / 3 Flash | Ambient AI visible. Total AI within cap. |
| **5.5** | Build Orchestrator GUI: map selector, scenario type, difficulty, weather/time, Generate button. | Orchestrator GUI | 5.3, 2.3 | **AI** | Sonnet 4.6 / 3 Flash | User generates complete .Mission in under 30 seconds. |
| **5.5h** | IN-GAME TEST: Generate 5+ missions across different maps and scenario types. Fly each. Report issues. | Testing | 5.5 | **HUMAN** | N/A | All generated missions flyable. AI behavior correct per scenario. |
| **5.6** | Implement DServer rotation: batch generation, SDS config update, rotation scheduling. | Orchestrator | 5.5 | **AI** | Sonnet 4.6 / 3 Flash | 10 missions generated. DServer cycles automatically. |
| **5.6h** | DSERVER TEST: Run automated rotation for 3+ hours. Monitor stability, mission transitions, player experience. | Testing | 5.6 | **HUMAN** | N/A | 3+ hour rotation stable. No crashes or AI leaks across transitions. |
| **5.7** | Implement inter-mission state feedback: read DServer logs, extract results, feed to next mission generation. | Orchestrator | 5.6 | **AI** | Opus 4.6 / 3.1 Pro | Post-Axis win: next mission has stronger Allied intercepts. Progression measurable. |

#### Phase 6 — Distribution + community

**Goal:** Standalone executable, documentation, community onboarding

| # | Task | Component | Dep. | Actor | Model tier | Acceptance criteria |
|---|---|---|---|---|---|---|
| **6.1** | Package with PyInstaller: standalone .exe for Windows. Include all dependencies, map databases, module templates. | Distribution | 5.5 | **AI** | Sonnet 4.6 / 3 Flash | User downloads .exe, runs without Python, generates a mission. |
| **6.2** | Write user documentation: getting started, module reference, scenario descriptions, DServer guide. | Docs | 5.5 | **AI** | Sonnet 4.6 / 3 Flash | New user generates and flies a mission within 10 minutes. |
| **6.3** | Write contributor documentation: architecture overview, adding modules, adding maps, extending type catalog. | Docs | 5.5 | **AI** | Sonnet 4.6 / 3 Flash | External contributor adds module type from guide. No core changes needed. |
| **6.4** | Community beta: release to IL-2 server operators and mission designers for real-world testing. | Testing | 6.1, 6.2 | **HUMAN** | N/A | 10+ hours MP server time. Feedback incorporated. |

---

## 7. Kanban Board Configuration

See `docs/KANBAN_SETUP.md` for the full board configuration including columns, WIP limits, entry/exit criteria, automation rules, and label taxonomy.

### Summary

| Column | WIP Limit |
|---|---|
| Triage | None |
| Ready | 10 |
| In Progress | 5 |
| In Review | 5 |
| Done | None |
| Blocked | None |

**Spike Constraint (Ground Rule 7):** Issues labeled `spike` cannot move to "Done" until a linked formalization issue reaches "In Review."

---

## 8. Operational Ground Rules

These rules are non-negotiable for all contributors (human and AI).

| # | Rule | Enforcement Mechanism |
|---|---|---|
| 1 | **Issue Binding** — No code or documentation generated without an active, assigned Issue. | PR template requires Issue reference. AI prompt headers include Issue ID. |
| 2 | **Decision Logging** — All architectural decisions → KEY_DECISION_LOG.md. All code decisions → `working/CODE_DECISIONS_PATCH.md` during active development. Patch merged into CODE_DECISION_LOG.md at HUMAN gate on phase sign-off. Templates enforced. | PR review checklist includes decision log verification and patch merge confirmation. |
| 3 | **State Synchronization** — AI agents explicitly state Kanban column changes at start and end of every action. | Prompt headers include State Sync section. |
| 4 | **Source Truth** — ARCHITECTURE.md updated concurrently with any structural change. | PR review checklist includes architecture drift check. |
| 5 | **Constraint Traceability** — Any decision impacting an FMEA constraint references the FMEA ID in the decision log and prompt header. | FMEA labels on Issues. Prompt headers include FMEA reference field. |
| 6 | **Template Adherence** — AI must execute a file read on templates before generating any project file. No reconstruction from memory. | Embedded in workflow. Templates at `docs/templates/templates.md`. |
| 7 | **[SPIKE] Exemption** — Spike issues bypass structural requirements. Formalization required before Done. | `spike` label + Kanban Done-lock. |
| 8 | **Execution-Locked FMEA** — FMEA constraints are immutable during task execution. No ad hoc alterations. | Prompt headers reference constraints with immutability notice. |
| 9 | **FMEA Amendment Protocol** — Constraint conflicts or new failure modes halt execution for formal human review. | FMEA Amendment Proposal template. |
| 10 | **Codebase State Sync** — Fresh repository map required at start of execution sessions. | Prompt header preamble check. |

---

## 9. Documentation Framework

| Document | Status | Initial Content Source |
|---|---|---|
| `README.md` | Generated | §2 + §4.2 + §8 |
| `ARCHITECTURE.md` | Generated | §4 (Version 2.0 Post-FMEA) |
| `CONSTRAINTS.md` | Generated | §3.2 + §3.3 + FMEA traceability |
| `docs/FMEA.md` | Generated | §5 (DRAFT S/O/D scores) |
| `KEY_DECISION_LOG.md` | Generated | Phase 0 decisions (5 entries) |
| `CODE_DECISION_LOG.md` | Generated | Phase 0.2 decisions (13 entries + 5 assumptions) |
| `docs/KANBAN_SETUP.md` | Generated | §7 |
| `working/CODE_DECISIONS_PATCH.md` | Ephemeral | AI sessions write provisional decisions here during active development. Merged into `CODE_DECISION_LOG.md` at HUMAN gate when phase passes all tests and receives user sign-off. File is reset after each merge. |
| `docs/MMF_Specification_V2.md` | Reference | Post-FMEA architecture specification |
| `docs/MMF_FMEA_Report_v2.md` | Reference | Full FMEA analytical narrative |
| `docs/IL-2_Sturmovik_Mission_Editor_Manual.pdf` | Reference | IL-2 Mission Editor manual — gitignored, excluded from Repomix |
| `docs/templates/templates.md` | Reference | All document templates — read before generating any project file (Ground Rule 6) |
| `docs/templates/master-plan-template.md` | Reference | Master Project Plan template — read before generating Phase 0 output (Ground Rule 6) |

### Conditional Documents

| Document | Status | Condition |
|---|---|---|
| `.repomixignore` | N/A | Not using Repomix |
| `repomix.config.json` | N/A | Not using Repomix |

---

## 10. Phase 0 Decisions

Five architectural decisions were made during Phase 0 planning. All are RESOLVED.

See `KEY_DECISION_LOG.md` for full details:

1. **DECISION 1** — Phase 3 Human Gates for Ground Attack and Bomber Escort (RESOLVED — Option C)
2. **DECISION 2** — Parser Module Name Coupling 0.2 ↔ 0.6 (RESOLVED — Option A)
3. **DECISION 3** — Phase 2 MRE Override Note Removal (RESOLVED — Note removed)
4. **DECISION 4** — Master Project Plan Total Task Count (RESOLVED — 54 total)
5. **DECISION 5** — `data/mcu_catalog.json` Location (RESOLVED — No action required)

---

## Appendix A: Phase Dependency Summary

Each phase depends on prior phases but produces a standalone deliverable:

**Phase 0 (Foundation)** → No dependencies. Produces the shared parser library and JSON schema. Contains 2 human gates: file collection (0.1) and schema approval (0.5h).

**Phase 1 (Compiler)** → Depends on Phase 0. Produces a working compiler and first flyable module. Contains 1 human gate: in-game test (1.10h).

**Phase 2 (GUI + MRE)** → Depends on Phases 0–1. Two parallel tracks. Contains 2 human gates: hand-built .Group files (2.1h) and in-game test (2.5h).

**Phase 3 (Module types)** → Depends on Phases 1–2. Each module independently usable. Contains 5 human gates: per-module in-game tests (3.1h, 3.2h, 3.3h, 3.4h) and cross-module integration (3.5).

**Phase 4 (Map data)** → Depends on Phase 0 ONLY. Can run parallel with Phases 1–3. Contains 2 human gates: file provision (4.0h) and coordinate validation (4.2h).

**Phase 5 (Orchestrator)** → Depends on Phases 1, 3, 4. Contains 3 human gates: DServer tests and mission flight tests.

**Phase 6 (Distribution)** → Depends on Phase 5. Contains 1 human gate: community beta.

### Total task count

37 AI tasks, 17 human gates, 54 total tasks across 7 phases.

- **Tier 1** (Opus / 3.1 Pro) sessions: 16 tasks — the FMEA-constrained compiler primitives, orchestrator assembly, and validation corpus.
- **Tier 2** (Sonnet / 3 Flash) sessions: 17 tasks — standard coding, GUI forms, data extraction, documentation.
- **Tier 3** (Haiku / 3.1 Flash-Lite) sessions: 1 task — project scaffolding. Also suitable for generating prompt headers from this document.

---

## Appendix B: AI Module Use Recommendations

*As of 3/16/2026*

Use Claude (Opus 4.6) for the parser library, all compiler primitives (Phase 1.3–1.6), the Module Reverse Engineer, the core orchestrator assembly engine (Phase 5.1–5.3), and the JSON schema definition. These are the constraint-dense, high-consequence tasks where cross-reference reasoning determines correctness.

Use Gemini (3.1 Pro) for the orchestrator's spatial planning tasks (Phase 4.4 route generation, Phase 5.3 scenario template coordinate calculation) where multimodal map reasoning adds value, and for the orchestrator GUI (Phase 5.5) where iterative visual design benefits from Gemini's frontend coding strengths.

Use Gemini (3 Flash) for the module GUI (Phase 2.3–2.6), the Map Data Extractor's extraction runs (Phase 4.1–4.3), ambient AI module composition (Phase 5.4), and DServer rotation scripting (Phase 5.6). Standard coding tasks with clear specifications.

Use either model's efficiency tier (Haiku / 3.1 Flash-Lite) for scaffolding, documentation, and prompt header generation.

The net effect is that Claude owns the "correctness layer" — everything that must satisfy the FMEA constraints and engine semantics — while Gemini owns the "productivity layer" — everything that benefits from rapid iteration, visual reasoning, and frontend development velocity. The JSON schema is the contract that keeps them aligned.

This changes if Google ships a model update that demonstrates sustained multi-constraint reasoning across 14+ interacting engine-specific rules in a single session. The benchmark to watch isn't general coding scores — it's whether the model can hold the timer-pause-semantics constraint (SM-003) in mind while implementing the Magazine Array counter logic (EL-001) three thousand tokens later without being reminded. That's the specific cognitive pattern this project's tool layer demands.

---

## Appendix C: Prompt Header Generation Guidance

Any Tier 2 or Tier 3 model can generate task-specific session prompts from this document. The prompt header for each AI task should include: the task ID and description, the relevant sections of the revised MMF Specification (Rev 2), the dependency outputs that the session receives as input, and the acceptance criteria as the exit condition. Tier 1 (Opus / 3.1 Pro) is not needed for prompt generation — it is reserved for executing the sessions themselves.

See `docs/prompts/` for all phase-specific session prompt headers.
