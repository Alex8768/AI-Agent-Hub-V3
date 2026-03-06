# DEVELOPMENT WORKFLOW

## Core principle
One patch = one reason.

## Development loop

1. Analyze problem
2. Prepare autopatch
3. Apply patch
4. Run checks:
   python -m compileall -q src
   pytest -q
5. If green -> commit
6. Move to next anchor

## Important rules

Do not mix multiple architectural changes in one commit.

If tests fail:
fix only the failure cause.

## Chat collaboration

Assistant provides:
- analysis
- autopatch
- terminal commands

User executes commands in terminal.
