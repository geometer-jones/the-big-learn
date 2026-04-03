# Claude Code Host

This directory contains Claude Code host assets for The Big Learn.

The current model is:

- Claude Code is a main user interface for The Big Learn.
- The Big Learn installs `SKILL.md` folders into Claude Code.
- Those skills turn ordinary Claude Code threads into Chinese tutorial threads.
- The guided-reading menu should present the full curriculum listed in `CURRICULUM.md`.
- A normal install now comes bundled with local full-book source catalogs and raw chapter files for the current curriculum set: `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi`.
- The repo now starts clean from bundled source text rather than a seeded annotation stash.
- Richer line-shell help is generated and saved locally as learners read.
- For books outside that bundled curriculum set, or when the learner wants an alternate source, Claude Code should search the web for plausible source pages, let the learner choose among multiple sources, then use the optional `the-big-learn` CLI to build a real full-book chapter menu, save raw chapters locally, and continue guided reading from saved reading units.
- If Claude Code cannot search or browse the web in the current environment, it should warn plainly instead of pretending source discovery succeeded.

## Install

For a Claude-style clone-and-setup install:

```bash
git clone --single-branch --depth 1 https://github.com/geometer-jones/the-big-learn.git ~/.claude/skills/the-big-learn
cd ~/.claude/skills/the-big-learn
./setup
```

That installs the current checkout in editable mode and installs The Big Learn skills into `~/.claude/skills`.

## Current Host Assets

- a Claude Code launcher skill for guided reading
- installed copies of the repo's internal skills under a `the-big-learn-` prefix
