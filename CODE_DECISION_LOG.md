# Code Decision Log

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
| D-14 | `_format_value()` checks `bool` before `int` explicitly. Booleans serialize as `1`/`0`, not `True`/`False`. | Python `bool` is a subclass of `int`. IL-2 requires numeric `1`/`0` for flags. Explicit check prevents a future maintainer from adding a `bool` branch that emits Python literals. | If boolean fields suddenly output `True`/`False` in IL-2 files: someone reordered or removed the `bool` check in `_format_value()`. |
| D-15 | Unquoted string detection uses value-regex heuristic (`_UNQUOTED_RE`) as primary, with a negative key blacklist (`_STRING_ONLY_KEYS`) for defense-in-depth. Positive key whitelist rejected. Regex requires at least one `.` or `:` in the value — pure digit strings like `'0000'` are always quoted since the parser would have coerced them to `int` if they were unquoted. | IL-2 has more unquoted date/time keys than any static whitelist can enumerate. The regex catches all values that survived the D-07 coercion cascade as raw strings. The blacklist shields only freeform user text keys (`Name`, `Desc`, `Description`, `Model`, `Script`, `Class`, `Callsign`) — a short, stable set. | If a new freeform text key is discovered that matches the unquoted regex: add it to `_STRING_ONLY_KEYS`. If IL-2 requires an unquoted value for a blacklisted key: remove that key from the blacklist — the regex will handle it automatically. If a pure-digit quoted string like `TCodeColor = "0000"` serializes wrong: verify the regex requires a `.` or `:`. |
| D-16 | `_sanitize_string()` logs a warning when PI-002 filter mutates a value. No silent data mutation. | Silent string mutation in a data pipeline makes debugging impossible for mission builders. Warning log preserves PI-002 compliance while providing traceability. | If log output is noisy on corpus files: the corpus itself contains reserved characters. This is expected for first-pass validation. Suppress with log level config, do not remove the warning. |
| D-17 | Separator metadata (`'separator': ':'` or `','`) injected into block dicts by `deserializer.py`. Serializer reads `block.get('separator', ':')`. | Intentional technical debt. Alternative is hardcoding schema rules (`if block.type == 'WindLayers'`) into the serializer, making it rigid and schema-coupled. This keeps the serializer schema-agnostic. | If a new row-type block appears that uses a different separator: patch the deserializer's row-detection branch to inject the correct separator value. The serializer will handle it automatically. |
| D-18 | `write_file()` enforces CRLF (`newline='\r\n'`). `serialize()` returns LF-only strings. | IL-2 is Windows-only. CRLF at the file I/O boundary guarantees correct output regardless of dev/CI OS. Keeping `serialize()` LF-only preserves clean in-memory string handling. | If IL-2 editor rejects written files: verify `newline='\r\n'` is still on the `open()` call. If round-trip binary diff fails on line endings: the test must read in binary mode (`'rb'`), not text mode. |

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
| A-06 | MITIGATED | No freeform user string in IL-2 mission files matches the unquoted regex `^-?\d[\d.:-]*[.:].+$` for keys outside `_STRING_ONLY_KEYS`. | String value on a non-blacklisted key serializes unquoted, IL-2 engine misparses it. Add the offending key to `_STRING_ONLY_KEYS` per D-15. |

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
| F-06 | 0.3 | `_sanitize_string()` silently stripped reserved characters with no log trail. | Added `logging.warning()` on mutation. D-16. |
| F-07 | 0.3 | `bool` type dispatch relied on implicit Python `isinstance(True, int)` quirk. | Explicit `bool` check added before `int` in `_format_value()`. D-14. |
| F-08 | 0.3 | `_is_unquoted_string()` used regex-only detection with no protection for freeform text keys. A user string like `Name = 12.5` would serialize unquoted. Also, pure-digit quoted strings like `TCodeColor = "0000"` matched the original regex and lost leading zeros on round-trip. | Added `_STRING_ONLY_KEYS` negative blacklist and tightened regex to require `.` or `:`. D-15, A-06. |
| F-09 | 0.3 | Float comparison in `_compare_blocks()` used `abs(a - b) < 1e-9`, which fails at both near-zero and large magnitudes (IL-2 coordinates reach 100k+). | Replaced with `pytest.approx()` (relative tolerance, scales correctly). |
| F-10 | 0.3 | `write_file()` used OS-default line endings. Linux/macOS CI produces LF, breaking IL-2 (Windows-only) and causing Git diff churn. | Hardcoded `newline='\r\n'` in `write_file()`. D-18. Test updated to assert CRLF specifically. |

---

## 6. Downstream Phase Coupling

Decisions in the parser directly affect these future components. When debugging a downstream failure, trace back to the decision ID here.

| Phase | Component | Depends On | Critical Decisions |
|-------|-----------|------------|--------------------|
| 0.3 | ASCII Writer | Node structure, comment positions, blank lines, special block representations, separator metadata | D-01, D-02, D-03, D-04, D-11, D-12, D-14, D-15, D-16, D-17 |
| 0.4 | MCU Type Catalog | Field access ergonomics, type coercion accuracy, numeric keys | D-01, D-05, D-07, D-13 |
| 1.1–1.8 | MMF Compiler | PI-001 field validation, `get_field()`/`get_children()` API | D-01, D-04, D-05, D-12, D-13 |
| 2.2 | Module Reverse Engineer | Field iteration, child block traversal, special block handling | D-01, D-04, D-09, D-12, D-13 |
| 4.x | Map Data Extractor | `parse_file()` API, numeric coercion for coordinates, encoding fallback | D-06, D-07, F-01 |

---

*Last updated: Phase 0.3 Rev 2 — Test suite hardening. D-18 added, F-09/F-10 resolved.*
