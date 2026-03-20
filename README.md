# IL-2 Great Battles Modular Mission Orchestrator

## What This Is

IL-2 Great Battles multiplayer missions are built by hand in a proprietary mission editor, one object at a time. A single reusable AI patrol group — aircraft, waypoints, triggers, activation logic — can take hours to assemble correctly and breaks in subtle ways when copied between missions. There is no standard way to test whether it will actually work until you load it on a server with players.

This tool solves that problem. You define a mission module once as a structured JSON file, and the Modular Mission Orchestrator compiles it into a valid IL-2 mission file (`.Group` or `.Mission`) that loads directly in the editor and runs correctly on a dedicated multiplayer server. Modules are reusable — a Static CAP patrol built once can be dropped into any mission on any map. The orchestrator handles the tedious parts: unique object IDs, coordinate placement, activation sequencing, and garbage collection when flights are destroyed.

The end goal is a tool comparable to Vander's Easy Mission Generator — a complete multiplayer mission generated from high-level parameters in under 30 seconds.

## Project Status

**Phase 0 (Foundation) — In Progress.** The IL-2 ASCII parser is complete. The compiler, GUI, and orchestrator are not yet built. Each phase produces a usable standalone deliverable — the project can stop at any phase boundary and the completed work has value.

## Quick Start

[Placeholder — populated during Phase 2 execution]

## Documentation

This project is developed using AI coding assistants (Claude Code, Gemini) under human oversight. The documents below define how it is built, what constraints govern it, and how decisions are recorded. If you are new to the project, read `ARCHITECTURE.md` first.

| Document | Purpose |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Directory structure, component descriptions, data flow, phase status, **code comment standard** |
| [`CONSTRAINTS.md`](CONSTRAINTS.md) | Engine behavior constraints, technical stack constraints, and code quality requirements |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Code comment standard, contribution workflow, ground rules for contributors |
| [`KEY_DECISION_LOG.md`](KEY_DECISION_LOG.md) | Architectural decisions and rationale |
| [`CODE_DECISION_LOG.md`](CODE_DECISION_LOG.md) | Code-level decisions and debugging heuristics |
| [`docs/KANBAN_SETUP.md`](docs/KANBAN_SETUP.md) | Project board configuration |
| [`docs/FMEA.md`](docs/FMEA.md) | Failure Mode and Effects Analysis — the catalogue of ways this project can fail silently in the IL-2 engine and how each is mitigated |
| [`docs/MMO_Master_Project_Plan.md`](docs/MMO_Master_Project_Plan.md) | Full project plan, ground rules, task registry |

## Automation

This repo includes GitHub Actions and Project automation for Kanban enforcement. See [`docs/KANBAN_SETUP.md`](docs/KANBAN_SETUP.md) for setup steps and workflow details.

## Ground Rules

This project uses AI coding assistants to generate code under human review. Eleven operational ground rules govern how that works — covering issue tracking, decision logging, FMEA constraint enforcement, and code comment standards. See the [Master Plan](docs/MMO_Master_Project_Plan.md) for the full list. Rule 11 (Code Comment Standard) is also documented in [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Contributing

[Placeholder — populated during Phase 2 execution. In the meantime, see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the code comment standard and workflow ground rules.]
