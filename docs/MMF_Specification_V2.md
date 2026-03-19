# Modular Mission Framework (MMF) — Architecture Specification

**Revision 2.0 — Post-FMEA**

| Field | Value |
|---|---|
| Target Environment | IL-2 Sturmovik Great Battles Mission Editor |
| Output Format | .Mission / .Group ASCII Syntax |
| Primary Language | Python (UI and Logic Matrix Generator) |
| Context | Reference document for AI-assisted canvas coding |

**Revision History**

- **Rev 1.0** — Original specification
- **Rev 2.0** — Incorporates 14 FMEA amendments (4 CRITICAL, 5 HIGH, 3 MEDIUM, 2 LOW); evaluates 2 proposed amendments (1 accepted, 1 modified, 3 rejected)

---

## 1. Project Objective

The Modular Mission Framework (MMF) is a UI-driven generation tool designed to bypass the structural limitations and manual repetition inherent in the IL-2 Mission Editor (BOSEditor). By abstracting logic creation into a Python interface, MMF compiles complex, reusable .Group assets that interlock natively without human routing errors or spatial logic entanglement.

The framework targets continuous 180-minute multiplayer DServer sessions with automated AI unit cycling, enforcing the engine's approximately 100-unit active AI cap through event-driven garbage collection and formation-preserving activation patterns.

---

## 2. Architectural Design Principles

This framework enforces strict separation of concerns to maintain human-readable editor workspaces and ensure resilience against engine updates.

### 2.1 JSON Intermediary

The Python UI outputs an intermediate JSON schema representing the logic graph. A distinct compiler translates this JSON into the proprietary IL-2 .Group ASCII syntax.

> **[PI-002] CONSTRAINT:** The JSON-to-ASCII compiler SHALL apply a second-pass reserved-character filter to all string-type fields. Reserved characters in IL-2 syntax (`{}[];="`) SHALL be stripped. This filter operates independently of any GUI-side sanitization.

### 2.2 Syntax Agnosticism

If 1C Game Studios updates node parameters or the file schema, only the JSON-to-ASCII compiler mapping requires modification. Core logic generation remains untouched.

### 2.3 Spatial Blackboxing

To prevent manual interference, the Python generator compiles all core calculation MCUs at grid coordinates offset by at least 50km from the playable map. Only the user-facing Proxy Nodes (I/O) are placed at the target coordinates.

> **[PI-004] CONSTRAINT:** The remote coordinate zone SHALL be partitioned. Each imported module SHALL receive a unique offset block within the remote zone, incremented by 1000m on the Z-axis per module. The compiler SHALL track allocated blocks per session to prevent overlap.

### 2.4 ID Management

The compiler dynamically assigns unique integer IDs to all entities, MCUs, and translators to prevent .Mission file collisions when importing multiple groups.

> **[PI-003] CONSTRAINT:** The compiler SHALL maintain a single monotonically increasing ID counter per compilation session. The counter SHALL initialize from max(all existing Index values in the target .Mission file) + 1. Per-module fixed offsets are explicitly prohibited. Each entity, MCU, and translator SHALL receive the next sequential integer from this counter.

---

## 3. Standardized I/O & Logic Hooks

All generated modules must interact exclusively through a standardized API layer. External modules are strictly prohibited from linking directly to a module's internal calculation nodes.

- **[IN]_Activate (Timer, 0s):** The sole entry point for external logic. Initiates the module's sequence.
- **[OUT]_Success (Timer, 0s):** Fired when the objective is met (e.g., target destroyed).
- **[OUT]_Fail (Timer, 0s):** Fired when the module's actors are destroyed or time expires.
- **[CFG]_Params (Counter/ComplexTrigger):** Internal nodes reserved for passing parameters before activation.

### 3.1 Compiler Validation

> **[PI-001] CONSTRAINT:** The compiler SHALL enforce a Required Field Schema. Any MCU command node (AttackArea, Cover, Waypoint) with a null or zero-length Targets or Objects array SHALL abort compilation and return a diagnostic error identifying the module, node type, and missing field.

### 3.2 Dependency Management (The Stub System)

The MMF compiler executes a pre-flight dependency check. If an [OUT] node points to a missing module's [IN] node, the compiler automatically generates an isolated, 0-second MCU_Timer to catch the call and prevent fatal DServer crash exceptions on mission load.

> **[EC-002] CONSTRAINT:** Stub MCU_Timers SHALL be allocated from a reserved ID range (900000–999999) that is excluded from the dynamic ID generator's allocation pool. The compiler SHALL emit a comment block at the top of the .Group file listing all generated stubs, their IDs, and the missing module references they are catching.

---

## 4. State Management & Entity Extraction

The IL-2 engine does not support complex internal variables. MMF simulates state using mechanical workarounds.

### 4.1 The Command Buffer

To prevent AI behavior locking when simultaneous commands are issued (e.g., "Scramble" overlapping with "Attack"), all [IN] signals pass through a Command Buffer. The buffer serializes state transitions to prevent race conditions caused by non-deterministic MCU processing order within a single engine tick.

#### 4.1.1 Serialization Sequence

The Command Buffer enforces the following state transition sequence for every [IN] signal: MCU_Deactivate (clears previous state) followed by a staggered MCU_Timer, followed by MCU_Activate (engages new state). This serialization pattern is modeled on the IL-2 manual's Damage Display Switch (pg. 287–289), which uses staggered timer increments to serialize simultaneous events.

> **[SM-001] CONSTRAINT:** All [IN] signals SHALL route through a serialization timer before entering the Command Buffer. The state transition sequence SHALL be: MCU_Deactivate → MCU_Timer (50–100ms) → MCU_Activate. Each [IN] entry point within a module SHALL be assigned a unique delay value, staggered in 50ms increments (e.g., [IN]_Primary = 50ms, [IN]_Secondary = 100ms). Delays exceeding 200ms are prohibited to prevent AI command-vacuum drift. This serialization layer SHALL be automatically generated by the compiler based on the module's [IN] port count.

#### 4.1.2 Timer Pause Semantics

The IL-2 engine pauses a deactivated timer at its current countdown position rather than resetting it to zero. Reactivation resumes the countdown from the paused position (IL-2 Manual, Timer Trigger, pg. 283). This means the Command Buffer's Deactivate-then-reissue pattern does NOT reset in-progress timers. A ToS timer paused at 8 of 10 minutes fires after only 2 more minutes when reactivated.

> **[SM-003] CONSTRAINT:** MCU_Timer nodes used for time-gated logic (ToS, patrol duration) SHALL NOT be reused across Command Buffer state transitions. The compiler SHALL generate a discrete timer instance for each possible activation path. Previously triggered timers SHALL be permanently deactivated, not recycled. Each new [IN] activation SHALL engage a fresh, never-triggered timer.

### 4.2 State Extraction (MCU_TR_Entity)

Spatial MCU_TR_CheckZone polling causes severe multiplayer desyncs and logic stutter. MMF extracts state natively from the engine using MCU_TR_Entity proxy bindings.

**Generation Rule:** The Python generator must output an MCU_TR_Entity block for every generated lead aircraft.

**Two-Way Binding:** The MisObjID field within the Entity block must match the aircraft's Index. The aircraft's LinkTrId must match the Entity's Index.

**Output-Only Constraint:** MCU_TR_Entity is strictly an output proxy. It extracts OnKilled or OnTookOff states into the logic graph. It cannot accept incoming Command: Waypoint or Command: Attack nodes. All commands must Object Link directly to the aircraft.

> **[EL-003] CONSTRAINT:** The compiler SHALL execute a post-emission binding integrity check on every MCU_TR_Entity block. The check SHALL assert: (1) Entity.MisObjID == Aircraft.Index, (2) Aircraft.LinkTrId == Entity.Index, (3) Entity.MisObjID != Entity.Index. Failure of any assertion SHALL abort compilation.

#### 4.2.1 Entity Binding Temporal Dependency

The MCU_TR_Entity proxy requires the referenced aircraft to exist as a 3D physics object in the simulation, not merely as a declared entity in the mission file. During mass activation events, 3D object instantiation is queued and processed sequentially by the physics engine. An Entity that attempts to resolve its MisObjID binding before its target aircraft is physically instantiated will bind to nothing. The binding fails silently, and all downstream state extraction (OnKilled, OnTookOff) becomes permanently orphaned.

> **[EL-002] CONSTRAINT:** No MCU or logic node SHALL reference an MCU_TR_Entity's output events (OnKilled, OnTookOff, OnDamaged) within 2 seconds of the associated aircraft's Activate trigger firing. The compiler SHALL insert a mandatory 2-second MCU_Timer between any Activate trigger and the first downstream consumer of the Entity proxy's event outputs.

---

## 5. Tickrate Optimization (The 180-Minute Session)

A core requirement is supporting 180-minute multiplayer sessions with continuous unit generation without exceeding the approximately 100-unit active AI DServer limit. Exceeding this cap causes non-linear tickrate degradation: DServer SPS drops below the physics simulation threshold, producing desync, rubber-banding, and eventual server instability.

### 5.1 The Initialization Buffer

Loading thousands of MCUs at T=0 causes dropped frames and skipped logic triggers.

**Rule:** The framework generates a mandatory "Master Core" module containing an MCU_TR_MissionBegin linked to a configurable initialization delay timer. All subsequent [IN]_Activate proxy nodes must be routed from this timer to delay processing until 3D physics instantiation completes.

> **[EC-001] CONSTRAINT:** The Master Core initialization delay SHALL be a configurable parameter (default: 3 seconds, range: 3–10 seconds). The compiler SHALL emit a warning if the total count of Enabled=FALSE entities in the compiled output exceeds 200 and the initialization delay is set below 5 seconds.

### 5.2 The Magazine Array (Formation-Preserving Wave Activation)

The native MCU_CMD_Spawn node destroys pre-configured Target Link hierarchies, forcing spawned aircraft to ignore Command: Formation and preventing coordinated target delegation (IL-2 Manual, Spawner Trigger, pg. 282). MMF uses an alternative activation pattern to preserve native AI combat coordination.

#### 5.2.1 Activation Pattern

The Python script loops a user-defined "Wave Count" (e.g., 20), outputting identical, fully formed flights with Enabled=FALSE, stacked at the exact same spatial coordinates in a "Sleep" state. An indexing MCU_Counter with Reset After Operation = TRUE routes the activation trigger sequentially to the next deactivated flight via MCU_Activate, preserving the internal wingman hierarchy so the leader can properly execute Command: Attack Area delegation.

> **WARNING:** MCU_CMD_Spawn breaks Target Link formation hierarchies (IL-2 Manual, pg. 282: "Do not spawn objects that are in formation because the wingmen do not follow commands given to the leader"). The Magazine Array is the explicit architectural response to this engine limitation.

> **[EC-003] CONSTRAINT:** Magazine Array flights SHALL use the Activate/Deactivate (Enabled=FALSE → MCU_Activate) pattern exclusively. MCU_CMD_Spawn SHALL NOT be used for Magazine Array flights. The Spawner Trigger breaks Target Link formation hierarchies, preventing wingmen from following leader commands.

#### 5.2.2 Counter Behavior & Session Sizing

The IL-2 engine does not reset an MCU_Counter's internal count when the counter is deactivated (IL-2 Manual, Counter Trigger, pg. 278). A deactivated counter continues incrementing on input but does not fire; it fires immediately upon reactivation if the count has reached the maximum during the deactivated period. This behavior makes counter recycling across rotation cycles unreliable.

> **[EL-001] CONSTRAINT:** The Magazine Array indexing MCU_Counter SHALL use Reset After Operation = TRUE and SHALL NOT be deactivated during the mission session. The wave_count parameter in the GUI SHALL be validated against the formula: `wave_count >= ceil(session_duration_minutes / estimated_average_sortie_duration_minutes)`. The compiler SHALL emit a warning if `wave_count < ceil(180 / ToS)`. The MCU_Counter SHALL NOT be reused across rotation cycles; each Magazine Array is a single-use sequential dispenser.

#### 5.2.3 GC-Gated Wave Activation

The next wave in the Magazine Array must not activate until the previous wave's garbage collection has confirmed completion. This prevents transient AI count spikes during the overlap window between wave activation and previous-wave despawn. Timer-based wave activation (e.g., "activate wave N at T+10 minutes") without a garbage collection confirmation gate is architecturally prohibited because it decouples activation from actual AI slot availability.

> **[EC-004] CONSTRAINT:** The next-wave activation counter SHALL NOT fire until the previous wave's garbage collection chain has completed (either via Despawn confirmation or OnKilled). Time-based wave activation without GC gating is prohibited. The GUI SHALL calculate and display: `max_concurrent_AI = flight_size × max_simultaneous_waves`, and SHALL warn if this value exceeds 80.

### 5.3 Garbage Collection

All active flights are tethered to their MCU_TR_Entity OnKilled event listener and a Time-on-Station (ToS) timer. Upon expiration, the module executes MCU_CMD_Despawn to purge active objects from server memory, ensuring baseline tickrate stability.

#### 5.3.1 Dual-Path Activation

A flight may be destroyed (triggering OnKilled) before the ToS timer expires and fires Despawn. If Despawn is the sole trigger for the next Magazine Array wave, early kills break the activation chain and the Magazine stalls permanently. Both cleanup paths must independently advance the wave counter.

> **[SM-004] CONSTRAINT:** Garbage collection SHALL implement dual-path activation. Both the MCU_TR_Entity OnKilled chain AND the ToS-triggered Despawn chain SHALL independently route to the Magazine Array's next-wave activation counter. Each path SHALL pass through a dedicated 1-count non-resetting MCU_Counter to prevent double-counting. The downstream wave-advance counter SHALL accept input from both paths.

#### 5.3.2 Leader-Kill Resilience

If the flight leader is killed at ToS expiration, the Command:RTB Object Link target no longer exists in the 3D world. The command is silently dropped. Surviving wingmen enter a permanent idle state, consuming AI slots indefinitely. The MCU_TR_Entity is an output-only proxy and cannot route incoming commands to promoted wingmen.

> **[SM-002] CONSTRAINT:** All Command:RTB and Command:Waypoint nodes generated for ToS expiration SHALL Object Link to every aircraft in the flight, not exclusively the formation leader. Additionally, the leader's MCU_TR_Entity OnKilled output SHALL trigger a parallel garbage collection chain: ForceComplete → 30s Timer → Despawn, Object Linked to all wingmen. Area-based MCU_TR_CheckZone fallbacks SHALL NOT be used for garbage collection — they cause multiplayer desync and logic stutter (per Section 4.2). This ensures AI slot reclamation regardless of leader survival state at ToS expiration.

---

## 6. Module Testing & Development Path

Dynamic interception modules contain too many gameplay variables (player altitude, speed, spawn timing) for baseline logic validation.

### 6.1 Initial Validation Prototype

**Static Combat Air Patrol (CAP) or Logistics Convoy:** A closed loop of Command: Waypoint nodes and a single Command: Attack Area MCU. This requires zero dynamic player triggers and negligible tickrate overhead. Success of the CAP route validates the core MMF compiler pipeline: I/O proxy nodes, ID generation, spatial offsets, Entity proxy binding integrity checks, Command Buffer serialization, and syntax hygiene.

### 6.2 Future Modules

**Scramble:** Transitions from parked to airborne combat. Gated by an MCU_TR_ComplexTrigger at the runway boundary validating the OnEntered altitude state before unlocking airborne intercept logic.

**Bomber Escort:** Dynamic tethering via Object Links, alternating between Command: Cover and localized Command: Attack parameters based on threat proximity. Note: moving CheckZones should be minimized per Section 4.2 performance guidance.

---

## Appendix A: FMEA Traceability Index

Every constraint box in this specification is keyed to an FMEA entry from the Failure Mode & Effects Analysis (Rev 2). The following index maps constraint IDs to their FMEA severity ratings and the specification section where they appear.

| FMEA ID | Component | Severity | Spec Section | Constraint Summary |
|---|---|---|---|---|
| **PI-001** | JSON-to-ASCII Translator | **CRITICAL** | 3.1 | Required Field Schema validation |
| **PI-002** | JSON-to-ASCII Translator | **HIGH** | 2.1 | Reserved-character filter |
| **PI-003** | Dynamic ID Generator | **CRITICAL** | 2.4 | Monotonic ID counter |
| **PI-004** | Spatial Offset Engine | **MEDIUM** | 2.3 | Partitioned remote coordinate zone |
| **EL-001** | Magazine Array Counter | **CRITICAL** | 5.2.2 | Counter non-deactivation, session sizing |
| **EL-002** | Entity Proxy Binding | **HIGH** | 4.2.1 | 2-second post-Activate delay |
| **EL-003** | Entity Proxy Binding | **CRITICAL** | 4.2 | Post-emission binding integrity check |
| **SM-001** | Command Buffer | **HIGH** | 4.1.1 | 50–100ms serialization timers |
| **SM-002** | ToS RTB + Leader Kill | **HIGH** | 5.3.2 | All-flight Object Links, parallel GC chain |
| **SM-003** | Timer Pause Semantics | **HIGH** | 4.1.2 | No timer reuse across state transitions |
| **SM-004** | Despawn Logic | **LOW** | 5.3.1 | Dual-path GC activation |
| **EC-001** | Initialization Buffer | **MEDIUM** | 5.1 | Configurable init delay |
| **EC-002** | Dependency Stubs | **MEDIUM** | 3.2 | Reserved ID range for stubs |
| **EC-003** | Spawner vs. Activate | **HIGH** | 5.2.1 | Spawn prohibited for Magazine flights |
| **EC-004** | AI Unit Cap | **HIGH** | 5.2.3 | GC-gated wave activation |
