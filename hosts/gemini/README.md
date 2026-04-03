# Gemini Host

This directory contains Gemini CLI host assets for The Big Learn.

The current model is:

- Gemini CLI is a supported main interface for The Big Learn.
- The Big Learn installs custom command files into Gemini CLI.
- Those commands turn ordinary Gemini CLI threads into Chinese tutorial threads.
- The guided-reading menu should present the full curriculum listed in `CURRICULUM.md`.
- A normal install now comes bundled with local full-book source catalogs and raw chapter files for the current curriculum set: `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi`.
- The repo now starts clean from bundled source text rather than a seeded annotation stash.
- Richer line-shell help is generated and saved locally as learners read.
- For books outside that bundled curriculum set, or when the learner wants an alternate source, Gemini should search the web for plausible source pages, let the learner choose among multiple sources, then use the optional `the-big-learn` CLI to build a real full-book chapter menu, save raw chapters locally, and continue guided reading from saved reading units.
- If Gemini cannot search or browse the web in the current environment, it should warn plainly instead of pretending source discovery succeeded.

## Install

From a local checkout:

```bash
git clone --single-branch --depth 1 https://github.com/geometer-jones/the-big-learn.git ~/.gemini/commands/the-big-learn
cd ~/.gemini/commands/the-big-learn
./setup
```

That installs the current checkout in editable mode and installs The Big Learn commands into `~/.gemini/commands` by default. From any other checkout location, run `./setup gemini`.

## Current Host Assets

- `/the-big-learn:guided-reading` for line-by-line reading with immediate, line-grounded questions
- `/the-big-learn:explode-char` for structural Hanzi decomposition and synthesis examples during reading or review
- `/the-big-learn:flashcard-review` for weighted random flashcard review that alternates between one visible face and a full reveal
