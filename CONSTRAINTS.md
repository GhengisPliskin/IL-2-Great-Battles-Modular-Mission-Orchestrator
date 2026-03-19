# Constraints — IL-2 Great Battles Modular Mission Orchestrator

**Last Updated:** March 18, 2026
**Source Documents:** `ARCHITECTURE.md`, `docs/MMF_Specification_V2.md`, `docs/MMF_FMEA_Report_v2.md`

---

## 1. Technical Stack Constraints

| ID | Constraint | Type | Impact |
|---|---|---|---|
| C-001 | Python 3.10+ required | Tech Stack | Minimum runtime version for all components. No language migration planned. |
| C-002 | PyQt6 for GUI layer | Tech Stack | GUI framework locked to PyQt6. No web-based or Electron alternatives. |
| C-003 | JSON Schema Draft 7 for intermediary format | Tech Stack | The MMF JSON schema contract uses Draft 7. All validation tooling must support this draft. |
| C-004 | No external database dependency | Infrastructure | All data is file-based (.json, .Group, .Mission). No PostgreSQL, SQLite, or other DB required at runtime. |
| C-005 | Windows primary target | Platform | IL-2 Sturmovik runs on Windows. PyInstaller distribution targets Windows .exe. |
| C-006 | Standalone distribution via PyInstaller | Distribution | Final deliverable must run without a Python installation. All dependencies bundled. |

---

## 2. Target Environment Constraints

| ID | Constraint | Type | Impact |
|---|---|---|---|
| C-007 | IL-2 Sturmovik Great Battles Mission Editor (BOSEditor) | Target | All .Group/.Mission output must load without error in the IL-2 Mission Editor. |
| C-008 | IL-2 ASCII syntax is undocumented and proprietary | Format | Zero official specification. Parser must handle all syntax variations discovered empirically via corpus validation. |
| C-009 | .Group/.Mission ASCII format has zero error tolerance | Format | A single malformed field causes cascade parse failure, offsetting every subsequent Index reference. |
| C-010 | DServer multiplayer environment | Runtime | Compiled missions must run on IL-2 Dedicated Server for multiplayer sessions. |

---

## 3. Engine Runtime Constraints

| ID | Constraint | Type | Impact |
|---|---|---|---|
| C-011 | ~100 active AI unit cap | Engine Limit | DServer tickrate degrades non-linearly above ~100 active AI units. Magazine Array must enforce this ceiling. See FMEA EC-004. |
| C-012 | 180-minute session duration target | Performance | The architecture must support continuous 3-hour multiplayer sessions with automated AI cycling and garbage collection. |
| C-013 | Engine tick rate: ~50 ticks/second (20ms/tick) | Engine Limit | Serialization timers must exceed one tick (20ms) to guarantee cross-tick separation. See FMEA SM-001. |
| C-014 | MCU_Counter.Deactivate does NOT reset internal state | Engine Behavior | Counter continues incrementing while deactivated (Manual pg. 278). Magazine Array counter must never be deactivated. See FMEA EL-001. |
| C-015 | MCU_Timer.Deactivate pauses, does not reset | Engine Behavior | Reactivation resumes from paused position (Manual pg. 283). Timer reuse across state transitions is prohibited. See FMEA SM-003. |
| C-016 | MCU_CMD_Spawn breaks formation Target Link hierarchies | Engine Behavior | Spawned wingmen ignore leader commands (Manual pg. 282). Magazine Array must use Activate/Deactivate exclusively. See FMEA EC-003. |
| C-017 | MCU_TR_Entity requires 3D physics object instantiation | Engine Behavior | Entity proxy binding fails silently if aircraft is not yet physically instantiated. 2-second delay required. See FMEA EL-002. |
| C-018 | Simultaneous MCU trigger ordering is non-deterministic | Engine Behavior | Triggers queued in the same tick execute in undefined order. Serialization timers required. See FMEA SM-001. |

---

## 4. FMEA Constraint Traceability

All 14 failure modes identified in the FMEA analysis. Full register at `docs/FMEA.md`. Full analytical narrative at `docs/MMF_FMEA_Report_v2.md`.

### Pipeline Integrity

| ID | Severity | Constraint | Source File |
|---|---|---|---|
| PI-001 | CRITICAL | Required Field Schema — null Targets[] array crashes DServer | `src/mmf/compiler/validator.py` |
| PI-002 | HIGH | Reserved-character filter — `{}[];=` stripped from string fields | `src/mmf/compiler/reserved_filter.py` |
| PI-003 | CRITICAL | Monotonic ID counter — no per-module offsets, global sequential | `src/mmf/compiler/id_generator.py` |
| PI-004 | MEDIUM | Partitioned remote coordinate zones — 1000m Z-axis increment | `src/mmf/compiler/spatial_offset.py` |

### Engine Limitation Compliance

| ID | Severity | Constraint | Source File |
|---|---|---|---|
| EL-001 | CRITICAL | Magazine Array counter: Reset=TRUE, never deactivated, sized for full session | `src/mmf/compiler/magazine_array.py` |
| EL-002 | HIGH | Entity proxy: 2-second post-Activate delay before binding consumers | `src/mmf/compiler/entity_proxy.py` |
| EL-003 | CRITICAL | Entity binding integrity: post-emission assertion, no self-reference | `src/mmf/compiler/entity_proxy.py` |

### State Management

| ID | Severity | Constraint | Source File |
|---|---|---|---|
| SM-001 | HIGH | Command Buffer serialization: 50-100ms staggered timers per [IN] port | `src/mmf/compiler/command_buffer.py` |
| SM-002 | HIGH | Leader-kill resilience: RTB to all flight members, parallel GC chain | `src/mmf/compiler/garbage_collection.py` |
| SM-003 | HIGH | Timer pause semantics: no timer reuse across state transitions | `src/mmf/compiler/command_buffer.py` |
| SM-004 | LOW | Dual-path GC: both OnKilled and Despawn increment next-wave counter | `src/mmf/compiler/garbage_collection.py` |

### Environmental / Configuration

| ID | Severity | Constraint | Source File |
|---|---|---|---|
| EC-001 | MEDIUM | Init buffer: configurable delay (3-10s), warning if entities > 200 | `src/mmf/compiler/init_buffer.py` |
| EC-002 | MEDIUM | Dependency stubs: reserved ID range 900000-999999 | `src/mmf/compiler/dependency_stubs.py` |
| EC-003 | HIGH | Spawn prohibited: Activate/Deactivate only for Magazine Array flights | `src/mmf/compiler/magazine_array.py` |
| EC-004 | HIGH | GC-gated wave activation: no time-based activation without GC confirmation | `src/mmf/compiler/magazine_array.py` |
