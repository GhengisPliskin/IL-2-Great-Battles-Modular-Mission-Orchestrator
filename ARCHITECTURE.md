# IL-2 Great Battles Modular Mission Orchestrator — Architecture Reference

**Version:** 2.0 (Post-FMEA)  
**Target Environment:** IL-2 Sturmovik Great Battles Mission Editor  
**Language:** Python 3.10+  
**Last Updated:** Phase 0.2 Complete

---

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User-Facing Applications (Layer 3)                         │
│  - PyQt6 GUI (Phase 2.3-2.6)                               │
│  - CLI (Phase 5.5, Phase 6.2)                              │
│  - Orchestrator Frontend (Phase 5.5)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Backend Tool Suite (Layer 2)                               │
│  - MMF Compiler (Phase 1.3-1.6) ← JSON to .Group           │
│  - Module Reverse Engineer (Phase 2.1-2.2)                 │
│  - Map Data Extractor (Phase 4.1-4.3)                      │
│  - Mission Orchestrator (Phase 5.1-5.3)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Shared Foundation (Layer 1)                                │
│  - IL-2 ASCII Parser Library (Phase 0.2) ✓                 │
│  - JSON Schema + Validation (Phase 0)                       │
│  - FMEA Constraint Registry                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

### Root Level

```
il2-mmo/
├── conftest.py                  # Pytest configuration (all tests)
├── README.md                    # Project overview, setup instructions
├── ARCHITECTURE.md              # This file
├── CONSTRAINTS.md               # FMEA traceability (PI-*, EL-*, SM-*, EC-*)
├── KEY_DECISION_LOG.md          # Architectural decision records
├── CODE_DECISION_LOG.md         # Code-level decisions and debugging heuristics
├── LICENSE
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies (pytest, black, mypy)
├── pyproject.toml               # Python project metadata
├── .gitignore                   # Git ignore patterns
│
└── working/                     # Ephemeral per-session scratch space
    └── CODE_DECISIONS_PATCH.md  # Provisional decisions — merged into CODE_DECISION_LOG.md at HUMAN gate
```

### src/ — Source Code

```
src/
├── mmf/                         # Shared framework (imported by all)
│   ├── __init__.py
│   │
│   ├── parser/                  # Phase 0.2: IL-2 ASCII Parser [COMPLETE ✓]
│   │   ├── __init__.py
│   │   ├── tokenizer.py         # Block/KVP/array tokenization
│   │   ├── deserializer.py      # ASCII → Python dict
│   │   ├── serializer.py        # Python dict → ASCII
│   │   │
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_roundtrip.py
│   │       └── fixtures/
│   │           └── (reference .group/.mission files from Phase 0.1)
│   │
│   ├── schema/                  # Phase 0: JSON Schema Contract
│   │   ├── __init__.py
│   │   ├── v2_0.py              # Pydantic models (mmf_version="2.0")
│   │   ├── validator.py         # JSON schema validation
│   │   ├── mmf-module-schema-v2_0.json  # Authoritative schema
│   │   │
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_schema_validation.py
│   │
│   ├── compiler/                # Phase 1: JSON → .Group (Tier 1: Opus)
│   │   ├── __init__.py
│   │   ├── id_generator.py      # [PI-003] Monotonic counter
│   │   ├── spatial_offset.py    # [PI-004] Remote coordinate zones
│   │   ├── reserved_filter.py   # [PI-002] Reserved-character stripping
│   │   ├── proxy_builder.py     # [IN]/[OUT]/[CFG] nodes
│   │   ├── command_buffer.py    # [SM-001] Serialization timers
│   │   ├── magazine_array.py    # [EL-001] Wave management
│   │   ├── entity_proxy.py      # [EL-002,EL-003] Entity binding
│   │   ├── garbage_collection.py # [SM-002,SM-004] GC chains
│   │   ├── dependency_stubs.py  # [EC-002] Stub generation
│   │   ├── init_buffer.py       # [EC-001] Initialization delay
│   │   ├── validator.py         # [PI-001] Required field check + [PI-002] reserved-char filter
│   │   ├── takeoff_sequence.py  # Phase 3.2: Scramble takeoff primitive
│   │   ├── cover_attack_toggle.py # Phase 3.4: Bomber Escort state machine
│   │   ├── compiler.py          # Main compilation driver
│   │   │
│   │   ├── modules/             # Phase 1+3: Module-specific compilers
│   │   │   ├── __init__.py
│   │   │   ├── static_cap.py    # Phase 1.10
│   │   │   ├── intercept.py     # Phase 3.1
│   │   │   ├── scramble.py      # Phase 3.2
│   │   │   ├── ground_attack.py # Phase 3.3
│   │   │   └── bomber_escort.py # Phase 3.4
│   │   │
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_id_generation.py
│   │       ├── test_magazine_array.py
│   │       ├── test_command_buffer.py
│   │       ├── test_entity_binding.py
│   │       ├── test_garbage_collection.py
│   │       └── fixtures/
│   │
│   ├── validation/              # FMEA Constraint Checking
│   │   ├── __init__.py
│   │   ├── fmea.py              # Constraint registry (14 constraints)
│   │   ├── checkers.py          # Validation logic
│   │   │
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_fmea.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       └── constants.py         # Reserved ID ranges, timing limits
│
├── backend/                     # Backend tools (UI-independent)
│   ├── mre/                     # Phase 2: Module Reverse Engineer
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── validator.py
│   │   ├── cli.py
│   │   └── tests/
│   │
│   ├── map_extractor/           # Phase 4: Map Data Extraction
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── coordinate_db.py
│   │   ├── cli.py
│   │   └── tests/
│   │
│   └── orchestrator/            # Phase 5: Mission Orchestrator
│       ├── __init__.py
│       ├── scenario_engine.py
│       ├── mission_builder.py
│       ├── dserver_interface.py
│       ├── cli.py
│       └── tests/
│
└── ui/                          # User-facing interfaces
    ├── gui/                     # Phase 2: PyQt6 GUI (Tier 2: Sonnet)
    │   ├── __init__.py
    │   ├── main_window.py
    │   ├── module_editor.py
    │   ├── schema_widgets.py
    │   ├── compiler_output.py
    │   ├── dialogs/
    │   └── tests/
    │
    └── cli/                     # CLI Interface
        ├── __init__.py
        ├── main.py
        ├── commands/
        └── tests/
```

### tests/ — Test Suite

```
tests/
├── conftest.py                  # Root pytest fixtures
├── integration/
│   ├── test_phase0_parser.py    # Parser round-trip [Phase 0.2]
│   ├── test_phase1_compiler.py  # Compiler validation [Phase 1]
│   ├── test_phase2_gui.py       # GUI workflows [Phase 2]
│   └── test_phase5_orchestrator.py
│
└── fixtures/
    ├── il2_files/               # Reference .group/.mission files (exclude from Repomix — binary data)
    │   └── (populated Phase 0.1)
    │
    └── json/
        ├── valid_modules/       # Valid JSON test cases
        └── invalid_modules/     # Invalid JSON test cases
```

### docs/ — Documentation

```
docs/
├── KANBAN_SETUP.md              # Project board configuration
├── PHASES.md                    # Phase breakdown, dependencies, tasks
├── FMEA.md                      # FMEA traceability index
├── MMF_Specification_V2.md      # Post-FMEA architecture specification (reference)
├── MMF_FMEA_Report_v2.md        # Full FMEA analytical narrative (reference)
├── IL-2_Sturmovik_Mission_Editor_Manual.pdf  # IL-2 Mission Editor reference (gitignored, excluded from Repomix)
├── USER_GUIDE.md                # Phase 6: End-user getting started
├── CONTRIBUTOR_GUIDE.md         # Phase 6: Developer onboarding
├── API_REFERENCE.md             # mmf, compiler, schema API docs
│
├── templates/                   # Skill reference templates (read-only after scaffolding)
│   ├── templates.md             # All document templates
│   └── master-plan-template.md  # Master Project Plan template
│
└── ARCHITECTURE/                # Architecture diagrams
    ├── three_layer_architecture.drawio
    └── state_machines.md
```

### data/ — Reference Materials & Outputs

```
data/
├── schemas/
│   └── mmf-module-schema-v2_0.json  # Contract between GUI and compiler
│
├── map_databases/               # Phase 4 Output
│   ├── maps.sqlite3
│   └── README.md
│
└── module_templates/            # Phase 2/3 Reference Modules
    ├── static_cap.json
    ├── scramble.json
    └── bomber_escort.json
```

### build/ & config/ & scripts/

```
build/
├── pyinstaller/                 # Phase 6: PyInstaller config
│   ├── mmf.spec
│   └── hook-mmf.py
└── dist/                        # Final executable

config/
├── il2_paths.yaml               # User's IL-2 install (gitignored)
├── compiler_defaults.yaml       # Default options
└── logging.yaml

scripts/
├── collect_reference_files.py   # Phase 0.1 helper
├── validate_schema.py           # Standalone validator
└── test_in_game.py              # Phase 1/2 HUMAN gate helper
```

---

## Phase Mapping

| Phase | Component | Output Directory | Status | Model Tier |
|-------|-----------|------------------|--------|------------|
| 0.1 | File Collection | `tests/fixtures/il2_files/` | HUMAN GATE | N/A |
| 0.2 | Parser (ASCII → dict) | `src/mmf/parser/` | **COMPLETE** ✓ | Tier 1 (Opus) |
| 0.3 | Writer (dict → ASCII) | `src/mmf/parser/` | Pending | Tier 2 (Sonnet) |
| 0.4 | MCU Type Catalog | `src/mmf/parser/`, `data/` | Pending | Tier 2 (Sonnet) |
| 0.5 | JSON Schema Contract | `src/mmf/schema/` | Pending | Tier 1 (Opus) |
| 0.5h | Schema Approval | (HUMAN GATE) | Pending | N/A |
| 0.6 | Project Structure | `src/` (all packages) | Pending | Tier 3 (Haiku) |
| 1.1 | ID Generator (PI-003) | `src/mmf/compiler/` | Pending | Tier 2 (Sonnet) |
| 1.2 | Spatial Offset (PI-004) | `src/mmf/compiler/` | Pending | Tier 2 (Sonnet) |
| 1.3 | Flight Emitter (EL-003) | `src/mmf/compiler/` | Pending | Tier 1 (Opus) |
| 1.4 | Magazine Array (EL-001) | `src/mmf/compiler/` | Pending | Tier 1 (Opus) |
| 1.5 | Command Buffer (SM-001) | `src/mmf/compiler/` | Pending | Tier 1 (Opus) |
| 1.6 | Garbage Collection (SM-002) | `src/mmf/compiler/` | Pending | Tier 1 (Opus) |
| 1.7 | Dependency Stubs (EC-002) | `src/mmf/compiler/` | Pending | Tier 2 (Sonnet) |
| 1.8 | Validator + Filter (PI-001) | `src/mmf/compiler/` | Pending | Tier 2 (Sonnet) |
| 1.9 | Init Buffer (EC-001) | `src/mmf/compiler/` | Pending | Tier 2 (Sonnet) |
| 1.10 | Static CAP Composition | `src/mmf/compiler/modules/` | Pending | Tier 1 (Opus) |
| 1.10h | In-game Test | (HUMAN GATE) | Pending | N/A |
| 2.1-2.2 | Module Reverse Engineer | `src/backend/mre/` | Pending | Tier 1 (Opus) |
| 2.3-2.6 | Module GUI | `src/ui/gui/` | Pending | Tier 2 (Sonnet) |
| 4.1-4.3 | Map Extraction | `src/backend/map_extractor/` | Pending | Tier 2 (Sonnet) |
| 5.1-5.3 | Orchestrator Core | `src/backend/orchestrator/` | Pending | Tier 1 (Opus) |
| 6.1-6.3 | Distribution | `build/dist/` | Pending | Tier 2 (Sonnet) |

---

## Dependency Graph

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

---

## FMEA Constraints by Layer

### Layer 1: Parser & Validation

| ID | Severity | Constraint | Location |
|----|----------|-----------|----------|
| PI-001 | CRITICAL | Required Field Schema | `src/mmf/compiler/compiler.py` |
| PI-002 | HIGH | Reserved-character filter | `src/mmf/compiler/reserved_filter.py` |
| PI-003 | CRITICAL | Monotonic ID counter | `src/mmf/compiler/id_generator.py` |
| PI-004 | MEDIUM | Partitioned remote zones | `src/mmf/compiler/spatial_offset.py` |

### Layer 2: Compiler Core

| ID | Severity | Constraint | Location |
|----|----------|-----------|----------|
| EL-001 | CRITICAL | Magazine Array counter | `src/mmf/compiler/magazine_array.py` |
| EL-002 | HIGH | Entity Proxy 2s delay | `src/mmf/compiler/entity_proxy.py` |
| EL-003 | CRITICAL | Binding integrity check | `src/mmf/compiler/entity_proxy.py` |
| SM-001 | HIGH | Serialization timers | `src/mmf/compiler/command_buffer.py` |
| SM-002 | HIGH | All-flight RTB Links | `src/mmf/compiler/garbage_collection.py` |
| SM-003 | HIGH | Timer pause semantics | `src/mmf/compiler/command_buffer.py` |
| SM-004 | LOW | Dual-path GC | `src/mmf/compiler/garbage_collection.py` |
| EC-001 | MEDIUM | Init delay config | `src/mmf/schema/v2_0.py` |
| EC-002 | MEDIUM | Stub ID range | `src/mmf/compiler/dependency_stubs.py` |
| EC-003 | HIGH | Spawn vs Activate | `src/mmf/compiler/magazine_array.py` |
| EC-004 | HIGH | GC-gated wave activation | `src/mmf/compiler/magazine_array.py` |

---

## Import Structure

**All external imports start from `src/`:**

```python
# In any module:
from mmf.parser import deserializer, serializer
from mmf.compiler import compiler
from mmf.schema import validator
from mmf.validation import fmea

# Backends import Layer 1:
from mmf.parser import deserializer
from mmf.compiler import compiler
from mmf.schema import validator
```

**Never:**
```python
# DON'T do this:
from ..parser import deserializer  # Relative imports (fragile)
import sys; sys.path.append('..')  # Path manipulation (anti-pattern)
```

---

## Testing Strategy

### Unit Tests
- Located: `src/*/tests/`
- Pattern: `test_<module>.py`
- Scope: Single module or function
- Example: `src/mmf/compiler/tests/test_id_generation.py`

### Integration Tests
- Located: `tests/integration/`
- Pattern: `test_phase<N>_<component>.py`
- Scope: Cross-module workflows
- Example: `tests/integration/test_phase1_compiler.py`

### Fixtures
- Shared: `tests/conftest.py` (root)
- Component-specific: `src/*/tests/conftest.py` (if needed)
- Reference data: `tests/fixtures/`

**All tests run with:**
```bash
pytest                    # All tests
pytest -v                 # Verbose
pytest src/mmf/parser/    # Specific directory
```

---

## For Claude Code / Projects / Cowork

**This file is the reference.** When starting a session:

1. **Claude Code / Projects discovers and reads `ARCHITECTURE.md` automatically** from the repo
2. No need to paste it into every prompt
3. For phase-specific work, reference the **Phase** section above
4. FMEA constraints are **always checked** in Layer 2 (compiler) work

**Example prompt for Phase 1.3:**

```
**Task:** Implement ID Generator (Phase 1.3)

Reference: See ARCHITECTURE.md, Phase Mapping, and FMEA Constraint PI-003

**Input:** MMF module JSON (from schema)
**Output:** src/mmf/compiler/id_generator.py

**Acceptance Criteria:**
- Monotonic counter initialized from max(existing IDs) + 1
- Per-session allocation (no fixed per-module offsets)
- Tests: src/mmf/compiler/tests/test_id_generation.py
```

Claude will find the directory structure and understand placement immediately.

---

## Updating This Document

**When completing a phase:**
1. Update the **Phase Mapping** table (change "Pending" → "COMPLETE ✓")
2. Update the **Last Updated** date at the top
3. Commit with message: `Phase X.Y complete, update ARCHITECTURE.md`

**When adding new constraints:**
1. Add row to **FMEA Constraints** table
2. Reference the specific module location
3. Commit with message: `Add constraint <ID> to FMEA registry`

---

## Quick Reference: Directory Purpose

| Directory | Purpose | Updated By |
|-----------|---------|----------|
| `src/mmf/` | Shared parser + schema | All phases |
| `src/backend/` | Compiler, MRE, Extractor, Orchestrator | Phases 1-5 |
| `src/ui/` | GUI and CLI | Phases 2, 5, 6 |
| `tests/` | Test harness | All phases |
| `data/` | Reference modules, maps, schemas | Phases 2-4 |
| `docs/` | User/contributor guides | Phase 6 |
| `config/` | User-specific settings | End-users |

---

**Last Updated:** March 18, 2026  
**Phase Progress:** 0.2 Complete (1/7 phases)  
**Next Phase:** 0.3 (ASCII Writer), 0.4 (MCU Catalog), 0.5 (JSON Schema), 0.6 (Project Structure)
