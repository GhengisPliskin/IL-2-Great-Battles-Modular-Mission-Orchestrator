# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 5 — Mission Orchestrator
### Session Prompt Headers
*Full .Mission file generation from high-level scenario parameters*

**7 AI Sessions | 3 Human Gates | Task IDs 5.1 – 5.7**

---

## Phase 5 Overview

Phase 5 builds the Mission Orchestrator: the engine that merges multiple compiled .Group modules into a complete .Mission file, adds mission-level infrastructure (player spawns, coalitions, briefing text, mission begin/end logic), and provides a GUI for generating missions from high-level scenario parameters. This is where the entire MMF stack integrates — the compiler (Phase 1), module types (Phase 3), and map databases (Phase 4) converge into a single pipeline that outputs flyable .Mission files for DServer multiplayer or single-player use.

Every FMEA constraint from Phases 0–3 remains active at this layer. The Orchestrator does not re-implement compiler primitives — it invokes them. But it is responsible for mission-level concerns that compound constraint interactions: multiple modules sharing a single ID counter (PI-003), multiple Magazine Arrays competing for the ~100 AI unit cap (EC-004), and initialization timing across dozens of modules (EC-001). Errors at this layer produce missions that load but behave incorrectly — the most expensive failure mode to diagnose.

Tasks 5.1–5.3 and 5.7 are Tier 1 (Opus 4.6 / Gemini 3.1 Pro) — they require cross-constraint reasoning across the full FMEA set and engine-semantic understanding of mission-level assembly. Tasks 5.4, 5.5, and 5.6 are Tier 2 (Sonnet 4.6 / Gemini 3 Flash) — they compose existing infrastructure with well-defined specifications.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 5.1 | Build mission assembly engine: merge .Groups, mission properties, coalitions, begin/end translators | Orchestrator | AI | Tier 1: Opus 4.6 |
| 5.2 | Implement player spawn management: airfields, plane sets, spawn points, briefing text (SP + MP) | Orchestrator | AI | Tier 1: Opus 4.6 |
| 5.2h | DSERVER TEST: Load assembled .Mission, verify MP client connection, spawning, mission execution | Testing | HUMAN | N/A |
| 5.3 | Implement scenario templates: Intercept, Patrol, Ground Attack, Escort, Free Hunt | Orchestrator | AI | Tier 1: Opus 4.6 |
| 5.4 | Implement ambient AI: background transport, artillery, convoys using lightweight modules | Orchestrator | AI | Tier 2: Sonnet 4.6 |
| 5.5 | Build Orchestrator GUI: map selector, scenario type, difficulty, weather/time, Generate button | Orchestrator GUI | AI | Tier 2: Sonnet 4.6 |
| 5.5h | IN-GAME TEST: Generate 5+ missions across maps and scenario types, fly each, report issues | Testing | HUMAN | N/A |
| 5.6 | Implement DServer rotation: batch generation, SDS config update, rotation scheduling | Orchestrator | AI | Tier 2: Sonnet 4.6 |
| 5.6h | DSERVER TEST: Run automated rotation for 3+ hours, monitor stability and transitions | Testing | HUMAN | N/A |
| 5.7 | Implement inter-mission state feedback: read DServer logs, extract results, feed to next generation | Orchestrator | AI | Tier 1: Opus 4.6 |

**Dependency order:** 5.1 depends on 1.10 (working compiler) and 4.2 (validated map database). 5.2 depends on 5.1 and 4.2. 5.2h depends on 5.2. 5.3 depends on 5.1, 5.2, and 4.3 (front-line data). 5.4 depends on 5.3. 5.5 depends on 5.3 and 2.3 (GUI framework from Phase 2). 5.5h depends on 5.5. 5.6 depends on 5.5. 5.6h depends on 5.6. 5.7 depends on 5.6.

```
Phase 1 (1.10 Compiler) + Phase 3 (Module Types) + Phase 4 (4.2 Map DB, 4.3 Front Lines)
    ↓
    5.1 (Mission Assembly Engine)
    ↓
    5.2 (Player Spawn Management) ← 4.2 (Map DB)
    ↓
    5.2h (HUMAN: DServer MP Test)
    ↓
    5.3 (Scenario Templates) ← 4.3 (Front-Line Data)
    ↓
    ├──→ 5.4 (Ambient AI)
    │
    └──→ 5.5 (Orchestrator GUI) ← 2.3 (GUI Framework)
         ↓
         5.5h (HUMAN: In-Game Flight Test)
         ↓
         5.6 (DServer Rotation)
         ↓
         5.6h (HUMAN: DServer Stability Test)
         ↓
         5.7 (Inter-Mission State Feedback)
```

---

## Session 5.1 — Mission Assembly Engine

| | |
|---|---|
| **Task ID** | 5.1 |
| **Component** | Orchestrator (`src/backend/orchestrator/mission_builder.py`) |
| **Model Tier** | Tier 1 |
| **Assigned Model** | Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 1.10 (working compiler + all primitives), 4.2 (validated map database with airfield coordinates) |
| **Delivers To** | 5.2 (player spawn layer), 5.3 (scenario templates), 5.5 (GUI), 5.6 (batch generation) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/orchestrator/`, Phase Mapping → 5.1–5.3, FMEA Constraints (full set) |

### Role

You are a Principal Python Systems Developer building the top-level mission assembly engine for the IL-2 Modular Mission Orchestrator. This engine is the integration point where multiple compiled .Group modules are merged into a single .Mission file with all required mission-level infrastructure. Every FMEA constraint from the compiler layer propagates here — a mission-level assembly error can silently invalidate constraints that were individually satisfied in each module.

### Context

An IL-2 .Mission file is a superset of the .Group format. It contains everything a .Group contains (MCU blocks, entity blocks, translator blocks) plus mission-level structures: `Options` (weather, time, date, wind), `MissionBegin` trigger, `MissionEnd` trigger, `Countries` with coalition assignments, and airfield/spawn infrastructure. The assembly engine must merge N compiled .Group module outputs into this mission envelope while maintaining a single global ID counter, non-overlapping spatial zones, and correct coalition wiring.

The compiler (Phase 1) already handles per-module constraint enforcement. The assembly engine's unique responsibility is cross-module constraint management: the global ID counter must span all modules without collision, the combined AI count across all modules must respect the ~100 unit cap, and the initialization buffer must stagger module activation to prevent frame drops from mass MCU loading.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - Section 2.1: JSON Intermediary — the assembly engine consumes compiled module outputs and wraps them in mission-level structure
> - Section 2.4: ID Management — PI-003 monotonic counter must span all modules in a single mission
> - Section 5.1: Initialization Buffer — EC-001 Master Core delays all module activation until 3D physics loads
> - Section 5.2.3: GC-Gated Wave Activation — EC-004 AI cap must be calculated across ALL modules in the mission, not per-module
> - [PI-003] CRITICAL — Single monotonic counter per compilation session; mission-level assembly is a single session even if it contains 10+ modules
> - [EC-001] MEDIUM — Master Core initialization delay configurable (default 3s, range 3–10s); warn if >200 Enabled=FALSE entities with delay <5s
> - [EC-004] HIGH — Total max_concurrent_AI = sum of all modules' (flight_size × max_simultaneous_waves); warn if >80
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Phase 1 outputs: all compiler primitives in `src/mmf/compiler/`, the `compiler.py` driver, the JSON schema at `src/mmf/schema/`
- Phase 4 outputs: map database at `data/map_databases/`, airfield coordinate data
- Module template JSON files from Phase 2/3: `data/module_templates/*.json`
- Parser library: `src/mmf/parser/` (for reading existing .Mission files and writing new ones)

### Requirements

**R1 — Mission Envelope Generation**

Generate the mission-level ASCII structures that wrap compiled module blocks:
- `Options` block: date, time, weather preset, wind layers, cloud base, temperature
- `MissionBegin` trigger: linked to the Master Core initialization timer
- `MissionEnd` trigger: linked to optional end conditions or a hard session timer
- Coalition assignment: `Countries` block with Axis and Allied country lists
- Map selector: `GuiMap` field referencing the correct map directory name

**R2 — Multi-Module Merging**

Accept N compiled module outputs (each a list of IL-2 ASCII blocks) and merge them into a single .Mission file:
- A single `IDGenerator` instance spans all modules — no per-module counters
- Spatial offset engine allocates distinct remote zones per module (PI-004)
- All `[IN]_Activate` proxies route from the shared Master Core initialization chain
- Module outputs (`[OUT]_Success`, `[OUT]_Fail`) are available for cross-module wiring

**R3 — Mission-Level AI Cap Enforcement**

Before emitting the final .Mission, calculate the aggregate AI load:

```python
total_max_ai = sum(
    module.flight_size * module.max_simultaneous_waves
    for module in all_modules
)
if total_max_ai > 80:
    emit_warning(f"Aggregate AI cap risk: {total_max_ai} exceeds 80-unit threshold")
```

This is a mission-level check — individual modules may pass EC-004 in isolation but exceed the cap in combination.

**R4 — Master Core Generation**

Generate the shared Master Core module containing:
- `MCU_TR_MissionBegin` → initialization delay timer (EC-001)
- Delay timer output fans out to all module `[IN]_Activate` proxies
- Configurable delay with entity-count-based warning

**R5 — Public API**

```python
class MissionBuilder:
    def __init__(self, map_name: str, options: MissionOptions)
    def add_module(self, module_json: dict) -> None
    def set_coalitions(self, axis: list[str], allied: list[str]) -> None
    def build(self) -> str  # returns .Mission ASCII content
    def write(self, path: str) -> None
```

> **[PI-003] — CRITICAL** The mission assembly engine is a single compilation session. The IDGenerator initializes once and serves all modules. If a target .Mission file is provided, the counter starts from max(existing IDs) + 1. Per-module ID counter restarts are prohibited.

> **[EC-004] — HIGH** The ~100 AI unit cap is a mission-level constraint. Individual modules may satisfy EC-004 in isolation but exceed the cap in combination. The assembly engine must calculate and enforce the aggregate AI count across ALL modules before emitting the .Mission file.

> **[EC-001] — MEDIUM** The initialization delay must account for the total entity count across all modules. A 10-module mission with 200+ Enabled=FALSE entities needs a delay of at least 5 seconds — the default 3 seconds risks dropped triggers during mass activation.

> **EXIT CONDITION — Acceptance Criteria**
> - Assembled .Mission file loads in DServer without parse errors
> - All module blocks are present in the merged output with unique, non-colliding IDs
> - `Options` block contains valid weather, time, date fields
> - `MissionBegin` trigger chains through Master Core to all module `[IN]_Activate` proxies
> - Aggregate AI cap calculated and warning emitted when total exceeds 80
> - IDGenerator emits a strictly ascending sequence spanning all modules with no gaps in the reserved range (900000–999999)
> - Spatial offset zones are unique per module — no remote coordinate overlap
> - Unit tests: merge 3+ modules, verify ID uniqueness, verify spatial isolation, verify coalition assignment

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

## Session 5.2 — Player Spawn Management

| | |
|---|---|
| **Task ID** | 5.2 |
| **Component** | Orchestrator (`src/backend/orchestrator/mission_builder.py`) |
| **Model Tier** | Tier 1 |
| **Assigned Model** | Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 5.1 (mission assembly engine), 4.2 (validated airfield database with spawn positions) |
| **Delivers To** | 5.2h (DServer MP test), 5.3 (scenario templates use player spawns) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/orchestrator/`, Phase Mapping → 5.1–5.3 |

### Role

You are a Principal Python Systems Developer implementing the player-facing infrastructure layer of the Mission Orchestrator. Player spawns are the bridge between the generated AI mission and the human players who fly in it. This task requires understanding both the IL-2 multiplayer architecture (DServer client connection, plane selection, coalition assignment) and the single-player mission briefing system.

### Context

An IL-2 .Mission file for multiplayer requires specific infrastructure that .Group files do not contain: airfield objects with spawn points, plane sets defining available aircraft per coalition, briefing text describing the scenario, and the coalition structure that assigns players to Axis or Allied sides. For single-player, additional elements include a player-controlled aircraft entity and a scripted mission flow.

The airfield database from Phase 4 provides coordinates, runway headings, and spawn point locations for every airfield on every map. The Orchestrator must select appropriate airfields based on the scenario's front-line position, generate the spawn infrastructure at those coordinates, and wire the plane sets to match the scenario's time period and theater.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - Section 1: Project Objective — targets continuous 180-minute multiplayer DServer sessions
> - Section 5.1: Initialization Buffer — player spawns are loaded at mission start; init delay (EC-001) must account for airfield object count
> - [PI-003] CRITICAL — Airfield objects, spawn points, and plane set entities all receive IDs from the shared monotonic counter
> - [PI-001] CRITICAL — Airfield and spawn MCU blocks have required fields; null or empty arrays abort compilation
> - IL-2 Mission Editor Manual: Airfield objects (pg. 109–112), Multiplayer spawn configuration
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Task 5.1 outputs: `MissionBuilder` class with module merging and Master Core generation
- Phase 4 outputs: airfield database with per-map coordinates, runway headings, spawn point positions
- Phase 4.3 outputs: front-line reference data for airfield selection by coalition
- IL-2 Mission Editor reference: airfield block structure, plane set syntax, briefing format

### Requirements

**R1 — Airfield Object Generation**

For each coalition, generate one or more airfield objects:
- Airfield position from the map database (Phase 4.2)
- Runway heading from extracted data
- Spawn points positioned along the runway at correct offsets
- Airfield objects receive IDs from the shared `IDGenerator` (PI-003)
- All required fields populated — no null arrays (PI-001)

**R2 — Plane Set Generation**

For each airfield, generate plane set blocks defining available aircraft:
- Aircraft list filtered by map, date, and coalition (historically accurate)
- Loadout options per aircraft type
- Fuel range constraints per scenario type
- Plane sets wired to the correct airfield spawn points

**R3 — Briefing Text Generation**

Generate structured briefing text for the mission:
- Scenario type and objective description
- Weather and time summary
- Coalition-specific briefing (Axis sees Axis objectives; Allied sees Allied)
- Airfield names and locations referenced

**R4 — Single-Player Mode**

When `output_mode == 'mission'` with SP configuration:
- Generate a player-controlled aircraft entity at the selected airfield
- Wire mission begin to player takeoff sequence
- Link scenario objectives to mission success/failure conditions

**R5 — Multiplayer Mode**

When `output_mode == 'mission'` with MP configuration:
- Generate DServer-compatible spawn infrastructure
- Multiple spawn points per airfield (support concurrent player connections)
- Coalition balance: configurable max players per side
- No player-controlled aircraft entities — DServer manages player assignment

> **[PI-003] — CRITICAL** Airfield objects, spawn points, plane sets, and briefing MCUs all participate in the shared ID counter. The spawn management layer does not maintain a separate counter — it draws from the same `IDGenerator` instance that the module assembly uses.

> **[PI-001] — CRITICAL** Every airfield MCU and plane set block must pass the Required Field validator. An airfield with an empty spawn point array is structurally invalid — the DServer will fail to load the mission. The assembly engine must refuse to emit incomplete airfield infrastructure.

> **EXIT CONDITION — Acceptance Criteria**
> - Player spawns correctly in multiplayer: DServer accepts client connection, player selects coalition and plane, spawns at airfield
> - Player spawns correctly in single-player: player aircraft present at airfield, mission begins on takeoff
> - Airfield positions match the map database coordinates (within 10m tolerance)
> - Plane sets contain historically appropriate aircraft for the scenario's map, date, and coalition
> - Briefing text renders correctly in the IL-2 mission briefing screen
> - All airfield and spawn IDs are unique and drawn from the shared counter
> - No null or empty required fields in airfield/spawn blocks (PI-001 validated)

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

## Human Gate 5.2h — DServer Multiplayer Test

| | |
|---|---|
| **Gate ID** | 5.2h |
| **Depends On** | 5.2 — assembled .Mission file with player spawn infrastructure |
| **Actor** | Project Owner |
| **Blocks** | 5.3 cannot begin until basic mission loading and MP spawning are confirmed |

### Required Actions

- Load the assembled .Mission file on a DServer instance
- Connect with an MP client from a second machine or instance
- Select a coalition, choose an aircraft from the plane set, and spawn at the airfield
- Verify mission execution: AI modules activate after initialization delay, AI aircraft patrol/engage as expected

### Verification Checklist

- **DServer loads:** mission file accepted without parse errors or console warnings
- **Client connection:** MP client connects to the server and sees the mission lobby
- **Coalition selection:** both Axis and Allied sides are available with correct plane sets
- **Player spawn:** player spawns at the correct airfield position on the correct runway
- **Module activation:** AI modules activate after the Master Core initialization delay
- **AI behavior:** AI aircraft follow their programmed behavior (patrol, engage, RTB, despawn)
- **No crash:** DServer runs stable for at least 10 minutes with a connected player

### Report Requirements

Document the test results before task 5.3 begins. For each verification item: PASS, FAIL, or NOT OBSERVED. If any item is FAIL, return to the relevant session (5.1 or 5.2) with the failure evidence. A mission that loads but does not support MP spawning correctly is a blocker for all downstream Phase 5 work.

---

## Session 5.3 — Scenario Templates

| | |
|---|---|
| **Task ID** | 5.3 |
| **Component** | Orchestrator (`src/backend/orchestrator/scenario_engine.py`) |
| **Model Tier** | Tier 1 |
| **Assigned Model** | Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 5.1 (mission assembly engine), 5.2 (player spawn management), 4.3 (front-line reference data) |
| **Delivers To** | 5.4 (ambient AI), 5.5 (GUI — scenario type selector), 5.6 (batch generation) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/orchestrator/`, Phase Mapping → 5.1–5.3, FMEA Constraints (full set) |

### Role

You are a Principal Python Systems Developer with domain expertise in tactical air combat mission planning. The scenario engine translates high-level parameters (scenario type, map, difficulty, front-line position) into a fully wired mission by selecting modules, calculating coordinates from the map database, and assembling them via the mission builder. This is where spatial reasoning meets constraint enforcement — every coordinate must be tactically plausible AND satisfy the FMEA constraints that govern how modules interact.

### Context

A scenario template is a recipe for generating a complete mission from high-level inputs. The user selects "Intercept on Stalingrad" and the engine must: identify appropriate Axis and Allied airfields from the map database, calculate waypoint chains from airfields to the engagement area near the front line, select and configure the correct module types (Intercept, Patrol, Ground Attack, etc.), wire them together via `[OUT]`→`[IN]` connections, and pass the assembled configuration to the mission builder.

The front-line data from Phase 4.3 provides the geographic anchor: engagement areas are placed near the front line, airfields are selected by coalition side, and flight paths route from rear airfields through the front to the engagement zone and back. The route generation utility from Phase 4.4 calculates tactically plausible waypoint chains accounting for altitude, speed, and distance.

Five scenario templates are required: Intercept (fighters defend against incoming attackers), Patrol (fighters sweep an area), Ground Attack (bombers/attackers hit ground targets), Escort (fighters protect bombers), and Free Hunt (player-directed objectives with ambient AI activity).

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - Section 5: Tickrate Optimization — session sizing, AI cap, wave management all apply at the scenario level
> - Section 6.2: Future Modules — Intercept, Scramble, Bomber Escort, Ground Attack behavioral descriptions
> - [EC-004] HIGH — Aggregate AI cap across ALL modules selected by the scenario template; the template must calculate the combined AI load before assembly
> - [EL-001] CRITICAL — wave_count per module must be validated against session_duration / ToS; the scenario template sets these parameters
> - [EC-001] MEDIUM — Initialization delay scaled to total entity count; complex scenarios with many modules need higher delays
> - [PI-004] MEDIUM — Each module in the scenario receives a unique spatial offset; the scenario engine must not place two modules in the same remote zone
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Task 5.1 outputs: `MissionBuilder` class
- Task 5.2 outputs: player spawn management (airfield selection, plane sets)
- Phase 4.2 outputs: airfield database
- Phase 4.3 outputs: front-line reference data
- Phase 4.4 outputs: route generation utility
- Phase 3 outputs: compiled module types (Intercept, Patrol, Ground Attack, Escort from tasks 3.1–3.4)

### Requirements

**R1 — Scenario Template Interface**

```python
class ScenarioTemplate(ABC):
    @abstractmethod
    def generate(self, params: ScenarioParams) -> MissionConfig:
        """Translate high-level params into a MissionConfig for the builder."""
        ...

class ScenarioParams:
    map_name: str
    scenario_type: str  # 'intercept', 'patrol', 'ground_attack', 'escort', 'free_hunt'
    difficulty: str     # 'easy', 'medium', 'hard'
    time_of_day: str
    weather: str
    session_duration_minutes: int  # default 180
    front_line_variant: str | None
```

**R2 — Intercept Template**

Generate an intercept scenario:
- Allied attacker flight(s) approaching a target beyond the front line
- Axis defender flight(s) scrambling or patrolling to intercept
- Engagement area calculated near the front line
- Waypoints: attackers route from rear airfield → front line → target; defenders route from airfield → patrol area overlapping the attack vector
- Difficulty scales: number of flights, AI skill level, flight sizes, wave counts

**R3 — Patrol Template**

Generate a patrol scenario:
- One or both coalitions patrol a defined sector
- Patrol waypoints form a loop (or racetrack) pattern over the engagement area
- Opposing flights enter the patrol zone on timed intervals
- Difficulty scales: opposition density, patrol area size, encounter frequency

**R4 — Ground Attack Template**

Generate a ground attack scenario:
- Attacker flight(s) with ground-attack waypoints to a target area
- Defender fighter flight(s) protecting the target zone
- Ground targets generated at the target area (vehicle columns, artillery positions, or airfield objects)
- Difficulty scales: AAA density, fighter cover intensity, target hardness

**R5 — Escort Template**

Generate a bomber escort scenario:
- Bomber flight(s) with a straight-line or shallow-arc route to the target
- Escort fighter flight(s) using the Bomber Escort module (Phase 3.4) — Cover/Attack toggle, proximity tethering
- Opposing interceptor flight(s) attacking the bomber formation
- Difficulty scales: interceptor wave count, bomber survivability, escort AI skill

**R6 — Free Hunt Template**

Generate a free hunt scenario:
- Player-oriented: minimal scripted AI, maximum ambient activity
- Multiple patrol and ground-attack modules scattered across the map
- Player chooses their own objectives from the briefing
- High replayability through randomized module placement within the map's engagement zones

**R7 — Coordinate Calculation**

For each template, calculate all coordinates from the map database and front-line data:
- Airfield selection: choose airfields by coalition side relative to the front line
- Engagement area: calculated at a configurable offset from the front line
- Waypoint chains: generated by the Phase 4.4 route utility — airfield → climb → cruise → engagement → RTB → landing approach
- All coordinates validated against map boundaries

**R8 — Pre-Assembly Validation**

Before passing the assembled module configuration to `MissionBuilder.build()`:
- Calculate aggregate AI load (EC-004): `sum(flight_size × max_simultaneous_waves)` across all modules
- Validate wave_count per module against session duration (EL-001): `wave_count >= ceil(session_duration / ToS)`
- Scale initialization delay based on total entity count (EC-001)
- Verify no spatial offset collisions (PI-004)

> **[EC-004] — HIGH** The scenario template is the first point where aggregate AI load is known. Individual modules are configured in isolation — only the template knows how many modules will be active simultaneously. The template MUST calculate the combined AI count and refuse to assemble if it exceeds 80 without explicit user override.

> **[EL-001] — CRITICAL** The scenario template sets each module's wave_count and session_duration. If the template configures a 180-minute session with a 15-minute ToS but only 8 waves, the Magazine Array exhausts at 120 minutes and the sky goes empty. The template must validate: `wave_count >= ceil(180 / 15) = 12`.

> **EXIT CONDITION — Acceptance Criteria**
> - Select "Intercept on Stalingrad" → complete flyable .Mission generated with correct AI behavior
> - All five scenario templates produce valid .Mission files that load in DServer
> - Waypoint coordinates are tactically plausible: flights route from airfields through the engagement area and return
> - Aggregate AI cap is calculated and warning is emitted when the total exceeds 80
> - wave_count is validated against session_duration / ToS for every module in the scenario
> - Initialization delay scales with entity count (≥5s when >200 entities)
> - No spatial offset collisions between modules in the generated mission
> - Difficulty scaling produces measurably different missions: easy has fewer flights, hard has more

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

## Session 5.4 — Ambient AI

| | |
|---|---|
| **Task ID** | 5.4 |
| **Component** | Orchestrator (`src/backend/orchestrator/scenario_engine.py`) |
| **Model Tier** | Tier 2 |
| **Assigned Model** | Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 5.3 (scenario templates — ambient AI is layered on top of the scenario's core modules) |
| **Delivers To** | 5.5 (GUI exposes ambient AI density controls), 5.5h (in-game test includes ambient AI) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/orchestrator/` |

### Role

You are a Senior Python Developer implementing the ambient AI layer for the Mission Orchestrator. Ambient AI creates the illusion of a living battlefield by populating the mission with non-combat or low-priority AI activity: transport aircraft, supply convoys, artillery barrages, and rear-area logistics. These are lightweight modules that consume minimal AI slots but add substantial atmosphere.

### Context

A mission with only the core scenario modules (Intercept, Patrol, etc.) feels sterile — the sky is empty except for the scripted engagement. Ambient AI fills the gaps: a transport flight crossing the map at high altitude, a truck convoy moving along a road behind the front line, an artillery barrage firing periodically near the engagement zone. These are not player objectives — they are environmental set dressing that makes the world feel populated.

The critical constraint is AI slot consumption. Ambient AI modules must fit within the remaining AI cap budget after the core scenario modules are allocated. The scenario engine (5.3) calculates the core AI load; the ambient AI layer fills the remaining capacity without exceeding the ~80-unit warning threshold.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EC-004] HIGH — Ambient AI modules are added AFTER core scenario modules. The ambient layer receives a remaining AI budget = 80 - core_ai_load. Ambient modules must not exceed this budget.
> - [EC-001] MEDIUM — Additional ambient modules increase the total Enabled=FALSE entity count, potentially requiring a higher initialization delay.
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Task 5.3 outputs: scenario templates with core module configurations and calculated AI load
- Phase 3 outputs: module types that can be configured as ambient (Static CAP for transport flights, Ground Attack for artillery)
- Phase 4 outputs: road networks, rear-area coordinates for convoy routes

### Requirements

**R1 — Ambient Module Types**

Implement lightweight ambient AI modules:
- **Transport flight:** single aircraft or small formation on a straight-line route across the map at high altitude; no combat engagement; Magazine Array with long ToS
- **Supply convoy:** ground vehicle column following road waypoints; low priority; despawns after reaching destination
- **Artillery barrage:** periodic artillery fire near the front line; uses ground-attack MCU patterns without aircraft
- **Rear-area patrol:** low-skill fighter patrol behind friendly lines; does not cross the front; provides background activity for players in the rear

**R2 — AI Budget Allocation**

```python
def allocate_ambient(core_ai_load: int, ambient_modules: list[AmbientConfig]) -> list[AmbientConfig]:
    remaining_budget = 80 - core_ai_load
    allocated = []
    for module in ambient_modules:
        if module.max_concurrent_ai <= remaining_budget:
            allocated.append(module)
            remaining_budget -= module.max_concurrent_ai
    return allocated
```

Ambient modules are added greedily by priority until the budget is exhausted. The function returns only the modules that fit.

**R3 — Ambient Density Control**

Expose a density parameter (`none`, `low`, `medium`, `high`) that scales the number and variety of ambient modules:
- `none`: no ambient AI — core scenario only
- `low`: 1–2 transport flights, 1 convoy
- `medium`: 2–3 transports, 2 convoys, 1 artillery
- `high`: maximum ambient fill within AI budget

**R4 — Integration with Scenario Engine**

Ambient AI is layered on top of the scenario template's output. The integration sequence is:
1. Scenario template generates core module config (5.3)
2. Ambient layer calculates remaining AI budget
3. Ambient modules allocated and configured with coordinates from the map database
4. Combined module list passed to `MissionBuilder` (5.1)

> **EXIT CONDITION — Acceptance Criteria**
> - Ambient AI visible in-game: transport flights cross the map, convoys move along roads
> - Total AI count (core + ambient) does not exceed 80-unit warning threshold
> - Ambient density `none` produces zero ambient modules
> - Ambient density `high` fills remaining AI budget without exceeding cap
> - Ambient modules use the shared IDGenerator and spatial offset engine — no collisions with core modules
> - Unit tests: with a core AI load of 60, ambient layer allocates at most 20 units of ambient AI

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

## Session 5.5 — Orchestrator GUI

| | |
|---|---|
| **Task ID** | 5.5 |
| **Component** | Orchestrator GUI (`src/ui/gui/`) |
| **Model Tier** | Tier 2 |
| **Assigned Model** | Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 5.3 (scenario engine — GUI drives the template system), 2.3 (PyQt6 GUI framework from Phase 2) |
| **Delivers To** | 5.5h (in-game test — missions generated via GUI), 5.6 (DServer rotation — batch mode shares the same generation pipeline) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/ui/gui/`, Phase Mapping |

### Role

You are a Senior Python Developer building the PyQt6 user interface for the Mission Orchestrator. The GUI is the primary user-facing entry point for mission generation — it must translate high-level user choices into the `ScenarioParams` that drive the scenario engine (5.3). The design target: a user generates a complete, flyable .Mission file in under 30 seconds.

### Context

The Orchestrator GUI is the top of the three-layer architecture. It sits above the scenario engine (5.3), which sits above the mission builder (5.1), which sits above the compiler (Phase 1). The GUI collects user inputs, passes them to the scenario engine, and presents the result — a .Mission file written to disk with a confirmation of the scenario's key parameters.

The Phase 2 GUI framework (task 2.3) established the PyQt6 application structure, main window, and widget patterns. The Orchestrator GUI extends this framework with a new panel or workflow specifically for mission generation.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 1: Project Objective — UI-driven generation tool
> - [EC-004] HIGH — GUI SHALL calculate and display max_concurrent_AI, warn if >80
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Task 5.3 outputs: scenario engine and all five scenario templates
- Task 5.4 outputs: ambient AI density control
- Phase 2.3 outputs: PyQt6 application framework and widget patterns
- Phase 4 outputs: map database (for map selector population)

### Requirements

**R1 — Map Selector**

Dropdown or list widget populated from the map database. Display map name and theater/front. Only maps with validated airfield data are selectable.

**R2 — Scenario Configuration Panel**

- Scenario type selector: Intercept, Patrol, Ground Attack, Escort, Free Hunt
- Difficulty slider or dropdown: Easy, Medium, Hard
- Session duration: dropdown (60, 90, 120, 180 minutes, default 180)
- Time of day: dropdown (Dawn, Morning, Noon, Afternoon, Dusk, Night)
- Weather: dropdown (Clear, Light Cloud, Overcast, Rain, Snow — filtered by map and season)
- Ambient AI density: None, Low, Medium, High

**R3 — AI Load Display**

Real-time calculation as the user changes parameters:
- Display: "Estimated AI load: XX / 80"
- Color-coded: green (≤60), yellow (61–80), red (>80)
- Updates when scenario type, difficulty, or ambient density changes
- Warning dialog if user clicks Generate with AI load >80

**R4 — Generate Button**

Single "Generate Mission" button that:
1. Constructs `ScenarioParams` from the GUI state
2. Calls the scenario engine's `generate()` method
3. Writes the .Mission file to a user-specified output path
4. Displays a summary: scenario type, map, module count, AI load, file path
5. Total generation time target: under 30 seconds

**R5 — Error Handling**

- Map database missing or empty: disable Generate, show diagnostic
- AI cap exceeded: warning dialog with option to proceed or reduce difficulty
- Compilation error: display the compiler's diagnostic message (PI-001, EL-003, etc.)
- File write error: display path and permission diagnostic

> **EXIT CONDITION — Acceptance Criteria**
> - User generates a complete .Mission file in under 30 seconds via the GUI
> - Map selector shows all maps with validated airfield data
> - Scenario type, difficulty, weather, time, and ambient density controls are functional
> - AI load display updates in real time as parameters change
> - Warning dialog appears when AI load exceeds 80
> - Generated .Mission file loads in DServer and is flyable (verified in 5.5h)
> - Error states display actionable diagnostics — no silent failures

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

## Human Gate 5.5h — In-Game Flight Test

| | |
|---|---|
| **Gate ID** | 5.5h |
| **Depends On** | 5.5 — Orchestrator GUI generating complete .Mission files |
| **Actor** | Project Owner |
| **Blocks** | 5.6 cannot begin until generated missions are confirmed flyable across maps and scenario types |

### Required Actions

- Use the Orchestrator GUI to generate 5+ missions:
  - At least 2 different maps
  - At least 3 different scenario types
  - At least 1 mission with ambient AI enabled (medium or high)
  - At least 1 mission with difficulty set to Hard
- Load each mission on DServer (MP) or single-player
- Fly or observe each mission for at least 15 minutes

### Verification Checklist

- **Mission loads:** all 5+ generated missions load without DServer errors
- **Player spawns:** player can select coalition, plane, and spawn at the correct airfield on every mission
- **AI behavior:** AI flights follow scenario-appropriate behavior (intercept engages, patrol loops, ground attack hits targets)
- **Wave cycling:** Magazine Array activates subsequent waves after GC — no stalls
- **Ambient AI:** transport flights and convoys visible when ambient density is enabled
- **Difficulty scaling:** Hard missions have noticeably more AI activity than Easy missions
- **AI cap:** no DServer tickrate degradation or lag spikes during peak AI activity
- **Briefing text:** mission briefing displays correctly with scenario description, objectives, and weather summary
- **15-minute stability:** no crashes, logic stalls, or runaway AI counts during the observation period

### Report Requirements

Document the test results per mission. For each: map name, scenario type, difficulty, ambient density, and per-item PASS/FAIL/NOT OBSERVED. If any mission fails to load or exhibits incorrect AI behavior, return to the relevant session (5.1–5.4) with the failure evidence before proceeding to 5.6.

---

## Session 5.6 — DServer Rotation

| | |
|---|---|
| **Task ID** | 5.6 |
| **Component** | Orchestrator (`src/backend/orchestrator/dserver_interface.py`) |
| **Model Tier** | Tier 2 |
| **Assigned Model** | Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 5.5 (GUI — the rotation system uses the same generation pipeline) |
| **Delivers To** | 5.6h (DServer stability test), 5.7 (inter-mission state feedback reads DServer logs) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/orchestrator/`, IL-2 DServer SDS configuration reference |

### Role

You are a Senior Python Developer implementing DServer mission rotation for the IL-2 Mission Orchestrator. The rotation system automates the continuous generation and cycling of missions on a multiplayer DServer — the operational target for the entire MMF project. A well-implemented rotation means a server operator sets parameters once, and the DServer cycles through freshly generated missions indefinitely.

### Context

The IL-2 DServer uses an SDS (Server Data Settings) configuration file to define its mission rotation. The SDS file lists .Mission files in sequence; the DServer loads and runs each one, advancing to the next when the current mission ends (time limit, objective completion, or admin command). The rotation system must: generate a batch of N missions with varied scenarios, write them to the DServer's mission directory, update the SDS configuration to reference them, and optionally schedule regeneration to keep the rotation fresh.

The key risk is mission transition stability. When the DServer loads a new mission, all connected clients experience a loading screen. If the new .Mission file has a parse error, the DServer crashes — disconnecting all players. The rotation system must validate every generated mission before adding it to the SDS rotation.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EL-001] CRITICAL — Each mission in the rotation is a fresh Magazine Array; counters are NOT reused across rotation cycles (single-use sequential dispenser)
> - [EC-004] HIGH — Each mission independently enforces the AI cap; rotation does not accumulate AI across missions
> - Section 5: Tickrate Optimization — each mission in the rotation targets 180 minutes of stable DServer performance
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Task 5.5 outputs: Orchestrator GUI and the underlying generation pipeline
- IL-2 DServer SDS configuration format documentation
- DServer mission directory path (configurable)

### Requirements

**R1 — Batch Generation**

```python
class RotationGenerator:
    def generate_batch(self, count: int, params: RotationParams) -> list[Path]:
        """Generate N missions with varied scenarios. Returns file paths."""
        ...
```

Generate a batch of missions with configurable variety:
- Rotate through scenario types (or weight by preference)
- Vary maps (if multiple maps configured)
- Randomize difficulty within a configured range
- Vary weather and time of day across the batch

**R2 — SDS Configuration Update**

Read the existing SDS file, update the mission rotation list with the newly generated .Mission file paths, and write the updated SDS. Preserve all non-rotation SDS settings (server name, port, password, max players, etc.).

**R3 — Pre-Rotation Validation**

Before adding any mission to the SDS rotation:
- Parse the generated .Mission file with the IL-2 parser to verify structural validity
- Verify all required mission-level blocks are present (Options, MissionBegin, Countries, at least one airfield)
- Log a diagnostic for any mission that fails validation — exclude it from the rotation rather than crashing the DServer

**R4 — Rotation Scheduling**

Support two modes:
- **Static batch:** generate N missions once, write SDS, done. Server operator restarts DServer manually.
- **Live regeneration:** after each mission cycle completes, generate the next mission and append to the SDS. Requires monitoring the DServer log for mission-end events.

**R5 — CLI Interface**

```bash
mmf-rotate --maps stalingrad,kuban --count 10 --difficulty medium --output /path/to/dserver/missions/
mmf-rotate --live --maps stalingrad --difficulty random --sds /path/to/SDS.txt
```

> **[EL-001] — CRITICAL** Each mission in the rotation is an independent compilation session. Magazine Array counters are single-use and do not carry over between missions. The rotation system must NOT attempt to share or persist counter state across missions — each generation starts fresh.

> **EXIT CONDITION — Acceptance Criteria**
> - 10 missions generated in batch mode, all structurally valid
> - SDS configuration updated with correct .Mission file paths; DServer loads the rotation
> - DServer cycles through missions automatically — transitions are seamless
> - Pre-rotation validation catches and excludes any structurally invalid mission
> - CLI interface: `mmf-rotate --count 10` produces 10 varied missions in the output directory
> - Unit tests: batch of 5 missions, verify all load in DServer, verify SDS file is well-formed

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

## Human Gate 5.6h — DServer Rotation Stability Test

| | |
|---|---|
| **Gate ID** | 5.6h |
| **Depends On** | 5.6 — rotation system generating batched missions and updating SDS |
| **Actor** | Project Owner |
| **Blocks** | 5.7 cannot begin until rotation stability is confirmed |

### Required Actions

- Generate a rotation batch of at least 5 missions using the CLI or GUI
- Load the SDS configuration on a DServer instance
- Run the DServer for 3+ hours with at least 2 full mission rotations
- Monitor: DServer console log, SPS (ticks per second), mission transitions, client connections

### Verification Checklist

- **3+ hour runtime:** DServer runs for at least 3 hours without crash
- **Mission transitions:** server transitions between missions cleanly — no loading failures, no client disconnects during transition
- **AI cap compliance:** no sustained SPS drops below 50% during any mission in the rotation
- **AI slot cleanup:** AI count returns to zero between missions — no AI leaks across transitions
- **Player experience:** connected players experience smooth mission cycling — briefing screens display correctly, spawns work on each new mission
- **Variety:** missions in the rotation are visibly different (different scenarios, weather, time of day)
- **Log stability:** DServer log contains no error-level entries related to mission loading or MCU resolution

### Report Requirements

Document: total runtime, number of mission transitions observed, SPS range (min/max), any error log entries, and per-checklist-item PASS/FAIL/NOT OBSERVED. If the DServer crashes or exhibits AI leaks across transitions, return to 5.6 (rotation) or 5.1 (assembly) with the failure evidence. AI leaks across mission transitions indicate that the rotation system is not generating independent missions — each mission must be a clean, standalone compilation session (EL-001).

---

## Session 5.7 — Inter-Mission State Feedback

| | |
|---|---|
| **Task ID** | 5.7 |
| **Component** | Orchestrator (`src/backend/orchestrator/dserver_interface.py`) |
| **Model Tier** | Tier 1 |
| **Assigned Model** | Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 5.6 (DServer rotation — feedback requires a running rotation to read logs from) |
| **Delivers To** | Phase 6 (distribution — state feedback is the capstone feature of the Orchestrator) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/orchestrator/`, DServer log format |

### Role

You are a Principal Python Systems Developer implementing the adaptive mission generation system. Inter-mission state feedback closes the loop between mission outcomes and the next mission's generation parameters — a DServer that responds to what happened in the previous mission. This requires parsing DServer log output, extracting mission results, and feeding those results into the scenario engine as parameter modifiers for the next generation cycle.

### Context

Without state feedback, the DServer rotation is static: each mission is generated independently with no knowledge of what happened before. State feedback transforms the rotation into a dynamic campaign: if the Axis side dominated the previous mission (more kills, objectives completed), the next mission generates with stronger Allied opposition — more interceptor waves, higher AI skill, additional ambient patrols. If a side is consistently losing, the engine tilts the balance toward equilibrium to keep the server competitive.

The DServer writes detailed logs during mission execution: kill events, objective completion, player connections/disconnections, mission timer events. The feedback system parses these logs after each mission completes, extracts aggregate statistics, and passes them to the scenario engine as difficulty modifiers for the next generation.

This is Tier 1 because the feedback loop introduces state across missions — a domain where subtle logic errors (double-counting kills, misattributing coalition results, applying feedback in the wrong direction) produce cascading balance errors that are difficult to diagnose. The feedback system must be deterministic: given the same log input, it produces the same parameter modifications every time.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - [EL-001] CRITICAL — Each mission is a fresh compilation session. State feedback modifies PARAMETERS, not compiled state. Magazine Arrays, counters, and GC chains are regenerated from scratch — feedback adjusts wave_count, flight_size, and AI_skill, not internal MCU state.
> - [EC-004] HIGH — Feedback-driven parameter increases (more waves, larger flights) must still respect the AI cap. The feedback system must recalculate the aggregate AI load after applying modifiers and cap any increases that would breach the threshold.
> - Section 5: Tickrate Optimization — feedback must not cause the AI load to drift upward over multiple cycles; a balancing mechanism is required.
>
> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.

### Inputs

- Task 5.6 outputs: DServer rotation system with log monitoring capability
- DServer log format: text-based event log with timestamps, event types, and entity references
- Task 5.3 outputs: scenario engine accepting `ScenarioParams` with difficulty modifiers

### Requirements

**R1 — Log Parser**

Parse the DServer log for a completed mission and extract:
- Kill events: which coalition killed which, aircraft types, timestamps
- Objective completions: which coalition completed scenario objectives
- Player statistics: connection time, kills, deaths per player per coalition
- Mission duration: actual time vs. configured session duration
- Wave activity: how many waves activated, how many were garbage collected cleanly

**R2 — Result Aggregation**

From the parsed log, compute:
- Coalition kill ratio (Axis kills / Allied kills)
- Objective completion rate per coalition
- Average wave lifetime (time from activation to GC)
- AI cap utilization peak (if extractable from SPS data)

**R3 — Feedback Parameter Modifiers**

Translate aggregated results into parameter modifiers for the next mission:

```python
class FeedbackModifiers:
    axis_difficulty_delta: float   # +0.1 = harder for Axis, -0.1 = easier
    allied_difficulty_delta: float
    wave_count_modifier: int       # +2 = more waves for the disadvantaged side
    ai_skill_modifier: int         # +1 skill level for the disadvantaged side
    ambient_density_modifier: int  # increase ambient AI for the winning side's territory
```

Rules:
- Dominant coalition gets harder opposition in the next mission
- Dominated coalition gets easier opposition (fewer enemy waves, lower enemy AI skill)
- Modifiers are capped: no single feedback cycle changes difficulty by more than one step
- Modifiers decay: if no log data is available, revert to neutral parameters

**R4 — AI Cap Guard**

After applying feedback modifiers, recalculate the aggregate AI load:

```python
modified_ai_load = calculate_aggregate_ai(modified_params)
if modified_ai_load > 80:
    scale_back_modifiers(modified_params, target=80)
```

Feedback-driven increases must not breach the AI cap. If the feedback would push the AI load above 80, scale back the modifiers proportionally until the cap is satisfied.

**R5 — Determinism**

Given the same log input, the feedback system must produce identical modifiers every time. No random number generation in the feedback path. Randomness belongs in the scenario engine's template selection — not in the feedback-driven parameter modifications.

**R6 — Integration with Rotation**

In live regeneration mode (5.6 R4):
1. Mission completes → DServer writes log
2. Feedback system parses log → computes modifiers
3. Modifiers passed to scenario engine → next mission generated with adjusted parameters
4. New mission added to SDS rotation → DServer loads it

> **[EL-001] — CRITICAL** State feedback modifies generation PARAMETERS, not compiled state. Each mission is a clean compilation session. The feedback system does not carry over Magazine Array counters, Entity bindings, or GC chain state between missions. It adjusts `wave_count`, `flight_size`, `ai_skill`, and `difficulty` — all of which are inputs to the scenario template, not artifacts of compilation.

> **[EC-004] — HIGH** Feedback-driven difficulty increases (more waves, larger flights for the losing side's opposition) can push the aggregate AI load above the 80-unit threshold. The feedback system MUST recalculate and enforce the AI cap after applying modifiers. Uncapped feedback creates a positive feedback loop: one side dominates → opposition increases → AI cap exceeded → DServer degrades → both sides lose.

> **EXIT CONDITION — Acceptance Criteria**
> - Post-Axis win: next mission has measurably stronger Allied intercepts (more waves or higher AI skill)
> - Post-Allied win: next mission has measurably stronger Axis presence
> - Progression is measurable: difficulty modifiers extracted from two consecutive missions show the feedback effect
> - Feedback modifiers are deterministic: same log input → same modifiers (tested with a fixed log file)
> - AI cap is enforced after feedback: a log indicating maximum Axis dominance does not produce a mission with >80 AI units
> - Modifiers decay to neutral when no log data is available
> - Unit tests: mock DServer log → parse → aggregate → compute modifiers → verify modifier values and AI cap compliance
> - Integration test: run 3 consecutive missions with feedback, verify difficulty trend matches outcome trend

### Ground Rule Compliance

- **Issue Binding:** This task is bound to Issue #[TBD].
- **Decision Logging:** Update `CODE_DECISION_LOG.md` with any structural code decisions made during this session.
- **State Sync:** Move Kanban card from Ready → In Progress at start; In Progress → In Review at completion.

---

## Recommended Execution Sequence

```
5.1 (Assembly Engine)         ← Start here; depends on Phase 1 + Phase 4
    ↓
5.2 (Player Spawns)           ← Extends assembly engine
    ↓
5.2h (HUMAN: DServer MP Test) ← Gate: basic mission must load and support MP
    ↓
5.3 (Scenario Templates)     ← Core value: high-level params → flyable mission
    ↓
    ├── 5.4 (Ambient AI)      ← Can run in parallel with 5.5
    │
    └── 5.5 (Orchestrator GUI) ← Can run in parallel with 5.4
         ↓
         5.5h (HUMAN: In-Game Flight Test) ← Gate: 5+ missions across maps/scenarios
         ↓
         5.6 (DServer Rotation)
         ↓
         5.6h (HUMAN: DServer Stability Test) ← Gate: 3+ hours stable rotation
         ↓
         5.7 (Inter-Mission Feedback) ← Capstone: adaptive campaign
```

Tasks 5.4 and 5.5 can run in parallel — they have no interdependency. All other tasks are strictly sequential. The three human gates are positioned at integration boundaries: after basic MP functionality (5.2h), after full mission generation (5.5h), and after automated rotation (5.6h). Each gate catches integration errors before they propagate to the next complexity layer.
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

