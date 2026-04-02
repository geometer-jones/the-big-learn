---
name: the-big-learn-update
description: Update the local The Big Learn package when a newer upstream version is available. Use when the user wants to check for a newer release, fast-forward this checkout to the official repository, reinstall the package, and verify the update.
---

# Update

Use this skill for package maintenance, not learner-state tracking.

## Startup

No startup command is required.

Work in the repository checkout already open in the workspace. Prefer the package's own update flow before inventing a new one.

## Job

- detect the local installed version
- check whether a newer upstream version is available
- if a newer version exists, update the repository checkout to the official upstream branch
- reinstall the package from the updated checkout
- verify that the CLI and tests still pass

## Detection

Use these checks in order:

1. `python3 -m the_big_learn version`
2. `python3 -m the_big_learn update-check --force`
3. inspect `git remote -v` and the current branch

Treat `UPGRADE_AVAILABLE <local> <remote>` as the signal that the package should be updated.

## Update Path

When the checkout is connected to the official repository and the working tree is clean enough to fast-forward safely:

1. fetch the remote branch
2. update with `git pull --ff-only origin <default-branch>`
3. run `python3 -m pip install -e .`
4. reinstall the current host assets with `python3 -m the_big_learn claude install --force`, `python3 -m the_big_learn codex install --force`, or `python3 -m the_big_learn gemini install --force` for the host that owns the checkout
5. run `python3 -m unittest discover -s tests`
6. rerun `python3 -m the_big_learn version`

The goal is to update the whole package from the repository source of truth: runtime code, host assets, and repo skills.

## Rules

- Prefer `python3 -m the_big_learn update-check --force` over ad hoc version comparisons.
- Prefer a fast-forward update. Do not create merge commits for routine package updates.
- Do not stop after the editable package reinstall; refresh the copied host assets too, or deleted skills can linger and new skills will not appear.
- If the working tree has local changes that would make the update unsafe, stop and explain the blocker instead of forcing through it.
- If no upstream repository or default branch can be determined, say so plainly and report what was missing.
- If `update-check` reports no newer version, say that the package is already up to date and stop.
- After updating, report the old version, the new version, and the verification results.

## Output

Return a short maintenance summary that includes:

- local version before update
- remote version if found
- whether the update was applied
- commands run
- verification result

## Handoff

If the repository cannot be updated safely because of local divergence or uncommitted work, stop with the exact git blocker and ask the user how they want to reconcile it.
