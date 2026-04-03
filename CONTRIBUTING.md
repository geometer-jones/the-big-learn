# Contributing

Thanks for helping build The Big Learn.

This repository is early. Right now, the project needs clean scope, strong skill design, and believable evaluation more than volume.

## What Contributions Are Useful

- skill definitions for focused Chinese learning tasks
- workflow specs that combine skills into useful study loops
- correction rubrics and explanation standards
- evaluation fixtures with good and bad examples
- documentation that clarifies scope, architecture, or contribution flow

## Before You Build

Start by reading:

- [README.md](./README.md)
- [PRODUCT.md](./PRODUCT.md)
- [CURRICULUM.md](./CURRICULUM.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ROADMAP.md](./ROADMAP.md)

For local runtime work:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
```

If you changed bundled docs or packaged assets, refresh the build output before you open a PR:

```bash
python3 setup.py build
```

For local Codex-host work:

```bash
the-big-learn codex install --force
```

For local Claude Code host work:

```bash
the-big-learn claude install --force
```

For local Gemini host work:

```bash
the-big-learn gemini install --force
```

If you want to add a new skill or workflow, write down:

- the learner problem
- the target level
- the expected input
- the expected output
- how we will tell if it is good

If that is fuzzy, the implementation will be fuzzy too.

## Contribution Guidelines

- Keep changes small and focused.
- Prefer extending shared rubrics over copying prompt logic.
- Be explicit about learner level, script choice, and output format.
- When script choice matters, mark the stored simplified and traditional forms explicitly.
- If content comes from the Four Books, identify the source work and section.
- Include the combined Reading form only when it helps the learner goal.
- Avoid adding dependencies unless there is a clear payoff.

## Skill Design Rules

Every skill should have:

- one clear job
- a defined learner level or audience
- a predictable output shape
- at least a few examples
- edge cases or failure notes

If the skill touches source-text reading, it should also state:

- which of the six stored layers it consumes
- which of the six stored layers it emits
- which learner-facing units it renders or expects
- whether it can create flashcard bank entries

Bad skill shape:

- "teach Chinese better"

Better skill shape:

- "review an intermediate learner's short paragraph, correct grammar and word choice, explain each fix in plain English, then generate two targeted follow-up drills"

## Workflow Design Rules

A workflow should describe:

- the entry point
- the ordered steps
- what context passes between steps
- what gets saved for later review
- when the workflow should stop

Do not hide important decisions inside a vague "then the agent figures it out" step. That is how quality drifts.

## Evaluation Expectations

If you change behavior, add or update fixtures that show:

- a normal case
- an edge case
- an obviously wrong output we want to avoid

Useful fixture areas:

- line rendering across the six stored layers and combined learner-facing units
- grammar correction
- vocabulary drill difficulty
- translation quality
- tone and register
- explanation clarity
- flashcard direction mapping

## Pull Request Checklist

Before opening a PR:

- update docs when scope or behavior changes
- keep the diff limited to the actual task
- explain why the change helps the learner
- note any assumptions that are still unresolved
- add fixtures or tests if behavior changed
- run `python3 -m unittest discover -s tests` if you changed the runtime layer
- run `python3 setup.py build` if you changed bundled docs or packaged assets under the top level, `evals/`, `flashcards/`, `hosts/`, `skills/`, or `books/`
- run `the-big-learn codex path` and `the-big-learn codex install --target <tmpdir>` if you changed Codex host integration
- run `the-big-learn claude path` and `the-big-learn claude install --target <tmpdir>` if you changed Claude Code host integration
- run `the-big-learn gemini path` and `the-big-learn gemini install --target <tmpdir>` if you changed Gemini host integration

## Project Conventions

Until a toolchain is added:

- use Markdown for planning and skill specs
- keep file and directory names simple
- prefer ASCII unless Chinese text is required for examples
- write examples that a reviewer can judge quickly
- keep the six-layer storage terminology and the learner-facing Hanzi/Reading terminology consistent across docs

## Code of Construction

Build for the learner. Be specific. Be testable.

If a contribution makes the project sound smart but does not make the learning workflow better, it is probably the wrong change.
