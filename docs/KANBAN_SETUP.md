# Kanban Board Configuration

## Board: IL-2 Great Battles Modular Mission Orchestrator

### Columns

| Column | Purpose | WIP Limit | Entry Criteria | Exit Criteria |
|---|---|---|---|---|
| Triage | New issues awaiting decomposition | None | Issue created | Task decomposed, dependencies identified |
| Ready | Fully specified, unblocked tasks | 10 | Prompt header generated, dependencies met | Assigned to developer/agent |
| In Progress | Actively being worked | 5 | Assigned, Kanban state announced (Rule 3) | All acceptance criteria met |
| In Review | Awaiting human review | 5 | PR opened or artifact submitted | Review approved |
| Done | Completed and documented | None | Review approved, docs updated (Rule 4), patch merged (Rule 2) | N/A |
| Blocked | Tasks with unresolved dependencies | None | Blocker identified | Blocker resolved |

### Spike Constraint (Ground Rule 7)

Issues labeled `spike` are prohibited from moving to "Done." They may only reach "Done" after a linked formalization issue is created and itself reaches "In Review."

Enforcement is two-layer:

**Layer 1 — GitHub Project Automation (visual friction)**
Set up in the GitHub Projects UI under "Workflows":
- Trigger: Item moved to "Done"
- Condition: Item has label `spike`
- Action: Move item back to "In Review"

This gives immediate visible feedback on the board without requiring any code.

Setup steps:
1. Open your GitHub Project board
2. Click "..." → "Workflows" → "New Workflow"
3. Set trigger to "Item moved to a column"
4. Filter: label = `spike` and column = "Done"
5. Action: Move to "In Review"
6. Save and enable

**Layer 2 — GitHub Actions CI check (hard enforcement)**
Defined in `.github/workflows/spike-check.yml`. Triggers on `issues.closed` events. If the closed issue has the `spike` label, the workflow checks for a linked formalization issue in "In Review" or "Done." If none is found, the issue is automatically re-opened and a comment is posted explaining the requirement.

See `.github/workflows/spike-check.yml` for the full workflow definition.

### Automation Rules

- When PR is opened → move card to "In Review"
- When PR is merged → move card to "Done"
- When issue is labeled `blocked` → move card to "Blocked"
- When issue has label `spike` and moves to "Done" → move back to "In Review" (Project Automation, Layer 1)
- When issue with label `spike` is closed without linked formalization issue → re-open and comment (GitHub Actions, Layer 2)

### Labels

**Phase** — one per issue, required:
`phase:0`, `phase:1`, `phase:2`, `phase:3`, `phase:4`, `phase:5`, `phase:6`

**Boundary** — one per issue, required:
`human-gate`, `ai-eligible`, `ai-with-review`

**Type** — one per issue, required:
`task`, `spike`, `decision`, `amendment`

- `task` — standard execution work (coding, testing, documentation)
- `spike` — exploratory work under Ground Rule 7 (formalization issue required before Done)
- `decision` — open architectural question requiring human disposition (e.g., framework selection)
- `amendment` — modification to the project's rule set (constraints, FMEA, scope proposals)

**Priority** — one per issue, optional (default: `normal`):
`critical`, `high`, `normal`

- `critical` — blocks multiple other issues or threatens project integrity
- `high` — blocks at least one other issue or has a near-term deadline
- `normal` — standard priority, no urgency

**Total labels: 17.** All other label categories previously defined (component, complexity, tier, individual FMEA) are retired. Component, tier, and FMEA constraint information lives in the issue body and session prompt header — not in labels.
