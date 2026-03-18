# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 3 — Additional Module Types
### Session Prompt Headers
*3+ validated module types proving compositional architecture*

**4 AI Sessions | 5 Human Gates | Task IDs 3.1 – 3.5**

---

## Phase 3 Overview

Phase 3 expands the compiler beyond the Static CAP prototype. Four additional module types are implemented, each exercising the Phase 1 compiler primitives in a distinct behavioral pattern. The Intercept and Ground Attack modules reuse existing primitives without modification. The Scramble and Bomber Escort modules introduce new compiler primitives — `emit_takeoff_sequence()` and `emit_cover_attack_toggle()` respectively — requiring cross-constraint reasoning across the full FMEA set.

All Phase 1 FMEA constraints remain active for every module. Constraints with CRITICAL or HIGH severity are called out in each session where their violation risk is elevated by the module's behavioral pattern.

Tasks 3.1 and 3.3 are Tier 2 (Sonnet 4.6) — they compose existing primitives with well-defined specifications. Tasks 3.2 and 3.4 are Tier 1 (Opus 4.6) — they introduce new primitives and require cross-constraint reasoning. Each module also requires a corresponding GUI parameter form in `src/ui/gui/` to expose its configuration through the PyQt6 interface.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 3.1 | Intercept module: non-looping waypoints, AttackArea, Magazine Array, GC | Compiler + GUI | AI | Tier 2: Sonnet 4.6 |
| 3.1h | IN-GAME TEST: Fly intercept module — verify AI intercept, engagement, RTB, GC | Testing | HUMAN | N/A |
| 3.2 | Scramble module: takeoff sequence, ComplexTrigger altitude gate, then intercept | Compiler + GUI | AI | Tier 1: Opus 4.6 |
| 3.2h | IN-GAME TEST: Fly scramble module — verify taxi, takeoff, altitude gate, intercept transition | Testing | HUMAN | N/A |
| 3.3 | Ground Attack module: waypoint chain to target, AttackArea (ground), [OUT]\_Success on destruction | Compiler + GUI | AI | Tier 2: Sonnet 4.6 |
| 3.3h | IN-GAME TEST: Fly ground attack module — verify ground engagement, destruction detection, [OUT]\_Success | Testing | HUMAN | N/A |
| 3.4 | Bomber Escort module: Cover/Attack toggle, proximity logic, dynamic tethering | Compiler + GUI | AI | Tier 1: Opus 4.6 |
| 3.4h | IN-GAME TEST: Fly bomber escort module — verify Cover/Attack cycling, CheckZone, bomber-lost fallback | Testing | HUMAN | N/A |
| 3.5 | Cross-module integration test: 2+ modules in same .Mission, wire [OUT] to [IN], verify interop | Testing | HUMAN | N/A |

**Dependency order:** 3.1 and 3.3 can start immediately after Phase 2 completes (both depend on 1.10 and 2.5h). 3.2 depends on 3.1 (builds on intercept behavior). 3.4 depends on 3.1 (reuses intercept waypoint chain as baseline). 3.1h follows 3.1. 3.2h follows 3.2. 3.3h follows 3.3. 3.4h follows 3.4. 3.5 requires all AI tasks (3.1–3.4) to be complete and all individual module tests (3.1h, 3.2h, 3.3h, 3.4h) to be passed.

```
Phase 2 (2.5h PASSED)
    ↓
    ├──→ 3.1 (Intercept) ──→ 3.1h ──┬──→ 3.2 (Scramble) ──→ 3.2h ──┐
    │                                 │                                │
    │                                 └──→ 3.4 (Bomber Escort) ──→ 3.4h ──┤
    │                                                                       │
    └──→ 3.3 (Ground Attack) ──→ 3.3h ────────────────────────────────────┤
                                                                            │
                                                                            └──→ 3.5 (Cross-Module Integration)
```

---

## Session 3.1 — Intercept Module

| | |
|---|---|
| **Task ID** | 3.1 |
| **Component** | Compiler (`src/mmf/compiler/modules/intercept.py`) + GUI (`src/ui/gui/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 1.10 (Static CAP composition — all compiler primitives), 2.5h (GUI compilation verified in-game) |
| **Delivers To** | 3.1h (in-game test), 3.2 (Scramble extends intercept behavior), 3.4 (Bomber Escort reuses intercept waypoint chain), 3.5 (cross-module integration) |
| **Reference** | See `ARCHITECTURE.md` — all FMEA Constraints active; Directory Structure → `src/mmf/compiler/modules/`, `data/module_templates/`; MMF Spec Section 6.2 |

### Role

You are a Senior Python Developer composing a new module type from existing compiler primitives. The Intercept module is architecturally identical to the Static CAP except that waypoints do not loop — the flight follows a one-way chain to an engagement area, executes AttackArea, then proceeds to RTB. No new compiler primitives are required.

### Context

The Intercept module validates that the compiler's composition pipeline generalizes beyond the Static CAP. The key structural difference is the non-looping waypoint chain: the flight navigates from a spawn point to a patrol/intercept zone via sequential waypoints, engages targets within an AttackArea, and then enters the GC pipeline (RTB or despawn). This proves that the waypoint emitter, Magazine Array, and GC chains function correctly when the waypoint terminal node routes to the RTB/GC sequence instead of looping back.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All 14 Phase 1 FMEA constraints remain active: PI-001 through PI-004, EL-001 through EL-003, SM-001 through SM-004, EC-001 through EC-004
> - Section 6.2: Future Modules — Intercept is the first non-CAP module type
> - Section 5.2: Magazine Array — wave management applies identically to intercept flights
> - Section 5.3: Garbage Collection — dual-path GC (OnKilled + ToS) applies identically

### Inputs

- Phase 1 outputs: all compiler primitives (`src/mmf/compiler/`)
- Phase 2 outputs: GUI shell and Static CAP parameter form (`src/ui/gui/`)
- `src/mmf/compiler/modules/static_cap.py` — reference composition pattern
- `mmf-module-schema-v2_0.json` — JSON schema (intercept module must validate against this)

### Requirements

**R1 — InterceptCompiler Class**

Implement `src/mmf/compiler/modules/intercept.py` as a module compiler that follows the same pipeline as `StaticCAPCompiler` (task 1.10) with these modifications:

1. Waypoints are non-looping: the terminal waypoint does NOT link back to the first waypoint. Instead, the terminal waypoint's OnWaypoint output routes to the RTB command sequence.
2. The `waypoints.loop` field in the JSON payload MUST be `false`. If `loop = true` is provided, raise `ConfigurationError` — a looping intercept is a Static CAP, not an intercept.
3. AttackArea placement occurs along the waypoint chain (user-specified index or terminal waypoint).

**R2 — JSON Template**

Create `data/module_templates/intercept.json` conforming to the MMF schema with `module_type: "intercept"`. The template must include: `waypoints` (non-looping, 3+ points), `attack` (AttackArea configuration), `magazine` (wave management), `flight` (formation parameters), and `proxy_coordinates`.

**R3 — GUI Parameter Form**

Add an Intercept module parameter form to the GUI (`src/ui/gui/`). The form must:
- Share the flight, magazine, and GC parameter widgets with the Static CAP form (extract common widgets if not already shared)
- Set `waypoints.loop = false` (locked, not user-editable)
- Expose AttackArea position along the waypoint chain
- Update the AI cap display (task 2.6) when parameters change

**R4 — Reuse Verification**

The Intercept module must call the same compiler primitives as the Static CAP — `IDGenerator`, `SpatialAllocator`, `FlightEmitter`, `MagazineArray`, `CommandBuffer`, `GarbageCollector`, `DependencyStubSystem`, `FieldValidator`, `InitBuffer`. No new primitives. If a new primitive appears necessary, stop and document why — this indicates a Phase 1 design gap.

> **[SM-002] — HIGH** RTB commands at ToS expiration must Object Link to every aircraft in the flight, not just the leader. This is especially important for intercept flights because the engagement area may disperse the formation — wingmen may be at significant distance from the leader when RTB fires.

> **[EC-004] — HIGH** The intercept module's Magazine Array must be GC-gated. Time-based wave activation is prohibited. The intercept's non-looping waypoint chain means flights transit the engagement area once — if they survive, RTB fires earlier than a looping CAP, which means GC completes sooner and the next wave activates sooner. Wave pacing is entirely GC-driven.

> **EXIT CONDITION — Acceptance Criteria**
> - Compiled .Group file imports into BOSEditor without errors
> - Waypoints form a non-looping chain (no terminal-to-initial link)
> - Terminal waypoint routes to RTB/GC sequence
> - `ConfigurationError` raised if `waypoints.loop = true`
> - All 14 FMEA constraint acceptance criteria from Phase 1 sessions are satisfied
> - Magazine Array activates next wave only after GC confirmation
> - GUI parameter form renders, exports valid JSON, compiles successfully
> - `data/module_templates/intercept.json` validates against the MMF schema

---

## Human Gate 3.1h — In-Game Test (Intercept Module)

| | |
|---|---|
| **Gate ID** | 3.1h |
| **Depends On** | 3.1 — compiled Intercept .Group file |
| **Actor** | Project Owner |
| **Blocks** | 3.2 (Scramble builds on intercept behavior), 3.4 (Bomber Escort reuses intercept waypoint chain) |

### Required Actions

- Compile an Intercept module via GUI or CLI
- Import the compiled .Group file into BOSEditor
- Link `[IN]_Activate` to an `MCU_TR_MissionBegin` in a test mission
- Configure a 30-minute test session on a DServer or single-player host
- Fly or observe the session for the full 30 minutes

### Verification Checklist

- **AI intercept path:** aircraft follow the non-looping waypoint chain from spawn to engagement area
- **AI engagement:** aircraft attack targets within the AttackArea
- **No waypoint loop:** after reaching the terminal waypoint, aircraft proceed to RTB — they do not return to the first waypoint
- **ToS expiry:** aircraft RTB at the configured time-on-station
- **Despawn:** aircraft are removed from the world after RTB + despawn delay
- **Next-wave activation:** second wave activates after first wave's GC confirms
- **Leader-kill path:** kill the leader mid-sortie — wingmen despawn within 30s, next wave activates
- **No AI slot leak:** slot count returns to baseline after each wave despawns
- **30-minute session stable:** no DServer crash, no logic stall, no runaway AI count

### Report Requirements

Document the test results before proceeding to tasks 3.2 or 3.4. For each verification item: PASS, FAIL, or NOT OBSERVED. If any item is FAIL, return to session 3.1 with the failure evidence. If a failure traces to a Phase 1 primitive, return to the relevant Phase 1 session.

---

## Session 3.2 — Scramble Module

| | |
|---|---|
| **Task ID** | 3.2 |
| **Component** | Compiler (`src/mmf/compiler/modules/scramble.py`, `src/mmf/compiler/takeoff_sequence.py`) + GUI (`src/ui/gui/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 3.1 (Intercept module — Scramble extends intercept behavior with a pre-flight takeoff sequence) |
| **Delivers To** | 3.2h (in-game test), 3.5 (cross-module integration) |
| **Reference** | See `ARCHITECTURE.md` — all FMEA Constraints active; Directory Structure → `src/mmf/compiler/`; MMF Spec Section 6.2 (Scramble description); IL-2 Manual: ComplexTrigger (pg. 286-287) |

### Role

You are a Principal Python Systems Developer. You are implementing the Scramble module, which introduces the first new compiler primitive since Phase 1: `emit_takeoff_sequence()`. The Scramble module transitions AI from a parked state through taxi, takeoff, and an altitude gate before entering intercept behavior. The altitude gate uses an `MCU_TR_ComplexTrigger` — a stateful IL-2 trigger type that requires careful construction to avoid silent failures.

### Context

The Scramble module is architecturally the most complex module type introduced in Phase 3. It composes three distinct phases of flight:

1. **Ground phase:** Aircraft start parked at an airfield. The activation trigger initiates taxi and takeoff.
2. **Transition gate:** An `MCU_TR_ComplexTrigger` validates that the aircraft has reached a minimum altitude (e.g., 500m AGL) before unlocking the airborne phase. This prevents the intercept logic from firing while aircraft are still on the runway.
3. **Airborne phase:** Once the altitude gate fires, the flight executes the intercept waypoint chain, AttackArea engagement, and GC sequence identically to task 3.1.

The `MCU_TR_ComplexTrigger` is the critical new element. It evaluates a compound boolean condition (object altitude > threshold AND object speed > threshold) and fires its output only when all conditions are simultaneously met. The trigger must be Object Linked to the flight leader. If the leader is killed during takeoff, the ComplexTrigger never fires and the airborne phase never activates — this must route to the GC chain to prevent permanent AI slot consumption.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All 14 Phase 1 FMEA constraints remain active
> - Section 6.2: "Scramble: Transitions from parked to airborne combat. Gated by an MCU_TR_ComplexTrigger at the runway boundary validating the OnEntered altitude state before unlocking airborne intercept logic."
> - [SM-001] HIGH — The scramble-to-intercept state transition introduces a second `[IN]` path. The Command Buffer serialization delay must stagger the ground-phase and airborne-phase activation to prevent simultaneous command issuance.
> - [EL-002] HIGH — Entity proxy binding is at elevated risk during mass takeoff events. Aircraft transition from parked (static 3D object) to airborne (dynamic physics object). The 2-second binding delay must account for this transition.
> - [SM-002] HIGH — If the leader is killed during the ground phase (e.g., strafed on the runway), all wingmen must be GC'd. The leader-kill GC chain must be active from the moment of activation, not deferred until the airborne phase.
> - [EC-003] HIGH — Scramble flights MUST use Activate/Deactivate, not Spawn. Formation hierarchy preservation is critical for the taxi/takeoff sequence — wingmen must follow the leader's taxi path.

### Inputs

- Task 3.1 output: Intercept module (the airborne phase is identical)
- All Phase 1 compiler primitives (`src/mmf/compiler/`)
- IL-2 Manual: ComplexTrigger reference (pg. 286-287) — compound boolean conditions
- MCU type catalog (task 0.4) — `MCU_TR_ComplexTrigger` field definitions

### Requirements

**R1 — New Primitive: `emit_takeoff_sequence()`**

Implement `src/mmf/compiler/takeoff_sequence.py`:

```python
class TakeoffSequenceEmitter:
    def __init__(self, id_gen: IDGenerator, spatial: SpatialAllocator)
    def emit(self, flight_config: dict, airfield_config: dict) -> list[MCUBlock]
```

The emitter generates:
1. `MCU_CMD_TakeOff` Object Linked to all aircraft in the flight (not just the leader — per SM-002 pattern)
2. An `MCU_TR_ComplexTrigger` configured with altitude and speed thresholds, Object Linked to the flight leader
3. A timeout timer (configurable, default 120s) that fires if the ComplexTrigger does not fire within the expected takeoff window — routes to GC chain as a stuck-on-ground failsafe
4. The ComplexTrigger output links to the intercept waypoint chain entry point

**R2 — ComplexTrigger Configuration**

The `MCU_TR_ComplexTrigger` must be configured with:
- `ObjectScript` referencing the flight leader aircraft
- Altitude condition: `OnEntered`, minimum altitude from `scramble_config.altitude_gate_meters` (default 500)
- Speed condition: minimum speed from `scramble_config.speed_gate_kph` (default 200)
- The trigger fires ONCE (not continuously). After firing, it is deactivated to prevent re-firing on subsequent altitude crossings.

**R3 — Leader-Kill During Ground Phase**

The leader's `MCU_TR_Entity` OnKilled output must be connected to the GC chain from the moment of flight activation — not deferred until the altitude gate fires. If the leader is killed on the runway:
1. The OnKilled chain triggers GC for all wingmen (ForceComplete → 30s Timer → Despawn, per SM-002)
2. The timeout timer (R1.3) is deactivated
3. The Magazine Array next-wave counter advances

**R4 — Scramble Module Compiler**

Implement `src/mmf/compiler/modules/scramble.py` that orchestrates:
1. All Static CAP / Intercept pipeline steps (validation, ID gen, spatial allocation, Magazine Array, entity binding, GC, stubs, init buffer)
2. Takeoff sequence emission (R1) inserted between Magazine Array activation and the waypoint chain
3. Command Buffer serialization for the ground→airborne transition (SM-001: the altitude gate output routes through a serialization timer before engaging the waypoint chain)

**R5 — JSON Template and GUI Form**

Create `data/module_templates/scramble.json` with additional fields: `scramble_config.altitude_gate_meters`, `scramble_config.speed_gate_kph`, `scramble_config.takeoff_timeout_seconds`, `scramble_config.airfield_id`.

Add a Scramble parameter form to the GUI that includes all intercept parameters plus the scramble-specific configuration. The altitude gate and speed gate fields must have validation ranges (altitude: 100–2000m; speed: 100–500 kph).

> **[SM-001] — HIGH** The scramble→intercept transition is a state change. The altitude gate output MUST route through a Command Buffer serialization timer (50–100ms) before engaging the intercept waypoint chain. Without serialization, a simultaneous TakeOff completion and AttackArea command can race within the same engine tick.

> **[EL-002] — HIGH** During mass scramble activation, multiple flights may be transitioning from parked to airborne simultaneously. The 2-second entity binding delay is critical. Entity proxies that attempt to resolve during the taxi phase — when the aircraft's 3D physics state is transitioning — will bind to nothing permanently.

> **[SM-002] — HIGH** Leader-kill GC must be active from activation, not from altitude gate. A leader strafed on the runway must trigger wingman GC immediately. Deferring OnKilled handling to the airborne phase creates a permanent AI slot leak for any flight whose leader dies on the ground.

> **EXIT CONDITION — Acceptance Criteria**
> - Compiled .Group file imports into BOSEditor without errors
> - Aircraft start parked and execute taxi → takeoff sequence on activation
> - `MCU_TR_ComplexTrigger` fires when leader reaches altitude and speed thresholds
> - Altitude gate triggers transition to intercept waypoint chain
> - Timeout timer fires GC if altitude gate does not fire within the configured window
> - Leader killed on runway: wingmen despawn within 30s, next wave activates
> - Leader killed in flight: standard SM-002 GC chain executes
> - All 14 FMEA constraint acceptance criteria satisfied
> - Command Buffer serialization timer present between altitude gate output and waypoint chain entry
> - GUI form renders scramble-specific parameters with validation ranges
> - `data/module_templates/scramble.json` validates against the MMF schema

---

## Human Gate 3.2h — In-Game Test (Scramble Module)

| | |
|---|---|
| **Gate ID** | 3.2h |
| **Depends On** | 3.2 — compiled Scramble .Group file |
| **Actor** | Project Owner |
| **Blocks** | 3.5 (cross-module integration requires Scramble to be verified) |

### Required Actions

- Compile a Scramble module via GUI or CLI
- Import the compiled .Group file into BOSEditor
- Place the module at an airfield with a valid runway
- Link `[IN]_Activate` to an `MCU_TR_MissionBegin` in a test mission
- Configure a 30-minute test session on a DServer or single-player host
- Observe the full scramble sequence for multiple waves

### Verification Checklist

- **Taxi sequence:** aircraft begin parked, taxi to runway on activation
- **Takeoff:** aircraft execute takeoff and climb
- **Altitude gate:** ComplexTrigger fires at the configured altitude — verify by observing the transition from climb to intercept waypoint navigation
- **No premature intercept:** aircraft do NOT begin navigating the waypoint chain while still below the altitude gate
- **Timeout failsafe:** set an extremely high altitude gate (e.g., 10000m) to test the timeout → GC path
- **Leader-kill on ground:** strafe the leader during taxi — verify wingmen despawn within 30s, next wave activates
- **Leader-kill in flight:** kill the leader after altitude gate — verify standard GC behavior
- **Full scramble-to-intercept flow:** aircraft take off, clear altitude gate, navigate waypoints, engage, RTB, despawn, next wave scrambles
- **Next-wave activation:** second wave activates after first wave's GC confirms
- **No AI slot leak:** slot count returns to baseline after each wave
- **30-minute session stable:** no DServer crash, no logic stall

### Report Requirements

Document the test results before proceeding. For each verification item: PASS, FAIL, or NOT OBSERVED. If any item is FAIL:
- Altitude gate failure → return to session 3.2, R1–R2
- Leader-kill on ground failure → return to session 3.2, R3
- Serialization/state-transition failure → return to session 3.2, R4 (SM-001)
- Phase 1 regression → return to the relevant Phase 1 primitive session

---

## Session 3.3 — Ground Attack Module

| | |
|---|---|
| **Task ID** | 3.3 |
| **Component** | Compiler (`src/mmf/compiler/modules/ground_attack.py`) + GUI (`src/ui/gui/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 1.10 (Static CAP composition — all compiler primitives), 2.5h (GUI compilation verified in-game) |
| **Delivers To** | 3.3h (in-game test), 3.5 (cross-module integration) |
| **Reference** | See `ARCHITECTURE.md` — all FMEA Constraints active; Directory Structure → `src/mmf/compiler/modules/`; MMF Spec Sections 3.1 (PI-001 — AttackArea validation), 5.3 (GC) |

### Role

You are a Senior Python Developer composing a Ground Attack module from existing compiler primitives. The Ground Attack module sends flights along a waypoint chain to a ground target area, executes AttackArea against ground objects, and fires `[OUT]_Success` on target destruction. No new compiler primitives are required.

### Context

The Ground Attack module differs from the Intercept module in two ways: (1) the AttackArea targets ground objects rather than airborne targets, and (2) the module exposes a `[OUT]_Success` output that fires when the specified ground targets are destroyed, enabling downstream module wiring (e.g., triggering a second wave or a mission-complete event). The ground target destruction check uses `MCU_CheckZone` or `MCU_TR_Entity` on the target objects — but per Section 4.2 of the spec, spatial `MCU_TR_CheckZone` polling must be minimized. The preferred approach is to use `MCU_TR_Entity` bindings on the ground target objects to detect their destruction via OnKilled events.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All 14 Phase 1 FMEA constraints remain active
> - [PI-001] CRITICAL — AttackArea Targets array must be non-empty. For ground attack, this array references ground target entities. Compiler must validate that referenced targets exist in the mission context.
> - [SM-002] HIGH — All RTB/Waypoint commands must Object Link to every aircraft in the flight. Ground attack flights may take heavy losses from ground defenses — leader-kill probability is higher than air-to-air intercept modules.
> - [SM-004] LOW — Dual-path GC remains active. OnKilled and ToS both route to Magazine Array advance.
> - [EC-004] HIGH — GC-gated wave activation. Ground attack sorties may be shorter than air patrols (target destroyed → RTB), so wave pacing may be faster. The AI cap must not be exceeded.

### Inputs

- Phase 1 outputs: all compiler primitives (`src/mmf/compiler/`)
- Phase 2 outputs: GUI shell and parameter forms (`src/ui/gui/`)
- `src/mmf/compiler/modules/static_cap.py` and `src/mmf/compiler/modules/intercept.py` — reference composition patterns
- `mmf-module-schema-v2_0.json` — JSON schema

### Requirements

**R1 — GroundAttackCompiler Class**

Implement `src/mmf/compiler/modules/ground_attack.py` following the Intercept pipeline (non-looping waypoints) with these modifications:

1. AttackArea `AttackGround` parameter set to `1` (ground target mode). The AttackArea `Targets` array references ground object Indices rather than airborne targets.
2. `[OUT]_Success` proxy node fires when ground target destruction is confirmed. Target destruction detection uses `MCU_TR_Entity` bound to the ground target object(s) — when OnKilled fires for all specified targets, `[OUT]_Success` activates.
3. If partial destruction semantics are configured (e.g., "3 of 5 targets destroyed"), use an `MCU_Counter` to accumulate OnKilled events and fire `[OUT]_Success` at the threshold.

**R2 — Target Destruction Detection**

For each ground target referenced in the `attack.ground_targets` array:
- Generate an `MCU_TR_Entity` bound to the ground target object (applying EL-003 binding integrity check)
- Route the Entity's OnKilled output to a destruction counter
- The destruction counter fires `[OUT]_Success` when the configured threshold is met

Note: Ground target `MCU_TR_Entity` bindings do NOT require the 2-second EL-002 delay because ground objects are statically instantiated at mission load — they are not dynamically activated like Magazine Array flights.

**R3 — JSON Template and GUI Form**

Create `data/module_templates/ground_attack.json` with additional fields: `attack.ground_targets` (array of target object references), `attack.destruction_threshold` (integer, default = all targets), `attack.attack_ground` (boolean, locked to `true`).

Add a Ground Attack parameter form to the GUI. The form must include a ground target reference list (populated from the mission context when available, or manual ID entry) and the destruction threshold spinner.

**R4 — Reuse Verification**

Same as task 3.1 R4: the Ground Attack module must call existing compiler primitives only. The destruction counter is a standard `MCU_Counter` composed from the existing `MagazineArray` counter pattern — it is not a new primitive.

> **[PI-001] — CRITICAL** The `attack.ground_targets` array must be non-empty at compilation. An AttackArea node targeting ground objects with an empty target list causes the same DServer crash as an air AttackArea with empty Targets. The compiler must abort with a diagnostic error if ground_targets is empty.

> **[SM-002] — HIGH** Ground attack missions have higher leader-kill probability than air-to-air intercept. Flights descending to attack altitude are exposed to ground fire — the leader may be killed before or during the attack run. RTB and GC chains must Object Link to all aircraft in the flight.

> **EXIT CONDITION — Acceptance Criteria**
> - Compiled .Group file imports into BOSEditor without errors
> - AttackArea configured for ground target mode (`AttackGround = 1`)
> - AI navigates waypoints to target area and attacks ground objects
> - `[OUT]_Success` fires when destruction threshold is met
> - `[OUT]_Success` does NOT fire if threshold is not met (partial destruction below threshold)
> - All 14 FMEA constraint acceptance criteria satisfied
> - Ground target `MCU_TR_Entity` bindings pass EL-003 integrity check
> - GUI form renders ground attack parameters, exports valid JSON, compiles successfully
> - `data/module_templates/ground_attack.json` validates against the MMF schema

---

## Human Gate 3.3h — In-Game Test (Ground Attack Module)

| | |
|---|---|
| **Gate ID** | 3.3h |
| **Depends On** | 3.3 — compiled Ground Attack .Group file |
| **Actor** | Project Owner |
| **Blocks** | 3.5 (cross-module integration requires Ground Attack to be verified) |

### Required Actions

- Compile a Ground Attack module via GUI or CLI
- Import the compiled .Group file into BOSEditor
- Place ground target objects (vehicles, buildings, or static objects) at the AttackArea coordinates
- Link `[IN]_Activate` to an `MCU_TR_MissionBegin` in a test mission
- Configure a 30-minute test session on a DServer or single-player host
- Observe the full ground attack sequence for multiple waves

### Verification Checklist

- **Waypoint navigation:** aircraft follow the non-looping waypoint chain to the target area
- **Ground engagement:** aircraft attack ground targets within the AttackArea (`AttackGround = 1`)
- **Target destruction detection:** `[OUT]_Success` fires when the destruction threshold is met
- **Partial destruction:** if threshold is set to 3-of-5, verify `[OUT]_Success` does NOT fire at 2-of-5
- **No false positive:** `[OUT]_Success` does not fire if no targets are destroyed
- **ToS expiry:** aircraft RTB at the configured time-on-station
- **Despawn:** aircraft are removed from the world after RTB + despawn delay
- **Leader-kill path:** kill the leader during the attack run — verify wingmen despawn within 30s, next wave activates
- **Next-wave activation:** second wave activates after first wave's GC confirms
- **No AI slot leak:** slot count returns to baseline after each wave despawns
- **30-minute session stable:** no DServer crash, no logic stall

### Report Requirements

Document the test results before proceeding. For each verification item: PASS, FAIL, or NOT OBSERVED. If any item is FAIL:
- Ground engagement failure → return to session 3.3, R1
- Destruction detection failure → return to session 3.3, R2
- `[OUT]_Success` wiring failure → return to session 3.3, R1 (proxy node wiring)
- Phase 1 regression → return to the relevant Phase 1 primitive session

---

## Session 3.4 — Bomber Escort Module

| | |
|---|---|
| **Task ID** | 3.4 |
| **Component** | Compiler (`src/mmf/compiler/modules/bomber_escort.py`, `src/mmf/compiler/cover_attack_toggle.py`) + GUI (`src/ui/gui/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 3.1 (Intercept module — Bomber Escort reuses the intercept waypoint chain and engagement logic) |
| **Delivers To** | 3.4h (in-game test), 3.5 (cross-module integration) |
| **Reference** | See `ARCHITECTURE.md` — all FMEA Constraints active; Directory Structure → `src/mmf/compiler/`; MMF Spec Section 6.2 (Bomber Escort description), Section 4.2 (CheckZone avoidance) |

### Role

You are a Principal Python Systems Developer. You are implementing the Bomber Escort module, which introduces the second new compiler primitive: `emit_cover_attack_toggle()`. The Escort module dynamically alternates between `Command:Cover` (formation escort) and localized `Command:AttackArea` (threat engagement) based on proximity triggers. This is the most stateful module in the framework — the Cover/Attack toggle is a two-state machine managed through the Command Buffer.

### Context

The Bomber Escort module pairs escort fighters with a bomber formation. The escort's default behavior is `Command:Cover` — fighters maintain formation on the bomber. When a threat enters the engagement zone, the escort transitions to `Command:AttackArea` to engage. After engagement (threat destroyed, threat exits zone, or combat timer expires), the escort returns to `Command:Cover`.

This is architecturally distinct from all prior modules because it introduces a **repeating state transition**: Cover → Attack → Cover → Attack → ... The Command Buffer must serialize each transition, and timer pause semantics (SM-003) are critical — the combat duration timer must be a fresh instance for each engagement, not a recycled timer that carries paused state from a previous cycle.

The proximity trigger presents a design tension with the spec's CheckZone avoidance guidance (Section 4.2). The spec warns that spatial `MCU_TR_CheckZone` polling causes multiplayer desyncs. The Bomber Escort module must use `MCU_TR_CheckZone` for threat detection — there is no alternative for area-based proximity in the IL-2 engine — but must minimize the performance impact by:
1. Using a single CheckZone per escort module (not per-aircraft)
2. Setting the CheckZone radius to the minimum effective value
3. Deactivating the CheckZone during Attack phase (it only needs to poll during Cover phase)

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - All 14 Phase 1 FMEA constraints remain active
> - Section 6.2: "Bomber Escort: Dynamic tethering via Object Links, alternating between Command: Cover and localized Command: Attack parameters based on threat proximity. Note: moving CheckZones should be minimized per Section 4.2 performance guidance."
> - [SM-001] HIGH — The Cover→Attack and Attack→Cover transitions are state changes. Each must route through the Command Buffer with serialization timers. The Cover→Attack transition and the Attack→Cover transition must use distinct serialization delay values (staggered 50ms increments).
> - [SM-003] HIGH — Timer pause semantics are CRITICAL for the combat duration timer. The escort's "attack duration" timer controls how long fighters stay in Attack mode before reverting to Cover. If this timer is recycled across engagements, it carries paused state and fires prematurely. Each engagement MUST use a fresh timer instance.
> - [EL-003] CRITICAL — Entity proxy binding for the escort fighters must pass integrity checks. The escort's MCU_TR_Entity proxies detect OnKilled for the escort fighters themselves (triggering GC) and must be distinct from any Entity proxies on the bomber formation.
> - Section 4.2: CheckZone avoidance — minimize spatial polling. One CheckZone per module maximum. Deactivate during non-polling phases.

### Inputs

- Task 3.1 output: Intercept module (airborne engagement behavior baseline)
- All Phase 1 compiler primitives (`src/mmf/compiler/`)
- IL-2 Manual: Command:Cover (pg. 275-276), MCU_TR_CheckZone (pg. 284-285)
- MCU type catalog (task 0.4) — `MCU_CMD_Cover`, `MCU_TR_CheckZone` field definitions

### Requirements

**R1 — New Primitive: `emit_cover_attack_toggle()`**

Implement `src/mmf/compiler/cover_attack_toggle.py`:

```python
class CoverAttackToggleEmitter:
    def __init__(self, id_gen: IDGenerator, spatial: SpatialAllocator, cmd_buffer: CommandBuffer)
    def emit(self, escort_config: dict, bomber_ref: dict) -> list[MCUBlock]
```

The emitter generates:
1. `MCU_CMD_Cover` Object Linked to all escort aircraft, with the bomber leader as the cover target
2. `MCU_TR_CheckZone` positioned at the bomber's location (or Object Linked to the bomber if the engine supports moving CheckZones — verify from IL-2 manual) with configurable radius
3. `MCU_CMD_AttackArea` for localized threat engagement, Object Linked to all escort aircraft
4. A combat duration timer (fresh instance per engagement — SM-003 compliance) that reverts from Attack to Cover when the timer expires
5. CheckZone OnEntered output → Command Buffer → Deactivate Cover → Attack transition (SM-001 serialized)
6. Combat timer expiry OR threat eliminated → Command Buffer → Deactivate Attack → Cover transition (SM-001 serialized)
7. CheckZone is Deactivated during Attack phase and Reactivated during Cover phase

**R2 — Bomber Reference Binding**

The escort module receives a `bomber_ref` configuration that identifies the bomber formation it is escorting:
- `bomber_ref.leader_index` — the Index of the bomber leader aircraft
- `bomber_ref.module_id` — the MMF module ID of the bomber module (for inter-module wiring)

The `Command:Cover` target is the bomber leader. The CheckZone is placed at the bomber's coordinates. If the bomber is destroyed (bomber module fires `[OUT]_Fail`), the escort transitions to a fallback intercept behavior along the remaining waypoint chain, then enters GC.

**R3 — State Machine Integrity**

The Cover/Attack toggle is a two-state machine:

```
                ┌──────────────────────────────┐
                │                              │
                ▼                              │
    [Cover Phase]  ──(threat enters)──→  [Attack Phase]
         ▲                                     │
         │                                     │
         └──(threat eliminated / timer)────────┘
```

- **Cover → Attack:** CheckZone OnEntered fires → serialize through Command Buffer (SM-001) → Deactivate Cover → Activate Attack → Start combat timer → Deactivate CheckZone
- **Attack → Cover:** Combat timer fires OR all threats eliminated → serialize through Command Buffer (SM-001) → Deactivate Attack → Activate Cover → Reactivate CheckZone → Reset with fresh combat timer for next engagement (SM-003)

Each transition must use a FRESH timer instance (SM-003). Previously used timers must be permanently deactivated.

**R4 — GC Integration**

The escort module's GC chain is identical to the Intercept module (dual-path: OnKilled + ToS), with one addition: if the bomber is destroyed (external `[IN]_BomberLost` signal), the escort transitions to fallback intercept → RTB → GC. This requires a third `[IN]` port with its own Command Buffer serialization delay (SM-001: staggered 50ms beyond the Cover and Attack delays).

**R5 — JSON Template and GUI Form**

Create `data/module_templates/bomber_escort.json` with additional fields: `escort_config.cover_radius_meters` (CheckZone radius, default 3000), `escort_config.combat_duration_seconds` (attack phase timer, default 120), `escort_config.bomber_ref` (reference to the bomber module/leader).

Add a Bomber Escort parameter form to the GUI. The form must include: bomber reference selector (populated from other modules in the session when available), cover radius slider with min/max validation, combat duration timer configuration, and all standard flight/magazine/GC parameters.

> **[SM-001] — HIGH** The Cover/Attack toggle introduces THREE serialized transitions: (1) Cover→Attack at 50ms, (2) Attack→Cover at 100ms, (3) BomberLost→Fallback at 150ms. Each must use a distinct delay value within the Command Buffer. Simultaneous Cover→Attack and BomberLost transitions must resolve deterministically.

> **[SM-003] — HIGH** The combat duration timer is the highest-risk SM-003 violation point in the entire project. The escort may cycle through Cover→Attack→Cover multiple times per sortie. Each cycle MUST engage a fresh timer. A recycled timer from a previous engagement carries paused countdown state — a 120s timer paused at 30s remaining fires after only 30s in the next engagement, causing premature Cover reversion during active combat.

> **[EL-003] — CRITICAL** The escort module generates Entity proxies for the escort fighters. These Entity proxies must have unique bindings that do not collide with Entity proxies for the bomber formation (which is a separate module). The IDGenerator's monotonic counter prevents Index collisions, but the binding integrity check must verify that each Entity's MisObjID references an aircraft within the ESCORT formation, not the bomber formation.

> **EXIT CONDITION — Acceptance Criteria**
> - Compiled .Group file imports into BOSEditor without errors
> - Escort fighters execute Command:Cover on the bomber formation by default
> - CheckZone triggers Cover→Attack transition when a threat enters the engagement radius
> - Escort fighters engage threats within localized AttackArea
> - Combat timer expires: escort reverts to Cover
> - Multiple Cover→Attack→Cover cycles execute without timer corruption (SM-003)
> - Bomber destroyed: escort transitions to fallback intercept → RTB → GC
> - All Command Buffer transitions use distinct serialization delays (SM-001)
> - CheckZone deactivated during Attack phase, reactivated during Cover phase
> - All 14 FMEA constraint acceptance criteria satisfied
> - Entity proxy bindings for escort fighters are distinct from bomber Entity proxies
> - GUI form renders escort parameters including bomber reference selector
> - `data/module_templates/bomber_escort.json` validates against the MMF schema

---

## Human Gate 3.4h — In-Game Test (Bomber Escort Module)

| | |
|---|---|
| **Gate ID** | 3.4h |
| **Depends On** | 3.4 — compiled Bomber Escort .Group file |
| **Actor** | Project Owner |
| **Blocks** | 3.5 (cross-module integration requires Bomber Escort to be verified) |

### Required Actions

- Compile a Bomber Escort module via GUI or CLI
- Compile or hand-build a bomber formation module for the escort to reference
- Import both .Group files into BOSEditor
- Wire the bomber module's `[OUT]_Fail` to the escort module's `[IN]_BomberLost`
- Link `[IN]_Activate` on both modules to an `MCU_TR_MissionBegin` in a test mission
- Configure a 30-minute test session on a DServer or single-player host
- Observe the escort behavior across multiple engagements and wave cycles

### Verification Checklist

- **Cover behavior:** escort fighters maintain formation on the bomber by default (Command:Cover)
- **Threat detection:** CheckZone triggers Cover→Attack transition when an enemy aircraft enters the engagement radius
- **Attack engagement:** escort fighters engage threats within localized AttackArea during Attack phase
- **Attack→Cover reversion:** combat timer expires — escort reverts to Cover and resumes formation on bomber
- **Multiple cycles:** execute 2+ Cover→Attack→Cover transitions — verify no timer corruption (SM-003). Each engagement duration should match the configured combat timer, not fire prematurely.
- **CheckZone management:** CheckZone is deactivated during Attack phase, reactivated during Cover phase (verify by observing that a second threat entering during an active engagement does not trigger a redundant transition)
- **Bomber destroyed:** destroy the bomber mid-flight — verify escort transitions to fallback intercept → RTB → GC
- **Leader-kill path:** kill the escort leader — verify wingmen despawn within 30s, next wave activates
- **Command Buffer serialization:** simultaneous Cover→Attack and BomberLost signals resolve deterministically (verify by triggering both at approximately the same time)
- **No AI slot leak:** slot count returns to baseline after each wave despawns
- **30-minute session stable:** no DServer crash, no logic stall, no state machine deadlock

### Report Requirements

Document the test results before proceeding. For each verification item: PASS, FAIL, or NOT OBSERVED. If any item is FAIL:
- Cover/Attack toggle failure → return to session 3.4, R1 (cover_attack_toggle primitive)
- Timer corruption (premature reversion) → return to session 3.4, R3 (SM-003 fresh timer violation)
- Bomber-lost transition failure → return to session 3.4, R4 (GC integration, `[IN]_BomberLost`)
- CheckZone management failure → return to session 3.4, R1 (CheckZone deactivation logic)
- Serialization conflict → return to session 3.4, R1 + Phase 1 session 1.5 (SM-001)
- Phase 1 regression → return to the relevant Phase 1 primitive session

---

## Human Gate 3.5 — Cross-Module Integration Test

| | |
|---|---|
| **Gate ID** | 3.5 |
| **Depends On** | 3.1–3.4 (all AI module tasks complete), 3.1h, 3.2h, 3.3h, and 3.4h (all individual module tests passed) |
| **Actor** | Project Owner |
| **Blocks** | Phase 5 cannot begin until this gate is passed |

### Required Actions

- Compile 2+ modules of different types (minimum: one Intercept or Ground Attack + one Scramble or Bomber Escort)
- Import all compiled .Group files into the same .Mission in BOSEditor
- Wire `[OUT]` nodes from one module to `[IN]` nodes of another (e.g., Intercept `[OUT]_Fail` → Scramble `[IN]_Activate` to trigger a scramble response when the intercept module's flights are destroyed)
- Configure a 60-minute test session on a DServer or single-player host
- Observe the session for the full 60 minutes

### Verification Checklist

- **Module interop:** `[OUT]` → `[IN]` wiring between modules triggers correctly. When module A fires `[OUT]_Success` or `[OUT]_Fail`, module B activates.
- **ID isolation:** No Index collisions between modules. Entities, MCUs, and translators from different modules have unique IDs. (Verify in BOSEditor's entity list — no duplicate Index values.)
- **Spatial isolation:** Internal MCUs from different modules occupy distinct remote coordinate blocks. (Verify in BOSEditor at remote coordinates — modules are separated by 1000m Z-axis increments.)
- **AI cap compliance:** Total concurrent AI across all active modules never exceeds the ~100 AI cap. The GUI's AI cap display (task 2.6) aggregates correctly across modules.
- **GC independence:** Each module's GC chain operates independently. One module's wave cycling does not interfere with another module's Magazine Array.
- **No cross-contamination:** Entity proxy OnKilled events from one module do not accidentally trigger GC chains in another module. Leader-kill in module A does not affect module B's flights.
- **Dependency stubs:** If module B references a module C that is not present, the stub system (EC-002) catches the dangling reference without crashing the DServer.
- **60-minute session stable:** No DServer crash, no logic stall, no runaway AI count, no progressive performance degradation.

### Test Configurations

Run at least two of the following configurations:

1. **Intercept + Ground Attack:** Two independent modules operating simultaneously. Verifies parallel GC and AI cap compliance.
2. **Scramble + Bomber Escort:** Scramble activates on `[IN]_Activate`; Bomber Escort `[IN]_BomberLost` wired to an external trigger. Verifies state machine modules under concurrent operation.
3. **Chain wiring:** Intercept `[OUT]_Fail` → Scramble `[IN]_Activate`. When the intercept flights are all destroyed, a scramble response launches. Verifies sequential module activation through the I/O proxy system.

### Report Requirements

Document the test results before Phase 5 begins. For each verification item and each test configuration: PASS, FAIL, or NOT OBSERVED.

- If ID collision is detected: return to Phase 1, session 1.1 (IDGenerator). This is a CRITICAL regression.
- If spatial overlap is detected: return to Phase 1, session 1.2 (SpatialAllocator).
- If AI cap is exceeded: return to Phase 1, session 1.4 (Magazine Array) and session 1.6 (GC). Check EC-004 compliance.
- If cross-module GC contamination occurs: return to the relevant Phase 3 module session — Entity proxy bindings or GC chain wiring is incorrect.
- If interop wiring fails: return to Phase 1, session 1.7 (dependency stubs) and session 1.9 (init buffer).

Phase 5 (Mission Orchestrator) will compose arbitrary combinations of these modules programmatically. Any interop failure discovered in Phase 5 that traces to Phase 3 integration defects is 3–5× more expensive to isolate than one caught here.

---

## Recommended Execution Sequence

```
Phase 2.5h PASSED
    │
    ├──→ 3.1 (Intercept) ─────────→ 3.1h (Test) ──┬──→ 3.2 (Scramble) ──→ 3.2h (Test) ──┐
    │                                                │                                      │
    │                                                └──→ 3.4 (Bomber Escort) ──→ 3.4h (Test) ──┤
    │                                                                                             │
    └──→ 3.3 (Ground Attack) ──→ 3.3h (Test) ────────────────────────────────────────────────────┤
                                                                                                   │
                                                                                                   └──→ 3.5 (Cross-Module Integration)
                                                                                                          │
                                                                                                          ▼
                                                                                                    Phase 5 begins
```

- **Start immediately (parallel):** Session 3.1 (Intercept) and Session 3.3 (Ground Attack) — both depend only on Phase 2 outputs
- **After 3.1:** Gate 3.1h (in-game test)
- **After 3.3:** Gate 3.3h (in-game test)
- **After 3.1h (parallel):** Session 3.2 (Scramble) and Session 3.4 (Bomber Escort) — both depend on verified Intercept behavior
- **After 3.2:** Gate 3.2h (in-game test)
- **After 3.4:** Gate 3.4h (in-game test)
- **After all AI tasks + all individual tests (3.1h, 3.2h, 3.3h, 3.4h):** Gate 3.5 (cross-module integration)
- **Phase 5 begins after:** Gate 3.5 PASSED
