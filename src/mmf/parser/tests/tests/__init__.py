"""
Parser module tests.

Tests for the IL-2 ASCII parser library (Phase 0.2).
- Tokenization: Breaking ASCII into blocks, key-value pairs, arrays
- Deserialization: Converting ASCII into Python dictionaries
- Serialization: Converting Python dictionaries back into ASCII
- Round-trip: Parse → Serialize → Compare (output matches input)
"""