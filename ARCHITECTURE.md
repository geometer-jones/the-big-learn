# Architecture

This file describes the intended architecture of The Big Learn. It now reflects a small content-first implementation scaffold plus the larger planned system.

## System Purpose

The Big Learn aims to package Chinese-learning expertise into reusable agent skills and multi-step workflows that run inside coding assistants.

The primary product shape is:

- host-native conversation UX in Codex, Claude Code, and Gemini
- repository-native curriculum and fixture files that the host skills can read directly
- optional local CLI for verification, source catalog caching, raw chapter downloads, and installer helpers
- portable skill-pack structure for future host expansion

The system should help an assistant move through a repeatable loop:

1. present source text in the right format
2. capture questions without breaking reading flow
3. answer those questions immediately in the current line discussion
4. generate review artifacts from real confusion
5. carry useful memory into the next session

## Current Repository State

As of now, the repository contains docs plus a first content-first scaffold.

- Primary languages: Markdown, JSON, and Python
- Application entry points: host launcher skills and commands under `hosts/`, repo skills under `skills/`, and an optional Python CLI for rendering, progress inspection, source cataloging, chapter download, update checks, config management, and host installation
- Core modules: starter curriculum records, bundled curriculum source catalogs and raw chapter snapshots, skill definitions, workflow definitions, fixture data, and an optional Python support layer for rendering, verification, state management, source ingest, updates, and host installation
- Dependency management: `pyproject.toml` with `setuptools`
- Build system: `setuptools` via `pyproject.toml` and `setup.py`, with `setup.py build` copying bundled assets into `the_big_learn/bundle`
- Test framework: Python `unittest`
- Config and environment files: `pyproject.toml`, `MANIFEST.in`, `setup.py`, `VERSION`, plus optional `THE_BIG_LEARN_ROOT`, `THE_BIG_LEARN_STATE_DIR`, and `THE_BIG_LEARN_REMOTE_VERSION_URL`

Recommended initial stack:

- Markdown and JSON for curriculum, skill, and workflow records
- Python standard library for the first runtime and local verification
- Python `unittest` for current runtime checks
- TypeScript or Node.js later if host adapters need it

The Python choices above are facts on disk. The current supported hosts are Codex, Claude Code, and Gemini.

## Logical Modules

### 1. Skill Definitions

Purpose: define single-role behaviors such as assessment, drill generation, correction, or review.

Likely location:

```text
skills/<skill-name>/
  SKILL.md
  examples/
  fixtures/
```

Responsibilities:

- describe the role and boundaries of the skill
- define required inputs and expected outputs
- include examples for common learner scenarios
- keep behavior narrow and composable

Early examples:

- `the-big-learn-flashcard-bank-add`
- `the-big-learn-flashcard-review`

### 2. Workflows

Purpose: coordinate multiple skills into longer learning loops.

Examples:

- Four Books guided reading workflow
- daily idle-time study workflow
- writing feedback workflow
- reading comprehension workflow

Likely location:

```text
workflows/<workflow-name>/
  README.md
  prompts/
  fixtures/
```

Responsibilities:

- choose which skills run and in what order
- pass learner context across steps
- define stop conditions and follow-up actions

The first workflow should center on continuous reading plus line-grounded question handling inside the same guided-reading session.

### 3. Annotation Library

Purpose: store provenance, lookup rules, and canonical line-level annotations that the rest of the system uses.

Likely location:

```text
annotations/
  da-xue/
  zhong-yong/
  lunyu/
  mengzi/
```

Responsibilities:

- store source provenance, line order, and segmentation
- keep the full six-layer line record local so host-native skills can read it directly
- derive learner-facing Hanzi and Reading units from that stored record instead of duplicating display logic across tools
- preserve lookup metadata for provenance and future verification
- store bundled curriculum source catalogs, locally saved raw chapter snapshots, and raw-source reading-unit payloads for curriculum books whose full chapter menus are not yet fully encoded in-repo
- support future enrichment without changing the base text record

### 4. Shared Learning Library

Purpose: centralize reusable teaching rules so the project does not fork its own logic across many skills.

Likely location:

```text
lib/
content/
```

Responsibilities:

- combined Hanzi display rules
- combined Reading display rules
- correction rubrics
- difficulty labels
- lesson and exercise templates
- reusable explanation patterns

### 5. Flashcard Bank

Purpose: store learner-relevant items and support weighted flashcard review across the learner-facing units derived from the six stored layers.

Likely location:

```text
flashcards/
  templates/
  fixtures/
```

Responsibilities:

- create bank entries from learner questions
- support phrase-level and character-level cards
- generate card variants between any relevant learner-facing units while preserving the six stored layers
- track which prompt direction was used

### 6. Host Adapters

Purpose: package the same skills for different coding assistant hosts.

Likely location:

```text
hosts/
  codex/
  claude/
  gemini/
```

Responsibilities:

- host-specific installation layout
- registration metadata
- compatibility notes and constraints
- guided-reading menu presentation from `CURRICULUM.md`
- host-side web discovery and source selection for curriculum books that do not yet have local six-layer annotations
- explicit warnings when the current host environment cannot search or browse the web

Current state:

- Codex host scaffolding exists
- Claude Code host scaffolding exists
- Gemini CLI command scaffolding exists
- the CLI can install The Big Learn host assets into their default user directories
- the CLI can build source-backed chapter catalogs from supported web pages and save raw chapters locally
- the CLI can inspect saved progress for source-backed curriculum chapters
- the CLI can manage update-check state and local config

### 7. Evaluation Layer

Purpose: verify that generated exercises and corrections stay useful and consistent as prompts evolve.

Likely location:

```text
evals/
  fixtures/
  snapshots/
```

Responsibilities:

- correction regression checks
- line rendering checks
- question-answer quality checks
- flashcard direction checks
- prompt output comparisons
- edge-case fixtures for grammar, vocabulary, and register
- quality bars for explanations and exercise difficulty

## Core Data Model

The central record should be a line object with six stored representations.

Conceptually:

```text
line
  id
  work
  section
  order
  traditional
  simplified
  zhuyin
  pinyin
  gloss_en
  translation_en
```

Around that record, the system will likely need:

- question records
- answer records
- flashcard bank entries
- review event history
- learner profile and weak-point summaries

Learner-facing renderers and flashcard generators should derive:

- `hanzi` from simplified plus traditional
- `reading` from pinyin plus zhuyin

## Data Flow

The intended data flow is:

```text
Learner request
  -> host adapter
  -> workflow router
  -> selected reading workflow
  -> curriculum menu from CURRICULUM.md
  -> if locally annotated: annotation records
  -> else if bundled source text exists: packaged source catalog -> bundled raw chapter -> local reading units
  -> else: web query -> source selection -> source catalog -> saved raw chapter -> local reading units
  -> selected skill
  -> shared rubrics/content
  -> generated answer, explanation, or card
  -> evaluation or validation step
  -> final response
  -> optional progress memory for later sessions
```

Example:

```text
User reads a Da Xue passage
  -> workflow renders each line in a line-first view derived from the six stored layers
  -> user asks line-grounded questions while continuing to read
  -> guided reading answers those questions in the same line discussion
  -> referenced words are added to the flashcard bank
  -> workflow generates review cards for later sessions
```

```text
User opens Zhong Yong from the guided-reading menu
  -> host reads the book list from CURRICULUM.md
  -> host loads the bundled full-book source catalog that ships with the install
  -> host keeps all catalog chapters visible instead of collapsing the menu to only locally annotated material
  -> the selected bundled raw chapter is loaded into local reading units for guided reading
  -> if the learner wants a different source or the current book is outside the bundled curriculum set, host falls back to live source discovery
```

## Service Boundaries

The project should keep these boundaries clean:

- Skill boundary: a skill should do one job well.
- Workflow boundary: a workflow composes skills, it should not duplicate their internal logic.
- Curriculum boundary: source text data should be canonical and reusable.
- Content boundary: shared language rules and examples should live in reusable libraries, not be copy-pasted into every skill.
- Flashcard boundary: review generation should be derived from canonical line data and learner events, not stored as ad hoc prompt text.
- Host boundary: packaging and registration details should be isolated from the learning logic.
- Evaluation boundary: tests and fixtures should validate outputs without becoming production logic.

## Entry Points

Current entry points:

- `python3 -m the_big_learn`
- `the-big-learn version`
- `the-big-learn render --work da-xue --start 1 --end 3`
- `the-big-learn session`
- `the-big-learn progress`
- `the-big-learn codex install`
- `the-big-learn claude install`
- `the-big-learn gemini install`
- `the-big-learn source catalog --url <source-url>`
- `the-big-learn source download --url <source-url> --chapter <chapter>`
- `the-big-learn source read --url <source-url> --chapter <chapter>`
- `the-big-learn update-check`
- `the-big-learn update-snooze --version <version>`
- `the-big-learn config list`
- installed host-specific skill discovery directories such as `~/.codex/skills`, `~/.claude/skills`, and `~/.gemini/commands`
- workflow entry skills such as `the-big-learn-guided-reading`

Additional planned entry points:

- future workflow entry skills such as `four-books-read` or `writing-review`

## Configuration

Current repository and packaging configuration files:

- `pyproject.toml` for project metadata and the `setuptools` build backend
- `setup.py` for copying bundled docs, content, skills, hosts, and workflow assets into `the_big_learn/bundle`
- `MANIFEST.in` for source distribution inclusion
- `VERSION` for the release/version-check source of truth

Current local runtime state files under `~/.the-big-learn/` or `$THE_BIG_LEARN_STATE_DIR`:

- `config.json`
- `last-update-check.json`
- `update-snoozed.json`
- `installed-version`
- `reading-progress.json`
- `source-store/`

Current config surfaces:

- `config.json` keys: `update_check`, `remote_version_url`
- `THE_BIG_LEARN_ROOT` to override the repository root for repository-backed asset loading
- `THE_BIG_LEARN_STATE_DIR` to relocate local runtime state, including progress and source caches
- `THE_BIG_LEARN_REMOTE_VERSION_URL` to override the inferred upstream `VERSION` URL

Likely future configuration areas:

- default learner profile
- script preference
- Hanzi display rules
- Reading display rules
- difficulty target
- study session length
- flashcard generation defaults
- host integration settings

## Where New Work Should Go

Architecture and product-shape changes still land in top-level docs and planning files. Implementation changes should follow these module boundaries:

- new single-purpose behaviors belong under `skills/`
- multi-step sequences belong under `workflows/`
- canonical six-layer annotation records belong under `annotations/`
- bundled and cached raw-source catalogs or chapters belong under `source-store/`
- reusable rubrics and structured content belong under shared libraries
- flashcard logic and templates belong under `flashcards/`
- packaging logic belongs under `hosts/`, `setup.py`, and `MANIFEST.in`
- runtime state and CLI behavior belong under `the_big_learn/`
- quality checks belong under `evals/`
- regression tests belong under `tests/`

## Architectural Guardrails

- Start with text-first workflows before audio or speech scoring.
- Preserve the six-layer line model as the base storage abstraction.
- Prefer a narrow set of high-quality skills over a giant prompt dump.
- Start with the Four Books wedge before broadening to general Chinese content.
- Keep skill outputs structured enough to test.
- Avoid hard-coding host-specific behavior into core learning logic.
- Add dependencies only when they reduce real maintenance cost.
