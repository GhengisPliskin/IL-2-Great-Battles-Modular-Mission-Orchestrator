"""
Template compliance fixer for session prompt headers.
Adds missing template fields to all AI session headers across Phase 0-6 files.

Changes applied:
1. Split "Model Tier" field into "Model Tier" + "Assigned Model"
2. Add "Ground Rule Compliance" section after Requirements/EXIT CONDITION
3. Add "Execution Sequence & Two-Phase Commit" section for Tier 1/2 sessions
4. Add "Ground Rule 8 applies" blockquote to Context sections with FMEA refs

NO existing content is deleted or rewritten.
"""

import re
import os

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "prompts")

GROUND_RULE_COMPLIANCE = """
### Ground Rule Compliance

- **Issue Binding:** This task is bound to Issue #[TBD].
- **Decision Logging:** Update `CODE_DECISION_LOG.md` with any structural code decisions made during this session.
- **State Sync:** Move Kanban card from Ready → In Progress at start; In Progress → In Review at completion.
"""

TWO_PHASE_COMMIT = """
### Execution Sequence & Two-Phase Commit

**PHASE 1: Execution**
1. Generate or modify the required code files per the Requirements above.
2. Output the exact string: `[AWAITING_HUMAN_APPROVAL: Code generation complete. Please test and verify.]`
3. HALT completely. Do not proceed to Phase 2.

**PHASE 2: Documentation (Execute ONLY after human replies "Approved")**
1. Audit the final, approved code against the current FMEA constraints.
2. Generate the required `CODE_DECISION_LOG.md` entry.
3. Generate an `ARCHITECTURE_PATCH.md` if structural drift occurred.
4. Output the final Kanban board state change.
"""

GROUND_RULE_8 = """\n> **Ground Rule 8 applies:** These constraints are immutable during execution.
> If a constraint is logically impossible, HALT and invoke Ground Rule 9.
"""


def fix_model_tier_split(content):
    """Split combined Model Tier + Model Name into separate rows."""
    # Pattern: | **Model Tier** | Tier X — ModelName |
    # Split into: | **Model Tier** | Tier X | and | **Assigned Model** | ModelName |

    def replace_tier(match):
        full_match = match.group(0)
        tier_value = match.group(1).strip()

        # Try to split on " — " (em dash with spaces)
        if " — " in tier_value:
            tier_part, model_part = tier_value.split(" — ", 1)
        elif " - " in tier_value:
            tier_part, model_part = tier_value.split(" - ", 1)
        else:
            # No split possible, keep as-is
            return full_match

        return f"| **Model Tier** | {tier_part.strip()} |\n| **Assigned Model** | {model_part.strip()} |"

    content = re.sub(
        r'\| \*\*Model Tier\*\* \| (.+?) \|',
        replace_tier,
        content
    )
    return content


def add_ground_rule_compliance(content):
    """Add Ground Rule Compliance section after EXIT CONDITION blocks in AI sessions."""
    # Find EXIT CONDITION blocks that are NOT followed by Ground Rule Compliance
    # Insert Ground Rule Compliance after the last acceptance criterion line

    # Strategy: find each EXIT CONDITION block, find the end of its checklist,
    # and insert Ground Rule Compliance if not already present

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        new_lines.append(lines[i])

        # Check if this line starts an EXIT CONDITION block
        if '**EXIT CONDITION' in lines[i] and 'Acceptance Criteria' in lines[i]:
            # Scan forward through the checklist items
            i += 1
            while i < len(lines) and (lines[i].startswith('> -') or lines[i].startswith('>') and lines[i].strip().startswith('-')):
                new_lines.append(lines[i])
                i += 1

            # Check if Ground Rule Compliance already follows
            remaining = '\n'.join(lines[i:i+5])
            if '### Ground Rule Compliance' not in remaining:
                # Check if we're in an AI session (not a Human Gate)
                # Look back for "Session" in recent headers
                recent = '\n'.join(new_lines[-50:])
                if '## Session' in recent or '**Task ID**' in recent:
                    new_lines.append(GROUND_RULE_COMPLIANCE.rstrip())
            continue

        i += 1

    return '\n'.join(new_lines)


def add_two_phase_commit(content):
    """Add Two-Phase Commit section after Ground Rule Compliance for Tier 1/2 sessions."""
    # Find Ground Rule Compliance sections and check if Two-Phase Commit follows
    # Only add for Tier 1 and Tier 2 sessions

    sections = content.split('\n---\n')
    new_sections = []

    for section in sections:
        if '### Ground Rule Compliance' in section and '### Execution Sequence & Two-Phase Commit' not in section:
            # Check if this is a Tier 1 or Tier 2 session
            if '| **Model Tier** | Tier 1' in section or '| **Model Tier** | Tier 2' in section:
                # Add Two-Phase Commit at the end of the section
                section = section.rstrip() + '\n' + TWO_PHASE_COMMIT.rstrip()

        new_sections.append(section)

    return '\n---\n'.join(new_sections)


def add_ground_rule_8(content):
    """Add Ground Rule 8 notice to Context sections that reference FMEA/Spec constraints."""
    # Find blockquotes in Context sections that mention "Relevant" specs/FMEA
    # Add Ground Rule 8 notice if not already present

    if '**Ground Rule 8 applies**' in content:
        return content  # Already has it somewhere

    # Find patterns like "> **Relevant MMF Spec" or "> **Relevant Specs"
    # and add Ground Rule 8 after the blockquote block

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        new_lines.append(lines[i])

        # Check if this starts a "Relevant Specs" blockquote
        if lines[i].startswith('> **Relevant') and ('Spec' in lines[i] or 'FMEA' in lines[i]):
            # Scan to end of blockquote
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                new_lines.append(lines[i])
                i += 1

            # Add Ground Rule 8 notice
            new_lines.append('>')
            new_lines.append('> **Ground Rule 8 applies:** These constraints are immutable during execution.')
            new_lines.append('> If a constraint is logically impossible, HALT and invoke Ground Rule 9.')
            continue

        i += 1

    return '\n'.join(new_lines)


def process_file(filepath):
    """Apply all fixes to a single prompt header file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Apply fixes in order
    content = fix_model_tier_split(content)
    content = add_ground_rule_compliance(content)
    content = add_two_phase_commit(content)
    content = add_ground_rule_8(content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    files = sorted([
        os.path.join(PROMPTS_DIR, f)
        for f in os.listdir(PROMPTS_DIR)
        if f.endswith('.md') and f.startswith('Phase')
    ])

    print(f"Processing {len(files)} prompt header files...")

    for filepath in files:
        filename = os.path.basename(filepath)
        changed = process_file(filepath)
        status = "UPDATED" if changed else "no changes"
        print(f"  {filename}: {status}")

    print("\nDone. Verify with a diff tool that no content was deleted.")


if __name__ == '__main__':
    main()
