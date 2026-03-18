# IL-2 Great Battles — Modular Mission Orchestrator
## Phase 4 — Map Data Extractor + Geographic Databases
### Session Prompt Headers
*Machine-readable map data for automated coordinate generation*

**5 AI Sessions | 2 Human Gates | Task IDs 4.1 – 4.5**

---

## Phase 4 Overview

Phase 4 builds the Map Data Extractor and populates the geographic databases that the Phase 5 Orchestrator consumes for automated coordinate generation. This phase depends on Phase 0 ONLY and can run in parallel with Phases 1–3.

The Extractor parses stock IL-2 .Mission files, identifies airfield objects, extracts coordinates, runway headings, and spawn positions, and outputs structured JSON per map. The route generation utility (4.4) is the only Tier 1 task in this phase — it requires spatial reasoning to produce tactically plausible flight paths from airfield to target area and back, accounting for altitude, speed, and terrain constraints that the Orchestrator will consume directly.

No FMEA constraints from the compiler domain (PI-*, EL-*, SM-*, EC-*) apply directly to Phase 4 code. However, the data produced here feeds Phase 5's mission assembly engine, where PI-001 (required field validation), PI-004 (spatial partitioning), and the full constraint set govern how coordinates are consumed. Data quality errors in Phase 4 propagate silently into Phase 5 as invalid waypoint coordinates, incorrect spawn positions, or out-of-bounds airfield references.

| Task | Description | Component | Actor | Model Tier |
|------|-------------|-----------|-------|------------|
| 4.0h | Provide stock .Mission files for each owned map | Data | HUMAN | N/A |
| 4.1 | Build Map Data Extractor (parse .Mission, extract airfields, coords, spawn positions) | MDE | AI | Tier 2: Sonnet 4.6 |
| 4.2h | IN-EDITOR VALIDATION: Spot-check extracted airfield coordinates | Testing | HUMAN | N/A |
| 4.2 | Extract data for primary maps, cross-reference community databases | MDE + Data | AI | Tier 2: Sonnet 4.6 |
| 4.3 | Extract front-line reference data from MP templates | MDE + Data | AI | Tier 2: Sonnet 4.6 |
| 4.4 | Build route generation utility (airfield → target → return) | MDE | AI | Tier 1: Opus 4.6 |
| 4.5 | Add remaining maps, establish repeatable extraction process | MDE + Data | AI | Tier 2: Sonnet 4.6 |

**Dependency order:** 4.0h must complete first (human provides map files). 4.1 depends on 0.2 (parser), 0.4 (MCU type catalog), and 4.0h. 4.2h depends on 4.1. 4.2 depends on 4.1 and 4.2h. 4.3 depends on 4.1 (independent of 4.2). 4.4 depends on 4.2 (needs validated airfield database). 4.5 depends on 4.2 (extends established extraction pipeline).

```
Phase 0 (0.2 Parser + 0.4 Catalog)
    ↓
    4.0h (HUMAN: Provide map files)
    ↓
    4.1 (Map Data Extractor)
    ↓
    4.2h (HUMAN: Coordinate validation)
    ↓
    ├──→ 4.2 (Primary map extraction) ──┬──→ 4.4 (Route generation)
    │                                    │
    │                                    └──→ 4.5 (Remaining maps + process doc)
    │
    └──→ 4.3 (Front-line data extraction)
```

---

## Human Gate 4.0h — Provide Stock Map Files

| | |
|---|---|
| **Gate ID** | 4.0h |
| **Depends On** | None |
| **Actor** | Project Owner |
| **Blocks** | 4.1 cannot begin until files are provided |

### Required Actions

- Locate stock .Mission files in your IL-2 installation directory (`data/Missions/`) for each owned map
- Maps to include: Stalingrad, Moscow, Kuban, Rhineland, Bodenplatte, Prokhorovka, Normandy, and any additional DLC maps owned
- Include multiplayer templates (these contain airfield definitions, spawn points, and front-line icon translators)
- Copy files to the working directory under a `data/map_sources/` subdirectory, organized by map name

### Exit Condition

- Files accessible in working directory
- At least 5 maps represented
- Multiplayer templates included for each map (these are the primary source of airfield and front-line data)

---

## Session 4.1 — Map Data Extractor

| | |
|---|---|
| **Task ID** | 4.1 |
| **Component** | Map Data Extractor (`src/backend/map_extractor/extractor.py`, `src/backend/map_extractor/coordinate_db.py`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 0.2 (parser library — reads .Mission ASCII), 0.4 (MCU type catalog — airfield and spawn point field definitions), 4.0h (stock map files) |
| **Delivers To** | 4.2 (primary map database population), 4.3 (front-line extraction), 4.4 (route generation consumes airfield DB), Phase 5.1 (mission assembly reads airfield coordinates) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/map_extractor/`, Phase Mapping → 4.1–4.3 |

### Role

You are a Senior Python Developer specializing in geospatial data extraction and structured database construction. You are building the Map Data Extractor — a tool that parses IL-2 stock .Mission files and extracts machine-readable airfield, spawn, and geographic reference data that the Orchestrator will consume for automated mission generation.

### Context

IL-2 stock .Mission files for multiplayer templates contain the authoritative definitions of airfield objects, spawn positions, runway headings, and coalition assignments for each map. This data is not available from any other programmatic source — it exists only inside these files. The Extractor reads them via the Phase 0 parser library, identifies airfield-related MCU blocks (Airfield, Plane Set, Spawn Point), extracts their coordinates, and outputs structured JSON per map.

The output feeds directly into the Phase 5 Orchestrator, which uses airfield coordinates for player spawn placement, AI takeoff positions, and waypoint origin calculations. Coordinate errors here produce missions where aircraft spawn underground, off the runway, or at incorrect airfields — failures that are only detectable through in-game testing.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.1: JSON Intermediary — Extractor output is JSON, consumed by the Orchestrator's mission assembly engine
> - Section 2.3: Spatial Blackboxing — Extractor deals with real map coordinates (not remote zones); these feed the user-facing proxy coordinate layer
> - ARCHITECTURE.md: Output directory → `data/map_databases/`

### Inputs

- Phase 0 outputs: `src/mmf/parser/` (parser library), MCU type catalog from task 0.4
- Stock .Mission files from 4.0h, organized by map
- At least 5 maps represented

### Requirements

**R1 — Airfield Object Extraction**

Parse each stock .Mission file and identify all airfield-related blocks:
- `Airfield` blocks: extract coordinates (XPos, ZPos), name, coalition, runway count
- `MCU_TR_Airfield` blocks: extract linked plane sets, spawn point references
- Spawn point MCUs: extract coordinates, heading, coalition assignment
- Plane set definitions: extract available aircraft types per airfield per coalition

**R2 — Coordinate Normalization**

All extracted coordinates must be stored in the IL-2 engine's native coordinate system (X = east-west, Z = north-south, Y = altitude). Do not convert to lat/lon or any external CRS. Store as floating-point values with full precision from the source file.

**R3 — Per-Map JSON Output Schema**

Each map produces a JSON file:

```json
{
  "map_id": "stalingrad",
  "map_display_name": "Stalingrad",
  "source_files": ["stalingrad_mp_template.Mission"],
  "airfields": [
    {
      "airfield_id": "stalingrad_axis_01",
      "name": "Pitomnik",
      "coalition": "axis",
      "coordinates": {"x": 12345.0, "z": 67890.0},
      "runway_heading": 270.0,
      "spawn_points": [
        {"x": 12340.0, "z": 67895.0, "heading": 270.0}
      ],
      "plane_sets": ["bf109g2", "bf109g4", "he111h6"]
    }
  ],
  "extraction_metadata": {
    "extractor_version": "1.0",
    "extraction_date": "...",
    "source_file_count": 1
  }
}
```

**R4 — CLI Interface**

```python
# src/backend/map_extractor/cli.py
extract_map(mission_file: str, output_dir: str) -> str  # returns output JSON path
extract_all(source_dir: str, output_dir: str) -> list[str]  # batch extraction
```

**R5 — Validation Pass**

After extraction, run a self-check:
- Every airfield must have at least 1 spawn point
- Every spawn point must have valid coordinates (non-zero X and Z)
- Coalition must be one of `['axis', 'allied']`
- Warn on duplicate airfield names within a single map

> **EXIT CONDITION — Acceptance Criteria**
> - Extractor processes all stock .Mission files from 4.0h without exception
> - Airfield coordinates extracted for at least 5 maps
> - Output JSON validates against the per-map schema defined in R3
> - Self-check validation pass reports no errors on stock files
> - Coordinates visually spot-checked in BOSEditor for at least 2 maps (human gate 4.2h)
> - CLI processes a single map file and a batch directory correctly

---

## Human Gate 4.2h — In-Editor Coordinate Validation

| | |
|---|---|
| **Gate ID** | 4.2h |
| **Depends On** | 4.1 — extracted airfield JSON files |
| **Actor** | Project Owner |
| **Blocks** | 4.2 cannot begin until validated coordinates are confirmed |

### Required Actions

- Open BOSEditor for each extracted map
- For each airfield in the extracted JSON, navigate to the reported coordinates
- Confirm the coordinates correspond to an actual airfield on the map (runway visible, correct location)
- Check spawn point coordinates — they should be on or adjacent to the runway

### Verification Checklist

- **Coordinate accuracy:** extracted coordinates match the airfield's actual position in BOSEditor for all checked maps
- **Coalition correctness:** Axis airfields are on the correct side of the front; Allied airfields on the other
- **Spawn point placement:** spawn points are on the runway, not in buildings or off the airfield
- **Runway heading:** reported heading matches the visible runway orientation (±10°)
- **No missing airfields:** all major airfields visible in BOSEditor have corresponding entries in the JSON

### Report Requirements

Document results per map. For each airfield: CONFIRMED, OFFSET (specify the error in meters), or MISSING. If any airfield is OFFSET by more than 200m, report it as an extraction bug — return to session 4.1 with the evidence before proceeding.

---

## Session 4.2 — Primary Map Database Population

| | |
|---|---|
| **Task ID** | 4.2 |
| **Component** | Map Data Extractor + Data (`src/backend/map_extractor/`, `data/map_databases/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 4.1 (Extractor tool), 4.2h (validated extraction accuracy) |
| **Delivers To** | 4.4 (route generation — needs complete airfield DB), 4.5 (remaining maps extend this DB), Phase 5.1 (mission assembly) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `data/map_databases/`, Phase Mapping → 4.1–4.3 |

### Role

You are a Senior Python Developer. You are populating the geographic database for all primary maps by running the Extractor across the validated file corpus and cross-referencing the output against community airfield databases to catch omissions.

### Context

Task 4.1 built the Extractor and task 4.2h confirmed its coordinate accuracy. This session runs the full extraction pipeline across all available maps, aggregates the per-map JSON outputs into a unified database, and cross-references the results against any available community airfield data (forum posts, community mission files, public airfield lists) to identify missing airfields or incorrect metadata.

The output is the production geographic database stored at `data/map_databases/`. The Phase 5 Orchestrator reads this database at runtime to resolve airfield references, calculate spawn positions, and generate waypoint origins.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.3: Spatial Blackboxing — the map database provides the real-world coordinates that the Orchestrator places proxy nodes at; internal MCU logic is offset to remote zones per PI-004
> - ARCHITECTURE.md: Output → `data/map_databases/maps.sqlite3`

### Inputs

- Task 4.1: validated Map Data Extractor
- Task 4.2h: coordinate validation results confirming extraction accuracy
- Stock .Mission files from 4.0h (all maps)
- Community airfield references (if available — treated as supplementary, not authoritative)

### Requirements

**R1 — Full Extraction Run**

Execute the Extractor across all stock .Mission files for all maps provided in 4.0h. Store per-map JSON in `data/map_databases/json/`.

**R2 — Unified Database**

Aggregate all per-map JSON into a SQLite database at `data/map_databases/maps.sqlite3` with the following tables:

```sql
CREATE TABLE maps (
    map_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    source_files TEXT NOT NULL  -- JSON array of filenames
);

CREATE TABLE airfields (
    airfield_id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL REFERENCES maps(map_id),
    name TEXT NOT NULL,
    coalition TEXT NOT NULL CHECK(coalition IN ('axis', 'allied')),
    x REAL NOT NULL,
    z REAL NOT NULL,
    runway_heading REAL,
    plane_sets TEXT  -- JSON array
);

CREATE TABLE spawn_points (
    spawn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airfield_id TEXT NOT NULL REFERENCES airfields(airfield_id),
    x REAL NOT NULL,
    z REAL NOT NULL,
    heading REAL NOT NULL
);
```

**R3 — Database Query API**

```python
# src/backend/map_extractor/coordinate_db.py
class MapDatabase:
    def get_airfields(self, map_id: str, coalition: str = None) -> list[dict]
    def get_spawn_points(self, airfield_id: str) -> list[dict]
    def get_nearest_airfield(self, map_id: str, x: float, z: float, coalition: str = None) -> dict
    def list_maps(self) -> list[dict]
```

**R4 — Community Cross-Reference**

If community airfield data is available, compare airfield counts and names against extracted data. Log discrepancies as warnings. Community data supplements but does not override the extracted data (stock files are the authoritative source).

**R5 — Database Integrity Checks**

Post-population validation:
- Every map has at least 2 airfields (1 per coalition minimum)
- Every airfield has at least 1 spawn point
- No duplicate airfield IDs across the entire database
- Coordinate ranges are within plausible bounds for each map

> **EXIT CONDITION — Acceptance Criteria**
> - Geographic database populated for 5+ maps
> - SQLite database at `data/map_databases/maps.sqlite3` passes all R5 integrity checks
> - `MapDatabase` API queries return correct results for at least 3 maps
> - Per-map JSON files stored in `data/map_databases/json/` and consistent with the SQLite database
> - Community cross-reference log produced (even if no community data was available)

---

## Session 4.3 — Front-Line Reference Data Extraction

| | |
|---|---|
| **Task ID** | 4.3 |
| **Component** | Map Data Extractor + Data (`src/backend/map_extractor/`, `data/map_databases/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 4.1 (Extractor tool — same parser pipeline extracts icon translator positions) |
| **Delivers To** | Phase 5.3 (scenario templates use front-line data to calculate intercept points, patrol zones, and target areas) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `data/map_databases/`, Phase Mapping → 4.1–4.3 |

### Role

You are a Senior Python Developer. You are extending the Map Data Extractor to extract front-line reference data from IL-2 stock multiplayer templates. This data defines where the battle line is drawn on each map for each historical scenario, which the Orchestrator uses to position AI engagements, patrol zones, and ground targets.

### Context

IL-2 multiplayer templates define front-line positions using icon translator MCUs placed along the battle line. These icons are visible in BOSEditor as a line of markers separating the two coalitions. The front-line position varies by scenario — the same map (e.g., Stalingrad) may have multiple templates representing different periods of the battle, each with the front line at a different position.

The Orchestrator (Phase 5.3) uses front-line data to calculate tactically plausible engagement zones: intercept modules are placed between the front line and the defending airfields; ground attack targets are placed near or behind the enemy front line; patrol zones straddle the front. Without this data, the Orchestrator cannot generate scenario-appropriate missions.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.3: Spatial Blackboxing — front-line coordinates are real map positions used for proxy node placement
> - Section 6.2: Future Modules — Scramble, Bomber Escort, and other modules reference target areas that derive from front-line positions

### Inputs

- Task 4.1: Map Data Extractor (parser pipeline)
- Stock multiplayer template .Mission files from 4.0h (these contain front-line icon translators)

### Requirements

**R1 — Icon Translator Extraction**

Parse multiplayer template .Mission files and identify icon translator MCUs that define the front-line boundary. Extract:
- Icon position coordinates (X, Z)
- Icon type (used to distinguish front-line markers from other icons)
- Coalition assignment (which side of the line)

**R2 — Front-Line Polyline Construction**

For each scenario template, construct an ordered polyline from the extracted icon positions representing the front line. Store as an ordered list of (X, Z) coordinate pairs.

**R3 — Scenario Association**

Each front-line definition is associated with a specific scenario (map + historical period). Store the association:

```json
{
  "map_id": "stalingrad",
  "scenario_id": "stalingrad_winter_42",
  "scenario_name": "Stalingrad — Winter 1942",
  "front_line": [
    {"x": 10000.0, "z": 20000.0},
    {"x": 11000.0, "z": 22000.0},
    {"x": 12500.0, "z": 24000.0}
  ],
  "source_file": "stalingrad_winter_mp.Mission"
}
```

**R4 — Database Extension**

Add front-line data to the SQLite database:

```sql
CREATE TABLE scenarios (
    scenario_id TEXT PRIMARY KEY,
    map_id TEXT NOT NULL REFERENCES maps(map_id),
    scenario_name TEXT NOT NULL,
    source_file TEXT NOT NULL
);

CREATE TABLE front_line_points (
    point_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT NOT NULL REFERENCES scenarios(scenario_id),
    sequence_order INTEGER NOT NULL,
    x REAL NOT NULL,
    z REAL NOT NULL
);
```

**R5 — API Extension**

```python
class MapDatabase:
    # Existing methods from 4.2...
    def get_scenarios(self, map_id: str) -> list[dict]
    def get_front_line(self, scenario_id: str) -> list[dict]  # ordered polyline
    def get_nearest_front_line_point(self, scenario_id: str, x: float, z: float) -> dict
```

> **EXIT CONDITION — Acceptance Criteria**
> - Front-line data extracted for at least 2 scenarios per map on 2+ maps
> - Front-line polylines are ordered (sequential traversal produces a coherent line, not a scatter)
> - Scenario associations stored in SQLite with correct map references
> - `get_front_line()` returns an ordered polyline for each extracted scenario
> - `get_nearest_front_line_point()` returns the geometrically closest point on the line to an arbitrary coordinate

---

## Session 4.4 — Route Generation Utility

| | |
|---|---|
| **Task ID** | 4.4 |
| **Component** | Map Data Extractor (`src/backend/map_extractor/`) |
| **Model Tier** | Tier 1 — Opus 4.6 / Gemini 3.1 Pro |
| **Depends On** | 4.2 (validated airfield database with coordinates and spawn points) |
| **Delivers To** | Phase 5.3 (scenario templates call the route generator for every AI flight path) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `src/backend/map_extractor/`, Phase Mapping; Master Project Plan — AI Module Use Recommendations (spatial planning assigned to Tier 1) |

### Role

You are a Principal Python Systems Developer with expertise in spatial reasoning, path planning, and military aviation simulation. You are building the route generation utility — the component that calculates tactically plausible flight paths from an origin airfield to a target area and back. This is a Tier 1 task because route quality depends on spatial reasoning about altitude profiles, approach angles, fuel constraints, and the relationship between airfield positions, front-line geometry, and target areas.

### Context

The Phase 5 Orchestrator generates complete missions by wiring together compiled modules. Each AI flight module needs a waypoint chain: take off from a specific airfield, climb to cruise altitude, fly toward the engagement area (derived from front-line data), execute the mission (patrol, intercept, attack), then return to base. Currently, waypoint coordinates are manually specified in the module JSON. The route generator automates this: given an origin airfield, a target area, and aircraft performance parameters, it produces a waypoint chain with plausible altitudes, speeds, and intermediate points.

Route plausibility is not cosmetic. A fighter patrol at 500m altitude over a heavily defended area will be engaged by ground fire before reaching the patrol zone. A bomber route that climbs to 6000m at maximum power and then descends to 2000m for the attack wastes fuel and time. The route generator must account for basic tactical considerations: cruise altitudes appropriate to the aircraft type and mission, approach angles that avoid overflying known airfield positions, and fuel-feasible round trips.

> **Relevant MMF Spec Rev 2 / FMEA Constraints**
> - Section 6.1: Static CAP validation prototype — the route generator produces the waypoint data structure that the compiler's waypoint emitter (Phase 1.10, R2) consumes
> - PI-001 (CRITICAL): Required Field Schema — generated waypoint data must include all fields the compiler expects (x, z, altitude, speed, area). Missing fields cause compilation abort.
> - PI-004 (MEDIUM): Spatial partitioning — the route generator outputs real map coordinates for proxy node placement; internal MCU coordinates are offset separately by the compiler

> **[PI-001] — CRITICAL** Route output must produce complete waypoint structures. The compiler will abort if any waypoint is missing required fields (x, z, altitude, speed). The route generator is the upstream source of these values for orchestrated missions.

### Inputs

- Task 4.2: populated geographic database (`data/map_databases/maps.sqlite3`) with validated airfield coordinates
- Task 4.3: front-line data (optional — enables front-line-aware routing; route generator must work without it for maps where front-line data is not yet available)
- Aircraft performance data: cruise speed, cruise altitude, climb rate (these are module-level parameters from the JSON schema's `flight` object)

### Requirements

**R1 — Route Calculation Engine**

```python
class RouteGenerator:
    def __init__(self, db: MapDatabase)

    def generate_route(
        self,
        origin_airfield_id: str,
        target_area: dict,        # {"x": float, "z": float}
        aircraft_params: dict,    # {"cruise_speed": int, "cruise_altitude": int, "climb_rate": int}
        mission_type: str,        # "patrol", "intercept", "ground_attack", "escort"
        return_to_base: bool = True
    ) -> list[dict]
    # Returns ordered list of waypoints: [{"x", "z", "altitude", "speed", "area"}]
```

**R2 — Altitude Profile**

Generate a realistic altitude profile:
- **Departure:** airfield altitude → climb to cruise altitude over first 1–2 waypoints
- **Cruise:** maintain cruise altitude en route to target area
- **Engagement:** altitude depends on mission type — patrol/intercept at cruise altitude, ground attack descends to attack altitude (500–1500m), escort matches bomber altitude
- **Return:** maintain altitude to home area, then descend to airfield altitude over final waypoints

**R3 — Intermediate Waypoints**

Do not generate a straight line from airfield to target. Insert intermediate waypoints:
- At least 1 intermediate waypoint between departure and target area
- Waypoints spaced 15–30km apart (realistic for WWII combat radius)
- If front-line data is available, ensure the route crosses the front line at a perpendicular or oblique angle (not parallel — parallel front-line crossing exposes the flight to extended ground fire)

**R4 — Speed Assignments**

Assign plausible speeds per segment:
- Climb segment: 70–80% of cruise speed
- Cruise segment: specified cruise speed
- Engagement area: 80–90% of cruise speed (maneuvering reserve)
- Return: cruise speed
- Descent: 80% of cruise speed

**R5 — Output Compatibility**

Each waypoint in the returned list must contain all fields the compiler's waypoint emitter expects:
- `x`: float (IL-2 engine X coordinate)
- `z`: float (IL-2 engine Z coordinate)
- `altitude`: int (meters)
- `speed`: int (km/h)
- `area`: int (waypoint area radius in meters — 500m default, 1500m for engagement area)

**R6 — Fuel Feasibility Check**

Calculate approximate total route distance. If the round-trip distance exceeds a configurable maximum (default: 300km for fighters, 600km for bombers), emit a warning. Do not abort — the user may have a reason — but log the overshoot.

> **EXIT CONDITION — Acceptance Criteria**
> - Generated route for a test case loads in BOSEditor (human can import waypoints and verify visually)
> - Route includes altitude profile: climb → cruise → engagement → return → descent
> - At least 1 intermediate waypoint between origin and target
> - All waypoints contain required fields (x, z, altitude, speed, area) — no nulls, no missing keys
> - Speed profile varies by segment (not a single constant speed)
> - Route for a Stalingrad intercept mission: departs from a known axis airfield, crosses the front line, reaches the patrol area at cruise altitude, and returns — total distance under 300km
> - Fuel feasibility warning emitted for a route exceeding 300km
> - Route is tactically plausible: no underground waypoints, no 90° turns at cruise speed, altitude appropriate to mission type

---

## Session 4.5 — Remaining Maps + Repeatable Process

| | |
|---|---|
| **Task ID** | 4.5 |
| **Component** | Map Data Extractor + Data (`src/backend/map_extractor/`, `data/map_databases/`) |
| **Model Tier** | Tier 2 — Sonnet 4.6 / Gemini 3 Flash |
| **Depends On** | 4.2 (established extraction pipeline and database schema) |
| **Delivers To** | Phase 5 (complete geographic database), Phase 6 (distribution — database bundled with executable) |
| **Reference** | See `ARCHITECTURE.md` — Directory Structure → `data/map_databases/`, Phase Mapping → 4.1–4.3 |

### Role

You are a Senior Python Developer. You are extending the geographic database to cover all remaining maps and documenting the extraction process so future DLC maps can be added within a single working day by any contributor.

### Context

Tasks 4.1–4.4 established the Extractor, validated it, and populated the database for primary maps. This session extends coverage to all remaining owned maps and produces a documented, repeatable process for adding future maps. IL-2 Great Battles releases DLC maps periodically — each new map must be extractable without modifying the Extractor's core code.

The deliverable is twofold: (1) a complete database covering every available map, and (2) a contributor-facing process document that specifies exactly what files to collect, what commands to run, and what validation to perform.

> **Relevant MMF Spec Rev 2 Sections**
> - Section 2.2: Syntax Agnosticism — the Extractor must handle new maps without core code changes; only the input files change
> - ARCHITECTURE.md: `data/map_databases/README.md` — process documentation belongs here

### Inputs

- Task 4.2: established extraction pipeline and populated database for primary maps
- Additional stock .Mission files for remaining maps (may require supplemental file collection from the project owner)
- Task 4.1: Extractor tool (proven on primary maps)

### Requirements

**R1 — Complete Map Coverage**

Run the Extractor on all remaining maps not covered in task 4.2. Add their airfields, spawn points, and front-line data (where available) to the SQLite database.

**R2 — Edge Case Handling**

Document and handle maps that may differ from the primary maps:
- Maps with non-standard airfield configurations (e.g., carrier-based maps if applicable)
- Maps with very few airfields (some smaller maps may have only 2–3)
- Maps where multiplayer templates are structured differently

If the Extractor fails on a specific map, fix the issue and document the fix as a known exception.

**R3 — Process Documentation**

Create `data/map_databases/README.md` documenting:
- Prerequisites: IL-2 installation, Python environment, parser library
- Step 1: Locate stock .Mission files for the new map
- Step 2: Run the Extractor CLI command
- Step 3: Run the coordinate validation spot-check (reference 4.2h procedure)
- Step 4: Import into the SQLite database
- Step 5: Run the integrity check
- Estimated time: under 1 working day for a single new map

**R4 — Database Version Metadata**

Add a metadata table to the SQLite database:

```sql
CREATE TABLE db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- Keys: 'version', 'last_updated', 'map_count', 'total_airfields'
```

Update metadata after each extraction run.

> **EXIT CONDITION — Acceptance Criteria**
> - All available maps are represented in the database (target: every map from 4.0h)
> - Process documented in `data/map_databases/README.md`
> - A new map (not previously extracted) is extractable by following the documented process within 1 working day
> - Database metadata table present and populated
> - No extraction errors on any map (edge cases documented and handled)
> - Database integrity checks pass on the full database

---

## Human Gates — Summary

Phase 4 contains two human gates. AI sessions cannot proceed past these gates until the required owner action is complete.

| Gate | Timing | Required Action | Exit Condition | Blocks |
|------|--------|-----------------|----------------|--------|
| 4.0h | Before any AI session | Provide stock .Mission files from IL-2 installation for each owned map. Include multiplayer templates. Minimum 5 maps. | Files accessible in working directory with multiplayer templates included | 4.1 |
| 4.2h | After task 4.1 completes | Spot-check extracted airfield coordinates in BOSEditor. Verify position accuracy, coalition, spawn placement, runway heading. | All checked airfields confirmed within 200m accuracy. Report any offsets. | 4.2 |

**Recommended execution sequence:**
- Complete gate 4.0h first (file collection)
- Run session 4.1 (builds the Extractor)
- Complete gate 4.2h (coordinate validation — cannot be skipped)
- Run sessions 4.2 and 4.3 in parallel (both depend on 4.1 but not on each other)
- Run session 4.4 after 4.2 completes (needs the populated airfield database)
- Run session 4.5 after 4.2 completes (extends the database; can run in parallel with 4.4)
