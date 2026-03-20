# Deferred: Compliance Audit Prompt System

**Created:** March 19, 2026  
**Status:** DEFERRED — implement after Phase 0.3 HUMAN gate review  
**Trigger:** If Phase 0.3 output contains comment compliance gaps despite Ground Rule 11 being present, implement immediately. If output is clean, revisit at Phase 1.3 (first FMEA-constrained compiler primitive).  
**Documents to update on implementation:** `ARCHITECTURE.md`, `CONSTRAINTS.md`, `SKILL.md`, `docs/templates/templates.md`

---

## Why This Was Deferred

The comment standard (Ground Rule 11, C-019–C-022) and standing acceptance criteria in every session prompt header are the primary enforcement mechanism. The audit prompt is a secondary independent check. Before building the secondary check, Phase 0.3 should be run and reviewed to determine whether the primary mechanism is working. That review provides the empirical data needed to justify the build.

Building now risks over-engineering infrastructure for a problem that may not materialize. Building at Phase 1.3 risks some retrofit cost but remains manageable — the codebase is small enough that a first audit run will be short.

---

## Design Decisions Already Made

These do not need to be re-litigated when implementation begins. Pick up from here.

### Prompt Structure

A single prompt with a **manifest block at the top**. The user fills in the manifest before running — no editing of the prompt body required. The prompt engine reads the manifest and executes only enabled modules.

### Module Set

| ID | Module | What It Checks | Context Cost |
|---|---|---|---|
| M1 | Directory Structure | Actual repo layout vs `ARCHITECTURE.md` | Low |
| M2 | Comment Compliance | `.py` files for missing docstrings and block comments | Medium–High (scales with codebase) |
| M3 | Document Consistency | FMEA IDs consistent across `CONSTRAINTS.md`, `ARCHITECTURE.md`, `FMEA.md` | Low |
| M4 | Decision Log Integrity | Patch file format, sequential numbering, no orphaned entries | Low |
| M5 | Phase Status | Phase Mapping table vs actual file existence on disk | Low |
| M6 | Constraint Traceability | Code touching FMEA-constrained components cites constraint ID inline | High |

### Pre-Configured Profiles

Two profiles baked into the manifest as starting points. User can deviate by toggling individual modules.

**GATE profile** — M1, M3, M4, M5 enabled. Fast, document-level. Default for HUMAN gate pre-merge checks.

**DEEP profile** — All modules. For phase completion, pre-handoff, or when compliance drift is suspected.

### Output Modes

**Inline mode** — Findings reported directly in the session response. For small scopes (single directory, single file). No artifact produced.

**Log mode** — Findings written to `working/COMPLIANCE_LOG.md`. For phase-wide or repo-wide scans. Session produces the log and halts — remediation is a separate session.

M2 and M6 default to log mode due to context cost. M1, M3, M4, M5 default to inline mode. All overridable in the manifest.

### Context Scaling for M2 and M6

When context is constrained, the prompt instructs the AI to scan the current phase's target directory only rather than the full repo. The log header records what scope was and was not covered so the human knows what the audit missed.

### Log File Format

Location: `working/COMPLIANCE_LOG.md` — same ephemeral working directory as the patch file.

A non-empty log at a HUMAN gate is a merge blocker. Findings marked DEFERRED must have an accompanying note and a linked GitHub Issue before the gate can proceed. Log is cleared when all findings are resolved.

**Log header (plain English):**

```markdown
# Compliance Log — Phase [X.Y]
**Generated:** [Date]
**Profile:** [GATE / DEEP / Custom]
**Modules run:** [M1, M2, ...]
**Scope:** [Directory or "Full repo"]

[2–3 plain sentences describing what was audited and what the findings mean
for the current gate status.]

Total findings: [N] | Open: [N] | In Progress: [N] | Resolved: [N] | Deferred: [N]
```

**Per-finding format (structured header + plain English paragraph):**

```markdown
## F-[NNN] — [Short violation title]
**File:** [path/to/file.py]
**Location:** [function name / line number]
**Constraint:** [C-0XX]
**Status:** [OPEN / IN PROGRESS / RESOLVED / DEFERRED]

[Plain English paragraph: what is missing, why it matters specifically in
this project's context, and what a future reader would get wrong without it.
Written for a human who may not be familiar with the constraint being violated.]

**Fix:** [Specific remediation instruction written precisely enough for an AI
session to act on directly without re-running the scan.]
```

**Status values:**
- `OPEN` — Not yet addressed
- `IN PROGRESS` — Being addressed in an active session
- `RESOLVED` — Fixed and verified by re-run
- `DEFERRED` — Pushed with a note explaining why and a linked GitHub Issue

### Re-ingestion Behavior

On subsequent runs, the audit prompt reads the existing log first and skips `RESOLVED` findings. Only `OPEN`, `IN PROGRESS`, and new findings are reported. This makes incremental fix sessions viable without re-scanning clean files.

### Workflow Integration

**At HUMAN gates:** GATE profile is the default pre-merge check. A non-empty log after a GATE run is a merge blocker.

**Ad hoc:** Any profile, any scope, any time. The prompt is fully self-contained — it reads `ARCHITECTURE.md` and `CONSTRAINTS.md` to determine what "correct" looks like, so it doesn't go stale as the project evolves.

---

## Documents to Update on Implementation

### `SKILL.md`
- Add to HUMAN gate merge protocol (Phase 3, step 9): run GATE profile audit before patch merge. Non-empty log is a merge blocker.
- Add to Phase 3 documentation audit step (step 6): reference the compliance log as the artifact that captures M2/M6 findings.

### `docs/templates/templates.md`
- Add new template section: `COMPLIANCE_LOG.md`
- Add new template section: `COMPLIANCE_AUDIT_PROMPT.md` (the manifest + module prompt itself)

### `ARCHITECTURE.md`
- Add `working/COMPLIANCE_LOG.md` to the directory structure under `working/`
- Add one-line reference in the "Code Comment Standard" section pointing to the audit prompt as the verification mechanism

### `CONSTRAINTS.md`
- Add note to C-022 referencing the audit prompt as the independent verification mechanism for comment preservation

### `README.md`
- No change required unless a docs/templates section is added to the documentation table

---

## Open Question at Implementation Time

Determine whether the manifest profile system warrants a dedicated `docs/templates/AUDIT_PROFILES.md` or whether the two profiles (GATE and DEEP) are sufficient as inline presets within the prompt itself. At the time of deferral, two presets appeared sufficient for this project's scale. Revisit if the module set grows.
