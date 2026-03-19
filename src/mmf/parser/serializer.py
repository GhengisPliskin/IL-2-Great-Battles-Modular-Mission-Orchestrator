"""
IL-2 Great Battles .Mission / .Group file writer.

Serializes the Python dictionary structure produced by the parser
(deserializer.py) back into the proprietary IL-2 ASCII format.
This is the inverse of the parser and the output channel for every
compiler primitive in the MMF pipeline.

Public API:
    serialize(data)             -> str
    write_file(data, path)      -> None
"""

import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# D-15: Heuristic regex for dates/times that must be emitted unquoted.
# Matches values that were originally NUMBER tokens but failed int/float
# coercion in the parser (multi-dot dates like 30.9.1944, colon times
# like 6:49:38). Must contain at least one dot or colon — pure digit
# strings (e.g., '0000') are quoted strings, not unquoted numbers,
# because the parser would have coerced them to int if unquoted.
_UNQUOTED_RE = re.compile(r'^-?\d[\d.:-]*[.:].+$')

# PI-002: Reserved characters that must be stripped from string values.
_RESERVED_RE = re.compile(r'[{}\[\];="]')

# D-15: Keys known to carry freeform user text — always quoted regardless
# of value pattern. Defense-in-depth against the unquoted regex matching
# user-authored strings like Name = "12.5".
_STRING_ONLY_KEYS = frozenset({
    "Name", "Desc", "Description", "Model",
    "Script", "Class", "Callsign",
})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sanitize_string(value):
    """Strip PI-002 reserved characters from a string value.

    Logs a warning when characters are actually removed so that
    mission builders have a traceable breadcrumb (D-16).
    """
    sanitized = _RESERVED_RE.sub('', value)
    if sanitized != value:
        logger.warning(
            "Sanitized reserved characters from string: %r -> %r",
            value, sanitized,
        )
    return sanitized


def _is_unquoted_string(key, value):
    """Return True if *value* should be emitted without quotes.

    Short-circuits to False for keys in _STRING_ONLY_KEYS (D-15).
    Otherwise checks whether the value matches the unquoted numeric-
    string pattern (dates, times, and similar).
    """
    if key in _STRING_ONLY_KEYS:
        return False
    return bool(_UNQUOTED_RE.match(value))


def _format_value(key, value):
    """Format a single field value for IL-2 ASCII output.

    Returns the formatted value string (without trailing semicolon —
    the caller adds that along with the key and equals sign).
    """
    # D-14: bool MUST be checked before int — Python bool is a subclass
    # of int. IL-2 expects 1/0 for boolean flags, not True/False.
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        if _is_unquoted_string(key, value):
            return value
        return f'"{_sanitize_string(value)}"'
    if isinstance(value, list):
        return _format_array(value)
    raise TypeError(f"Unsupported value type: {type(value).__name__}")


def _format_array(items):
    """Format an array value as [elem1,elem2,elem3]."""
    if not items:
        return '[]'
    parts = []
    for item in items:
        if isinstance(item, bool):
            parts.append(str(int(item)))
        elif isinstance(item, (int, float)):
            parts.append(str(item))
        elif isinstance(item, str):
            # Array string elements are always quoted
            parts.append(f'"{_sanitize_string(item)}"')
        else:
            raise TypeError(
                f"Unsupported array element type: {type(item).__name__}"
            )
    return f'[{",".join(parts)}]'


# ---------------------------------------------------------------------------
# Block serializers
# ---------------------------------------------------------------------------

def _serialize_block(block, indent, lines):
    """Dispatch to the appropriate body serializer based on block keys."""
    pad = ' ' * indent
    lines.append(f'{pad}{block["type"]}')
    lines.append(f'{pad}{{')

    if 'items' in block:
        _serialize_carriages_body(block, indent + 2, lines)
    elif 'mapping' in block:
        _serialize_mapping_body(block, indent + 2, lines)
    elif 'rows' in block:
        _serialize_rows_body(block, indent + 2, lines)
    else:
        _serialize_standard_body(block, indent + 2, lines)

    lines.append(f'{pad}}}')


def _serialize_standard_body(block, indent, lines):
    """Emit fields then children for a standard block."""
    pad = ' ' * indent

    for key, value in block.get('fields', []):
        formatted = _format_value(key, value)
        lines.append(f'{pad}{key} = {formatted};')

    for child in block.get('children', []):
        _emit_block_with_comments(child, indent, lines)


def _serialize_carriages_body(block, indent, lines):
    """Emit bare quoted strings for Carriages-style blocks."""
    pad = ' ' * indent
    for item in block['items']:
        lines.append(f'{pad}"{item}";')


def _serialize_mapping_body(block, indent, lines):
    """Emit key : value pairs for Countries-style blocks."""
    pad = ' ' * indent
    for row in block['mapping']:
        lines.append(f'{pad}{row[0]} : {row[1]};')


def _serialize_rows_body(block, indent, lines):
    """Emit colon-separated or comma-separated rows.

    Uses the 'separator' metadata injected by the deserializer (D-17).
    """
    pad = ' ' * indent
    sep_char = block.get('separator', ':')
    if sep_char == ':':
        sep = ' : '
    else:
        sep = ', '

    for row in block['rows']:
        values = sep.join(str(v) for v in row)
        lines.append(f'{pad}{values};')


# ---------------------------------------------------------------------------
# Comment and whitespace handling
# ---------------------------------------------------------------------------

def _emit_block_with_comments(block, indent, lines):
    """Emit a block's preceding comments, blank lines, then the block itself."""
    pad = ' ' * indent

    # Blank lines before this block
    blank_count = block.get('blank_lines_before', 0)
    for _ in range(blank_count):
        lines.append('')

    # Preceding comments
    for comment in block.get('preceding_comments', []):
        lines.append(f'{pad}{comment}')

    _serialize_block(block, indent, lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def serialize(data):
    """Serialize a parsed IL-2 dictionary back to ASCII format.

    Parameters
    ----------
    data : dict
        The top-level dictionary produced by ``parse_file()`` or
        ``parse_string()``, containing ``'comments'``, ``'blocks'``,
        and ``'trailing_comments'`` keys.

    Returns
    -------
    str
        The IL-2 ASCII representation.
    """
    lines = []

    # Header comments
    for comment in data.get('comments', []):
        lines.append(comment)

    # Blocks
    for block in data.get('blocks', []):
        _emit_block_with_comments(block, 0, lines)

    # Trailing comments
    for comment in data.get('trailing_comments', []):
        lines.append(comment)

    # Ensure trailing newline
    if lines:
        lines.append('')

    return '\n'.join(lines)


def write_file(data, path):
    """Serialize and write to a file.

    Parameters
    ----------
    data : dict
        The top-level dictionary produced by the parser.
    path : str
        Output file path.
    """
    content = serialize(data)
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content)
