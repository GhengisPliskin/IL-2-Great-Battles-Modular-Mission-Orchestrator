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

- **Component labels:** `comp:parser`, `comp:compiler`, `comp:mre`, `comp:map-extractor`, `comp:orchestrator`, `comp:gui`, `comp:cli`, `comp:schema`
- **Complexity labels:** `complexity:low`, `complexity:medium`, `complexity:high`
- **Tier labels:** `tier:1`, `tier:2`, `tier:3`
- **FMEA labels:** `fmea:PI-001`, `fmea:PI-002`, `fmea:PI-003`, `fmea:PI-004`, `fmea:EL-001`, `fmea:EL-002`, `fmea:EL-003`, `fmea:SM-001`, `fmea:SM-002`, `fmea:SM-003`, `fmea:SM-004`, `fmea:EC-001`, `fmea:EC-002`, `fmea:EC-003`, `fmea:EC-004`
- **Boundary labels:** `human-only`, `ai-eligible`, `ai-with-review`
- **Phase labels:** `phase:0`, `phase:1`, `phase:2`, `phase:3`, `phase:4`, `phase:5`, `phase:6`
- **Spike label:** `spike` for exploratory tasks under Ground Rule 7
