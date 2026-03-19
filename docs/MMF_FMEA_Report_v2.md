# Failure Mode & Effects Analysis — Modular Mission Framework (MMF) Architecture

**IL-2 Sturmovik Great Battles — DServer Multiplayer Environment**

**Revision 2 — Includes evaluation of proposed specification amendments**

---

## 1. Executive Summary

This FMEA identifies 14 failure points in the proposed MMF architecture across four domains: Pipeline Integrity (JSON-to-ASCII translation and ID management), Engine Limitation Compliance (Magazine Array activation, Entity proxy binding, tickrate mechanics), State Management (Command Buffer race conditions, timer pause semantics, leader-kill edge cases), and Garbage Collection (despawn-activation coupling, AI cap enforcement). Four failure modes are rated CRITICAL — they will crash the DServer or produce silently corrupt .Group files. Five are rated HIGH — they cause logic orphaning or AI slot leakage that degrades the server over a 180-minute session. Three are MEDIUM and two are LOW.

**Revision 2 adds Section 6:** an evaluation of two proposed specification amendments submitted after the initial FMEA. Of five discrete elements across the two proposals, one is accepted as-is, one is accepted with modification, and three are rejected on the basis that they reintroduce failure modes already identified in the original analysis. The accepted elements have been incorporated into the updated amendment language in Section 8.

---

## 2. Pipeline Integrity Analysis

The JSON-to-ASCII translation layer is the single point of failure between the GUI and the IL-2 engine. The IL-2 .Group/.Mission ASCII format is an undocumented proprietary syntax with zero error tolerance — a single malformed field causes a cascade parse failure that can offset every subsequent Index reference in the file. The specification currently defines the JSON intermediary (Section 2, Principle 1) and the compiler mapping (Principle 2), but does not mandate input validation against the engine's required field schema.

The most dangerous vector is null or empty array fields. An MCU_CMD_AttackArea with an empty `Targets[]` array is not merely illogical — it is structurally invalid. The engine expects a populated target reference to resolve during mission load. A null dereference here halts the DServer loading cycle. The compiler must refuse to emit any command MCU with unresolved dependencies, not silently emit a malformed block and hope the engine handles it gracefully. It will not.

ID generation presents a subtler risk. The specification calls for "dynamic ID generation" and "coordinate offsets to prevent ID collisions" (Section 2, Principle 4), but does not specify the algorithm. A per-module fixed offset scheme (e.g., Module A starts at ID 1000, Module B at 2000) is the intuitive implementation but it is mathematically unsafe when the same module is imported multiple times — import 10 copies of a module requiring 150 IDs each, and a fixed 100-ID offset per import causes collisions at import 7. Only a global monotonically increasing counter eliminates this class of error entirely.

---

## 3. Engine Limitation Analysis

The Magazine Array is the architectural linchpin of the entire 180-minute session model. Its design (Section 5.2) relies on an MCU_Counter to sequentially activate deactivated flights. The specification does not address what happens when the counter exhausts its sequence — and the engine's counter behavior under deactivation is actively hostile to the naive assumption that deactivating a counter resets it.

The manual is unambiguous (Counter Trigger, pg. 278): deactivating a counter does not reset its internal count. The count continues to increment on input even while deactivated. If Reset After Operation is cleared, the counter is permanently exhausted after one full cycle. If Reset After Operation is set, the counter resets after each firing — but deactivation during a mid-count state creates a deferred fire on reactivation that can trigger the wrong wave. The specification must explicitly prohibit deactivation of the Magazine Array counter and must size the wave count to cover the entire session without recycling.

The MCU_TR_Entity proxy binding is the second critical engine constraint. The two-way binding (Entity.MisObjID = Aircraft.Index, Aircraft.LinkTrId = Entity.Index) is a hard structural requirement documented in the specification (Section 4.2). But the specification does not address the temporal dependency: the Entity proxy requires the aircraft to exist as a 3D physics object, not merely as a declared entity in the mission file. During mass activation events, 3D instantiation is queued — the physics engine processes spawn requests sequentially. An Entity that resolves its binding before its target aircraft is physically instantiated binds to nothing. The binding fails silently. All downstream state extraction is dead.

The Spawner Trigger's formation-breaking behavior (pg. 282: "Do not spawn objects that are in formation because the wingmen do not follow commands given to the leader") is a critical trap for the Magazine Array implementation. The specification describes deactivated flights in a "Sleep state" with sequential activation — this correctly implies Activate/Deactivate, not Spawn/Delete. But the specification never explicitly prohibits using the Spawner. Given that the Canvas Prompt 1 (Backend) names the function "The Magazine Array Spawner," there is a significant risk that an implementer reads "Spawner" literally and uses MCU_CMD_Spawn. This must be made terminologically unambiguous.

---

## 4. State Management Vulnerability Analysis

The Command Buffer (Section 4.1) uses MCU_Deactivate to clear previous states before issuing new commands. This pattern is sound in isolation but vulnerable to race conditions when two modules fire [IN] triggers simultaneously. The IL-2 engine processes MCU triggers sequentially within a server tick, but the ordering of simultaneously-queued triggers is non-deterministic. The manual's own Damage Display Switch (pg. 287–289) demonstrates awareness of this problem — it uses staggered 5ms timers to serialize simultaneous OnKilled events. The Command Buffer needs the same serialization layer.

The correct serialization delay is 50–100ms per [IN] port, staggered in 50ms increments. This is long enough to guarantee cross-tick separation (the engine runs at ~50 ticks/second, so one tick = 20ms) but short enough to prevent AI behavioral drift. A 1-second delay — as proposed in one submitted amendment — creates a full second of command vacuum where AI defaults to autonomous engagement behavior. Fighters break formation to attack nearby targets; bombers deviate from waypoints. The damage is often irreversible within that window.

The Timer pause semantics introduce a second, more subtle state corruption vector. The manual states explicitly (Timer Trigger, pg. 283): deactivating a mid-countdown timer pauses it; reactivation resumes from the paused position. The Command Buffer's Deactivate-then-reissue pattern therefore does NOT reset in-progress timers. A ToS timer paused at 8 of 10 minutes fires after only 2 more minutes when reactivated — a logic error that causes premature RTB or premature garbage collection. The specification must prohibit timer reuse across state transitions.

The flight leader kill scenario during ToS expiration exposes a fundamental architectural gap. Commands must Object Link directly to the aircraft, not to the Entity proxy. If the leader is dead, the Object Link target is gone, the command is dropped, and the surviving wingmen enter a permanent idle state. The fix requires RTB commands to Object Link to all flight members, plus a parallel OnKilled garbage collection chain targeting all wingmen. Area-based CheckZone fallbacks — proposed in one submitted amendment — reintroduce the spatial polling overhead that Section 4.2 of the specification explicitly warns against.

---

## 5. Garbage Collection & AI Cap Analysis

The ~100 active AI unit cap is a hard performance cliff. DServer tickrate degradation above this threshold is non-linear. The Magazine Array's next-wave activation must be structurally gated behind the previous wave's garbage collection confirmation. Any architecture that allows time-based wave activation without a GC confirmation gate — including timer cascades — risks transient AI count spikes during the overlap window between wave activation and previous-wave despawn.

The dual-path activation problem is the subtlest failure mode in the garbage collection system. If the Magazine Array's next-wave counter is only incremented by the Despawn trigger, then a flight that dies before the ToS timer (and thus before the Despawn fires) never increments the counter. The Magazine stalls permanently. Both the OnKilled path and the Despawn path must independently route to the next-wave counter, each through a dedicated 1-count non-resetting sub-counter to prevent double-counting.

---

## 6. Proposed Amendment Review

Two specification amendments were submitted for review after the initial FMEA. This section evaluates each discrete element against the engine documentation and the failure modes identified in Sections 2–5. Elements are individually accepted, rejected, or accepted with modification.

### 6.1 Proposed Amendment: Section 5.2 — Spawn Queuing & Logic Routing

**Proposal:** *Replace Magazine Array activation with MCU_CMD_Spawn triggered via an MCU_Timer cascade, with a mandatory 2-second delay before Entity binding.*

This proposal contains three discrete elements: (1) the use of MCU_CMD_Spawn instead of Activate/Deactivate, (2) the 2-second post-activation Entity binding delay, and (3) replacing the MCU_Counter with an MCU_Timer cascade for sequential wave activation. These elements have independent failure characteristics and must be evaluated separately.

**Element 1 — MCU_CMD_Spawn: REJECTED.** The manual's Spawner Trigger reference (pg. 282) is unambiguous: "Do not spawn objects that are in formation because the wingmen do not follow commands given to the leader." The Magazine Array's entire purpose is preserving the native wingman Target Link hierarchy so the leader can delegate Command:AttackArea across the formation. MCU_CMD_Spawn destroys that hierarchy. Every spawned wingman operates independently — no coordinated combat, no formation integrity, no delegation. This is not a degraded mode; it is a total functional failure of the AI combat model. The correct pattern remains Activate/Deactivate: pre-placed formations with Enabled=FALSE, woken by MCU_Activate, which preserves all Target Links because the formation structure exists intact from mission load.

**Element 2 — 2-second Entity binding delay: ACCEPTED.** This correctly addresses FMEA item EL-002. The delay mirrors the manual's explicit guidance (Activate Trigger, pg. 274) and ensures the 3D physics object exists before the Entity proxy attempts to resolve its MisObjID binding. This element is valid regardless of the activation mechanism. In the recommended architecture, the 2-second timer is placed between the MCU_Activate trigger output and the first downstream consumer of the Entity proxy's event outputs.

**Element 3 — Timer cascade replacing MCU_Counter: REJECTED.** A timer cascade is time-driven: waves activate on a fixed schedule regardless of whether the previous wave has been garbage collected. This removes the GC confirmation gate that prevents AI cap breaches (FMEA EC-004). If wave N dies in 2 minutes but the cascade expects 10, 8 minutes of AI slot capacity is wasted. If wave N survives 15 minutes but the cascade fires at 10, two waves overlap and the AI count spikes above the ~100 cap. The MCU_Counter with Reset After Operation = TRUE, fed by the dual-path GC confirmation chain (FMEA SM-004), is event-driven and self-regulating — the next wave activates precisely when the previous wave confirms cleanup, never before.

### 6.2 Proposed Amendment: Section 3 — Command Buffer & Entity Resilience

**Proposal:** *Command Buffer serialization via Deactivate → 1-second Timer → Activate. Entity link resilience via area-based CheckZone fallback for wingman garbage collection when leader is killed.*

This proposal contains two discrete elements: (1) the Command Buffer serialization pattern with a 1-second timer, and (2) area-based CheckZone fallback for Entity link resilience.

**Element 4 — Command Buffer serialization (Deactivate → Timer → Activate): ACCEPTED WITH MODIFICATION.** The Deactivate → Timer → Activate pattern is structurally correct and addresses FMEA SM-001. However, the 1-second (1000ms) delay is an order of magnitude too high. During the command vacuum, AI defaults to autonomous behavior — fighters break formation to engage nearby targets, bombers deviate from waypoints. This behavioral drift is often irreversible. The manual's Damage Display Switch (pg. 287–289) uses 5ms staggered increments to serialize simultaneous events. The correct range for the Command Buffer is 50–100ms per [IN] port, staggered in 50ms increments. This guarantees cross-tick serialization (one engine tick = ~20ms at 50 ticks/second) while keeping the command vacuum below the threshold where AI behavioral reactions occur. The updated amendment adds an explicit ceiling: serialization delays SHALL NOT exceed 200ms.

**Element 5 — Area-based CheckZone fallback for wingman GC: REJECTED.** The MMF Specification itself (Section 4.2) warns that "spatial MCU_TR_CheckZone polling causes severe multiplayer desyncs and logic stutter." Introducing CheckZones as the fallback garbage collection mechanism reintroduces the exact performance pathology the MMF was designed to eliminate. On a 180-minute server with 20+ Magazine waves, each with a fallback CheckZone, active zone-polling MCUs accumulate and degrade tickrate cumulatively. The problem is fully solvable without spatial polling: Object Link RTB commands to ALL aircraft in the flight (not just the leader), and trigger a parallel ForceComplete → 30s Timer → Despawn chain Object Linked to all wingmen on leader OnKilled. This provides complete coverage with zero spatial overhead.

### 6.3 Disposition Matrix

| Proposed Element | Source | Verdict | FMEA Ref | Analysis | Final Recommendation |
|---|---|---|---|---|---|
| **MCU_CMD_Spawn for wave activation** | Proposed §5.2 | **REJECT** | EC-003 | Manual pg. 282 explicitly warns: spawning objects in formation breaks Target Link hierarchies. Wingmen will not follow leader commands. The Magazine Array's core value is preserving native AI combat coordination through intact formations. MCU_CMD_Spawn destroys this. The correct pattern remains Activate/Deactivate (Enabled=FALSE → MCU_Activate). | Retain FMEA amendment EC-003: Magazine Array flights SHALL use Activate/Deactivate exclusively. MCU_CMD_Spawn is prohibited for formation-based flights. |
| **2-second MCU_Timer delay post-activation before Entity binding** | Proposed §5.2 | **ACCEPT** | EL-002 | Correctly addresses the 3D instantiation race condition. The 2-second delay mirrors the manual's explicit guidance (Activate Trigger, pg. 274): add a delay before issuing commands to a just-activated object. Entity binding resolution has the same temporal dependency. This element is sound regardless of whether Spawn or Activate is used. | Adopt as written. Attach the 2-second timer to the MCU_Activate trigger output (not MCU_CMD_Spawn, which is rejected). The delay gates all downstream Entity proxy consumers. |
| **MCU_Timer cascade replacing MCU_Counter for sequential activation** | Proposed §5.2 | **REJECT** | EL-001, EC-004 | A timer cascade is time-driven: waves activate on a fixed schedule regardless of whether the previous wave has been garbage collected. This removes the GC confirmation gate that prevents AI cap breaches (EC-004). If wave N dies in 2 minutes but the timer cascade expects 10, 8 minutes of AI slot capacity is wasted. If wave N survives 15 minutes but the cascade fires at 10, two waves overlap and the AI count spikes. The MCU_Counter with Reset After Operation = TRUE, fed by the dual-path GC confirmation (SM-004), is event-driven and self-regulating. | Retain FMEA architecture: MCU_Counter (Reset=TRUE, never deactivated) with GC-gated next-wave activation. Timer cascades are prohibited for wave sequencing. |
| **Command Buffer: Deactivate → 1-second Timer → Activate serialization** | Proposed §3 | **MODIFY** | SM-001 | The serialization pattern (Deactivate → Timer → Activate) is correct and addresses the same-tick race condition identified in SM-001. However, 1 second (1000ms) is an order of magnitude too long. During the delay, the AI flight has no active command and defaults to autonomous behavior — fighters break formation to engage nearby targets, which can scatter a flight irreversibly. The manual's Damage Display Switch uses 5ms increments. The FMEA recommends 50ms increments, which guarantees cross-tick serialization (engine runs at ~50 ticks/sec = 20ms/tick) while keeping the command vacuum below the AI behavioral reaction threshold. | Adopt the Deactivate → Timer → Activate pattern. Reduce the timer from 1000ms to 50–100ms per [IN] port, staggered in 50ms increments. Add an explicit ceiling: serialization delays SHALL NOT exceed 200ms to prevent AI command-vacuum drift. |
| **Entity Link Resilience: area-based CheckZone fallback for wingman GC when leader killed** | Proposed §3 | **REJECT** | SM-002 | The MMF Specification itself (Section 4.2) warns that "spatial MCU_TR_CheckZone polling causes severe multiplayer desyncs and logic stutter." Introducing CheckZones as the fallback garbage collection mechanism reintroduces the exact performance pathology the MMF was designed to eliminate. On a 180-minute server with 20+ Magazine waves, each with a fallback CheckZone, active zone-polling MCUs accumulate and degrade tickrate cumulatively. The problem is solvable without spatial polling. | Retain FMEA mitigation SM-002: Object Link RTB commands to ALL aircraft in the flight (not just the leader). On leader OnKilled, trigger ForceComplete → 30s Timer → Despawn chain Object Linked to all wingmen. No CheckZones. |

---

## 7. FMEA Matrix

The following matrix catalogs all identified failure points with their severity ratings, engine effects, and required mitigations. Amendment language has been updated in Rev 2 to incorporate accepted elements from the proposed amendments evaluated in Section 6.

| ID | Component | Failure Mode | Severity | Engine Effect | Mitigation | Spec Amendment |
|---|---|---|---|---|---|---|
| **PI-001** | JSON-to-ASCII Translator | Null or empty `Targets[]` array passed for MCU_CMD_AttackArea | **CRITICAL** | DServer throws unhandled null reference on mission load. Mission file fails to parse; server halts loading cycle and drops all connected clients. | Compiler MUST validate all required MCU fields against a schema whitelist before ASCII emission. Any MCU_CMD node with an empty `Targets[]` or `Objects[]` array must halt compilation with a named error, not emit a malformed block. | YES — See §8 |
| **PI-002** | JSON-to-ASCII Translator | String field containing unescaped characters (backslash, semicolon, curly brace) injected into Name or Desc field | **HIGH** | IL-2 ASCII parser treats semicolons as field terminators and braces as block delimiters. Unescaped injection truncates or corrupts the containing MCU block, causing silent data loss or a cascade parse failure that offsets all subsequent Index references. | The compiler string sanitizer must strip or escape all reserved ASCII syntax characters (`{}[];=`) from user-supplied string fields before emission. The GUI export validator must perform first-pass sanitization, but the compiler must enforce a second-pass whitelist as defense in depth. | YES — See §8 |
| **PI-003** | Dynamic ID Generator | ID namespace collision when importing the same module 10+ times consecutively | **CRITICAL** | Duplicate Index values in a .Mission file cause the engine to silently overwrite the first entity with the second. All Target Links and Object Links referencing the overwritten Index bind to the wrong object. AI flights receive commands meant for other flights; state extraction returns data from the wrong entity. In worst case, DServer crashes on cyclic link resolution. | The ID generator MUST use a monotonically increasing global counter, not a per-module offset scheme. Each compilation session initializes from the highest existing Index in the target .Mission file + 1. Each module import increments from the session counter, never resetting. | YES — See §8 |
| **PI-004** | Spatial Offset Engine | Two modules compiled in the same session receive overlapping remote coordinates for internal MCUs at the 50km offset zone | **MEDIUM** | Overlapping MCU icons in the editor are a usability failure, not an engine crash. However, if a mission designer manually opens the file and attempts to debug, they cannot distinguish between modules. More critically, if the engine processes spatially co-located MCU_TR_CheckZone nodes from different modules, zone overlap causes false-positive detection triggering cross-module logic corruption. | The spatial offset function must increment the remote coordinate block per module import within a session. E.g., Module 1 at (50000, 50000), Module 2 at (50000, 51000), etc. The increment must exceed the maximum spatial footprint of any single module's internal node layout. | YES — See §8 |
| **EL-001** | Magazine Array MCU_Counter (Sequential Activation) | Counter internal state persists through Deactivate/Activate cycle. After a full 20-wave loop, the counter has fired 20 times with Reset After Operation enabled. If the counter is deactivated and reactivated for a second 180-min rotation, the internal count is NOT reset — it continues incrementing from 20, never reaching its target again. | **CRITICAL** | The manual explicitly states (Counter Trigger, pg. 278): deactivating a counter does not reset its internal count. The count continues to increment on input even while deactivated. For a non-resetting counter, the counter is permanently exhausted after its first full cycle. For a resetting counter, deactivation during mid-count creates a phantom fire on reactivation. Neither behavior supports clean multi-rotation Magazine loops across a 180-minute session. | The Magazine Array counter SHALL use Reset After Operation = TRUE and SHALL NOT be deactivated during the mission session. The wave_count parameter SHALL be validated: `wave_count >= ceil(session_duration_minutes / estimated_average_sortie_duration_minutes)`. The MCU_Counter is a single-use sequential dispenser sized for the full session. | YES — See §8 |
| **EL-002** | MCU_TR_Entity Proxy Binding | During a mass activation event (3+ flights activating within the same server tick), the engine's 3D object instantiation queue delays physical entity creation. The MCU_TR_Entity attempts to bind via MisObjID to an aircraft whose 3D mesh has not yet been instantiated in the physics simulation. | **HIGH** | The Entity proxy requires the referenced object to exist in the 3D world, not just in the mission file's logical graph. If the object's 3D instantiation is still queued when the Entity attempts to resolve its MisObjID binding, the binding silently fails. The Entity's OnKilled and OnTookOff event outputs never fire. All downstream logic becomes permanently orphaned. The flight operates in the 3D world but is invisible to the logic graph — a ghost flight consuming AI slots with no cleanup path. | All MCU_Activate triggers that wake Magazine Array flights MUST chain through a mandatory 2-second MCU_Timer before any logic that depends on the Entity proxy's output events. This mirrors the manual's explicit instruction (Activate Trigger, pg. 274): "Before issuing a command to an object that has just been activated, add a one or two-second delay using a timer trigger." | YES — See §8 |
| **EL-003** | MCU_TR_Entity Proxy Binding | Entity MisObjID/LinkTrId two-way binding emitted with swapped values (Entity.MisObjID = Entity.Index instead of Aircraft.Index) | **CRITICAL** | The engine creates a self-referential binding loop. The Entity listens to itself for OnKilled events. The aircraft is unbound — no state extraction occurs. This is a silent logic failure: no crash, no error log, just total state blindness for that flight. | The compiler's Entity Proxy Binding function must include a post-emission assertion: `assert(entity.MisObjID != entity.Index)` and `assert(aircraft.LinkTrId == entity.Index)`. These assertions must run against the final ASCII output buffer, not the intermediate JSON. | YES — See §8 |
| **SM-001** | Command Buffer (MCU_Deactivate clearing) | Two modules fire conflicting [IN] triggers within the same 1/50th-second server tick. The Deactivate from Module B clears the state that Module A just set, producing non-deterministic command interleaving. | **HIGH** | The IL-2 engine processes MCU triggers sequentially within a tick but the ordering of simultaneous triggers is non-deterministic. The Damage Display Switch in the manual (pg. 287–289) explicitly addresses this: it uses staggered 5ms timer increments to serialize simultaneous events. The same race condition applies to the Command Buffer. | The Command Buffer must serialize state transitions: MCU_Deactivate → staggered MCU_Timer (50–100ms) → MCU_Activate. Each [IN] entry point SHALL be assigned a unique delay value staggered in 50ms increments. This guarantees deterministic non-overlapping execution windows without the AI command vacuum caused by longer delays. | YES — See §8 |
| **SM-002** | Time-on-Station (ToS) RTB Gate + Flight Leader Kill | AI flight leader is killed at the exact moment the ToS timer expires. Command:RTB has no valid object link target. Wingmen enter permanent idle state. | **HIGH** | MCU_TR_Entity is strictly an output proxy (MMF Spec Section 4.2). It cannot accept incoming Command nodes. Commands must Object Link directly to the aircraft. If the leader is dead, the command is silently dropped. Wingmen receive no RTB and consume AI slots indefinitely with no garbage collection path. | Two-layer solution: (1) Command:RTB must Object Link to ALL aircraft in the flight, not just the leader. (2) The leader's OnKilled event must trigger a parallel cleanup chain: ForceComplete → 30s Timer → Despawn, all Object Linked to every wingman. No area-based CheckZone fallbacks — these reintroduce the spatial polling overhead the MMF was designed to eliminate. | YES — See §8 |
| **SM-003** | Command Buffer + Timer Pause Semantics | MCU_Deactivate targeting a Timer that is mid-countdown pauses it instead of resetting it. Reactivation resumes from the paused position, not from zero. | **HIGH** | The manual explicitly states (Timer Trigger, pg. 283): deactivating a mid-countdown timer pauses it; reactivation resumes from the paused position. The Command Buffer's Deactivate-then-reissue pattern does NOT reset in-progress timers. A ToS timer paused at 8 of 10 minutes fires after only 2 more minutes when reactivated. | The Command Buffer must NOT reuse timers across state transitions. Each [IN] activation must trigger a fresh, previously-untouched timer instance. The compiler must generate a pool of ToS timers equal to the number of possible state transitions, each starting in Enabled=FALSE state. | YES — See §8 |
| **SM-004** | Garbage Collection / Despawn Logic | MCU_CMD_Despawn fires on a flight already destroyed. If Despawn is the only trigger for the next Magazine wave, a flight killed before the ToS timer stalls the Magazine permanently. | **LOW** | Despawning a dead object is a no-op — no crash. But if Despawn is the sole next-wave trigger, early kills break the activation chain. The Magazine Array stalls permanently. | Both OnKilled (Entity proxy) AND ToS Despawn paths must independently increment the Magazine Array's next-wave counter. Each path passes through a dedicated 1-count non-resetting MCU_Counter to prevent double-counting. | YES — See §8 |
| **EC-001** | Initialization Buffer (Master Core) | Master Core 3-second delay is insufficient on heavily loaded DServer. 3D physics instantiation for 50+ pre-placed deactivated flights exceeds 3 seconds. | **MEDIUM** | If [IN]_Activate fires before all deactivated flights are registered in the physics engine, Activate triggers targeting those flights silently fail. Flights remain in Sleep state permanently. | The 3-second delay should be configurable via the GUI (default: 3s, range: 3–10s). Compiler warning if deactivated entity count exceeds 200 and delay is below 5 seconds. | YES — See §8 |
| **EC-002** | Dependency Stub System | Stub timer at missing ID fires immediately and may collide with legitimate MCUs added later. | **MEDIUM** | The stub catches the call (preventing crash) but consumes the trigger signal. If a real module is later added at that ID slot, the stub intercepts the signal — non-deterministic behavior. | Stubs must occupy a reserved ID range (900000–999999) excluded from the dynamic ID generator. Compiler emits a manifest comment block listing all stubs. | YES — See §8 |
| **EC-003** | Spawner Trigger + Formation Hierarchy | MCU_CMD_Spawn used for Magazine Array flights breaks all wingman Target Link hierarchies. Manual pg. 282: "Do not spawn objects that are in formation because the wingmen do not follow commands given to the leader." | **HIGH** | Spawned wingmen ignore the leader's Command:AttackArea delegation. Each aircraft operates independently — no coordinated combat, no formation integrity. AI effectiveness collapses. | The compiler MUST use Activate/Deactivate (Enabled=FALSE → MCU_Activate) exclusively for Magazine Array flights. MCU_CMD_Spawn is explicitly prohibited. | YES — See §8 |
| **EC-004** | ~100 Active AI Unit Cap | Magazine Array activates new wave before garbage collection despawns previous wave. Active AI count exceeds ~100 during the overlap window. | **HIGH** | Exceeding the active AI cap causes non-linear tickrate degradation. DServer SPS drops below physics simulation threshold, causing desync, rubber-banding, and eventual server instability. | Next-wave activation MUST be gated behind GC confirmation. Time-based activation without GC gate is prohibited. GUI displays worst-case concurrent AI count and warns if exceeding 80. | YES — See §8 |

---

## 8. Required MMF_Specification.md Amendments (Rev 2)

The following amendments must be applied to the MMF_Specification.md before any Python code is written for either the frontend GUI or the backend compiler. Each amendment is keyed to its FMEA matrix entry. Rev 2 amendments incorporate the accepted elements from the proposed amendments evaluated in Section 6: the 2-second post-Activate Entity binding delay (Element 2) and the Deactivate → Timer → Activate serialization pattern with corrected timing (Element 4).

**[PI-001] JSON-to-ASCII Translator**

> *Add to Section 3: "The compiler SHALL enforce a Required Field Schema. Any MCU command node (AttackArea, Cover, Waypoint) with a null or zero-length Targets or Objects array SHALL abort compilation and return a diagnostic error identifying the module, node type, and missing field."*

**[PI-002] JSON-to-ASCII Translator**

> *Add to Section 2, Principle 1: "The JSON-to-ASCII compiler SHALL apply a second-pass reserved-character filter to all string-type fields. Reserved characters in IL-2 syntax (`{}[];="`) SHALL be stripped. This filter operates independently of any GUI-side sanitization."*

**[PI-003] Dynamic ID Generator**

> *Amend Section 2, Principle 4: "The compiler SHALL maintain a single monotonically increasing ID counter per compilation session. The counter SHALL initialize from max(all existing Index values in the target .Mission file) + 1. Per-module fixed offsets are explicitly prohibited. Each entity, MCU, and translator SHALL receive the next sequential integer from this counter."*

**[PI-004] Spatial Offset Engine**

> *Amend Section 2, Principle 3: "The remote coordinate zone SHALL be partitioned. Each imported module SHALL receive a unique offset block within the remote zone, incremented by 1000m on the Z-axis per module. The compiler SHALL track allocated blocks per session to prevent overlap."*

**[EL-001] Magazine Array MCU_Counter (Sequential Activation)**

> *Add to Section 5.2: "CONSTRAINT: The Magazine Array indexing MCU_Counter SHALL use Reset After Operation = TRUE and SHALL NOT be deactivated during the mission session. The wave_count parameter in the GUI SHALL be validated against the formula: `wave_count >= ceil(session_duration_minutes / estimated_average_sortie_duration_minutes)`. The compiler SHALL emit a warning if `wave_count < ceil(180 / ToS)`. The MCU_Counter SHALL NOT be reused across rotation cycles; each Magazine Array is a single-use sequential dispenser."*

**[EL-002] MCU_TR_Entity Proxy Binding**

> *Add to Section 4.2: "CONSTRAINT: No MCU or logic node SHALL reference an MCU_TR_Entity's output events (OnKilled, OnTookOff, OnDamaged) within 2 seconds of the associated aircraft's Activate trigger firing. The compiler SHALL insert a mandatory 2-second MCU_Timer between any Activate trigger and the first downstream consumer of the Entity proxy's event outputs."*

**[EL-003] MCU_TR_Entity Proxy Binding**

> *Add to Section 4.2: "The compiler SHALL execute a post-emission binding integrity check on every MCU_TR_Entity block. The check SHALL assert: (1) Entity.MisObjID == Aircraft.Index, (2) Aircraft.LinkTrId == Entity.Index, (3) Entity.MisObjID != Entity.Index. Failure of any assertion SHALL abort compilation."*

**[SM-001] Command Buffer (MCU_Deactivate clearing)**

> *Amend Section 4.1: "All [IN] signals SHALL route through a serialization timer before entering the Command Buffer. The state transition sequence SHALL be: MCU_Deactivate → MCU_Timer (50–100ms) → MCU_Activate. Each [IN] entry point within a module SHALL be assigned a unique delay value, staggered in 50ms increments (e.g., [IN]_Primary = 50ms, [IN]_Secondary = 100ms). Delays exceeding 200ms are prohibited to prevent AI command-vacuum drift. This serialization layer SHALL be automatically generated by the compiler based on the module's [IN] port count."*

**[SM-002] Time-on-Station (ToS) RTB Gate + Flight Leader Kill**

> *Add to Section 5.3: "All Command:RTB and Command:Waypoint nodes generated for ToS expiration SHALL Object Link to every aircraft in the flight, not exclusively the formation leader. Additionally, the leader's MCU_TR_Entity OnKilled output SHALL trigger a parallel garbage collection chain: ForceComplete → 30s Timer → Despawn, Object Linked to all wingmen. Area-based MCU_TR_CheckZone fallbacks SHALL NOT be used for garbage collection — they cause multiplayer desync and logic stutter (per Section 4.2). This ensures AI slot reclamation regardless of leader survival state at ToS expiration."*

**[SM-003] Command Buffer + Timer Pause Semantics**

> *Add to Section 4.1: "CONSTRAINT: MCU_Timer nodes used for time-gated logic (ToS, patrol duration) SHALL NOT be reused across Command Buffer state transitions. The compiler SHALL generate a discrete timer instance for each possible activation path. Previously triggered timers SHALL be permanently deactivated, not recycled. Each new [IN] activation SHALL engage a fresh, never-triggered timer."*

**[SM-004] Garbage Collection / Despawn Logic**

> *Amend Section 5.3: "Garbage collection SHALL implement dual-path activation. Both the MCU_TR_Entity OnKilled chain AND the ToS-triggered Despawn chain SHALL independently route to the Magazine Array's next-wave activation counter. Each path SHALL pass through a dedicated 1-count non-resetting MCU_Counter to prevent double-counting. The downstream wave-advance counter SHALL accept input from both paths."*

**[EC-001] Initialization Buffer (Master Core)**

> *Amend Section 5.1: "The Master Core initialization delay SHALL be a configurable parameter (default: 3 seconds, range: 3–10 seconds). The compiler SHALL emit a warning if the total count of Enabled=FALSE entities in the compiled output exceeds 200 and the initialization delay is set below 5 seconds."*

**[EC-002] Dependency Stub System**

> *Amend Section 3 (Dependency Management): "Stub MCU_Timers SHALL be allocated from a reserved ID range (900000–999999) that is excluded from the dynamic ID generator's allocation pool. The compiler SHALL emit a comment block at the top of the .Group file listing all generated stubs, their IDs, and the missing module references they are catching."*

**[EC-003] Spawner Trigger + Formation Hierarchy**

> *Add to Section 5.2: "CONSTRAINT: Magazine Array flights SHALL use the Activate/Deactivate (Enabled=FALSE → MCU_Activate) pattern exclusively. MCU_CMD_Spawn SHALL NOT be used for Magazine Array flights. The Spawner Trigger breaks Target Link formation hierarchies, preventing wingmen from following leader commands."*

**[EC-004] ~100 Active AI Unit Cap**

> *Add to Section 5.2: "The next-wave activation counter SHALL NOT fire until the previous wave's garbage collection chain has completed (either via Despawn confirmation or OnKilled). Time-based wave activation without GC gating is prohibited. The GUI SHALL calculate and display: `max_concurrent_AI = flight_size × max_simultaneous_waves`, and SHALL warn if this value exceeds 80."*

---

## 9. Falsifiability Conditions

**This analysis changes if:**

1. 1C Game Studios documents that MCU_Counter.Deactivate resets internal state (contradicting the manual's explicit statement at pg. 278). If so, EL-001 downgrades from CRITICAL to LOW and the Magazine Array can use a single recyclable counter.

2. Engine testing reveals that MCU_TR_Entity binding resolves against the mission file declaration rather than 3D instantiation. If so, EL-002 downgrades from HIGH to LOW and the 2-second activation delay becomes unnecessary.

3. The DServer's MCU processing order within a single tick is deterministic (e.g., sorted by Index). If so, SM-001 downgrades from HIGH to MEDIUM — serialization timers become optional if Index ordering can be guaranteed by the compiler.

4. The ~100 AI unit cap has been raised in a recent engine patch. If so, EC-004's warning threshold must be recalibrated to the new ceiling.

5. MCU_CMD_Spawn is patched to preserve Target Link formation hierarchies. If so, EC-003 is eliminated entirely, the Magazine Array gains Spawn as a viable option, and the proposed Section 5.2 amendment (Element 1) should be re-evaluated.

6. CheckZone polling overhead is reduced to negligible cost in a recent engine update. If so, the area-based fallback for Entity link resilience (Element 5) becomes viable and SM-002's mitigation gains an alternative path.
