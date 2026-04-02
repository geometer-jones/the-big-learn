# Roadmap

This roadmap is intentionally narrow. The goal is to get to a believable first version, not to sketch ten future products.

## Phase 0: Repository Foundation

Status: shipped in-repo

Goals:

- define project scope
- document architecture
- document contribution rules
- choose initial host targets
- choose packaging and test strategy

Deliverables:

- top-level docs
- Python package metadata and versioning
- bundled asset build step in `setup.py`
- local `source-store/` for packaged curriculum data
- first-pass skill taxonomy
- proposed repository layout
- product thesis for the Four Books wedge
- curriculum definition for the initial five tracks
- six-layer line record spec

## Phase 1: First Skill Set

Status: mostly shipped, expanding examples and coverage

Goals:

- define the minimum useful Chinese-learning skills
- keep the set small enough to evaluate honestly

Candidate skills:

- `the-big-learn-guided-reading`
- `the-big-learn-flashcard-bank-add`
- `the-big-learn-flashcard-variation-generator`
- `the-big-learn-explode-char`
- `the-big-learn-update`

Exit criteria:

- each skill has a clear contract
- each skill has examples
- each skill has fixture coverage

## Phase 2: Workflow Layer

Status: initial workflow shipped, persistence still narrow

Goals:

- connect isolated skills into real learning loops

Candidate workflows:

- Four Books guided reading
- idle-time study loop for coding-assistant users
- writing submission review
- reading passage to flashcard generation

Exit criteria:

- each workflow has defined steps
- context handoff is explicit
- stop conditions are documented
- unencoded curriculum books have a documented live-source discovery path with source selection, real chapter counts, and local chapter saving
- current repo note: the CLI fixture path and saved progress file currently cover the locally annotated `Da Xue` starter slice, while the broader guided-reading flow is expressed through host assets plus bundled source catalogs

## Phase 3: Evaluation Harness

Status: in progress with meaningful coverage already checked in

Goals:

- catch regressions before prompts sprawl
- define what "good" means for the first workflows

Focus areas:

- six-layer line integrity
- correction accuracy
- explanation clarity
- difficulty targeting
- consistency across repeated runs
- flashcard mapping correctness

Exit criteria:

- fixture-based regression checks exist
- reviewers can compare expected and actual behavior quickly

## Phase 4: Host Packaging

Status: shipped for current host set

Goals:

- package the project for one or more coding assistant hosts

Likely targets:

- Codex
- Claude Code
- Gemini

Exit criteria:

- install path is documented
- skills are discoverable by the host
- host-specific constraints are written down

Current shipped surface:

- Codex skill installer and default path lookup
- Claude Code skill installer and default path lookup
- Gemini command-tree installer and default path lookup

## Phase 5: Expansion

Only after the first text-first loop works.

Possible areas:

- HSK-specific tracks
- spaced repetition integrations
- pronunciation and audio workflows
- richer learner memory
- teacher or classroom workflows
- broader non-canonical reading material

## Near-Term Gaps

These are the sharp edges still visible in the current repo state:

- extend saved progress beyond the `Da Xue` starter slice
- persist queued-question review and flashcard outputs across live host sessions, not only fixture playback
- expand six-layer local annotations beyond `Da Xue`
- keep packaged bundle copies under `build/lib/the_big_learn/bundle/` refreshed whenever bundled docs or assets change

## What We Are Not Doing First

- a full standalone app
- speech recognition infrastructure
- broad multi-language support
- social features
- analytics for the sake of analytics
- general Chinese-learning coverage before the Four Books loop works

Those can come later. The current job is to make the shipped curriculum and host surfaces honest and usable, extend the learning loop past the `Da Xue` starter slice, and keep the bundled package artifacts as accurate as the source repo.
