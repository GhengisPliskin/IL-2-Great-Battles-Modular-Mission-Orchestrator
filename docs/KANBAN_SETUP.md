# Kanban Board Configuration

## Board: IL-2 Great Battles Modular Mission Orchestrator

### Columns

| Column | Purpose | WIP Limit | Entry Criteria | Exit Criteria |
|---|---|---|---|---|
| Triage | New issues awaiting decomposition | None | Issue created | Task decomposed, dependencies identified |
| Ready | Fully specified, unblocked tasks | 10 | Prompt header generated, dependencies met | Assigned to developer/agent |
| In Progress | Actively being worked | 5 | Assigned, Kanban state announced (Rule 3) | All acceptance criteria met |
| In Review | Awaiting human review | 5 | PR opened or artifact submitted | Review approved |
| Done | Completed and documented | None | Review approved, docs updated (Rule 4) | N/A |
| Blocked | Tasks with unresolved dependencies | None | Blocker identified | Blocker resolved |

### Spike Constraint (Ground Rule 7)

Issues labeled `spike` are prohibited from moving to "Done." They may only reach "Done" after a linked formalization issue is created and itself reaches "In Review."

### Automation Rules

- When PR is opened → move card to "In Review"
- When PR is merged → move card to "Done"
- When issue is labeled `blocked` → move card to "Blocked"
- When issue is labeled `spike` → enforce Done-lock (manual or CI check)

### Labels

- **Component labels:** `comp:parser`, `comp:compiler`, `comp:mre`, `comp:map-extractor`, `comp:orchestrator`, `comp:gui`, `comp:cli`, `comp:schema`
- **Complexity labels:** `complexity:low`, `complexity:medium`, `complexity:high`
- **Tier labels:** `tier:1`, `tier:2`, `tier:3`
- **FMEA labels:** `fmea:PI-001`, `fmea:PI-002`, `fmea:PI-003`, `fmea:PI-004`, `fmea:EL-001`, `fmea:EL-002`, `fmea:EL-003`, `fmea:SM-001`, `fmea:SM-002`, `fmea:SM-003`, `fmea:SM-004`, `fmea:EC-001`, `fmea:EC-002`, `fmea:EC-003`, `fmea:EC-004`
- **Boundary labels:** `human-only`, `ai-eligible`, `ai-with-review`
- **Phase labels:** `phase:0`, `phase:1`, `phase:2`, `phase:3`, `phase:4`, `phase:5`, `phase:6`
- **Spike label:** `spike` for exploratory tasks under Ground Rule 7
