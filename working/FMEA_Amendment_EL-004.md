# FMEA Amendment — Proposed Constraint EL-004

**Status:** DRAFT — For human review and approval at next project gate
**Proposed by:** Claude Sonnet 4.6 (Phase 0.4 session)
**Date drafted:** 2026-03-19
**Review authority:** Project owner (Pablo Larson)
**Activation:** This amendment does NOT become active until the project owner explicitly accepts it.

---

## Gap Summary

The current FMEA (Rev 2) has no constraint covering minimum physical separation distances between 3D objects (aircraft, vehicles) pre-placed in their deactivated "sleep" state.

**Distinct from PI-004:** PI-004 concerns MCU node icon spacing in the Mission Editor's 2D logic view — it prevents editor UI confusion. MCUs are abstract logic nodes with no physical collision volume. Aircraft are 3D physics objects with wingspan, fuselage, and landing gear geometry that occupy real world-space. They can collide.

**The gap:** The compiler emits `XPos/YPos/ZPos` coordinates for deactivated flights without any constraint on their mutual separation. On activation, aircraft that are too close together will collide. This failure is silent until in-game testing because the Mission Editor displays MCU logic nodes, not 3D collision volumes.

---

## Proposed Constraint

**ID:** EL-004
**Severity:** HIGH
**Component:** Compiler spatial placement (`src/mmf/compiler/spatial_offset.py` — or a dedicated `src/mmf/compiler/placement_validator.py`)

---

## Section 7 Matrix Row

Insert into the FMEA matrix table in `MMF_FMEA_Report_v2.md` Section 7, after the EL-003 row:

| ID | Component | Failure Mode | Severity | Engine Effect | Mitigation | Spec Amendment |
|---|---|---|---|---|---|---|
| **EL-004** | Compiler Spatial Placement | Magazine Array compiler places deactivated flights at coordinates that are too close together or overlapping. On activation, aircraft collide — mid-air for airstarts, on the runway for ground starts. | **HIGH** | Aircraft collision on activation is not a DServer crash but produces unflyable missions that cannot be debugged without in-game testing. Mid-air collisions kill players immediately; runway pileups can destroy multiple aircraft and block the airfield for the session's duration. The failure is silent in the Mission Editor because the editor renders MCU logic nodes (point icons), not 3D aircraft collision volumes. A compiler that passes all logical checks can still produce an unplayable mission. | Compiler SHALL enforce minimum separation distances between pre-placed flight spawn coordinates. Ground-start placements SHALL be validated against airfield coordinates and runway geometry from the Phase 4 map database. Airstart placements SHALL enforce an altitude floor and vertical separation between stacked flights. Compiler SHALL warn when deactivated flight density in a spatial region exceeds a configurable threshold. | YES — See §8 |

---

## Section 8 Spec Amendment Language

Insert into `MMF_FMEA_Report_v2.md` Section 8 (Required Specification Amendments), after the EL-003 block:

**[EL-004] Compiler Spatial Placement**

> *Add to Section 5.2: "CONSTRAINT: The compiler SHALL enforce minimum physical separation between pre-placed deactivated flight spawn coordinates. The following rules apply:*
>
> *1. AIRSTART SEPARATION: The minimum horizontal separation between any two pre-placed aircraft spawn points SHALL be 500 meters. The minimum vertical separation between stacked airstarts SHALL be 200 meters. The altitude floor for all airstarts SHALL be at least 500 meters AGL unless the map database specifies an airfield elevation that requires a lower spawn altitude.*
>
> *2. GROUND START SEPARATION: Ground-start spawn coordinates SHALL be validated against the Phase 4 map database (airfield data). The compiler SHALL verify that: (a) the spawn point falls within the airfield's known boundary polygon, (b) minimum runway clearance of 150 meters is maintained from the runway centerline, and (c) no two ground-start spawn points for different flights are within 100 meters of each other.*
>
> *3. DENSITY WARNING: The compiler SHALL calculate the maximum concurrent deactivated flight density within any 1km² spatial region of the remote coordinate zone. If deactivated flight density exceeds 5 flights per 1km², the compiler SHALL emit a HIGH warning identifying the region coordinates and flight count.*
>
> *4. CONFIGURATION: Minimum separation distances SHALL be configurable compiler parameters with the above values as defaults. Mission designers running high-density scenarios MAY reduce these values with an explicit configuration override, which the compiler SHALL log in the output manifest.*
>
> *The compiler SHALL NOT block compilation for EL-004 violations — they generate warnings, not errors. This preserves the ability to compile specialist missions that intentionally place aircraft in formation from ground start. Block-on-warning mode may be enabled via compiler option."*

---

## Affected Phases

| Phase | Impact |
|---|---|
| **Phase 1 — Compiler** | Primary enforcement point. `spatial_offset.py` (or new `placement_validator.py`) must implement the four rules above. Airstart and density checks are compiler-only. Ground-start validation requires the Phase 4 map database. |
| **Phase 2 — Module Reverse Engineer (MRE)** | MRE must detect existing placement patterns in reference missions and classify them as compliant or non-compliant. Non-compliant patterns should be flagged in MRE output as EL-004 anomalies. |
| **Phase 4 — Map Data Extractor** | Airfield boundary polygons and runway centerline data extracted in Phase 4 feed directly into the compiler's ground-start validation (Rule 2). The map database schema must include these fields or Phase 4 output cannot support EL-004 enforcement. |

---

## Falsifiability Condition

This constraint becomes unnecessary or must be recalibrated if:

1. IL-2 engine testing reveals that deactivated (Enabled=FALSE) aircraft do not have active collision volumes — i.e., they occupy no physical space until activated. If true, separation is only required between *simultaneously activated* aircraft, not between pre-placed deactivated flights. EL-004 would then apply only to the activation sequence, not the placement coordinates.

2. The minimum safe distances are determined empirically to differ significantly from the defaults proposed above. The values in this amendment are engineering estimates based on typical IL-2 aircraft dimensions (wingspan ~12–15m, fuselage ~9–12m) with substantial safety margins. In-game testing must validate them.

---

## Relationship to Existing Constraints

| Existing Constraint | Relationship |
|---|---|
| PI-004 (MCU icon spatial offset, 1000m Z-increment) | Complementary but distinct. PI-004 = MCU logic node editor spacing (abstract). EL-004 = 3D physics object collision volumes (physical). Neither implies the other. |
| EC-001 (Init buffer, deactivated entity count warning >200) | Related context: if a mission has >200 deactivated entities (triggering EC-001 warning), it likely also has the spatial density that triggers EL-004 warnings. The two constraints are co-activated by the same mission architecture but enforce different physical properties. |
| EC-003 (Spawn prohibition) | EC-003 enforces Activate/Deactivate over Spawn/Delete. EL-004 assumes EC-003 compliance — it validates placement coordinates for deactivated (Enabled=FALSE) aircraft. A mission using MCU_CMD_Spawn (EC-003 violation) bypasses EL-004's placement check entirely. |
