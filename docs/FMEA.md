# Failure Mode and Effects Analysis (FMEA)

**IL-2 Great Battles — Modular Mission Orchestrator**

> **DRAFT — S/O/D scores derived from qualitative severity labels. Awaiting calibration by Project Owner.**
>
> Full analytical narrative and amendment review: `docs/MMF_FMEA_Report_v2.md`

## Risk Priority Legend

- **RPN** = Severity × Occurrence × Detection
- **Action threshold:** RPN ≥ 100 requires a mitigation plan before proceeding.

## Register

| ID | Failure Mode | Potential Effect | S | O | D | RPN | Mitigation | Status | Owner |
|---|---|---|---|---|---|---|---|---|---|
| PI-001 | Null or empty `Targets[]` array passed for MCU_CMD_AttackArea | DServer throws unhandled null reference on mission load. Server halts loading cycle and drops all connected clients. | 10 | 7 | 3 | 210 | Compiler MUST validate all required MCU fields against a schema whitelist before ASCII emission. Any MCU_CMD node with an empty `Targets[]` or `Objects[]` array must halt compilation with a named error. | Open | Project Owner |
| PI-002 | String field containing unescaped reserved characters (`{}[];=`) injected into Name or Desc field | IL-2 ASCII parser treats semicolons as field terminators and braces as block delimiters. Injection truncates or corrupts the containing MCU block, causing silent data loss or cascade parse failure. | 8 | 5 | 4 | 160 | Compiler string sanitizer must strip or escape all reserved ASCII syntax characters from user-supplied string fields. GUI export validator performs first-pass; compiler enforces second-pass whitelist. | Open | Project Owner |
| PI-003 | ID namespace collision when importing the same module 10+ times consecutively | Duplicate Index values cause engine to silently overwrite entities. Target Links and Object Links bind to wrong objects. Worst case: DServer crashes on cyclic link resolution. | 10 | 7 | 3 | 210 | ID generator MUST use a monotonically increasing global counter. Each compilation session initializes from max(existing Index) + 1. Per-module offsets explicitly prohibited. | Open | Project Owner |
| PI-004 | Two modules compiled in same session receive overlapping remote coordinates | Overlapping MCU icons in editor (usability failure). If CheckZone nodes overlap, cross-module logic corruption via false-positive detection. | 5 | 4 | 5 | 100 | Spatial offset function must increment remote coordinate block per module import. 1000m Z-axis increment per module. | Open | AI Session |
| EL-001 | Magazine Array MCU_Counter internal state persists through Deactivate/Activate cycle | Counter permanently exhausted after first full cycle. For resetting counter, deactivation during mid-count creates phantom fire on reactivation. Manual pg. 278 confirms. | 10 | 7 | 3 | 210 | Magazine Array counter SHALL use Reset After Operation = TRUE and SHALL NOT be deactivated. Wave count validated: `wave_count >= ceil(session_duration / avg_sortie_duration)`. Single-use sequential dispenser. | Open | Project Owner |
| EL-002 | During mass activation, Entity proxy binds before aircraft 3D instantiation completes | Entity binding silently fails. OnKilled/OnTookOff events never fire. Flight becomes a ghost — consuming AI slots with no cleanup path. | 8 | 5 | 4 | 160 | Mandatory 2-second MCU_Timer between MCU_Activate and first downstream Entity proxy consumer. Mirrors manual guidance (pg. 274). | Open | Project Owner |
| EL-003 | Entity MisObjID/LinkTrId two-way binding emitted with swapped values (self-reference) | Engine creates self-referential binding loop. Entity listens to itself. Aircraft is unbound — total state blindness for that flight. Silent logic failure. | 10 | 7 | 3 | 210 | Post-emission binding integrity check: `Entity.MisObjID == Aircraft.Index`, `Aircraft.LinkTrId == Entity.Index`, `Entity.MisObjID != Entity.Index`. Assertion against final ASCII output. | Open | Project Owner |
| SM-001 | Two modules fire conflicting [IN] triggers within same server tick | Non-deterministic command interleaving. Deactivate from Module B clears state Module A just set. | 8 | 5 | 4 | 160 | Command Buffer serialization: Deactivate → staggered Timer (50-100ms) → Activate. Each [IN] port gets unique delay staggered in 50ms increments. Max 200ms. | Open | Project Owner |
| SM-002 | Flight leader killed at ToS expiration — RTB command has no valid Object Link target | Wingmen enter permanent idle state. No RTB, no garbage collection. AI slots consumed indefinitely. | 8 | 5 | 4 | 160 | RTB commands Object Link to ALL aircraft in flight. Leader OnKilled triggers parallel chain: ForceComplete → 30s Timer → Despawn, Object Linked to all wingmen. No CheckZone fallbacks. | Open | Project Owner |
| SM-003 | Deactivating mid-countdown timer pauses instead of resetting. Reactivation resumes from paused position. | ToS timer paused at 8/10 minutes fires after only 2 more minutes on reactivation. Premature RTB or premature garbage collection. Manual pg. 283 confirms. | 8 | 5 | 4 | 160 | Timer nodes SHALL NOT be reused across state transitions. Each [IN] activation engages a fresh timer instance. Previously triggered timers permanently deactivated. | Open | Project Owner |
| SM-004 | Despawn fires on already-destroyed flight. If Despawn is sole next-wave trigger, early kills stall Magazine permanently. | Despawning dead object is no-op (no crash). But Magazine Array stalls — no more waves activate. | 3 | 3 | 3 | 27 | Dual-path activation: both OnKilled and Despawn independently increment next-wave counter. Each path through dedicated 1-count non-resetting sub-counter to prevent double-counting. | Open | AI Session |
| EC-001 | Master Core 3-second init delay insufficient on heavily loaded DServer | Activate triggers fire before deactivated flights registered in physics engine. Flights remain permanently in Sleep state. | 5 | 4 | 5 | 100 | Init delay configurable via GUI (default: 3s, range: 3-10s). Compiler warning if deactivated entity count > 200 and delay < 5s. | Open | AI Session |
| EC-002 | Dependency stub timer fires immediately, collides with legitimate MCUs added later | Stub intercepts signal meant for real module. Non-deterministic behavior. | 5 | 4 | 5 | 100 | Stubs occupy reserved ID range (900000-999999) excluded from dynamic ID generator. Compiler emits manifest comment block listing all stubs. | Open | AI Session |
| EC-003 | MCU_CMD_Spawn used for Magazine Array flights breaks wingman Target Link hierarchies | Spawned wingmen ignore leader commands (Manual pg. 282). No coordinated combat, no formation integrity. AI effectiveness collapses. | 8 | 5 | 4 | 160 | Compiler MUST use Activate/Deactivate exclusively for Magazine Array flights. MCU_CMD_Spawn explicitly prohibited. | Open | Project Owner |
| EC-004 | Magazine Array activates new wave before GC despawns previous wave. AI count exceeds ~100 during overlap. | Non-linear tickrate degradation. DServer SPS drops below physics threshold — desync, rubber-banding, instability. | 8 | 5 | 4 | 160 | Next-wave activation MUST be gated behind GC confirmation. Time-based activation without GC gate prohibited. GUI displays worst-case concurrent AI count, warns if > 80. | Open | Project Owner |

## Revision History

| Date | Change | Author | Amendment # |
|---|---|---|---|
| March 18, 2026 | Initial FMEA register generated from MMF_FMEA_Report_v2.md. S/O/D scores derived from qualitative severity labels (DRAFT). | Claude Opus 4.6 | — |
| March 18, 2026 | FMEA Report v2: evaluated 2 proposed amendments. Accepted Element 2 (2s Entity delay), accepted Element 4 with modification (Command Buffer 50-100ms), rejected Elements 1, 3, 5. | Claude Opus 4.6 | — |
