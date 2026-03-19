"""
IL-2 Great Battles .Mission / .Group file parser.

Parses the proprietary ASCII format into structured Python dictionaries.
This is the foundational layer of the MMF three-tier architecture —
every downstream component (compiler, reverse engineer, map extractor)
imports this module.

Public API:
    parse_file(path)   -> dict
    parse_string(text)  -> dict

Convenience helpers:
    get_field(node, key)              -> value or None
    get_fields(node, key)             -> list of values
    get_children(node, type_name=None) -> list of child nodes
"""


# ---------------------------------------------------------------------------
# ParseError
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """Raised when the parser encounters malformed or unexpected syntax."""

    def __init__(self, message, line=None, column=None, token=None):
        self.line = line
        self.column = column
        self.token = token
        parts = []
        if line is not None:
            loc = f"line {line}"
            if column is not None:
                loc += f", col {column}"
            parts.append(f"[{loc}]")
        parts.append(message)
        if token is not None:
            parts.append(f"(got {token!r})")
        super().__init__(" ".join(parts))


# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------

LBRACE = 'LBRACE'
RBRACE = 'RBRACE'
LBRACKET = 'LBRACKET'
RBRACKET = 'RBRACKET'
EQUALS = 'EQUALS'
SEMICOLON = 'SEMICOLON'
COLON = 'COLON'
COMMA = 'COMMA'
STRING = 'STRING'
NUMBER = 'NUMBER'
IDENTIFIER = 'IDENTIFIER'
COMMENT = 'COMMENT'
NEWLINE = 'NEWLINE'
EOF = 'EOF'


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class Tokenizer:
    """Character-level lexer for IL-2 mission files.

    Produces tokens as (type, value, line) tuples.
    Numeric tokens are emitted as raw strings — the parser handles coercion.
    NEWLINE tokens are emitted so the parser can count blank lines.
    """

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self._tokenize()
        self._idx = 0

    def _advance(self):
        ch = self.text[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _peek(self):
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _tokenize(self):
        while self.pos < len(self.text):
            ch = self.text[self.pos]

            # Newlines — emitted for blank-line counting
            if ch == '\n':
                self.tokens.append((NEWLINE, '\n', self.line))
                self._advance()
                continue

            # Skip other whitespace
            if ch in (' ', '\t', '\r'):
                self._advance()
                continue

            line = self.line
            col = self.col

            # Comment
            if ch == '#':
                start = self.pos
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self._advance()
                self.tokens.append((COMMENT, self.text[start:self.pos], line))
                continue

            # Single-character tokens
            if ch == '{':
                self.tokens.append((LBRACE, '{', line))
                self._advance()
                continue
            if ch == '}':
                self.tokens.append((RBRACE, '}', line))
                self._advance()
                continue
            if ch == '[':
                self.tokens.append((LBRACKET, '[', line))
                self._advance()
                continue
            if ch == ']':
                self.tokens.append((RBRACKET, ']', line))
                self._advance()
                continue
            if ch == '=':
                self.tokens.append((EQUALS, '=', line))
                self._advance()
                continue
            if ch == ';':
                self.tokens.append((SEMICOLON, ';', line))
                self._advance()
                continue
            if ch == ':':
                self.tokens.append((COLON, ':', line))
                self._advance()
                continue
            if ch == ',':
                self.tokens.append((COMMA, ',', line))
                self._advance()
                continue

            # Quoted string — no escape processing
            if ch == '"':
                self._advance()  # consume opening quote
                start = self.pos
                while self.pos < len(self.text) and self.text[self.pos] != '"':
                    self._advance()
                if self.pos >= len(self.text):
                    raise ParseError("Unterminated string literal", line, col)
                value = self.text[start:self.pos]
                self._advance()  # consume closing quote
                self.tokens.append((STRING, value, line))
                continue

            # Numeric token: starts with digit or minus-followed-by-digit
            # Consume longest run of [0-9.:\-] so dates/times stay as one token
            if ch.isdigit() or (ch == '-' and self.pos + 1 < len(self.text)
                                and self.text[self.pos + 1].isdigit()):
                start = self.pos
                self._advance()
                while self.pos < len(self.text) and self.text[self.pos] in '0123456789.:-':
                    self._advance()
                self.tokens.append((NUMBER, self.text[start:self.pos], line))
                continue

            # Identifier: letters, digits, underscores
            if ch.isalpha() or ch == '_':
                start = self.pos
                self._advance()
                while self.pos < len(self.text) and (self.text[self.pos].isalnum()
                                                      or self.text[self.pos] == '_'):
                    self._advance()
                self.tokens.append((IDENTIFIER, self.text[start:self.pos], line))
                continue

            raise ParseError(f"Unexpected character: {ch!r}", line, col)

        self.tokens.append((EOF, None, self.line))

    # --- Token stream access ---

    def next(self):
        tok = self.tokens[self._idx]
        self._idx += 1
        return tok

    def peek(self, offset=0):
        idx = self._idx + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return (EOF, None, self.line)

    def expect(self, tok_type):
        tok = self.next()
        if tok[0] != tok_type:
            raise ParseError(
                f"Expected {tok_type}", tok[2], token=tok[1]
            )
        return tok


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    """Recursive-descent parser for IL-2 mission/group files."""

    def __init__(self, tokenizer):
        self.tok = tokenizer
        self._comment_buffer = []
        self._blank_line_count = 0

    # --- value coercion ---

    @staticmethod
    def _coerce_value(raw):
        """Convert a raw numeric string to int, float, or leave as str."""
        try:
            return int(raw)
        except ValueError:
            pass
        if raw.count('.') <= 1 and ':' not in raw:
            try:
                return float(raw)
            except ValueError:
                pass
        return raw  # dates, times, anything else

    # --- helpers ---

    def _skip_newlines_and_buffer_comments(self):
        """Consume newlines and comments, buffering comments for the next block.

        Inserts None markers into the comment buffer at blank-line boundaries
        so _split_header_comments can find gaps between comment groups.
        """
        blank_lines = 0
        consecutive_newlines = 0
        while True:
            tt = self.tok.peek()[0]
            if tt == NEWLINE:
                self.tok.next()
                consecutive_newlines += 1
            elif tt == COMMENT:
                if consecutive_newlines >= 2:
                    blank_lines += consecutive_newlines - 1
                    # Insert blank-line marker into comment buffer
                    self._comment_buffer.append(None)
                consecutive_newlines = 0
                tok = self.tok.next()
                self._comment_buffer.append(tok[1])
            else:
                if consecutive_newlines >= 2:
                    blank_lines += consecutive_newlines - 1
                    # Insert blank-line marker (gap before next block)
                    self._comment_buffer.append(None)
                break
        self._blank_line_count = blank_lines

    def _flush_comments(self):
        """Return buffered comments and reset. Strips None markers."""
        comments = [c for c in self._comment_buffer if c is not None]
        self._comment_buffer = []
        return comments

    def _flush_blank_lines(self):
        """Return blank line count and reset."""
        bl = self._blank_line_count
        self._blank_line_count = 0
        return bl

    # --- top-level parse ---

    def parse(self):
        """Parse the full file. Returns top-level result dict."""
        header_comments = []
        blocks = []
        first_block_seen = False

        while self.tok.peek()[0] != EOF:
            if self.tok.peek()[0] == NEWLINE:
                self._skip_newlines_and_buffer_comments()
                continue
            if self.tok.peek()[0] == COMMENT:
                tok = self.tok.next()
                self._comment_buffer.append(tok[1])
                continue
            if self.tok.peek()[0] == IDENTIFIER:
                if not first_block_seen:
                    # Split: comments before a blank-line gap are header comments;
                    # comments after the gap are preceding_comments on this block.
                    # Simple heuristic: if there's a blank line in the buffer,
                    # everything before the last blank-line gap is header.
                    header_comments = self._split_header_comments()
                    first_block_seen = True
                block = self._parse_block()
                blocks.append(block)
                self._skip_newlines_and_buffer_comments()
                continue
            tok = self.tok.peek()
            raise ParseError(
                "Expected block or EOF", tok[2], token=tok[1]
            )

        trailing_comments = self._flush_comments()

        return {
            'comments': header_comments,
            'blocks': blocks,
            'trailing_comments': trailing_comments,
        }

    # NOTE FOR PHASE 0.3 WRITER:
    # If no blank line separates header comments from the first block,
    # all comments land in the first block's preceding_comments (not in
    # result['comments']). The writer must emit preceding_comments before
    # the block's type name to reconstruct the original layout.
    def _split_header_comments(self):
        """Split buffered comments into header vs preceding-block comments.

        Uses blank-line markers (None) in the comment buffer to find the last
        gap. Comments before the last gap become header comments; comments
        after become preceding_comments on the first block.

        If there is NO blank line between comments and the first block, ALL
        comments become preceding_comments on that block and the top-level
        comments list is empty. Example::

            # Mission File Version = 1.0;
            Options {

        Here result['comments'] is [] and
        result['blocks'][0]['preceding_comments'] contains the version comment.
        This preserves exact position for round-trip fidelity.
        """
        if not self._comment_buffer:
            return []

        # Find last blank-line marker (None) in buffer
        last_gap = -1
        for i, item in enumerate(self._comment_buffer):
            if item is None:
                last_gap = i

        if last_gap == -1:
            # No gaps — all comments are preceding_comments (no header)
            return []

        # Split at last gap
        header = [c for c in self._comment_buffer[:last_gap] if c is not None]
        self._comment_buffer = [c for c in self._comment_buffer[last_gap + 1:] if c is not None]
        return header

    # --- block parsing ---

    def _parse_block(self):
        """Parse a named block: IDENTIFIER { body }"""
        preceding_comments = self._flush_comments()
        blank_lines = self._flush_blank_lines()

        name_tok = self.tok.expect(IDENTIFIER)
        block_type = name_tok[1]

        # Skip newlines between name and opening brace
        while self.tok.peek()[0] == NEWLINE:
            self.tok.next()

        self.tok.expect(LBRACE)

        # Skip newlines after opening brace
        while self.tok.peek()[0] == NEWLINE:
            self.tok.next()

        # Detect special block body mode
        first = self.tok.peek()
        second = self.tok.peek(1)

        # Empty block
        if first[0] == RBRACE:
            self.tok.next()  # consume }
            return {
                'type': block_type,
                'fields': [],
                'children': [],
                'preceding_comments': preceding_comments,
                'blank_lines_before': blank_lines,
            }

        # Carriages-style: bare strings
        if first[0] == STRING and second[0] == SEMICOLON:
            items = self._parse_bare_string_body()
            return {
                'type': block_type,
                'items': items,
                'preceding_comments': preceding_comments,
                'blank_lines_before': blank_lines,
            }

        # Colon-row style: WindLayers / Countries
        if first[0] == NUMBER and second[0] == COLON:
            rows = self._parse_colon_row_body()
            # Determine if these are tuples (3+ values) or mappings (2 values)
            if rows and len(rows[0]) == 2:
                return {
                    'type': block_type,
                    'mapping': rows,
                    'preceding_comments': preceding_comments,
                    'blank_lines_before': blank_lines,
                }
            else:
                return {
                    'type': block_type,
                    'rows': rows,
                    'separator': ':',
                    'preceding_comments': preceding_comments,
                    'blank_lines_before': blank_lines,
                }

        # Boundary-style: comma-separated coordinate rows (NUMBER COMMA ...)
        if first[0] == NUMBER and second[0] == COMMA:
            rows = self._parse_comma_row_body()
            return {
                'type': block_type,
                'rows': rows,
                'separator': ',',
                'preceding_comments': preceding_comments,
                'blank_lines_before': blank_lines,
            }

        # Standard block body
        fields, children = self._parse_standard_body()
        return {
            'type': block_type,
            'fields': fields,
            'children': children,
            'preceding_comments': preceding_comments,
            'blank_lines_before': blank_lines,
        }

    def _parse_standard_body(self):
        """Parse key-value pairs and child blocks until }."""
        fields = []
        children = []

        while True:
            # Skip newlines and comments between entries
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()

            tt = self.tok.peek()[0]

            if tt == RBRACE:
                self.tok.next()
                return fields, children

            if tt == COMMENT:
                tok = self.tok.next()
                self._comment_buffer.append(tok[1])
                continue

            if tt in (IDENTIFIER, NUMBER):
                lookahead = self._peek_past_newlines(1)

                if lookahead[0] == EQUALS:
                    # Key-value pair (key can be IDENTIFIER or NUMBER for Damaged blocks)
                    key_tok = self.tok.next()
                    key = key_tok[1]
                    self.tok.expect(EQUALS)
                    while self.tok.peek()[0] == NEWLINE:
                        self.tok.next()
                    value = self._parse_value()
                    while self.tok.peek()[0] == NEWLINE:
                        self.tok.next()
                    self.tok.expect(SEMICOLON)
                    fields.append((key, value))

                elif tt == IDENTIFIER and (lookahead[0] in (LBRACE,) or lookahead[0] == IDENTIFIER):
                    # Child block
                    child = self._parse_block()
                    children.append(child)

                else:
                    tok = self.tok.peek()
                    raise ParseError(
                        f"Unexpected token after '{tok[1]}'",
                        tok[2], token=lookahead[1]
                    )
            else:
                tok = self.tok.peek()
                raise ParseError(
                    "Expected field name, child block, or '}'",
                    tok[2], token=tok[1]
                )

    def _peek_past_newlines(self, start_offset=0):
        """Peek past any NEWLINE tokens starting from offset."""
        offset = start_offset
        while self.tok.peek(offset)[0] == NEWLINE:
            offset += 1
        return self.tok.peek(offset)

    def _parse_bare_string_body(self):
        """Parse Carriages-style body: list of bare quoted strings."""
        items = []
        while True:
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            if self.tok.peek()[0] == RBRACE:
                self.tok.next()
                return items
            tok = self.tok.expect(STRING)
            items.append(tok[1])
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            self.tok.expect(SEMICOLON)

    def _parse_colon_row_body(self):
        """Parse WindLayers/Countries-style body: colon-separated value rows."""
        rows = []
        while True:
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            if self.tok.peek()[0] == RBRACE:
                self.tok.next()
                return rows
            # Parse one row: value (COLON value)+ SEMICOLON
            values = []
            tok = self.tok.expect(NUMBER)
            values.append(self._coerce_value(tok[1]))
            while self.tok.peek()[0] == COLON:
                self.tok.next()  # consume :
                # Skip whitespace/newlines
                while self.tok.peek()[0] == NEWLINE:
                    self.tok.next()
                tok = self.tok.expect(NUMBER)
                values.append(self._coerce_value(tok[1]))
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            self.tok.expect(SEMICOLON)
            rows.append(tuple(values))

    def _parse_comma_row_body(self):
        """Parse Boundary-style body: comma-separated coordinate rows."""
        rows = []
        while True:
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            if self.tok.peek()[0] == RBRACE:
                self.tok.next()
                return rows
            # Parse one row: NUMBER (COMMA NUMBER)* SEMICOLON
            values = []
            tok = self.tok.expect(NUMBER)
            values.append(self._coerce_value(tok[1]))
            while self.tok.peek()[0] == COMMA:
                self.tok.next()  # consume ,
                while self.tok.peek()[0] == NEWLINE:
                    self.tok.next()
                tok = self.tok.expect(NUMBER)
                values.append(self._coerce_value(tok[1]))
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            self.tok.expect(SEMICOLON)
            rows.append(tuple(values))

    # --- value parsing ---

    def _parse_value(self):
        """Parse a value: string, number, or array."""
        tt = self.tok.peek()[0]

        if tt == STRING:
            tok = self.tok.next()
            return tok[1]

        if tt == NUMBER:
            tok = self.tok.next()
            return self._coerce_value(tok[1])

        if tt == LBRACKET:
            return self._parse_array()

        tok = self.tok.peek()
        raise ParseError(
            "Expected value (string, number, or array)",
            tok[2], token=tok[1]
        )

    def _parse_array(self):
        """Parse an array: [ (value (COMMA value)*)? ]"""
        self.tok.expect(LBRACKET)
        items = []

        while self.tok.peek()[0] == NEWLINE:
            self.tok.next()

        if self.tok.peek()[0] == RBRACKET:
            self.tok.next()
            return items

        # First element
        tok = self.tok.next()
        if tok[0] == NUMBER:
            items.append(self._coerce_value(tok[1]))
        elif tok[0] == STRING:
            items.append(tok[1])
        else:
            raise ParseError("Expected array element", tok[2], token=tok[1])

        while self.tok.peek()[0] == COMMA:
            self.tok.next()  # consume comma
            while self.tok.peek()[0] == NEWLINE:
                self.tok.next()
            tok = self.tok.next()
            if tok[0] == NUMBER:
                items.append(self._coerce_value(tok[1]))
            elif tok[0] == STRING:
                items.append(tok[1])
            else:
                raise ParseError("Expected array element", tok[2], token=tok[1])

        while self.tok.peek()[0] == NEWLINE:
            self.tok.next()
        self.tok.expect(RBRACKET)
        return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_string(content):
    """Parse an IL-2 format string. Returns top-level result dict."""
    tokenizer = Tokenizer(content)
    parser = Parser(tokenizer)
    return parser.parse()


def parse_file(path):
    """Read and parse an IL-2 .Mission or .Group file. Returns top-level result dict."""
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
            return parse_string(content)
        except UnicodeDecodeError:
            continue
    raise ParseError(f"Cannot decode file: {path}")


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_field(node, key):
    """Return the first value for *key* in the node's fields, or None."""
    for k, v in node.get('fields', []):
        if k == key:
            return v
    return None


def get_fields(node, key):
    """Return all values for *key* in the node's fields (handles duplicate keys)."""
    return [v for k, v in node.get('fields', []) if k == key]


def get_children(node, type_name=None):
    """Return child block nodes, optionally filtered by type name."""
    children = node.get('children', [])
    if type_name is None:
        return children
    return [c for c in children if c.get('type') == type_name]
