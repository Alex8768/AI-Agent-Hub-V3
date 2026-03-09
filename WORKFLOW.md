# DEVELOPMENT WORKFLOW

## Core principle
One patch = one reason.

## Work style
Assistant analyzes, prepares autopatch and gives terminal commands.
User executes commands in terminal.
After each successful step, canonical project anchor docs must be updated.

## Standard loop

1. Identify current anchor
2. Analyze only that anchor
3. Prepare autopatch
4. Apply patch
5. Run checks:
   python -m compileall -q src
   pytest -q
6. If green -> update `docs/development/STATUS.md` and `docs/development/PROJECT_CHECKLIST.md`
7. Commit
8. Move to next anchor

## Hard rules

- Do not mix multiple architectural topics in one commit
- Do not silently redesign roadmap
- Do not skip anchor tracking
- Do not continue after red tests without fixing the actual failure
- Do not start delayed expansions before the core path is stable

## Anchor update rule

After each completed anchor:
- mark the anchor as DONE in `docs/development/PROJECT_CHECKLIST.md`
- move the next anchor to IN_PROGRESS if work starts immediately
- update `docs/development/STATUS.md` with:
  - last completed anchor
  - current active anchor
  - next anchor
  - short notes

## Collaboration rule

If there is uncertainty:
- inspect relevant files
- ask for outputs if needed
- then produce a focused autopatch

No broad unfocused rewrites.
