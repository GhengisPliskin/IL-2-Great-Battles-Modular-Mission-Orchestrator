# Manual Prompt Addition — Code Comment Standard
# Ground Rule 11 | Decision 6 | C-019 through C-022
#
# INSTRUCTIONS FOR USE:
# Paste the block below into any session prompt header, directly above the
# EXIT CONDITION / Acceptance Criteria section. It is self-contained and
# requires no editing. Remove this instruction header before pasting.
#
# When prompt headers are formally updated (separate session), this block
# will be absorbed into the standard template and this file can be archived.

---

### Code Comment Standard (Ground Rule 11)

All code produced in this session must comply with the project comment standard.
This requirement is non-negotiable and applies alongside all other acceptance criteria.

**Required in every `.py` file touched or created by this session:**

**Module docstring** — top of file:
```python
"""
MODULE:  <filename without .py>
PURPOSE: <What this module does. 1–3 sentences. Which layer it belongs to.>
FMEA:    <Constraint IDs directly implemented here, or "None".>
PHASE:   <Project phase that introduced this file, e.g. "Phase 0.3".>
"""
```

**Function docstring** — every public function or method:
```python
def example(arg1, arg2):
    """
    WHAT:    <What it does.>
    WHY:     <Why it exists / what failure it prevents.>
    ARGS:
        arg1 (type): <Description.>
        arg2 (type): <Description.>
    RETURNS:
        type: <Description. "None" if void.>
    FMEA:    <Constraint ID if directly enforced, else "None".>
    """
```

**Block comment** — above every non-trivial logic block:
```python
# --- WHAT THIS DOES ---
# <2–4 plain sentences. State the operation and its purpose.
# If an FMEA constraint drives this logic, cite the ID: [EL-001]>
```

**Why-Not comment** — when a constraint forces a non-obvious choice:
```python
# WHY NOT <obvious alternative>: [FMEA-ID] — <Plain explanation of why
# the obvious approach fails in the IL-2 engine or violates a constraint.>
```

**Preservation rules — binding for this session:**
- All existing docstrings and block comments must be preserved verbatim
- Existing comments are updated only if the underlying logic is replaced in this session
- New functions and logic blocks added in this session require the appropriate comment type
- Silent removal of comments to produce "cleaner" output is prohibited
- This applies to refactoring, reformatting, and test-writing tasks equally

**Standing acceptance criteria (add to EXIT CONDITION checklist):**
- [ ] All new `.py` files have module-level docstrings (MODULE / PURPOSE / FMEA / PHASE)
- [ ] All new public functions have structured docstrings (WHAT / WHY / ARGS / RETURNS / FMEA)
- [ ] All non-trivial new logic blocks have plain-English block comments
- [ ] No existing comments removed or truncated (C-022)

Full format specification: `ARCHITECTURE.md` — "Code Comment Standard" section.
Constraints: `CONSTRAINTS.md` C-019 through C-022.
