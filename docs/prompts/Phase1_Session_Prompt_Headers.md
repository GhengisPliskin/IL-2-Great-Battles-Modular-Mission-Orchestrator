# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 1 — Core Compiler + First Module
### Session Prompt Headers
*Compile a Static CAP .Group that flies correctly in-game*

**10 AI Sessions | 1 Human Gate | Task IDs 1.1 – 1.10**

---

## Phase 1 Overview

Phase 1 builds all ten compiler primitives and integrates them into a working Static CAP module. The Static CAP is the validation prototype: it requires zero dynamic player triggers, so any failure is attributable directly to the compiler.

All FMEA constraints with CRITICAL or HIGH severity have explicit acceptance criteria in their sessions. Sessions 1.3–1.6 and 1.10 are Tier 1 (Opus 4.6) — they require cross-constraint reasoning. The flight emitter (1.3) enforces EL-003 CRITICAL binding integrity. The Magazine Array (1.4) must satisfy three interacting constraints simultaneously (EL-001, EC-003, EL-002). The Command Buffer (1.5) addresses the timer-pause-semantics failure mode (SM-003) that only manifests at runtime. Garbage collection (1.6) manages the dual-path activation chain (SM-004) with leader-kill resilience (SM-002). The composition session (1.10) holds all 14 constraints active simultaneously. Sessions 1.1, 1.2, 1.7, 1.8, 1.9 are Tier 2 (Sonnet 4.6) — standard coding with well-defined specifications and no multi-constraint interaction.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 1.1 | Monotonic ID generator (PI-003) | Compiler | AI | Tier 2: Sonnet 4.6 |
| 1.2 | Spatial offset engine (PI-004) | Compiler | AI | Tier 2: Sonnet 4.6 |
| 1.3 | Flight emitter + Entity binding (EL-003) | Compiler | AI | Tier 1: Opus 4.6 |
| 1.4 | Magazine Array activator (EL-001, EC-003, EL-002) | Compiler | AI | Tier 1: Opus 4.6 |
| 1.5 | Command Buffer + serialization (SM-001, SM-003) | Compiler | AI | Tier 1: Opus 4.6 |
| 1.6 | Garbage collection (SM-004, SM-002) | Compiler | AI | Tier 1: Opus 4.6 |
| 1.7 | Dependency stub system (EC-002) | Compiler | AI | Tier 2: Sonnet 4.6 |
| 1.8 | Required Field validator + reserved-char filter (PI-001, PI-002) | Compiler | AI | Tier 2: Sonnet 4.6 |
| 1.9 | Initialization buffer (EC-001) | Compiler | AI | Tier 2: Sonnet 4.6 |
| 1.10 | Static CAP composition — all primitives integrated | Compiler | AI | Tier 1: Opus 4.6 |
| 1.10h | IN-GAME TEST: 30-min session, AI behavior verification | Testing | HUMAN | N/A |

**Dependency order:** 1.1 and 1.8 can start immediately (depend only on Phase 0). 1.2 follows 1.1. 1.3 requires 0.4 and 1.1. 1.4 requires 1.3. 1.5 requires 1.1. 1.6 requires 1.3 and 1.4. 1.7 requires 1.1. 1.9 requires 1.4. 1.10 requires all preceding tasks.

```
Phase 0 (0.2 Parser + 0.4 Catalog + 0.5 Schema + 0.6 Structure)
    ↓
    ├──→ 1.1 (ID Generator) ──┬──→ 1.2 (Spatial Offset)
    │                          │
    │                          ├──→ 1.3 (Flight Emitter) ← 0.4 (Catalog)
    │                          │        ↓
    │                          │        ├──→ 1.4 (Magazine Array)
    │                          │        │        ↓
    │                          │        │        └──→ 1.9 (Init Buffer)
    │                          │        │
    │                          │        └──→ 1.6 (GC) ← 1.4
    │                          │
    │                          ├──→ 1.5 (Command Buffer)
    │                          │
    │                          └──→ 1.7 (Dependency Stubs)
    │
    └──→ 1.8 (Validator) ← 0.4 (Catalog)
                    ↓
                    └────── All ──→ 1.10 (Static CAP Composition) ──→ 1.10h (HUMAN)
```

---

## Session 1.1 — Monotonic ID Generator

| | |
|---|---|
| **Task ID** | 1.1 |
| **Component** | Compiler (`src/mmf/compiler/id_generator.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 0.5 (JSON schema, defines `compiler_options.id_counter_start`) |
| **Delivers To** | Every compiler primitive (1.2 through 1.10) — all ID assignment routes through here |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → PI-003, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Senior Python Developer. You are implementing the ID management subsystem for the MMF compiler. This is the first compiler primitive and the dependency all other primitives share.

### Context

The IL-2 engine requires every entity, MCU, and translator block to have a unique integer Index. When multiple .Group files are imported into a .Mission, Index collisions cause silent data corruption — later-imported blocks overwrite earlier ones at the same ID. The MMF compiler must guarantee zero collisions across any number of modules imported in the same session.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [PI-003] CRITICAL — Compiler SHALL maintain a single monotonically increasing counter per session. Initializes from max(existing Index values) + 1. Per-module fixed offsets are PROHIBITED.
> - [EC-002] MEDIUM — Stub IDs use reserved range 900000–999999, excluded from the main counter pool.
> - Section 2.4: ID Management

### Inputs

- Phase 0 outputs: `src/mmf/` project structure, parser library
- `compiler_options.id_counter_start` from the JSON schema (null = scan target file; integer = explicit start)

### Requirements

**R1 — IDGenerator Class**

```python
class IDGenerator:
    def __init__(self, mission_data: dict | None = None, start: int | None = None)
    def next_id(self) -> int
    def peek(self) -> int
    def reserve_stub_range(self) -> None  # locks 900000–999999
```

Constructor logic: if `start` is provided, initialize counter to `start`. If `mission_data` is provided, scan all Index values in the parsed dictionary and initialize to `max(Index) + 1`. If neither, start at 1.

**R2 — Stub Range Exclusion**

The counter SHALL never emit an ID in the range 900000–999999. If the counter would enter that range, skip to 1000000. `reserve_stub_range()` documents this exclusion in the generator's internal state.

**R3 — Thread Safety Not Required**

Single-threaded compilation only. No locking needed.

> **[PI-003] — CRITICAL** Per-module fixed offsets are explicitly prohibited. The counter is global, never resets, never restarts per module.

> **EXIT CONDITION — Acceptance Criteria**
> - Import 10 copies of the same module in sequence: zero ID collisions across all 10 copies
> - All emitted IDs are strictly ascending
> - No emitted ID falls in range 900000–999999
> - With `mission_data` containing Index values [1, 5, 100], counter initializes to 101
> - Unit test: `next_id()` called 1000 times produces 1000 unique, ascending integers

---

## Session 1.2 — Spatial Offset Engine

| | |
|---|---|
| **Task ID** | 1.2 |
| **Component** | Compiler (`src/mmf/compiler/spatial_offset.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 1.1 (ID generator — spatial engine is session-scoped alongside the counter) |
| **Delivers To** | 1.3, 1.4, 1.10 — all MCU coordinate assignment goes through here |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → PI-004, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Senior Python Developer implementing the spatial isolation subsystem. Internal compiler MCUs must be placed far from the playable map so mission designers cannot accidentally interact with them in BOSEditor.

### Context

All core calculation MCUs — counters, timers, entity proxies, command buffers — must be compiled at coordinates at least 50km from the playable map boundary. Only the `[IN]` and `[OUT]` proxy nodes appear at the user-specified spawn coordinates. Each module in a session must occupy a distinct spatial block within the remote zone to prevent MCU overlap in the editor.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [PI-004] MEDIUM — Remote zone SHALL be partitioned. Each module receives a unique offset block, incremented by 1000m on the Z-axis per module. Compiler tracks allocated blocks per session.
> - Section 2.3: Spatial Blackboxing

### Requirements

**R1 — SpatialAllocator Class**

```python
class SpatialAllocator:
    REMOTE_BASE_X = 50000.0
    REMOTE_BASE_Z = 50000.0
    Z_INCREMENT = 1000.0

    def __init__(self)
    def allocate_block(self, module_id: str) -> tuple[float, float]
    def remote_coords(self, module_id: str, local_x: float, local_z: float) -> tuple[float, float]
    def proxy_coords(self, x: float, z: float) -> tuple[float, float]  # identity — passes through
```

`allocate_block` returns the (X, Z) origin for the module's remote block. Subsequent calls for the same `module_id` return the same block. New `module_id`s get `base_Z + (N * Z_INCREMENT)`.

**R2 — Coordinate Classification**

Every MCU must be classified as either remote (internal calculation) or proxy (I/O node). The offset is applied only to remote MCUs. Proxy nodes receive the user-supplied `proxy_coordinates` from the JSON payload unchanged.

**R3 — Session-Scoped State**

The allocator is instantiated once per compilation session and shared across all modules in that session. Destroying and recreating it mid-session is a bug.

> **[PI-004] — MEDIUM** Each module gets a unique 1000m Z-axis block within the remote zone. Blocks must not overlap. The allocator tracks which blocks are in use for the lifetime of the compilation session.

> **EXIT CONDITION — Acceptance Criteria**
> - Two modules compiled in the same session have non-overlapping remote coordinates
> - Module A's remote block origin is (50000, 50000); module B's is (50000, 51000)
> - Proxy coordinates pass through unchanged (user-specified X/Z are not altered)
> - Allocating the same `module_id` twice returns the same block (idempotent)
> - Unit test: 100 modules produce 100 distinct Z-axis blocks, none overlapping

---

## Session 1.3 — Flight Emitter + Entity Proxy Binding

| | |
|---|---|
| **Task ID** | 1.3 |
| **Component** | Compiler (`src/mmf/compiler/entity_proxy.py`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 0.4 (MCU type catalog — Aircraft and Entity field definitions), 1.1 (ID generator) |
| **Delivers To** | 1.4 (Magazine Array — needs flight hierarchy), 1.6 (GC — needs Entity proxy) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → EL-002, EL-003, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Principal Python Systems Developer. This session implements the most binding-critical compiler primitive: the flight emitter generates aircraft hierarchies and their Entity proxies, and enforces the two-way binding integrity check that FMEA rates CRITICAL. One missed assertion here produces a silent failure mode that is invisible until the mission is flown.

### Context

A flight in IL-2 is a leader aircraft with one or more wingmen. The leader has a Target Link to each wingman. All aircraft start `Enabled=FALSE` (Sleep state) — they are activated by the Magazine Array when their wave is due. Each leader requires an `MCU_TR_Entity` proxy for state extraction (`OnKilled`, `OnTookOff`). The binding between the Entity and its aircraft is two-way and must be verified post-emission before the compiler proceeds.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EL-003] CRITICAL — Post-emission binding check: `Entity.MisObjID == Aircraft.Index` AND `Aircraft.LinkTrId == Entity.Index` AND `Entity.MisObjID != Entity.Index`. Failure aborts compilation.
> - [EL-002] HIGH — No logic node may reference Entity output events within 2 seconds of the aircraft's Activate trigger. Compiler inserts mandatory 2s MCU_Timer between Activate and first Entity consumer.
> - Section 4.2: State Extraction (MCU_TR_Entity)
> - Section 4.2.1: Entity Binding Temporal Dependency
> - Section 5.2: The Magazine Array — flights start Enabled=FALSE

### Requirements

**R1 — Flight Hierarchy Generation**

For a flight of size N:
- Generate 1 leader Aircraft block + (N-1) wingman Aircraft blocks
- Leader `Aircraft.Targets = [wingman_1.Index, wingman_2.Index, ...]`
- All `Aircraft.Enabled = FALSE` (Enabled=0 in IL-2 syntax)
- All `Aircraft.Index` values from `IDGenerator.next_id()`
- `Aircraft.NumberInFormation`: leader = 0, wingmen = 1, 2, ...

**R2 — Entity Proxy Generation**

For every leader aircraft:
- Generate one `MCU_TR_Entity` block
- `Entity.MisObjID = leader.Index`
- `Leader.LinkTrId = Entity.Index`
- `Entity.Enabled = TRUE` (always active — it is an output monitor, not a command node)

**R3 — EL-002 Delay Timer**

Generate a mandatory 2-second `MCU_Timer` between any Activate trigger and the first downstream consumer of `Entity.OnKilled` or `Entity.OnTookOff`. This timer is not reusable (SM-003 applies here too — each activation path gets a fresh timer).

**R4 — Post-Emission Binding Check**

After emitting all blocks, execute the EL-003 assertion on every (aircraft, entity) pair:

```python
assert entity.MisObjID == aircraft.Index
assert aircraft.LinkTrId == entity.Index
assert entity.MisObjID != entity.Index
```

Any assertion failure raises `BindingIntegrityError` and aborts compilation with a diagnostic identifying the aircraft and entity IDs.

> **[EL-003] — CRITICAL** Post-emission binding integrity check is mandatory. Compile does not proceed if any assertion fails. This catches transient ID assignment bugs before they become invisible in-game failures.

> **[EL-002] — HIGH** The 2-second delay timer between Activate and Entity event consumers is mandatory. Silent failure mode: Entity attempts to resolve its MisObjID before the physics object is instantiated — binding fails permanently and OnKilled becomes orphaned.

> **EXIT CONDITION — Acceptance Criteria**
> - Post-emission assertion passes: `Entity.MisObjID == Aircraft.Index` for every leader
> - Post-emission assertion passes: `Aircraft.LinkTrId == Entity.Index` for every leader
> - Post-emission assertion passes: `Entity.MisObjID != Entity.Index` (no self-reference)
> - All `Aircraft.Enabled = FALSE` in emitted output
> - Wingman Target Links are present on the leader and reference correct wingman IDs
> - 2-second MCU_Timer inserted between Activate and first Entity event consumer
> - `BindingIntegrityError` raised and compilation aborted when assertions are injected to fail

---

## Session 1.4 — Magazine Array Activator

| | |
|---|---|
| **Task ID** | 1.4 |
| **Component** | Compiler (`src/mmf/compiler/magazine_array.py`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 1.3 (flight emitter — Magazine Array wraps flight hierarchies) |
| **Delivers To** | 1.6 (GC — GC-gated activation routes back to the counter), 1.10 (composition) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → EL-001, EC-003, EC-004, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Principal Python Systems Developer. The Magazine Array is the core wave-management architecture of the MMF. It must satisfy three interacting FMEA constraints simultaneously. Failure here either stalls the activation chain (EL-001), breaks formation integrity (EC-003), or causes silent double-binds (EL-002). Hold all three constraints in mind across the full implementation.

### Context

The Magazine Array is the answer to a specific IL-2 engine limitation: `MCU_CMD_Spawn` destroys Target Link formation hierarchies, so spawned wingmen ignore leader commands. The Magazine Array pre-instantiates all waves in Sleep state (`Enabled=FALSE`) and activates them sequentially via `MCU_Counter` + `MCU_Activate`. The counter must never be deactivated — the engine does not reset counter state on deactivation, making recycling unreliable. The counter must be session-sized: enough waves to cover the full 180-minute session.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EL-001] CRITICAL — MCU_Counter Reset=TRUE, NEVER deactivated. `wave_count >= ceil(session_duration / avg_sortie_duration)`. Compiler emits warning if `wave_count < ceil(180 / ToS)`.
> - [EC-003] HIGH — Activate/Deactivate pattern ONLY. MCU_CMD_Spawn PROHIBITED for Magazine Array flights.
> - [EL-002] HIGH — 2s delay timer between Activate trigger and first Entity event consumer (from 1.3).
> - Section 5.2: The Magazine Array
> - Section 5.2.1: Activation Pattern
> - Section 5.2.2: Counter Behavior & Session Sizing
> - [EC-004] HIGH — GC-gated wave activation: next-wave counter SHALL NOT fire until GC chain confirms completion.

### Requirements

**R1 — Wave Generation**

For `wave_count` N, generate N complete flight hierarchies (via FlightEmitter from 1.3), all at the same remote spatial coordinates, all `Enabled=FALSE`.

**R2 — MCU_Counter Configuration**

One `MCU_Counter` per Magazine Array:
- `Counter.Count = wave_count` (one output per wave)
- `Counter.ResetAfterOperation = TRUE`
- `Counter.Enabled = TRUE` — the counter is NEVER deactivated
- `Counter.Targets[i] = MCU_Activate[i].Index` (one Activate MCU per wave)
- Counter receives its trigger from the GC chain's completion signal (EC-004)

**R3 — Session Size Validation**

Calculate `required_waves = ceil(session_duration_minutes / time_on_station_minutes)`. If `wave_count < required_waves`, emit a `CompilerWarning` (not an error) identifying the shortfall and the formula.

**R4 — Spawn Prohibition**

The compiler must not emit any `MCU_CMD_Spawn` block for Magazine Array aircraft. Any code path that would emit a Spawn raises `ProhibitedNodeError`.

**R5 — First-Wave Activation**

Wave 0 (the first wave) is activated by the initialization buffer (from task 1.9) at mission start. The counter subsequently triggers wave 1, 2, ... N-1 as each GC chain completes.

> **[EL-001] — CRITICAL** Counter NEVER deactivated. Reset=TRUE. Session sizing warning emitted if `wave_count < ceil(180/ToS)`. Counter is single-use — there is no recycling mechanism.

> **[EC-003] — HIGH** MCU_CMD_Spawn is architecturally prohibited for Magazine Array flights. It destroys Target Link hierarchies. Use Activate/Deactivate exclusively.

> **EXIT CONDITION — Acceptance Criteria**
> - `Counter.ResetAfterOperation = TRUE` in emitted output
> - No `MCU_CMD_Spawn` block present in emitted Magazine Array output
> - `wave_count=12`, ToS=15 min: no warning. `wave_count=5`, ToS=15 min (requires 12): warning emitted
> - All N flights have `Enabled=FALSE`; `Counter.Enabled=TRUE`
> - `Counter.Count == wave_count`
> - Activating wave 0 via MCU_Activate produces a complete flight (EL-003 assertions still pass)

---

## Session 1.5 — Command Buffer + Serialization

| | |
|---|---|
| **Task ID** | 1.5 |
| **Component** | Compiler (`src/mmf/compiler/command_buffer.py`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 1.1 (ID generator) |
| **Delivers To** | 1.10 (composition — all `[IN]` signals route through the buffer) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → SM-001, SM-003, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Principal Python Systems Developer. The Command Buffer is the race-condition prevention layer. Without it, simultaneous `[IN]` signals produce non-deterministic state transitions because IL-2 processes MCU activations in a non-deterministic order within a single engine tick. The buffer serializes those transitions. Constraint SM-003 (timer pause semantics) is the subtlest failure mode here — a reused timer does not reset on reactivation, so a buffer that recycles timers silently produces incorrect timing behavior.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [SM-001] HIGH — All `[IN]` signals route through serialization timer before Command Buffer. Sequence: Deactivate → Timer (50–100ms) → Activate. Each `[IN]` port gets a unique delay in 50ms increments. Max delay 200ms. Auto-generated from module `[IN]` port count.
> - [SM-003] HIGH — MCU_Timer nodes for time-gated logic SHALL NOT be reused. Compiler generates a discrete timer instance for each possible activation path. Each activation engages a fresh, never-triggered timer.
> - Section 4.1: The Command Buffer
> - Section 4.1.1: Serialization Sequence
> - Section 4.1.2: Timer Pause Semantics

### Requirements

**R1 — Buffer Generation**

For each `[IN]` port in the module:
- `[IN]` proxy node (`MCU_Timer`, 0s delay) receives external activation signal
- `MCU_Deactivate` → clears any in-progress state
- `MCU_Timer` (serialization delay) — unique instance, never reused, never recycled
- `MCU_Activate` → engages new state

Delay values: `[IN]_Primary` = 50ms, `[IN]_Secondary` = 100ms, `[IN]_Tertiary` = 150ms. Max 200ms (four ports maximum).

**R2 — Timer Pool (No Reuse)**

The compiler maintains a timer pool per module. Once a timer is emitted into a Command Buffer path, it is marked used and can never be assigned to another path. Attempting to reuse raises `TimerReuseError`.

**R3 — Port Count Validation**

If a module defines more than 4 `[IN]` ports, emit a `CompilerWarning`: max serialization delay of 200ms would be exceeded. Do not abort — emit the warning and generate the extra timers with delays > 200ms flagged.

> **[SM-001] — HIGH** Each `[IN]` port gets a unique, staggered delay (50ms increments). Auto-generated from port count — the session author does not manually specify delays.

> **[SM-003] — HIGH** Timer pause semantics: IL-2 pauses a deactivated timer at its current countdown position, not zero. Reactivation resumes from the paused position. A reused timer fires early. Each activation path MUST have a fresh timer.

> **EXIT CONDITION — Acceptance Criteria**
> - Two simultaneous `[IN]` signals produce deterministic, non-interleaved state transitions
> - No MCU_Timer is referenced by more than one Command Buffer path
> - Serialization delays: `[IN]_Primary` = 50ms, `[IN]_Secondary` = 100ms (verified in emitted output)
> - `TimerReuseError` raised if timer assignment logic attempts to reuse a used timer
> - Module with 4 `[IN]` ports generates 4 distinct timer instances with delays 50/100/150/200ms

---

## Session 1.6 — Garbage Collection

| | |
|---|---|
| **Task ID** | 1.6 |
| **Component** | Compiler (`src/mmf/compiler/garbage_collection.py`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 1.3 (flight emitter — GC wraps Entity proxy events), 1.4 (Magazine Array — GC advances the counter) |
| **Delivers To** | 1.10 (composition — GC output feeds Magazine Array counter) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → SM-002, SM-004, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Principal Python Systems Developer. Garbage collection is the AI slot reclamation mechanism. The IL-2 DServer has an approximately 100-unit active AI cap. Without GC, every wave adds to the active count permanently. Two failure modes interact here: SM-004 (dual-path) ensures early leader kills don't stall the activation chain; SM-002 (leader-kill resilience) ensures wingmen don't idle indefinitely consuming AI slots when the leader dies before ToS.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [SM-004] LOW — Dual-path GC: both Entity.OnKilled chain AND ToS Despawn chain independently route to the next-wave counter. Each path through a dedicated 1-count non-resetting MCU_Counter to prevent double-counting.
> - [SM-002] HIGH — Command:RTB and Command:Waypoint SHALL Object Link to ALL aircraft, not leader only. Leader MCU_TR_Entity.OnKilled triggers parallel GC chain: ForceComplete → 30s Timer → Despawn, Object Linked to all wingmen. MCU_TR_CheckZone fallbacks PROHIBITED.
> - Section 5.3: Garbage Collection
> - Section 5.3.1: Dual-Path Activation
> - Section 5.3.2: Leader-Kill Resilience

### Requirements

**R1 — ToS Expiration Path**

On ToS timer expiry:
- Issue `Command:RTB` → Object Linked to ALL aircraft in flight (not leader only)
- `MCU_CMD_Despawn` → Object Linked to ALL aircraft
- Despawn confirmation → 1-count MCU_Counter (path A gate) → Magazine Array next-wave counter

**R2 — Leader-Kill Path**

On `Entity.OnKilled` (leader killed):
- ForceComplete → Object Linked to all wingmen
- 30-second `MCU_Timer` → `MCU_CMD_Despawn` → Object Linked to all wingmen
- Despawn → 1-count MCU_Counter (path B gate) → Magazine Array next-wave counter

**R3 — Double-Count Prevention**

Each path (A and B) passes through its own dedicated 1-count non-resetting MCU_Counter. Once a path fires, its gate counter has reached its count and will not fire again for that wave. The downstream wave-advance counter accepts input from both gates.

**R4 — CheckZone Prohibition**

`MCU_TR_CheckZone` must not appear in any GC chain. If code would emit a CheckZone, raise `ProhibitedNodeError`. Rationale: area-based polling causes multiplayer desync and logic stutter.

> **[SM-002] — HIGH** Object Links on RTB/Waypoint/Despawn must cover ALL aircraft. Leader kill before ToS leaves wingmen without a leader to receive RTB. Without all-aircraft links, surviving wingmen idle forever and consume AI slots permanently.

> **[SM-004] — LOW** Dual-path is mandatory even though SM-004 is rated LOW. If only the Despawn path routes to the counter, an early leader kill stalls the Magazine Array permanently. Both paths must independently advance the counter.

> **EXIT CONDITION — Acceptance Criteria**
> - Leader killed before ToS: wingmen receive ForceComplete + Despawn within 30s
> - Both kill path and Despawn path independently advance the next-wave counter
> - No double-counting: a wave where leader dies AND ToS fires advances counter exactly once
> - `Command:RTB` Object Links cover all aircraft (not just leader) in emitted output
> - No `MCU_TR_CheckZone` node in any GC chain
> - 30-second timer present in leader-kill parallel GC chain

---

## Session 1.7 — Dependency Stub System

| | |
|---|---|
| **Task ID** | 1.7 |
| **Component** | Compiler (`src/mmf/compiler/dependency_stubs.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 1.1 (ID generator — stub IDs are from a reserved range, excluded from the main counter) |
| **Delivers To** | 1.10 (composition — pre-flight validation runs before .Group file is written) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → EC-002, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Senior Python Developer implementing the pre-flight dependency check. Missing `[OUT]` targets cause fatal DServer crashes on mission load. The stub system catches those missing references before the .Group file is written.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EC-002] MEDIUM — Stub MCU_Timers allocated from reserved range 900000–999999 (excluded from dynamic ID counter). Compiler emits comment block listing all stubs, their IDs, and the missing module references they catch.
> - Section 3.2: Dependency Management (The Stub System)

### Requirements

**R1 — Pre-Flight Validation**

After all modules are compiled but before the .Group file is written, scan every `Targets` array in the output for IDs that do not correspond to any defined block. Collect the full list of missing references.

**R2 — Stub Generation**

For each missing reference ID:
- Generate a 0-second `MCU_Timer` at that ID (`stub.Index = missing_id`)
- `Stub.Targets = []` (no downstream connections)
- Stub ID must be in range 900000–999999

If the missing reference ID falls outside 900000–999999, reassign it to the next available stub ID in that range and update the reference in the `Targets` array.

**R3 — Stub Manifest Comment**

Emit a comment block at the top of the .Group file listing:

```
// MMF STUB MANIFEST
// Stub ID: 900001 → Missing module: [OUT]_Success of blue_escort_bravo
// Stub ID: 900002 → Missing module: [IN]_Activate of red_bomber_01
```

> **[EC-002] — MEDIUM** Stub IDs are isolated in 900000–999999 to prevent any collision with dynamically-assigned compiler IDs. The manifest makes stubs auditable — a mission designer can see exactly which cross-module references are unresolved.

> **EXIT CONDITION — Acceptance Criteria**
> - A module referencing a missing `[OUT]` target compiles without crash — stub is generated
> - `Stub.Index` falls in range 900000–999999
> - No stub ID collides with any dynamically-assigned compiler ID
> - Stub manifest comment block is present at top of emitted .Group file
> - Manifest accurately lists all stubs with their IDs and missing reference descriptions

---

## Session 1.8 — Required Field Validator + Reserved-Char Filter

| | |
|---|---|
| **Task ID** | 1.8 |
| **Component** | Compiler (`src/mmf/compiler/validator.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 0.4 (MCU catalog — catalog defines required fields per MCU type) |
| **Delivers To** | 1.10 (composition — validation runs at compilation entry point) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → PI-001, PI-002, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Senior Python Developer implementing the two input-hygiene gates. These run at the start of compilation — before any ID assignment or code generation — so malformed input is rejected cheaply and diagnostics are clean.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [PI-001] CRITICAL — Any MCU command node (AttackArea, Cover, Waypoint) with null or zero-length Targets/Objects array aborts compilation. Diagnostic identifies module, node type, and missing field.
> - [PI-002] HIGH — Second-pass reserved-character filter on all string fields. Reserved chars `{}[];="` stripped. Operates independently of GUI-side sanitization.
> - Section 3: Standardized I/O & Logic Hooks
> - Section 3.1: Compiler Validation
> - Section 2.1: JSON Intermediary (PI-002 context)

### Requirements

**R1 — Required Field Check (PI-001)**

For every MCU node in the compiled output, check against the 0.4 catalog:
- If the MCU type has required fields, verify each is present and non-null
- For command nodes (AttackArea, Cover, Waypoint): `Targets`/`Objects` must be a non-empty list
- Violation raises `CompilationError` with: `module_id`, `node_type`, `node_index`, `missing_field`

Compilation halts on the first violation. Do not accumulate and continue.

**R2 — Reserved-Char Filter (PI-002)**

Apply a second-pass filter to all string-type field values in the compiled output:

```python
RESERVED = set('{}[];="')
```

Strip all reserved characters from string values. This is not an error — it is a silent sanitization pass. Log stripped characters with their source field for debugging.

**R3 — Validation Ordering**

Validation order: PI-001 check first, PI-002 filter second. Both run before ID assignment and before any output is written.

> **[PI-001] — CRITICAL** A null Targets array on a command node causes a fatal DServer crash on mission load. The crash is silent and non-recoverable. This must be caught at compile time, not discovered by flying the mission.

> **[PI-002] — HIGH** The reserved-char filter is a second-pass defense, not a first-pass fix. The GUI should sanitize its output. The compiler sanitizes regardless. Two independent lines of defense.

> **EXIT CONDITION — Acceptance Criteria**
> - Compilation aborts on AttackArea node with empty Targets array; diagnostic identifies module and node
> - Compilation aborts on Waypoint node with null Objects; diagnostic present
> - String field containing `{}[];="` is serialized with those chars stripped
> - PI-002 filter log entry present for each stripped character
> - Valid input with no violations compiles without error

---

## Session 1.9 — Initialization Buffer

| | |
|---|---|
| **Task ID** | 1.9 |
| **Component** | Compiler (`src/mmf/compiler/init_buffer.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 1.4 (Magazine Array — init buffer triggers wave 0) |
| **Delivers To** | 1.10 (composition — Master Core is the mission start node) |
| **Reference** | See `ARCHITECTURE.md` — FMEA Constraints → EC-001, Directory Structure → `src/mmf/compiler/` |

### Role

You are a Senior Python Developer implementing the mission initialization gate. Loading thousands of MCUs at T=0 causes dropped frames and skipped logic triggers. The initialization buffer delays all activation until 3D physics instantiation completes.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EC-001] MEDIUM — Master Core initialization delay configurable (default 3s, range 3–10s). Compiler emits warning if total `Enabled=FALSE` entities > 200 AND delay < 5s.
> - Section 5.1: The Initialization Buffer

### Requirements

**R1 — Master Core Block**

Generate one Master Core per compiled output:
- `MCU_TR_MissionBegin` block (fires on mission load)
- Linked to `MCU_Timer` with delay = `initialization_delay_seconds` (from `compiler_options`)
- Timer output links to all `[IN]_Activate` proxy nodes for all modules in the session

**R2 — Delay Validation**

After emission, count total `Enabled=FALSE` entities in the output. If count > 200 and `initialization_delay_seconds < 5`, emit `CompilerWarning` identifying the entity count and recommended delay.

**R3 — Configurable Range**

`initialization_delay_seconds` must be in range [3, 10]. Values outside that range raise `ConfigurationError` before any compilation begins.

> **[EC-001] — MEDIUM** The 3-second default is insufficient for missions with > 200 sleeping entities. Physics instantiation is queued sequentially. Entity proxies that attempt to bind before their aircraft are instantiated will bind to nothing permanently.

> **EXIT CONDITION — Acceptance Criteria**
> - `MCU_TR_MissionBegin` present in emitted output, linked to initialization timer
> - Timer delay matches `initialization_delay_seconds` from `compiler_options` (default 3s)
> - Timer links to all module `[IN]_Activate` proxy nodes
> - Warning emitted for 250-entity mission with 3s delay
> - No warning emitted for 250-entity mission with 5s delay
> - `ConfigurationError` raised for delay values outside [3, 10]

---

## Session 1.10 — Static CAP Composition

| | |
|---|---|
| **Task ID** | 1.10 |
| **Component** | Compiler (`src/mmf/compiler/modules/static_cap.py`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 1.1–1.9 (all compiler primitives must be implemented and tested) |
| **Delivers To** | 1.10h (in-game test — the output of this session is what gets flown) |
| **Reference** | See `ARCHITECTURE.md` — all FMEA Constraints active simultaneously; Phase Mapping → Phase 1; Directory Structure → `src/mmf/compiler/` |

### Role

You are a Principal Python Systems Developer. This session wires all nine compiler primitives together into a complete Static CAP module. The inputs are a valid `mmf-sample-static-cap.json` payload and all prior primitive implementations. The output is a .Group file that imports into BOSEditor without errors.

### Context

The Static CAP is the first complete module and the proof that the compiler architecture is sound. It requires: a waypoint patrol loop, an AttackArea command, a Magazine Array for wave management, a Command Buffer for `[IN]` serialization, dual-path GC, Entity proxies with EL-002/EL-003 compliance, dependency stub pre-flight, field validation, and the Master Core initialization buffer. All FMEA constraints must be satisfied simultaneously.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All Phase 1 FMEA constraints active simultaneously: PI-001, PI-002, PI-003, PI-004, EL-001, EL-002, EL-003, SM-001, SM-002, SM-003, SM-004, EC-001, EC-002, EC-003, EC-004
> - Section 6.1: Initial Validation Prototype — Static CAP description
> - `mmf-sample-static-cap.json` — reference input payload

### Requirements

**R1 — Module Pipeline**

The `StaticCAPCompiler` class orchestrates the following sequence:

1. Validate input payload (PI-001, PI-002) via task 1.8 validator
2. Initialize IDGenerator from target mission (or from `counter_start`) — PI-003
3. Allocate spatial block for this module — PI-004
4. Generate Magazine Array (`wave_count` flights via FlightEmitter) — EL-001, EC-003, EL-002, EL-003
5. Generate waypoint loop and AttackArea command nodes
6. Generate Command Buffer for `[IN]_Activate` — SM-001, SM-003
7. Generate GC chains (dual-path, all-aircraft links) — SM-002, SM-004
8. Generate `[OUT]_Success` and `[OUT]_Fail` proxy nodes
9. Run dependency stub pre-flight — EC-002
10. Generate Master Core initialization buffer — EC-001
11. Serialize all blocks to IL-2 ASCII via task 0.3 writer

**R2 — Waypoint Loop**

Generate `Command:Waypoint` MCUs from the `waypoints.points` array. If `waypoints.loop = true`, link the last waypoint back to the first. Waypoint MCUs Object Link to the leader aircraft.

**R3 — AttackArea**

Generate one `MCU_CMD_AttackArea` node from the `attack` block. `AttackArea.Targets` must be non-empty (PI-001 catches this). AttackArea Object Links to the leader aircraft.

**R4 — Output Proxy Nodes**

`[IN]_Activate`, `[OUT]_Success`, `[OUT]_Fail`: each is a 0-second `MCU_Timer` placed at `proxy_coordinates`. These are the only nodes visible at the user-specified spawn location.

> **EXIT CONDITION — Acceptance Criteria**
> - Compiled .Group file imports into BOSEditor without errors (human verifies 1.10h)
> - All 14 FMEA constraint acceptance criteria from sessions 1.1–1.9 are satisfied in the integrated output
> - Waypoint loop present; last waypoint links back to first when `loop=true`
> - AttackArea node present with non-empty Targets
> - Proxy nodes (`[IN]`, `[OUT]`) appear at `proxy_coordinates` in BOSEditor
> - Internal MCUs appear at remote coordinates (50km+ offset)
> - `mmf-sample-static-cap.json` compiles to a valid .Group file without warnings

---

## Human Gate 1.10h — In-Game Test

| | |
|---|---|
| **Gate ID** | 1.10h |
| **Depends On** | 1.10 — compiled .Group file |
| **Actor** | Project Owner |
| **Blocks** | Phase 2 cannot begin until this gate is passed |

### Required Actions

- Import the compiled .Group file into BOSEditor
- Link `[IN]_Activate` to an `MCU_TR_MissionBegin` in a test mission
- Configure a 30-minute test session on a DServer or single-player host
- Fly or observe the session for the full 30 minutes

### Verification Checklist

- **AI patrol:** aircraft follow the waypoint loop continuously
- **AI engagement:** aircraft attack targets within the AttackArea
- **ToS expiry:** aircraft RTB at the configured time-on-station
- **Despawn:** aircraft are removed from the world after RTB + despawn delay
- **Next-wave activation:** second wave activates after first wave despawns
- **Leader-kill path:** kill the leader mid-sortie — wingmen despawn within 30s, next wave activates
- **No AI slot leak:** slot count returns to baseline after each wave despawns
- **30-minute session stable:** no DServer crash, no logic stall, no runaway AI count

### Report Requirements

Document the test results before Phase 2 begins. For each verification item: PASS, FAIL, or NOT OBSERVED. If any item is FAIL, report it as a compiler bug — return to the relevant primitive session (1.3–1.10) with the failure evidence before proceeding.

The Phase 2 GUI and Module Reverse Engineer depend on the compiler being correct. A compiler bug discovered in Phase 2 is 2–3× more expensive to fix than one caught here.

---

## Recommended Execution Sequence

```
Phase 0 (Complete: Parser, Writer, Catalog, Schema, Structure)
    ↓
    ├──→ 1.1 (ID Generator) ─────────────────────────────────────────┐
    │        ↓                                                        │
    │        ├──→ 1.2 (Spatial Offset)                               │
    │        ├──→ 1.5 (Command Buffer)                               │
    │        └──→ 1.7 (Dependency Stubs)                             │
    │                                                                 │
    ├──→ 1.8 (Validator) ← 0.4 (Catalog)                            │
    │                                                                 │
    └──→ 1.3 (Flight Emitter) ← 0.4, 1.1                           │
             ↓                                                        │
             ├──→ 1.4 (Magazine Array)                               │
             │        ↓                                               │
             │        └──→ 1.9 (Init Buffer)                         │
             │                                                        │
             └──→ 1.6 (GC) ← 1.4                                    │
                                                                      │
                      All tasks ──→ 1.10 (Static CAP Composition) ───┘
                                         ↓
                                         1.10h (HUMAN: In-Game Test)
                                         ↓
                                         Phase 2 begins
```

- **Start immediately (parallel):** Session 1.1 (ID generator), Session 1.8 (validator — depends only on 0.4)
- **After 1.1 (parallel):** Session 1.2 (spatial offset), Session 1.5 (command buffer), Session 1.7 (dependency stubs)
- **After 0.4 + 1.1:** Session 1.3 (flight emitter)
- **After 1.3:** Session 1.4 (Magazine Array)
- **After 1.3 + 1.4:** Session 1.6 (garbage collection)
- **After 1.4:** Session 1.9 (initialization buffer)
- **After all:** Session 1.10 (Static CAP composition)
- **After 1.10:** Gate 1.10h (in-game test)
- **Phase 2 begins after:** Gate 1.10h PASSED
