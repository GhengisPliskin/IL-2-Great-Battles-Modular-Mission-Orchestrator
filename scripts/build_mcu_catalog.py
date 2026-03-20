"""
MODULE:  build_mcu_catalog
PURPOSE: Corpus-driven generator and validator for data/mcu_catalog.json.
         Walks all .Group and .Mission files in the Phase 0.1 corpus, extracts
         every MCU type and its fields using the Phase 0.2 parser, computes
         required/optional splits, resolves typed list field types, detects
         duplicate-key fields (multi_fields, D-23), overlays FMEA constraint
         annotations, validates against the catalog meta-schema, and writes the
         finished catalog to data/mcu_catalog.json.
         Also writes logs/Corpus_Anomalies.md for human review of edge-case
         fields at >90% but <100% corpus occurrence and cardinality diagnostics
         for fields with max duplicate-key occurrences > 1.
         Belongs to: Shared Foundation — data layer (Phase 0 tooling).
FMEA:    EL-001 (MCU_Counter annotation), EL-002 (MCU_TR_Entity annotation),
         EL-003 (MCU_TR_Entity annotation), SM-003 (MCU_Timer annotation).
PHASE:   Phase 0.4
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from project root or scripts/ directory.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from mmf.parser.deserializer import parse_file  # noqa: E402  (after path fix)

# ---------------------------------------------------------------------------
# Project-relative paths
# ---------------------------------------------------------------------------
CORPUS_DIR = _PROJECT_ROOT / "tests" / "fixtures" / "il2_files"
CATALOG_OUTPUT = _PROJECT_ROOT / "data" / "mcu_catalog.json"
META_SCHEMA_PATH = _PROJECT_ROOT / "data" / "schemas" / "mcu_catalog_meta_schema.json"
ANOMALY_LOG_PATH = _PROJECT_ROOT / "logs" / "Corpus_Anomalies.md"

# ---------------------------------------------------------------------------
# FMEA constraint overlay — strings only, no enforcement predicates.
# Catalog documents; compiler enforces (see review triage 2026-03-19).
# Adding EL-002 is a scope expansion beyond Session 0.4 R4 — see D-22.
# ---------------------------------------------------------------------------
FMEA_OVERLAYS = {
    "MCU_Counter": [
        "EL-001: Counter state persists through Deactivate — does NOT reset (C-014). "
        "Reset (Dropcount=0, Counter>=1) required in Magazine Array context to prevent "
        "counter saturation across respawn cycles. Counter must never be deactivated.",
    ],
    "MCU_TR_Entity": [
        "EL-002: Entity proxy binding fails silently if aircraft not yet physically "
        "instantiated. A 2-second post-Activate delay must precede any logic consuming "
        "the Entity's output events.",
        "EL-003: Two-way binding integrity: MisObjID on this MCU must equal the Index "
        "of the linked game object; LinkTrId on the game object must equal this MCU's "
        "Index. Post-emission assertion required.",
    ],
    "MCU_Timer": [
        "SM-003: MCU_Timer.Deactivate pauses the timer; reactivation resumes from the "
        "paused position (does NOT reset). Timer reuse across state transitions is "
        "prohibited — allocate a fresh timer per logical state.",
    ],
}

# ---------------------------------------------------------------------------
# Anomaly detection threshold — fields above this rate but below 100%
# trigger a human-review entry in Corpus_Anomalies.md.
# WHY NOT use >99% as a statistical required threshold: [D-20] — automating
# the judgment hides edge cases instead of surfacing them. The anomaly report
# is the correct mechanism; the human decides whether the missing file is a
# known-faulty corpus member or a legitimate optional variant.
# ---------------------------------------------------------------------------
ANOMALY_THRESHOLD = 0.90


# ===========================================================================
# Data collection
# ===========================================================================

def collect_mcu_instances(corpus_dir: Path) -> tuple[dict, list[str]]:
    """
    WHAT:    Walks all .Group and .Mission files in corpus_dir and collects
             one raw record per MCU block instance found. Returns a dict keyed
             by MCU type mapping to a list of instance records, plus a list of
             successfully consumed file paths.
    WHY:     Centralises all corpus I/O so the rest of the pipeline works on
             clean in-memory data structures. Provenance (source_file) is
             captured here to support anomaly log generation downstream.
    ARGS:
        corpus_dir (Path): Root directory containing .Group and .Mission files.
    RETURNS:
        tuple: (instances_by_type, consumed_files)
               instances_by_type: dict[str, list[dict]] — each inner dict has
                   'fields': list[(str, any)], 'children': list[dict],
                   'source_file': str
               consumed_files: list[str] of paths successfully parsed.
    FMEA:    None — data collection only; no constraint enforcement here.
    """
    instances_by_type: dict[str, list[dict]] = defaultdict(list)
    consumed_files: list[str] = []

    # --- WALK THE CORPUS ---
    # Recursively visit every .Group and .Mission file. parse_file() handles
    # encoding detection (utf-8-sig → utf-8 → cp1252 → latin-1) so we don't
    # need to manage encoding here.
    for root, _dirs, files in os.walk(corpus_dir):
        for fname in sorted(files):
            if not fname.endswith((".Group", ".Mission")):
                continue
            fpath = os.path.join(root, fname)
            try:
                result = parse_file(fpath)
                consumed_files.append(fpath)
                _collect_from_blocks(result.get("blocks", []), fpath, instances_by_type)
            except Exception as exc:
                print(f"  [WARN] Failed to parse {fpath}: {exc}", file=sys.stderr)

    return dict(instances_by_type), consumed_files


def _count_field_occurrences_per_instance(fields: list) -> dict[str, int]:
    """
    WHAT:    Counts how many times each key appears in a single MCU block's
             fields list. Returns a dict of {field_name: occurrence_count}.
    WHY:     The deserializer preserves duplicate keys as separate list entries
             (D-05). compute_field_sets() uses set() which collapses them to
             one entry per key, losing cardinality information. This function
             captures per-instance key counts so compute_multi_fields() can
             detect fields that appear more than once in any single block (D-23).
    ARGS:
        fields (list): List of (key, value) tuples from a parsed MCU block.
    RETURNS:
        dict[str, int]: e.g. {'Country': 3, 'Index': 1, 'Name': 1}
    FMEA:    None
    """
    counts: dict[str, int] = defaultdict(int)
    for k, _v in fields:
        counts[k] += 1
    return dict(counts)


def _collect_from_blocks(
    blocks: list,
    source_file: str,
    instances_by_type: dict,
) -> None:
    """
    WHAT:    Recursively visits every block in a parsed file. Appends a record
             to instances_by_type for each block whose type starts with 'MCU_'.
    WHY:     MCU blocks can be nested inside Group blocks at arbitrary depth,
             so a flat single-pass scan would miss nested MCUs. Recursion
             guarantees full coverage regardless of nesting depth.
    ARGS:
        blocks (list): List of parsed block dicts from the deserializer.
        source_file (str): Absolute path of the originating file (provenance).
        instances_by_type (dict): Accumulator — mutated in place.
    RETURNS:
        None
    FMEA:    None
    """
    for block in blocks:
        btype = block.get("type", "")
        if btype.startswith("MCU_"):
            fields = block.get("fields", [])
            instances_by_type[btype].append(
                {
                    "fields": fields,
                    "children": block.get("children", []),
                    "source_file": source_file,
                    # Per-instance field occurrence counts for D-23 cardinality tracking.
                    # Captured here while the original fields list is in scope.
                    "field_instance_counts": _count_field_occurrences_per_instance(fields),
                }
            )
        # --- RECURSE INTO CHILDREN ---
        # Group blocks and other container blocks hold MCU children. Recurse
        # unconditionally so nested MCUs are never missed.
        child_list = block.get("children", [])
        if child_list:
            _collect_from_blocks(child_list, source_file, instances_by_type)


# ===========================================================================
# Required / optional field split
# ===========================================================================

def compute_field_sets(instances: list[dict]) -> tuple[set, set, dict]:
    """
    WHAT:    Given all corpus instances of one MCU type, computes the set of
             required fields (present in 100% of instances), optional fields
             (present in <100% of instances), and per-field occurrence stats.
    WHY:     The 100% strict intersection rule ensures a field is only marked
             required if it is truly universal. Near-universal fields (>90%)
             are surfaced in the anomaly log for human review rather than
             being silently promoted or demoted (D-20).
    ARGS:
        instances (list[dict]): List of MCU instance records from collect_mcu_instances.
    RETURNS:
        tuple: (required_fields, optional_fields, field_stats)
               required_fields: set[str]
               optional_fields: set[str]
               field_stats: dict[str, dict] with keys 'count', 'total', 'pct',
                            'missing_in': list[str] of source_file paths
    FMEA:    None
    """
    if not instances:
        return set(), set(), {}

    total = len(instances)

    # --- COUNT FIELD OCCURRENCES WITH PROVENANCE ---
    # Track which source files are missing each field so anomaly log entries
    # have actionable provenance data (D-20).
    field_count: dict[str, int] = defaultdict(int)
    field_missing: dict[str, list[str]] = defaultdict(list)

    for inst in instances:
        present = {k for k, _v in inst["fields"]}
        for k in present:
            field_count[k] += 1

    # Compute missing-in lists after full count
    all_fields = set(field_count.keys())
    for inst in instances:
        present = {k for k, _v in inst["fields"]}
        for field in all_fields:
            if field not in present:
                field_missing[field].append(inst["source_file"])

    # --- SPLIT INTO REQUIRED / OPTIONAL ---
    # WHY NOT use >99% statistical threshold: [D-20] — see module-level note.
    required: set[str] = set()
    optional: set[str] = set()
    field_stats: dict[str, dict] = {}

    for field, count in field_count.items():
        pct = count / total
        field_stats[field] = {
            "count": count,
            "total": total,
            "pct": pct,
            "missing_in": field_missing.get(field, []),
        }
        if pct == 1.0:
            required.add(field)
        else:
            optional.add(field)

    return required, optional, field_stats


# ===========================================================================
# Multi-field (duplicate key) detection — D-23
# ===========================================================================

def compute_multi_fields(instances: list[dict]) -> tuple[list[str], dict[str, dict]]:
    """
    WHAT:    Identifies fields that appear more than once in any single corpus
             instance of this MCU type. Returns a sorted list of multi-field
             names and a cardinality stats dict for the anomaly log.
    WHY:     compute_field_sets() uses set() over field keys, collapsing duplicate
             keys (D-05 parser behaviour) to a single entry. Without multi_fields,
             PI-001 has no signal that a field like Country is a collection field
             that may appear 2–5 times in one block (D-23). The catalog entry
             exports only the boolean list; raw max counts go to the anomaly log
             because the corpus ceiling is a sampling artifact — IL-2 treats
             duplicate keys as logically unbounded (D-23).
    ARGS:
        instances (list[dict]): List of MCU instance records from collect_mcu_instances.
                                Each record must have 'field_instance_counts' populated
                                by _count_field_occurrences_per_instance().
    RETURNS:
        tuple: (multi_field_names, cardinality_stats)
               multi_field_names: sorted list[str] — fields with max count > 1
               cardinality_stats: dict[str, dict] — {field_name: {max_count, files_with_duplicates}}
                                  for anomaly log section only; NOT exported to catalog.
    FMEA:    None
    """
    # WHY NOT export raw max counts to catalog: [D-23] — corpus ceiling is a
    # sampling artifact; IL-2 treats duplicate keys as logically unbounded.
    # Structural boolean list (present/absent in multi_fields) is the correct signal.
    field_max: dict[str, int] = defaultdict(int)
    field_dup_files: dict[str, list[str]] = defaultdict(list)

    for inst in instances:
        for field, count in inst.get("field_instance_counts", {}).items():
            if count > field_max[field]:
                field_max[field] = count
            if count > 1:
                field_dup_files[field].append(inst["source_file"])

    multi_field_names = sorted(f for f, max_c in field_max.items() if max_c > 1)
    cardinality_stats = {
        f: {
            "max_count": field_max[f],
            "files_with_duplicates": sorted(set(field_dup_files[f])),
        }
        for f in multi_field_names
    }
    return multi_field_names, cardinality_stats


# ===========================================================================
# Type resolution
# ===========================================================================

def resolve_field_types(instances: list[dict]) -> dict[str, str]:
    """
    WHAT:    Inspects all field values across all instances of one MCU type
             and returns a dict mapping field_name → type_string.
    WHY:     PI-001 validator needs typed list validation for Targets and
             Objects (which hold integer linking IDs). Storing untyped 'list'
             defers this to Phase 1 and forces a catalog rebuild (D-21).
             Scalar types follow the parser's float-over-int precedence (D-07).
    ARGS:
        instances (list[dict]): List of MCU instance records.
    RETURNS:
        dict[str, str]: e.g. {'Index': 'int', 'Targets': 'list[int]', ...}
    FMEA:    None
    """
    # --- ACCUMULATE SEEN TYPES PER FIELD ---
    # For lists: collect the set of inner element types seen across all values.
    # For scalars: collect the set of Python type names seen.
    scalar_types: dict[str, set[str]] = defaultdict(set)
    list_inner_types: dict[str, set[str]] = defaultdict(set)
    is_list_field: set[str] = set()

    for inst in instances:
        for k, v in inst["fields"]:
            if isinstance(v, list):
                is_list_field.add(k)
                for elem in v:
                    list_inner_types[k].add(type(elem).__name__)
            else:
                scalar_types[k].add(type(v).__name__)

    result: dict[str, str] = {}
    all_fields = set(scalar_types.keys()) | is_list_field

    for field in all_fields:
        if field in is_list_field:
            result[field] = _resolve_list_type(field, list_inner_types.get(field, set()))
        else:
            result[field] = _resolve_scalar_type(scalar_types.get(field, set()))

    return result


def _resolve_list_type(field_name: str, inner_types: set[str]) -> str:
    """
    WHAT:    Resolves a set of observed inner element type names to a typed
             list string such as 'list[int]', 'list[float]', or 'list[str]'.
    WHY:     Inner type resolution is cheap now and expensive to retrofit once
             PI-001 starts consuming the catalog (D-21). Empty inner_types
             defaults to 'list[int]' because all linking ID fields (Targets,
             Objects, Coalitions) are integer arrays — an empty list in corpus
             should not downgrade them to untyped 'list'.
    ARGS:
        field_name (str): Field name (used only for debugging context).
        inner_types (set[str]): Python type names observed in list elements.
    RETURNS:
        str: One of 'list[int]', 'list[float]', 'list[str]', 'list'.
    FMEA:    None
    """
    # WHY NOT 'list' (untyped): [D-21] — PI-001 needs element-level type info
    # for Targets/Objects validation. Untyped list is the last-resort fallback.
    if not inner_types:
        # Empty list observed only — default to list[int] for ID linking fields
        return "list[int]"
    if "str" in inner_types and len(inner_types) == 1:
        return "list[str]"
    if "float" in inner_types:
        # int + float → list[float] mirrors D-07 float-over-int precedence
        return "list[float]"
    if "int" in inner_types:
        return "list[int]"
    # Fallback: mixed non-numeric types — surface as generic list
    return "list"


def _resolve_scalar_type(seen_types: set[str]) -> str:
    """
    WHAT:    Resolves a set of observed Python type names to a single type
             string: 'float', 'int', 'str', or 'str' as fallback.
    WHY:     Mirrors the parser's D-07 coercion cascade. When a field shows
             both int and float across different corpus instances, the more
             permissive float wins so the PI-001 validator doesn't reject
             valid integer values stored in float fields.
    ARGS:
        seen_types (set[str]): Python type names observed for this scalar field.
    RETURNS:
        str: One of 'float', 'int', 'str'.
    FMEA:    None
    """
    if "float" in seen_types:
        return "float"
    if "int" in seen_types:
        return "int"
    if "bool" in seen_types:
        # IL-2 booleans are serialised as 0/1 integers; treat as int
        return "int"
    return "str"


# ===========================================================================
# Child block mapping
# ===========================================================================

def collect_child_blocks(instances: list[dict]) -> dict[str, int]:
    """
    WHAT:    Counts how many times each child block type appears across all
             corpus instances of one MCU type. Returns a shallow occurrence map.
    WHY:     Documents the event binding architecture (OnEvents/OnReports,
             SubtitleInfo, Boundary) for PI-001 and MRE without crossing into
             full recursive child field schemas, which are Phase 1 scope (D-19).
    ARGS:
        instances (list[dict]): List of MCU instance records.
    RETURNS:
        dict[str, int]: e.g. {'OnEvents': 47, 'SubtitleInfo': 12}
    FMEA:    None
    """
    counts: dict[str, int] = defaultdict(int)

    # --- COUNT DIRECT CHILD BLOCK OCCURRENCES ---
    # Only direct children are counted (shallow). Deeper nesting (e.g. OnEvent
    # inside OnEvents) is deferred to Phase 1 recursive schema work (D-19).
    for inst in instances:
        for child in inst.get("children", []):
            child_type = child.get("type", "")
            if child_type:
                counts[child_type] += 1

    return dict(counts)


# ===========================================================================
# Anomaly log
# ===========================================================================

def build_anomaly_log(
    all_field_stats: dict[str, dict[str, dict]],
    threshold: float = ANOMALY_THRESHOLD,
) -> list[dict]:
    """
    WHAT:    Collects all fields that appear in >threshold but <100% of corpus
             instances for their MCU type. Returns a list of anomaly records
             ready to be rendered into Corpus_Anomalies.md.
    WHY:     A single malformed corpus file silently downgrades a universally
             required field (e.g. 'Index') to optional under pure intersection.
             The anomaly log surfaces this for human review with provenance
             paths, making the corpus triage decision explicit (D-20).
    ARGS:
        all_field_stats (dict): {mcu_type: {field_name: {count, total, pct, missing_in}}}
        threshold (float): Lower bound for anomaly detection (exclusive). Default 0.90.
    RETURNS:
        list[dict]: Each record has keys: mcu_type, field, pct, count, total, missing_in.
    FMEA:    None
    """
    anomalies = []
    for mcu_type, field_stats in sorted(all_field_stats.items()):
        for field, stats in sorted(field_stats.items()):
            if threshold < stats["pct"] < 1.0:
                anomalies.append(
                    {
                        "mcu_type": mcu_type,
                        "field": field,
                        "pct": stats["pct"],
                        "count": stats["count"],
                        "total": stats["total"],
                        "missing_in": stats["missing_in"],
                    }
                )
    return anomalies


def write_anomaly_log(
    anomalies: list[dict],
    output_path: Path,
    consumed_files: list[str],
    all_cardinality_stats: dict | None = None,
) -> None:
    """
    WHAT:    Writes logs/Corpus_Anomalies.md — a Markdown report with two sections:
             (1) Fields at >90% but <100% occurrence (D-20 review required).
             (2) Cardinality diagnostics: fields with max duplicate-key count > 1
                 across any single instance, with raw max counts and provenance (D-23).
    WHY:     Human-readable report required by D-20. Cardinality section added for
             D-23 — raw max counts go here, NOT to the catalog, because the corpus
             ceiling is a sampling artifact. Developers use this section to verify
             that multi_fields classification is correct.
    ARGS:
        anomalies (list[dict]): Output of build_anomaly_log().
        output_path (Path): Destination file path (logs/Corpus_Anomalies.md).
        consumed_files (list[str]): All corpus files successfully parsed.
        all_cardinality_stats (dict | None): Per-type cardinality stats from
            build_catalog(). If None or empty, cardinality section is omitted.
    RETURNS:
        None
    FMEA:    None
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Corpus Anomalies — MCU Field Occurrence Report",
        "",
        f"**Generated by:** `scripts/build_mcu_catalog.py`  ",
        f"**Corpus files consumed:** {len(consumed_files)}  ",
        f"**Anomaly threshold:** >{int(ANOMALY_THRESHOLD * 100)}% but <100% occurrence  ",
        "",
        "Fields listed here are present in more than 90% but fewer than 100% of corpus",
        "instances for their MCU type. They are classified as **optional** in the catalog.",
        "Human review is required to determine whether the missing occurrences represent:",
        "- A known-faulty corpus file (field should be promoted to required)",
        "- A legitimate optional variant (classification is correct)",
        "",
        "**Decision authority:** Human (D-20). Do not automate this judgment.",
        "",
        "---",
        "",
    ]

    if not anomalies:
        lines += [
            "## Result: No Anomalies Found",
            "",
            "All fields were either present in 100% of instances (required) or",
            "fewer than 90% (clearly optional). No human review needed.",
            "",
        ]
    else:
        lines += [
            f"## {len(anomalies)} Anomaly Record(s) Found",
            "",
            "| MCU Type | Field | Occurrence | Missing In (count) |",
            "|---|---|---|---|",
        ]
        for a in anomalies:
            pct_str = f"{a['pct']*100:.1f}% ({a['count']}/{a['total']})"
            missing_count = len(a["missing_in"])
            lines.append(f"| `{a['mcu_type']}` | `{a['field']}` | {pct_str} | {missing_count} file(s) |")

        lines += ["", "---", "", "## Provenance Details", ""]
        for a in anomalies:
            lines += [
                f"### `{a['mcu_type']}` — `{a['field']}`",
                "",
                f"- **Occurrence:** {a['pct']*100:.1f}% ({a['count']} / {a['total']} instances)",
                f"- **Missing in {len(a['missing_in'])} file(s):**",
            ]
            for path in sorted(a["missing_in"]):
                lines.append(f"  - `{path}`")
            lines.append("")

    # --- CARDINALITY DIAGNOSTICS SECTION (D-23) ---
    # Raw max counts are corpus artifacts and must NOT appear in the catalog.
    # They belong here for developer verification that multi_fields is correct.
    if all_cardinality_stats:
        lines += [
            "---",
            "",
            "## Cardinality Diagnostics — Duplicate-Key Fields (D-23)",
            "",
            "Fields listed here appeared more than once in at least one corpus instance",
            "(duplicate keys, preserved by parser D-05). These fields are exported to",
            "the catalog as `multi_fields` entries — a structural boolean flag only.",
            "Raw max counts below are corpus sampling artifacts; IL-2 treats duplicate",
            "keys as logically unbounded. **Do not promote max counts to the catalog.**",
            "",
            "| MCU Type | Field | Max Count (any instance) | Files With Duplicates |",
            "|---|---|---|---|",
        ]
        for mcu_type in sorted(all_cardinality_stats.keys()):
            for field in sorted(all_cardinality_stats[mcu_type].keys()):
                stats = all_cardinality_stats[mcu_type][field]
                dup_count = len(stats["files_with_duplicates"])
                lines.append(
                    f"| `{mcu_type}` | `{field}` | {stats['max_count']} | {dup_count} file(s) |"
                )

        lines += ["", "### Provenance Details", ""]
        for mcu_type in sorted(all_cardinality_stats.keys()):
            for field in sorted(all_cardinality_stats[mcu_type].keys()):
                stats = all_cardinality_stats[mcu_type][field]
                lines += [
                    f"**`{mcu_type}.{field}`** — max {stats['max_count']} occurrence(s) per instance",
                    "",
                ]
                for path in stats["files_with_duplicates"]:
                    lines.append(f"- `{path}`")
                lines.append("")

    lines += [
        "---",
        "",
        "## Corpus Files Consumed",
        "",
        f"Total: {len(consumed_files)} files",
        "",
    ]
    for f in sorted(consumed_files):
        lines.append(f"- `{f}`")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ===========================================================================
# Catalog assembly
# ===========================================================================

def build_catalog(instances_by_type: dict) -> tuple[dict, dict, dict]:
    """
    WHAT:    Assembles the full catalog dict from raw corpus instances.
             Returns the catalog, per-type field stats (for anomaly logging),
             and per-type cardinality stats (for D-23 anomaly log section).
    WHY:     Single entry point for the full transformation pipeline: required/
             optional split → type resolution → child block mapping → FMEA
             overlay → multi-field detection (D-23). Keeping this as one
             function makes the sequence auditable.
    ARGS:
        instances_by_type (dict): Output of collect_mcu_instances().
    RETURNS:
        tuple: (catalog, all_field_stats, all_cardinality_stats)
               catalog: dict[str, dict] — the catalog keyed by MCU type name
               all_field_stats: dict[str, dict] — per-type field stats for anomaly log
               all_cardinality_stats: dict[str, dict] — per-type cardinality stats (D-23)
    FMEA:    EL-001, EL-002, EL-003, SM-003 (applied in FMEA overlay step)
    """
    catalog: dict[str, dict] = {}
    all_field_stats: dict[str, dict] = {}
    all_cardinality_stats: dict[str, dict] = {}

    for mcu_type in sorted(instances_by_type.keys()):
        instances = instances_by_type[mcu_type]

        # --- PHASE 2: REQUIRED / OPTIONAL SPLIT ---
        # Strict 100% intersection for required; anomaly threshold applied later.
        required, optional, field_stats = compute_field_sets(instances)
        all_field_stats[mcu_type] = field_stats

        # --- PHASE 3: TYPE FIDELITY RESOLUTION ---
        field_types = resolve_field_types(instances)

        # --- PHASE 5: CHILD BLOCK MAPPING ---
        # Shallow occurrence counts only (D-19).
        child_blocks = collect_child_blocks(instances)

        # --- PHASE 4: FMEA OVERLAY ---
        # Constraint strings are descriptive only — no enforcement predicates.
        constraints = FMEA_OVERLAYS.get(mcu_type, [])

        # --- PHASE 5b: MULTI-FIELD DETECTION (D-23) ---
        # Detect fields where max occurrences > 1 in any single instance.
        # Export only the boolean list to the catalog; raw counts go to anomaly log.
        multi_fields, cardinality_stats = compute_multi_fields(instances)
        if cardinality_stats:
            all_cardinality_stats[mcu_type] = cardinality_stats

        catalog[mcu_type] = {
            "type": mcu_type,
            "required_fields": sorted(required),
            "optional_fields": sorted(optional),
            "field_types": dict(sorted(field_types.items())),
            "child_blocks": dict(sorted(child_blocks.items())),
            "multi_fields": multi_fields,
            "constraints": constraints,
        }

    return catalog, all_field_stats, all_cardinality_stats


# ===========================================================================
# Validation
# ===========================================================================

def validate_against_meta_schema(catalog: dict, meta_schema_path: Path) -> None:
    """
    WHAT:    Validates the assembled catalog dict against the JSON Schema at
             meta_schema_path. Raises an exception and exits if validation fails.
    WHY:     PI-001 validator will load the catalog at runtime. A structurally
             invalid catalog must be caught here, not in production. Catching
             it in the build script makes the failure loud and early.
    ARGS:
        catalog (dict): The assembled catalog to validate.
        meta_schema_path (Path): Path to mcu_catalog_meta_schema.json.
    RETURNS:
        None
    FMEA:    None
    """
    try:
        import jsonschema
    except ImportError:
        print(
            "  [WARN] jsonschema not installed — skipping meta-schema validation.\n"
            "         Install with: pip install jsonschema",
            file=sys.stderr,
        )
        return

    # --- LOAD AND VALIDATE ---
    # Draft-7 compatibility: jsonschema.validate uses the $schema URI in the
    # meta-schema to select the right validator. No version override needed.
    meta_schema = json.loads(meta_schema_path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=catalog, schema=meta_schema)
        print("  [OK]   Catalog passes meta-schema validation.")
    except jsonschema.ValidationError as exc:
        print(f"  [FAIL] Meta-schema validation error: {exc.message}", file=sys.stderr)
        print(f"         Path: {list(exc.absolute_path)}", file=sys.stderr)
        sys.exit(1)


def check_coverage(catalog: dict, instances_by_type: dict) -> None:
    """
    WHAT:    Asserts that every MCU type found in the corpus has an entry in
             the catalog. Exits non-zero if any types are missing.
    WHY:     R1 — catalog coverage must be 100%. A missing type means the PI-001
             validator will accept malformed MCU blocks without flagging them.
    ARGS:
        catalog (dict): The assembled catalog.
        instances_by_type (dict): All corpus MCU instances keyed by type name.
    RETURNS:
        None
    FMEA:    None
    """
    corpus_types = set(instances_by_type.keys())
    catalog_types = set(catalog.keys())
    missing = corpus_types - catalog_types

    if missing:
        print(
            f"\n  [FAIL] Coverage check FAILED — {len(missing)} type(s) missing from catalog:",
            file=sys.stderr,
        )
        for t in sorted(missing):
            print(f"         - {t}", file=sys.stderr)
        sys.exit(1)

    print(f"  [OK]   Coverage: 100% — {len(corpus_types)} MCU type(s) in catalog.")


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> None:
    """
    WHAT:    Orchestrates the full catalog build pipeline: collect → split →
             type-resolve → child-map → FMEA overlay → validate → write.
             Also writes the anomaly log and prints a consumed-files report.
    WHY:     Top-level entry point so the script is runnable standalone from
             the project root: `python scripts/build_mcu_catalog.py`.
    ARGS:    None (reads PROJECT-relative paths from module-level constants).
    RETURNS: None (exits 0 on success, non-zero on any failure).
    FMEA:    None (orchestration only; constraint work is in build_catalog).
    """
    print("=" * 70)
    print("build_mcu_catalog.py — Phase 0.4 MCU Catalog Generator")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Phase 1 — Collect & Provenance
    # ------------------------------------------------------------------
    print(f"\n[1/5] Collecting MCU instances from corpus: {CORPUS_DIR}")
    instances_by_type, consumed_files = collect_mcu_instances(CORPUS_DIR)

    if not consumed_files:
        print("  [FAIL] No corpus files found. Check CORPUS_DIR path.", file=sys.stderr)
        sys.exit(1)

    print(f"  Consumed: {len(consumed_files)} file(s)")
    for f in sorted(consumed_files):
        print(f"    - {f}")

    print(f"\n  MCU types found: {len(instances_by_type)}")
    total_instances = sum(len(v) for v in instances_by_type.values())
    print(f"  Total MCU instances: {total_instances}")

    # ------------------------------------------------------------------
    # Phase 2–5 — Build catalog
    # ------------------------------------------------------------------
    print("\n[2/5] Building catalog (required/optional split, type resolution, child blocks, FMEA overlay, multi_fields)...")
    catalog, all_field_stats, all_cardinality_stats = build_catalog(instances_by_type)
    print(f"  Catalog entries: {len(catalog)}")
    total_multi = sum(len(e.get("multi_fields", [])) for e in catalog.values())
    print(f"  Multi-field keys detected (D-23): {total_multi} across all types")

    # ------------------------------------------------------------------
    # Phase 2 (cont.) — Write anomaly log
    # ------------------------------------------------------------------
    print(f"\n[3/5] Writing anomaly log: {ANOMALY_LOG_PATH}")
    anomalies = build_anomaly_log(all_field_stats)
    write_anomaly_log(anomalies, ANOMALY_LOG_PATH, consumed_files, all_cardinality_stats)
    if anomalies:
        print(f"  [WARN] {len(anomalies)} anomaly record(s) written — human review required.")
        print(f"         See: {ANOMALY_LOG_PATH}")
    else:
        print("  [OK]   No anomalies found.")

    # ------------------------------------------------------------------
    # Phase 6–7 — Validate and write
    # ------------------------------------------------------------------
    print(f"\n[4/5] Validating catalog against meta-schema: {META_SCHEMA_PATH}")
    validate_against_meta_schema(catalog, META_SCHEMA_PATH)

    print(f"\n[5/5] Writing catalog: {CATALOG_OUTPUT}")
    CATALOG_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_OUTPUT.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"  Written: {CATALOG_OUTPUT}")

    # ------------------------------------------------------------------
    # Phase 9 — Coverage check
    # ------------------------------------------------------------------
    print("\n[Coverage] Checking 100% corpus type coverage...")
    check_coverage(catalog, instances_by_type)

    print("\n" + "=" * 70)
    print("BUILD COMPLETE — data/mcu_catalog.json ready for PI-001 validator.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
