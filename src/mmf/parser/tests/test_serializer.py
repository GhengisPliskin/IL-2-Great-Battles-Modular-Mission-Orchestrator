"""Unit tests for the IL-2 Mission/Group file serializer (writer)."""

import logging
import os
import pytest
from pathlib import Path

from mmf.parser.deserializer import parse_string, parse_file
from mmf.parser.serializer import (
    serialize, write_file,
    _sanitize_string, _is_unquoted_string, _format_value,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(blocks=None, comments=None, trailing_comments=None):
    """Build a minimal top-level document dict."""
    return {
        'comments': comments or [],
        'blocks': blocks or [],
        'trailing_comments': trailing_comments or [],
    }


def _make_block(block_type, fields=None, children=None, **kwargs):
    """Build a minimal block dict."""
    node = {
        'type': block_type,
        'fields': fields or [],
        'children': children or [],
        'preceding_comments': kwargs.get('preceding_comments', []),
        'blank_lines_before': kwargs.get('blank_lines_before', 0),
    }
    for key in ('items', 'mapping', 'rows', 'separator'):
        if key in kwargs:
            node[key] = kwargs[key]
    # Remove fields/children keys for special blocks
    if 'items' in node or 'mapping' in node or 'rows' in node:
        node.pop('fields', None)
        node.pop('children', None)
    return node


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------

class TestValueFormatting:

    def test_integer(self):
        assert _format_value('Index', 5) == '5'

    def test_negative_integer(self):
        assert _format_value('Spotter', -1) == '-1'

    def test_zero(self):
        assert _format_value('Enabled', 0) == '0'

    def test_float(self):
        assert _format_value('XPos', 136105.11) == '136105.11'

    def test_float_fraction(self):
        assert _format_value('Haze', 0.6) == '0.6'

    def test_bool_true(self):
        """D-14: bool must serialize as 1, not True."""
        assert _format_value('Enabled', True) == '1'

    def test_bool_false(self):
        """D-14: bool must serialize as 0, not False."""
        assert _format_value('Enabled', False) == '0'

    def test_quoted_string(self):
        assert _format_value('Name', 'Alpha Flight') == '"Alpha Flight"'

    def test_empty_string(self):
        assert _format_value('Desc', '') == '""'

    def test_date_unquoted(self):
        """D-15: Multi-dot date strings emitted bare."""
        assert _format_value('Date', '30.9.1944') == '30.9.1944'

    def test_time_unquoted(self):
        """D-15: Colon time strings emitted bare."""
        assert _format_value('Time', '6:49:38') == '6:49:38'

    def test_negative_numeric_string(self):
        assert _format_value('SomeKey', '-10.5.3') == '-10.5.3'

    def test_backslash_path_preserved(self):
        """Backslash paths must not be double-escaped."""
        path = r'LuaScripts\WorldObjects\Trains\et.txt'
        result = _format_value('Script', path)
        assert result == f'"{path}"'

    def test_empty_array(self):
        """Empty arrays serialize as [] with no interior spaces."""
        assert _format_value('Targets', []) == '[]'

    def test_int_array(self):
        assert _format_value('Targets', [4, 5, 6]) == '[4,5,6]'

    def test_mixed_array(self):
        assert _format_value('Data', [1, 2.5, 3]) == '[1,2.5,3]'

    def test_string_array(self):
        result = _format_value('Config', ['alpha', 'bravo'])
        assert result == '["alpha","bravo"]'


# ---------------------------------------------------------------------------
# PI-002 Reserved character filter
# ---------------------------------------------------------------------------

class TestSanitizeString:

    def test_strips_braces(self):
        assert _sanitize_string('{bad}') == 'bad'

    def test_strips_semicolon(self):
        assert _sanitize_string('test;value') == 'testvalue'

    def test_strips_equals(self):
        assert _sanitize_string('a=b') == 'ab'

    def test_strips_brackets(self):
        assert _sanitize_string('[x]') == 'x'

    def test_strips_quotes(self):
        assert _sanitize_string('he"llo') == 'hello'

    def test_no_change(self):
        assert _sanitize_string('clean string') == 'clean string'

    def test_strips_all_reserved(self):
        assert _sanitize_string('a{b}c[d]e;f=g"h') == 'abcdefgh'

    def test_warning_logged_on_mutation(self, caplog):
        """D-16: Warning must be logged when sanitization modifies a value."""
        with caplog.at_level(logging.WARNING):
            _sanitize_string('{dirty}')
        assert 'Sanitized reserved characters' in caplog.text

    def test_no_warning_on_clean_string(self, caplog):
        with caplog.at_level(logging.WARNING):
            _sanitize_string('clean')
        assert 'Sanitized' not in caplog.text


# ---------------------------------------------------------------------------
# Negative key blacklist (D-15)
# ---------------------------------------------------------------------------

class TestStringOnlyKeys:

    def test_name_always_quoted(self):
        """Name = "12.5" must stay quoted even though 12.5 matches regex."""
        assert _format_value('Name', '12.5') == '"12.5"'

    def test_desc_always_quoted(self):
        assert _format_value('Desc', '10:30') == '"10:30"'

    def test_callsign_always_quoted(self):
        assert _format_value('Callsign', '3.14') == '"3.14"'

    def test_model_always_quoted(self):
        assert _format_value('Model', '1.2.3') == '"1.2.3"'

    def test_script_always_quoted(self):
        assert _format_value('Script', '5:00') == '"5:00"'

    def test_non_blacklisted_key_unquoted(self):
        """Non-blacklisted keys with date-like values emit bare."""
        assert _format_value('CustomDate', '30.9.1944') == '30.9.1944'

    def test_is_unquoted_string_blacklist(self):
        assert _is_unquoted_string('Name', '12.5') is False
        assert _is_unquoted_string('Date', '30.9.1944') is True


# ---------------------------------------------------------------------------
# Block serialization
# ---------------------------------------------------------------------------

class TestBlockSerialization:

    def test_simple_block(self):
        block = _make_block('MCU_Timer', fields=[
            ('Index', 5),
            ('Name', 'timer'),
            ('Time', 10.5),
        ])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        expected = (
            'MCU_Timer\n'
            '{\n'
            '  Index = 5;\n'
            '  Name = "timer";\n'
            '  Time = 10.5;\n'
            '}\n'
        )
        assert result == expected

    def test_empty_block(self):
        block = _make_block('Empty')
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert result == 'Empty\n{\n}\n'

    def test_nested_block(self):
        child = _make_block('OnEvent', fields=[
            ('Type', 13),
            ('TarId', 6358),
        ])
        parent = _make_block('OnEvents', children=[child])
        doc = _make_doc(blocks=[parent])
        result = serialize(doc)
        expected = (
            'OnEvents\n'
            '{\n'
            '  OnEvent\n'
            '  {\n'
            '    Type = 13;\n'
            '    TarId = 6358;\n'
            '  }\n'
            '}\n'
        )
        assert result == expected

    def test_deeply_nested(self):
        inner = _make_block('Inner', fields=[('Val', 1)])
        mid = _make_block('Mid', children=[inner])
        outer = _make_block('Outer', children=[mid])
        doc = _make_doc(blocks=[outer])
        result = serialize(doc)
        assert '      Val = 1;' in result
        assert '    Inner' in result
        assert '  Mid' in result

    def test_duplicate_keys(self):
        block = _make_block('Block', fields=[
            ('Country', 101),
            ('Country', 201),
        ])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        lines = result.strip().split('\n')
        country_lines = [l for l in lines if 'Country' in l]
        assert len(country_lines) == 2

    def test_numeric_keys(self):
        """Damaged-style blocks with numeric keys like -1, 0, 1."""
        block = _make_block('Damaged', fields=[
            ('-1', 0.5),
            ('0', 1.0),
            ('1', 0.8),
        ])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert '-1 = 0.5;' in result
        assert '0 = 1.0;' in result

    def test_fields_before_children(self):
        child = _make_block('Child', fields=[('X', 1)])
        parent = _make_block('Parent', fields=[
            ('Name', 'test'),
            ('Index', 5),
        ], children=[child])
        doc = _make_doc(blocks=[parent])
        result = serialize(doc)
        lines = result.strip().split('\n')
        name_idx = next(i for i, l in enumerate(lines) if 'Name' in l)
        child_idx = next(i for i, l in enumerate(lines) if 'Child' in l)
        assert name_idx < child_idx

    def test_multiple_top_level_blocks(self):
        b1 = _make_block('A', fields=[('X', 1)])
        b2 = _make_block('B', fields=[('Y', 2)])
        doc = _make_doc(blocks=[b1, b2])
        result = serialize(doc)
        assert 'A\n{' in result
        assert 'B\n{' in result


# ---------------------------------------------------------------------------
# Special blocks
# ---------------------------------------------------------------------------

class TestSpecialBlocks:

    def test_carriages(self):
        block = _make_block('Carriages', items=[
            r'LuaScripts\WorldObjects\Trains\et.txt',
            r'LuaScripts\WorldObjects\Trains\boxnb.txt',
        ])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert r'"LuaScripts\WorldObjects\Trains\et.txt";' in result
        assert r'"LuaScripts\WorldObjects\Trains\boxnb.txt";' in result

    def test_wind_layers_colon_rows(self):
        block = _make_block('WindLayers', rows=[
            (0, 160, 0),
            (0, 144, 0.2),
        ], separator=':')
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert '0 : 160 : 0;' in result
        assert '0 : 144 : 0.2;' in result

    def test_countries_mapping(self):
        block = _make_block('Countries', mapping=[
            (0, 0),
            (101, 1),
            (102, 1),
        ])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert '0 : 0;' in result
        assert '101 : 1;' in result

    def test_boundary_comma_rows(self):
        block = _make_block('Boundary', rows=[
            (100.0, 200.0),
            (300.0, 400.0),
        ], separator=',')
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert '100.0, 200.0;' in result
        assert '300.0, 400.0;' in result


# ---------------------------------------------------------------------------
# Comments and blank lines
# ---------------------------------------------------------------------------

class TestCommentsAndWhitespace:

    def test_header_comments(self):
        doc = _make_doc(
            comments=['# Mission File Version = 1.0;'],
            blocks=[_make_block('Options', fields=[('LCName', 0)])],
        )
        result = serialize(doc)
        lines = result.split('\n')
        assert lines[0] == '# Mission File Version = 1.0;'

    def test_preceding_comments_on_block(self):
        block = _make_block('Block', fields=[('X', 1)],
                            preceding_comments=['# A comment'])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        lines = result.split('\n')
        comment_idx = next(i for i, l in enumerate(lines) if '# A comment' in l)
        block_idx = next(i for i, l in enumerate(lines) if l.strip() == 'Block')
        assert comment_idx < block_idx

    def test_trailing_comments(self):
        doc = _make_doc(
            blocks=[_make_block('Block', fields=[('X', 1)])],
            trailing_comments=['# end of file'],
        )
        result = serialize(doc)
        assert '# end of file' in result
        lines = result.strip().split('\n')
        assert lines[-1] == '# end of file'

    def test_blank_lines_before(self):
        b1 = _make_block('A', fields=[('X', 1)])
        b2 = _make_block('B', fields=[('Y', 2)], blank_lines_before=2)
        doc = _make_doc(blocks=[b1, b2])
        result = serialize(doc)
        # Find the gap between } and B
        lines = result.split('\n')
        close_idx = next(i for i, l in enumerate(lines) if l.strip() == '}')
        b_idx = next(i for i, l in enumerate(lines) if l.strip() == 'B')
        blank_count = sum(1 for l in lines[close_idx + 1:b_idx] if l.strip() == '')
        assert blank_count == 2

    def test_no_gap_comments_in_preceding(self):
        """When comments have no blank-line gap from the block, they land
        in preceding_comments. Writer must emit them before the block."""
        block = _make_block('Options', fields=[('LCName', 0)],
                            preceding_comments=['# Mission File Version = 1.0;'])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        lines = result.split('\n')
        assert lines[0] == '# Mission File Version = 1.0;'
        assert lines[1] == 'Options'


# ---------------------------------------------------------------------------
# IL-2 edge cases (review feedback)
# ---------------------------------------------------------------------------

class TestIL2EdgeCases:

    def test_empty_array_no_spaces(self):
        """Targets = []; must serialize without interior spaces."""
        block = _make_block('Block', fields=[('Targets', [])])
        doc = _make_doc(blocks=[block])
        result = serialize(doc)
        assert 'Targets = [];' in result
        assert 'Targets = [ ]' not in result

    def test_backslash_paths_no_double_escape(self):
        """Carriages paths must not double-escape backslashes."""
        src = 'Carriages\n{\n  "LuaScripts\\WorldObjects\\Trains\\et.txt";\n}\n'
        parsed = parse_string(src)
        output = serialize(parsed)
        assert 'LuaScripts\\WorldObjects\\Trains\\et.txt' in output
        # Must NOT contain double backslashes
        assert '\\\\' not in output

    def test_write_file_line_endings(self, tmp_path):
        """write_file() must produce CRLF line endings for IL-2 compatibility."""
        block = _make_block('Block', fields=[('X', 1)])
        doc = _make_doc(blocks=[block])
        outfile = tmp_path / 'test.Group'
        write_file(doc, str(outfile))
        raw = outfile.read_bytes()
        assert b'\r\n' in raw
        bare_lf = raw.replace(b'\r\n', b'').count(b'\n')
        assert bare_lf == 0, f"Found {bare_lf} bare LF bytes — expected all CRLF"


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

def _compare_blocks(original, roundtripped):
    """Deep-compare two block lists for semantic equality."""
    assert len(original) == len(roundtripped), \
        f"Block count mismatch: {len(original)} vs {len(roundtripped)}"

    for orig, rt in zip(original, roundtripped):
        assert orig['type'] == rt['type'], \
            f"Block type mismatch: {orig['type']} vs {rt['type']}"

        # Compare special block content
        if 'items' in orig:
            assert orig['items'] == rt['items']
        elif 'mapping' in orig:
            assert orig['mapping'] == rt['mapping']
        elif 'rows' in orig:
            assert len(orig['rows']) == len(rt['rows'])
            for o_row, r_row in zip(orig['rows'], rt['rows']):
                assert len(o_row) == len(r_row)
                for o_val, r_val in zip(o_row, r_row):
                    if isinstance(o_val, float):
                        assert o_val == pytest.approx(r_val)
                    else:
                        assert o_val == r_val
        else:
            # Standard block — compare fields
            assert len(orig.get('fields', [])) == len(rt.get('fields', []))
            for (o_key, o_val), (r_key, r_val) in zip(
                orig.get('fields', []), rt.get('fields', [])
            ):
                assert o_key == r_key, f"Key mismatch: {o_key} vs {r_key}"
                if isinstance(o_val, float):
                    assert o_val == pytest.approx(r_val)
                else:
                    assert o_val == r_val, \
                        f"Value mismatch for {o_key}: {o_val!r} vs {r_val!r}"

            # Compare children recursively
            _compare_blocks(
                orig.get('children', []),
                rt.get('children', []),
            )

        # Compare comments
        assert orig.get('preceding_comments', []) == \
            rt.get('preceding_comments', [])


class TestRoundTrip:

    def test_simple_roundtrip(self):
        src = 'Block\n{\n  Index = 5;\n  Name = "test";\n}\n'
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        _compare_blocks(parsed['blocks'], reparsed['blocks'])

    def test_roundtrip_with_comments(self):
        src = (
            '# Header comment\n'
            '\n'
            'Block\n'
            '{\n'
            '  X = 1;\n'
            '}\n'
        )
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        assert parsed['comments'] == reparsed['comments']
        _compare_blocks(parsed['blocks'], reparsed['blocks'])

    def test_roundtrip_special_blocks(self):
        src = (
            'Group\n'
            '{\n'
            '  Name = "test";\n'
            '  Index = 1;\n'
            '  Carriages\n'
            '  {\n'
            '    "path1";\n'
            '    "path2";\n'
            '  }\n'
            '}\n'
        )
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        _compare_blocks(parsed['blocks'], reparsed['blocks'])

    def test_roundtrip_wind_layers(self):
        src = (
            'WindLayers\n'
            '{\n'
            '  0 :     160 :     0;\n'
            '  0 :     160 :     0;\n'
            '  0 :     144 :     0.2;\n'
            '}\n'
        )
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        _compare_blocks(parsed['blocks'], reparsed['blocks'])

    def test_roundtrip_countries(self):
        src = (
            'Countries\n'
            '{\n'
            '  0 : 0;\n'
            '  101 : 1;\n'
            '}\n'
        )
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        _compare_blocks(parsed['blocks'], reparsed['blocks'])

    def test_roundtrip_arrays(self):
        src = (
            'Block\n'
            '{\n'
            '  Targets = [4,5,6];\n'
            '  Objects = [];\n'
            '}\n'
        )
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        _compare_blocks(parsed['blocks'], reparsed['blocks'])

    def test_roundtrip_date_time(self):
        src = (
            'Options\n'
            '{\n'
            '  Time = 6:49:38;\n'
            '  Date = 30.9.1944;\n'
            '}\n'
        )
        parsed = parse_string(src)
        output = serialize(parsed)
        reparsed = parse_string(output)
        _compare_blocks(parsed['blocks'], reparsed['blocks'])


# ---------------------------------------------------------------------------
# Corpus round-trip validation
# ---------------------------------------------------------------------------

CORPUS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / \
    'Group and Mission Examples'


def _collect_corpus_files():
    """Collect all .Group and .Mission files from the corpus directory."""
    if not CORPUS_DIR.exists():
        return []
    files = []
    for ext in ('*.Group', '*.Mission'):
        files.extend(CORPUS_DIR.rglob(ext))
    return sorted(files)


CORPUS_FILES = _collect_corpus_files()


@pytest.mark.skipif(not CORPUS_FILES, reason="No corpus files found")
@pytest.mark.parametrize(
    "corpus_file",
    CORPUS_FILES,
    ids=[f.name for f in CORPUS_FILES],
)
def test_roundtrip_corpus(corpus_file):
    """Parse a corpus file, serialize, re-parse, and compare — zero data loss."""
    parsed = parse_file(str(corpus_file))
    output = serialize(parsed)
    reparsed = parse_string(output)

    # Compare header and trailing comments
    assert parsed['comments'] == reparsed['comments']
    assert parsed['trailing_comments'] == reparsed['trailing_comments']

    # Compare all blocks recursively
    _compare_blocks(parsed['blocks'], reparsed['blocks'])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class TestPublicAPI:

    def test_serialize_returns_string(self):
        doc = _make_doc(blocks=[_make_block('Block', fields=[('X', 1)])])
        result = serialize(doc)
        assert isinstance(result, str)

    def test_serialize_empty_input(self):
        doc = _make_doc()
        result = serialize(doc)
        assert result == '\n' or result == ''

    def test_write_file_creates_file(self, tmp_path):
        doc = _make_doc(blocks=[_make_block('Block', fields=[('X', 1)])])
        outfile = tmp_path / 'output.Group'
        write_file(doc, str(outfile))
        assert outfile.exists()

    def test_write_file_content_matches_serialize(self, tmp_path):
        doc = _make_doc(blocks=[_make_block('Block', fields=[('X', 1)])])
        outfile = tmp_path / 'output.Group'
        write_file(doc, str(outfile))
        expected = serialize(doc)
        actual = outfile.read_text(encoding='utf-8')
        assert actual == expected
