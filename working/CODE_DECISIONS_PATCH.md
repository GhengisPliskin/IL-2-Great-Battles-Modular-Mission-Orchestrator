# Code Decision Log — Phase 0.4 Patch

**Session:** Phase 0.4 — MCU Type Catalog
**Date:** 2026-03-19
**Author:** Claude Sonnet 4.6
**Review:** Gemini Pro (triage by Claude Opus 4.6)
**Status:** READY TO MERGE into `CODE_DECISION_LOG.md`

Copy the four entries below verbatim into the appropriate section of `CODE_DECISION_LOG.md`.

---

## New Entries (D-19 through D-22)

### D-19

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-19 | Extended catalog entry schema with `child_blocks` key — shallow mapping only. Records presence and occurrence frequency of child block type names (OnEvents, OnReports, SubtitleInfo, Boundary) per MCU type. Full recursive child block internals deferred to Phase 1. | Maps event binding architecture for PI-001 validator and Module Reverse Engineer without crossing the Phase 0.4 boundary into enforcement logic. Official R2 schema (Session 0.4, Requirement R2) did not include this key — this is an explicit scope expansion. | If PI-001 or MRE expects child block field-level schemas from the catalog: those don't exist yet. Phase 1 must build recursive child block validation independently. If a new child block type appears in expanded corpus: re-run `build_mcu_catalog.py` — it discovers child types dynamically, not from a hardcoded list. |

### D-20

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-20 | Required/optional field split uses strict 100% set intersection with an anomaly report (`logs/Corpus_Anomalies.md`) for fields at >90% but <100% occurrence. No statistical threshold. Report records MCU type, field name, occurrence percentage, and provenance paths of files missing the field. | A single malformed corpus file silently downgrades a universally required field (e.g., `Index`) to optional under pure intersection. The anomaly report surfaces this for human review without automating the judgment. Provenance paths allow immediate cross-reference against corpus tiers (verified-correct vs. unverified vs. known-faulty). | If a field known to be required (e.g., `Index`, `Targets`) appears in `optional_fields`: check `logs/Corpus_Anomalies.md` first — it will name the exact corpus files missing that field. Verify whether those files are known-faulty or represent a legitimate schema variant. If anomaly report is empty but optional list is wrong: the >90% threshold may need adjustment, or the corpus file count is too low for the threshold to be meaningful. |

### D-21

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-21 | `field_types` resolves iterable inner types: `list[int]`, `list[float]`, `list[str]`. Resolution inspects all elements across all corpus instances of that field. Mixed inner types resolve to the more permissive type (int+float → `list[float]`). Empty lists resolve to `list[int]` (default for linking ID fields). | PI-001 validator needs typed list validation for `Targets` and `Objects` fields, which hold integer linking IDs. Storing untyped `list` defers this requirement to Phase 1 and forces a catalog rebuild. The permissive upcasting rule mirrors D-07's float-over-int precedent from the parser. | If a list field contains mixed types that aren't int/float (e.g., strings mixed with ints): the resolution logic needs a third branch. Check what the actual corpus values are — this likely indicates a parser bug upstream (D-07 coercion cascade not handling that value). If empty list default (`list[int]`) is wrong for a specific field: override it in the FMEA overlay (Phase 4) as a per-field annotation. |

### D-22

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-22 | Added EL-002 to the FMEA overlay for `MCU_TR_Entity`. Session 0.4 R4 lists three constraints (EL-001, EL-003, SM-003); EL-002 is a scope expansion. Constraint text: Entity proxy binding fails silently if aircraft not yet physically instantiated — a 2-second post-Activate delay must precede any logic consuming the Entity's output events. | EL-002 is a HIGH-severity FMEA item that directly describes `MCU_TR_Entity` behavior. Omitting it from the catalog while including EL-003 (also `MCU_TR_Entity`) creates an incomplete picture of the same MCU type's failure modes. The catalog is the source of truth for PI-001 — if EL-002 isn't annotated here, the compiler has no reference for the temporal binding dependency. | If Phase 1 compiler omits the 2-second post-Activate timer: check whether the catalog entry for `MCU_TR_Entity` includes the EL-002 constraint string. If it's missing, the compiler author had no signal that this constraint existed. |

---

## Downstream Phase Coupling

These decisions affect the following downstream phases:

| Decision | Affected Phase | Impact |
|---|---|---|
| D-19 | Phase 1 (PI-001 validator, MRE) | PI-001 has `child_blocks` available as shallow reference. Full recursive child schemas must be built independently in Phase 1. |
| D-20 | Phase 0.4 re-runs (corpus expansion) | Re-run `build_mcu_catalog.py` when corpus is expanded. Review new anomaly entries before accepting updated catalog. |
| D-21 | Phase 1 (PI-001 validator) | Typed list strings (`list[int]`) are the canonical field type representation. PI-001 validation logic must parse these strings. |
| D-22 | Phase 1 (entity_proxy.py, command_buffer.py) | EL-002 is now in catalog. Phase 1 compiler must implement the 2-second post-Activate delay for MCU_TR_Entity consumers. |
