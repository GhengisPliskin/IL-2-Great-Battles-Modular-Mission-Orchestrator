"""Unit tests for the IL-2 Mission/Group file parser."""

import os
import pytest
from parser import (
    parse_string, parse_file, ParseError,
    get_field, get_fields, get_children,
)


# ---------------------------------------------------------------------------
# Basic key-value pairs
# ---------------------------------------------------------------------------

class TestKeyValueParsing:

    def test_integer_field(self):
        result = parse_string('Block\n{\n  Index = 5;\n}\n')
        block = result['blocks'][0]
        assert get_field(block, 'Index') == 5
        assert isinstance(get_field(block, 'Index'), int)

    def test_negative_integer(self):
        result = parse_string('Block\n{\n  Spotter = -1;\n}\n')
        assert get_field(result['blocks'][0], 'Spotter') == -1
        assert isinstance(get_field(result['blocks'][0], 'Spotter'), int)

    def test_float_field(self):
        result = parse_string('Block\n{\n  XPos = 136105.110;\n}\n')
        val = get_field(result['blocks'][0], 'XPos')
        assert isinstance(val, float)
        assert abs(val - 136105.110) < 0.001

    def test_float_fraction(self):
        result = parse_string('Block\n{\n  Haze = 0.6;\n}\n')
        assert get_field(result['blocks'][0], 'Haze') == pytest.approx(0.6)

    def test_quoted_string(self):
        result = parse_string('Block\n{\n  Name = "Alpha Flight";\n}\n')
        assert get_field(result['blocks'][0], 'Name') == 'Alpha Flight'

    def test_empty_string(self):
        result = parse_string('Block\n{\n  Desc = "";\n}\n')
        assert get_field(result['blocks'][0], 'Desc') == ''

    def test_backslash_path_preserved(self):
        result = parse_string(
            'Block\n{\n  Script = "LuaScripts\\WorldObjects\\Trains\\e.txt";\n}\n'
        )
        val = get_field(result['blocks'][0], 'Script')
        assert 'LuaScripts' in val
        assert '\\' in val

    def test_time_as_raw_string(self):
        result = parse_string('Block\n{\n  Time = 6:49:38;\n}\n')
        val = get_field(result['blocks'][0], 'Time')
        assert val == '6:49:38'
        assert isinstance(val, str)

    def test_date_as_raw_string(self):
        result = parse_string('Block\n{\n  Date = 30.9.1944;\n}\n')
        val = get_field(result['blocks'][0], 'Date')
        assert val == '30.9.1944'
        assert isinstance(val, str)


# ---------------------------------------------------------------------------
# Arrays
# ---------------------------------------------------------------------------

class TestArrayParsing:

    def test_empty_array(self):
        result = parse_string('Block\n{\n  Targets = [];\n}\n')
        assert get_field(result['blocks'][0], 'Targets') == []

    def test_single_element_array(self):
        result = parse_string('Block\n{\n  Targets = [6372];\n}\n')
        assert get_field(result['blocks'][0], 'Targets') == [6372]

    def test_multi_element_array(self):
        result = parse_string('Block\n{\n  Targets = [1,2,3];\n}\n')
        assert get_field(result['blocks'][0], 'Targets') == [1, 2, 3]

    def test_array_with_spaces(self):
        result = parse_string('Block\n{\n  Coalitions = [1, 2];\n}\n')
        assert get_field(result['blocks'][0], 'Coalitions') == [1, 2]

    def test_string_array(self):
        result = parse_string('Block\n{\n  Items = ["alpha", "bravo"];\n}\n')
        val = get_field(result['blocks'][0], 'Items')
        assert val == ['alpha', 'bravo']


# ---------------------------------------------------------------------------
# Nested blocks
# ---------------------------------------------------------------------------

class TestNestedBlocks:

    def test_child_block(self):
        src = '''Group
{
  Name = "Logic";
  MCU_Timer
  {
    Index = 3;
    Time = 10.5;
  }
}
'''
        result = parse_string(src)
        group = result['blocks'][0]
        assert group['type'] == 'Group'
        assert get_field(group, 'Name') == 'Logic'
        children = get_children(group)
        assert len(children) == 1
        timer = children[0]
        assert timer['type'] == 'MCU_Timer'
        assert get_field(timer, 'Index') == 3
        assert get_field(timer, 'Time') == pytest.approx(10.5)

    def test_deeply_nested_blocks(self):
        src = '''Group
{
  Name = "Outer";
  Group
  {
    Name = "Inner";
    MCU_Timer
    {
      Index = 1;
    }
  }
}
'''
        result = parse_string(src)
        outer = result['blocks'][0]
        inner = get_children(outer, 'Group')[0]
        timer = get_children(inner, 'MCU_Timer')[0]
        assert get_field(timer, 'Index') == 1

    def test_multiple_children(self):
        src = '''Group
{
  MCU_Timer
  {
    Index = 1;
  }
  MCU_Counter
  {
    Index = 2;
  }
  MCU_Waypoint
  {
    Index = 3;
  }
}
'''
        result = parse_string(src)
        group = result['blocks'][0]
        children = get_children(group)
        assert len(children) == 3
        assert [c['type'] for c in children] == ['MCU_Timer', 'MCU_Counter', 'MCU_Waypoint']

    def test_filter_children_by_type(self):
        src = '''Group
{
  MCU_Timer { Index = 1; }
  MCU_Counter { Index = 2; }
  MCU_Timer { Index = 3; }
}
'''
        result = parse_string(src)
        group = result['blocks'][0]
        timers = get_children(group, 'MCU_Timer')
        assert len(timers) == 2

    def test_sub_block_within_mcu(self):
        """SubtitleInfo nested within MCU_TR_Subtitle."""
        src = '''MCU_TR_Subtitle
{
  Index = 4;
  Enabled = 1;
  SubtitleInfo
  {
    Duration = 10;
    FontSize = 20;
  }
  Coalitions = [1, 3];
}
'''
        result = parse_string(src)
        subtitle = result['blocks'][0]
        assert get_field(subtitle, 'Enabled') == 1
        assert get_field(subtitle, 'Coalitions') == [1, 3]
        info = get_children(subtitle, 'SubtitleInfo')[0]
        assert get_field(info, 'Duration') == 10
        assert get_field(info, 'FontSize') == 20


# ---------------------------------------------------------------------------
# Duplicate keys
# ---------------------------------------------------------------------------

class TestDuplicateKeys:

    def test_duplicate_keys_preserved(self):
        src = '''Block
{
  MultiplayerPlaneConfig = "planes/bf109.txt";
  MultiplayerPlaneConfig = "planes/fw190.txt";
  MultiplayerPlaneConfig = "planes/p51.txt";
}
'''
        result = parse_string(src)
        block = result['blocks'][0]
        vals = get_fields(block, 'MultiplayerPlaneConfig')
        assert len(vals) == 3
        assert vals[0] == 'planes/bf109.txt'
        assert vals[2] == 'planes/p51.txt'

    def test_get_field_returns_first(self):
        src = 'Block\n{\n  Country = 201;\n  Country = 202;\n}\n'
        result = parse_string(src)
        assert get_field(result['blocks'][0], 'Country') == 201

    def test_field_order_preserved(self):
        src = '''Block
{
  A = 1;
  B = 2;
  A = 3;
  C = 4;
}
'''
        result = parse_string(src)
        fields = result['blocks'][0]['fields']
        keys = [k for k, v in fields]
        assert keys == ['A', 'B', 'A', 'C']


# ---------------------------------------------------------------------------
# Special block types
# ---------------------------------------------------------------------------

class TestSpecialBlocks:

    def test_carriages_bare_strings(self):
        src = '''Carriages
{
  "LuaScripts\\WorldObjects\\Trains\\et.txt";
  "LuaScripts\\WorldObjects\\Trains\\boxnb.txt";
}
'''
        result = parse_string(src)
        block = result['blocks'][0]
        assert block['type'] == 'Carriages'
        assert 'items' in block
        assert len(block['items']) == 2
        assert 'et.txt' in block['items'][0]

    def test_wind_layers_tuples(self):
        src = '''WindLayers
{
  0 :     160 :     0;
  500 :     129 :     1.4;
  1000 :     118 :     2.6;
}
'''
        result = parse_string(src)
        block = result['blocks'][0]
        assert block['type'] == 'WindLayers'
        assert 'rows' in block
        assert len(block['rows']) == 3
        assert block['rows'][0] == (0, 160, 0)
        assert block['rows'][1] == (500, 129, pytest.approx(1.4))

    def test_countries_mapping(self):
        src = '''Countries
{
  0 : 0;
  101 : 1;
  201 : 2;
}
'''
        result = parse_string(src)
        block = result['blocks'][0]
        assert block['type'] == 'Countries'
        assert 'mapping' in block
        assert block['mapping'] == [(0, 0), (101, 1), (201, 2)]

    def test_damaged_numeric_keys(self):
        src = '''Damaged
{
  -1 = 0.5;
  0 = 1;
  1 = 1;
}
'''
        result = parse_string(src)
        block = result['blocks'][0]
        assert block['type'] == 'Damaged'
        fields = block['fields']
        assert fields[0] == ('-1', pytest.approx(0.5))
        assert fields[1] == ('0', 1)
        assert fields[2] == ('1', 1)

    def test_boundary_comma_rows(self):
        src = '''Boundary
{
  90419, 241617;
  94319, 243053;
  100240, 244712;
}
'''
        result = parse_string(src)
        block = result['blocks'][0]
        assert block['type'] == 'Boundary'
        assert 'rows' in block
        assert len(block['rows']) == 3
        assert block['rows'][0] == (90419, 241617)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class TestComments:

    def test_header_comment(self):
        src = '# Mission File Version = 1.0;\n\nGroup\n{\n  Index = 1;\n}\n'
        result = parse_string(src)
        assert len(result['comments']) == 1
        assert 'Mission File Version' in result['comments'][0]

    def test_no_comments(self):
        result = parse_string('Block\n{\n  Index = 1;\n}\n')
        assert result['comments'] == []

    def test_preceding_comments_on_block(self):
        src = '''# Header

# This is a timer
MCU_Timer
{
  Index = 1;
}
'''
        result = parse_string(src)
        assert 'Header' in result['comments'][0]
        timer = result['blocks'][0]
        assert len(timer['preceding_comments']) == 1
        assert 'timer' in timer['preceding_comments'][0]

    def test_trailing_comments(self):
        src = 'Block\n{\n  X = 1;\n}\n# trailing note\n'
        result = parse_string(src)
        assert len(result['trailing_comments']) == 1
        assert 'trailing' in result['trailing_comments'][0]

    def test_multiple_trailing_comments(self):
        src = 'Block\n{\n  X = 1;\n}\n# note 1\n# note 2\n'
        result = parse_string(src)
        assert len(result['trailing_comments']) == 2


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestParseError:

    def test_unterminated_string(self):
        with pytest.raises(ParseError) as exc_info:
            parse_string('Block\n{\n  Name = "unterminated;\n}\n')
        assert exc_info.value.line is not None

    def test_unexpected_token_in_block(self):
        with pytest.raises(ParseError):
            parse_string('Block\n{\n  @@@ = 5;\n}\n')

    def test_missing_semicolon(self):
        with pytest.raises(ParseError):
            parse_string('Block\n{\n  Index = 5\n}\n')

    def test_missing_closing_brace(self):
        with pytest.raises(ParseError):
            parse_string('Block\n{\n  Index = 5;\n')

    def test_error_has_line_number(self):
        with pytest.raises(ParseError) as exc_info:
            parse_string('Block\n{\n  Name = "ok";\n  @@@ bad;\n}\n')
        assert exc_info.value.line == 4


# ---------------------------------------------------------------------------
# Numeric type inference
# ---------------------------------------------------------------------------

class TestNumericInference:

    def test_zero_is_int(self):
        result = parse_string('B { X = 0; }')
        assert get_field(result['blocks'][0], 'X') == 0
        assert isinstance(get_field(result['blocks'][0], 'X'), int)

    def test_zero_point_zero_is_float(self):
        result = parse_string('B { X = 0.00; }')
        val = get_field(result['blocks'][0], 'X')
        assert isinstance(val, float)

    def test_multi_dot_stays_string(self):
        """Dates like 30.9.1944 must not be split into float + parse error."""
        result = parse_string('B { Date = 30.9.1944; }')
        val = get_field(result['blocks'][0], 'Date')
        assert val == '30.9.1944'
        assert isinstance(val, str)

    def test_colon_value_stays_string(self):
        result = parse_string('B { Time = 11:20:0; }')
        val = get_field(result['blocks'][0], 'Time')
        assert val == '11:20:0'
        assert isinstance(val, str)


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_get_field_missing_returns_none(self):
        result = parse_string('Block\n{\n  Index = 1;\n}\n')
        assert get_field(result['blocks'][0], 'Missing') is None

    def test_get_fields_empty(self):
        result = parse_string('Block\n{\n  Index = 1;\n}\n')
        assert get_fields(result['blocks'][0], 'Missing') == []

    def test_get_children_empty(self):
        result = parse_string('Block\n{\n  Index = 1;\n}\n')
        assert get_children(result['blocks'][0]) == []

    def test_get_children_no_filter(self):
        src = 'G { A { X = 1; } B { X = 2; } }'
        result = parse_string(src)
        assert len(get_children(result['blocks'][0])) == 2


# ---------------------------------------------------------------------------
# Multiple top-level blocks
# ---------------------------------------------------------------------------

class TestTopLevel:

    def test_multiple_top_level_blocks(self):
        src = '''Options
{
  MissionType = 1;
}

Group
{
  Name = "Logic";
}

Group
{
  Name = "Planes";
}
'''
        result = parse_string(src)
        assert len(result['blocks']) == 3
        assert result['blocks'][0]['type'] == 'Options'
        assert result['blocks'][1]['type'] == 'Group'
        assert result['blocks'][2]['type'] == 'Group'

    def test_empty_block(self):
        result = parse_string('Block\n{\n}\n')
        block = result['blocks'][0]
        assert block['type'] == 'Block'
        assert block['fields'] == []
        assert block['children'] == []

    def test_empty_file(self):
        result = parse_string('')
        assert result['comments'] == []
        assert result['blocks'] == []
        assert result['trailing_comments'] == []

    def test_comments_only_no_blocks(self):
        result = parse_string('# Just a comment\n# Another one\n')
        assert result['blocks'] == []
        total = len(result['comments']) + len(result['trailing_comments'])
        assert total == 2

    def test_blank_lines_before_tracked(self):
        src = 'A\n{\n  X = 1;\n}\n\n\nB\n{\n  Y = 2;\n}\n'
        result = parse_string(src)
        assert result['blocks'][1]['blank_lines_before'] > 0
        assert result['blocks'][0]['blank_lines_before'] == 0


# ---------------------------------------------------------------------------
# Corpus validation
# ---------------------------------------------------------------------------

class TestCorpusValidation:

    @staticmethod
    def _get_corpus_files():
        example_dir = os.path.join(
            os.path.dirname(__file__), 'Group and Mission Examples'
        )
        if not os.path.isdir(example_dir):
            return []
        files = []
        for root, dirs, fnames in os.walk(example_dir):
            for f in fnames:
                if f.endswith('.Group') or f.endswith('.Mission'):
                    files.append(os.path.join(root, f))
        return sorted(files)

    def test_all_corpus_files_parse(self):
        files = self._get_corpus_files()
        if not files:
            pytest.skip("No corpus files found")
        for fp in files:
            try:
                result = parse_file(fp)
                assert 'blocks' in result
                assert len(result['blocks']) > 0
            except Exception as e:
                pytest.fail(f"Failed to parse {fp}: {e}")
