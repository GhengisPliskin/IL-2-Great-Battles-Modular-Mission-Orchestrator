# MMO Code Decision Log

**IL-2 Great Battles — Modular Mission Orchestrator**

*Living document. Updated each phase. First place to look when something breaks.*

This log records every structural code decision made during development and its downstream implications. Each entry identifies what was decided, why, and where to start debugging if that decision causes failures in later phases.

---

## 1. Data Model Decisions

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-01 | Separate `fields`/`children` lists instead of unified `entries` with `__block__` sentinel. | Downstream compiler (PI-001 validation) and Reverse Engineer (0.4 MCU catalog) iterate fields constantly. Filtering past hundreds of child blocks per lookup is unnecessary overhead and unergonomic code. | If the writer (0.3) produces reordered output vs. original file: fields and children were interleaved in source. See D-02. |
| D-02 | Start WITHOUT an `_order` tracker for field/child interleaving. Assume IL-2 tolerates intra-block reordering. | 97-file corpus validation will confirm or deny. Over-engineering the order tracker before evidence demands it delays delivery. | If round-trip diff fails on block reordering: retrofit an `_order` list that records original interleaved sequence. Compare parse→serialize→parse output semantically, not textually. |
| D-03 | `preceding_comments` list on every block node. Top-level comments in `result['comments']`. Trailing in `result['trailing_comments']`. Split heuristic: last blank-line gap separates header from block-preceding comments. | Phase 0.2 acceptance: output matches input (whitespace-normalized). Hoisting all comments to top-level makes positional re-serialization impossible. **NOTE:** If no blank line separates comments from first block, all comments land in `preceding_comments`, not `result['comments']`. Writer must check both. | If comments appear in wrong position after round-trip: check whether comments are between fields inside a block (not between blocks). May need field-level comment attachment. |
| D-04 | Special blocks (Carriages, WindLayers, Countries, Boundary) get dedicated node representations — not forced into fields/children model. | These blocks use non-standard internal syntax (bare strings, colon-separated tuples, comma-separated rows). Forcing them into key-value pairs loses structural information. | If a new special block type is found in corpus that wasn't anticipated: the special block detection logic in `parse_block()` needs a new branch. Check what token follows the opening brace. |
| D-05 | Duplicate keys preserved as separate ordered entries in `fields` list. | IL-2 files use duplicate keys (multiple `Country`, `Enabled`, `MultiplayerPlaneConfig`). A dict would silently drop duplicates. | If `get_field()` returns wrong value for a duplicate key: it returns the first match. Use `get_fields()` for all values. If order matters, the fields list index is authoritative. |

---

## 2. Tokenizer / Lexer Decisions

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-06 | Tokenizer emits raw character sequences for numeric-like tokens. No type classification at lexer level. | Dates (`30.9.1944`) and times (`6:49:38`) contain dots and colons that break naive float/int detection. Tokenizer consumes longest run of `[0-9.:-]` and passes raw string to parser. | If tokenizer chokes on a numeric-like value: check whether a new character appears in numeric context. Extend the character class in the tokenizer's numeric consumption loop. |
| D-07 | Type coercion cascade lives in parser's `parse_value()`: `int()` → `float()` (with multi-dot AND colon guard) → raw string fallback. | Strict ordering prevents `30.9.1944` from partially parsing as float `30.9`. The colon guard rejects time strings from float conversion without needing try/except. Multi-dot guard rejects date strings. | If a legitimate float with scientific notation fails: the cascade doesn't handle `e` notation. Add it to the float branch if corpus evidence requires it. Currently no IL-2 files use scientific notation. |
| D-08 | Quoted strings preserved literally — no escape sequence processing. Backslash paths kept as-is. | IL-2 uses backslash paths (`LuaScripts\\WorldObjects\\...`) that are not escape sequences. Processing them would corrupt file paths. | If a string value has unexpected characters: verify the tokenizer's string consumption handles the specific character. Check for unmatched quotes or embedded newlines in the source file. |

---

## 3. Parser Architecture Decisions

| # | Decision | Rationale | If This Breaks, Check... |
|---|----------|-----------|--------------------------|
| D-09 | Special block detection by peeking at first token after opening brace: `STRING`+`SEMICOLON` → Carriages, `NUMBER`+`COLON` → colon-row, `NUMBER`+`COMMA` → comma-row, otherwise standard. | Four syntactically distinct block body types exist in IL-2 format. Detection must happen before consuming any body tokens. | If a new block type uses a different internal syntax: the peek logic in `parse_block()` returns wrong mode. Add a new detection branch. Check what the first two tokens inside the brace actually are for that block type. |
| D-10 | `ParseError` is a hard fail — no partial recovery. Exception carries line number, column, and offending token. | Partial recovery adds complexity with no benefit for this use case. A malformed mission file should fail loudly so the user can fix it in the editor, not silently produce corrupt output. | If `ParseError` reports wrong line number: the tokenizer's line counter may drift if it doesn't count newlines inside multi-line constructs (shouldn't exist in IL-2, but verify). |
| D-11 | Blank-line presence tracked between blocks (`blank_lines_before` count on every block node). | Writer needs to reproduce visual spacing between blocks for round-trip diff fidelity. | If output has wrong vertical spacing vs. original: check whether `blank_lines_before` is being set correctly by `_skip_newlines_and_buffer_comments` when consuming whitespace between blocks. |
| D-12 | **[CORPUS FINDING]** Boundary block: comma-separated coordinate rows (`NUMBER COMMA NUMBER... SEMICOLON`). Detected by peek: `NUMBER` followed by `COMMA`. Stored as `rows` list of tuples. | Discovered during corpus validation. Fourth special block type not in original spec. Uses same `rows` key as WindLayers (3+ element tuples) since the data shape is the same: ordered tuples of numbers. | If Boundary rows have variable-length tuples within the same block: the current parser handles this correctly (each row is independent). If a block starts with `NUMBER COMMA` but isn't coordinate data: detection heuristic is wrong — check what the block type name actually is. |
| D-13 | **[CORPUS FINDING]** Damaged block: numeric keys (`-1`, `0`, `1`) used as field names with `EQUALS` syntax. `_parse_standard_body` accepts `NUMBER` tokens as keys, stored as raw strings in fields list. | Discovered during corpus validation. Standard blocks assumed `IDENTIFIER`-only keys. Damaged blocks use integer indices as field names. Keys stored as strings (`'-1'`, `'0'`, `'1'`) not ints to maintain consistent tuple structure: `(str_key, value)`. | If `get_field()` lookups fail for numeric keys: caller must pass string key, not int. e.g., `get_field(node, '-1')` not `get_field(node, -1)`. If another block type uses non-identifier keys: same pattern applies — `_parse_standard_body` already handles it. |

---

## 4. Assumptions Register

Status tracks whether corpus validation has confirmed, invalidated, or left assumptions unverified.

| # | Status | Assumption | What Breaks If Wrong |
|---|--------|-----------|----------------------|
| A-01 | UNVERIFIED | IL-2 engine tolerates intra-block reordering of fields and child blocks. | Round-trip diff fails. Retrofit `_order` tracker per D-02. |
| A-02 | UNVERIFIED | Comments only appear between blocks, never inline within a field line (e.g., not `Index = 5; # spawn point`). | Comments lost during parse. Need field-level comment attachment, not just `preceding_comments` on blocks. |
| A-03 | UNVERIFIED | No IL-2 mission file uses scientific notation for floats. | Type coercion cascade in `parse_value()` rejects valid numbers. Add `e` handling to float branch. |
| A-04 | **INVALIDATED** | Originally assumed only three special block types (Carriages, WindLayers, Countries). Corpus validation found Boundary (comma-separated coordinate rows) and Damaged (numeric keys). Parser updated: D-12 and D-13. | RESOLVED. Detection branches added. If a fifth special type is found, add another peek branch in `parse_block()`. |
| A-05 | UNVERIFIED | Quoted strings never contain escaped quotes (no `\"` inside strings). | Tokenizer's string reader terminates early on embedded quote. Need escape-aware consumption. |

---

## 5. Post-Review Fixes

Issues identified during code review. All resolved.

| # | Phase | Issue | Resolution |
|---|-------|-------|------------|
| F-01 | 0.2 | `parse_file()` used `encoding='utf-8'` only. Community mission files with cp1252/latin-1 accented characters would throw `UnicodeDecodeError`, bypassing `ParseError` reporting. | Replaced with encoding fallback cascade: `utf-8-sig` → `utf-8` → `cp1252` → `latin-1`. Falls through to `ParseError` if all fail. |
| F-02 | 0.2 | Dead `_skip_newlines` method (without `_and_buffer_comments`) was never called but had fragile blank-line counting logic. | Deleted. Only `_skip_newlines_and_buffer_comments` remains — correct and active code path. |
| F-03 | 0.2 | Numeric token character class included `+` which could silently misparse tokens like `1.5+2` as a single raw string. | Removed `+` from character class. Now `[0-9.:-]` only. Corpus scan confirmed no IL-2 files use `+` in numeric contexts. |
| F-04 | 0.2 | Missing test coverage: trailing_comments, blank_lines_before values, empty file, comments-only file, string arrays. | Six new tests added: `test_trailing_comments`, `test_multiple_trailing_comments`, `test_empty_file`, `test_comments_only_no_blocks`, `test_blank_lines_before_tracked`, `test_string_array`. |
| F-05 | 0.2 | `_split_header_comments` behavior undocumented: when no blank line separates comments from first block, all comments land in `preceding_comments`, not `result['comments']`. | Added Phase 0.3 writer note and expanded docstring documenting the exact behavior and its round-trip implications. |

---

## 6. Downstream Phase Coupling

Decisions in the parser directly affect these future components. When debugging a downstream failure, trace back to the decision ID here.

| Phase | Component | Depends On | Critical Decisions |
|-------|-----------|------------|--------------------|
| 0.3 | ASCII Writer | Node structure, comment positions, blank lines, special block representations | D-01, D-02, D-03, D-04, D-11, D-12 |
| 0.4 | MCU Type Catalog | Field access ergonomics, type coercion accuracy, numeric keys | D-01, D-05, D-07, D-13 |
| 1.1–1.8 | MMF Compiler | PI-001 field validation, `get_field()`/`get_children()` API | D-01, D-04, D-05, D-12, D-13 |
| 2.2 | Module Reverse Engineer | Field iteration, child block traversal, special block handling | D-01, D-04, D-09, D-12, D-13 |
| 4.x | Map Data Extractor | `parse_file()` API, numeric coercion for coordinates, encoding fallback | D-06, D-07, F-01 |

---

*Last updated: Phase 0.2 Rev 2 — Post-review fixes applied, corpus findings (D-12, D-13) incorporated, A-04 invalidated*
