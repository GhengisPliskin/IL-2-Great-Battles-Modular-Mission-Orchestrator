"""
V2: More robust Ground Rule Compliance and Two-Phase Commit insertion.
Runs AFTER the v1 script which already handled Model Tier split and Ground Rule 8.
"""

import os
import re

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "prompts")

GROUND_RULE_COMPLIANCE = """\n### Ground Rule Compliance

- **Issue Binding:** This task is bound to Issue #[TBD].
- **Decision Logging:** Update `CODE_DECISION_LOG.md` with any structural code decisions made during this session.
- **State Sync:** Move Kanban card from Ready → In Progress at start; In Progress → In Review at completion.
"""

TWO_PHASE_COMMIT = """\n### Execution Sequence & Two-Phase Commit

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


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Split content into session blocks by "---" separator
    # Then process each block independently

    # Strategy: Use regex to find each AI session block (starts with ## Session)
    # and add missing sections

    # Find all session blocks
    sessions = re.split(r'(^## (?:Session|Human Gate) .+$)', content, flags=re.MULTILINE)

    new_parts = []
    for i, part in enumerate(sessions):
        if part.startswith('## Session') and i + 1 < len(sessions):
            header = part
            body = sessions[i + 1]

            # Check if this session already has Ground Rule Compliance
            if '### Ground Rule Compliance' not in body:
                # Find the EXIT CONDITION block and insert after it
                # Pattern: > **EXIT CONDITION... followed by > - lines
                exit_match = re.search(
                    r'(> \*\*EXIT CONDITION.*?\n(?:> .*\n)*)',
                    body
                )
                if exit_match:
                    insert_pos = exit_match.end()
                    body = body[:insert_pos] + GROUND_RULE_COMPLIANCE + body[insert_pos:]

            # Check if this session needs Two-Phase Commit
            if '### Execution Sequence & Two-Phase Commit' not in body:
                # Only for Tier 1 and Tier 2
                if '| **Model Tier** | Tier 1' in body or '| **Model Tier** | Tier 2' in body:
                    # Check if Tier 3 — skip
                    if '| **Model Tier** | Tier 3' not in body:
                        # Insert at the very end of the session body (before the next ---)
                        # Find the last --- or end of body
                        if body.rstrip().endswith('---'):
                            # Insert before the trailing ---
                            last_sep = body.rstrip().rfind('\n---')
                            if last_sep > 0:
                                body = body[:last_sep] + TWO_PHASE_COMMIT + body[last_sep:]
                        else:
                            body = body.rstrip() + TWO_PHASE_COMMIT + '\n'

            sessions[i + 1] = body

        new_parts.append(part)

    content = ''.join(sessions)

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

    print(f"Processing {len(files)} prompt header files (v2)...")

    for filepath in files:
        filename = os.path.basename(filepath)
        changed = process_file(filepath)
        status = "UPDATED" if changed else "no changes"
        print(f"  {filename}: {status}")

    # Count results
    gc_count = 0
    tpc_count = 0
    for filepath in files:
        with open(filepath, 'r') as f:
            content = f.read()
        gc_count += content.count('### Ground Rule Compliance')
        tpc_count += content.count('### Execution Sequence & Two-Phase Commit')

    print(f"\nTotals: {gc_count} Ground Rule Compliance sections, {tpc_count} Two-Phase Commit sections")


if __name__ == '__main__':
    main()
