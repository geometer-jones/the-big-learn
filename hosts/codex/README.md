# Codex Host

This directory contains Codex-facing host assets for The Big Learn.

The current model is:

- Codex is the main user interface.
- The Big Learn installs `SKILL.md` folders into Codex.
- Those skills turn ordinary Codex threads into Chinese tutorial threads.
- The guided-reading menu should present the full curriculum listed in `CURRICULUM.md`.
- Locally annotated texts such as `Da Xue` still read directly from repository annotation files where that annotation exists.
- A normal install now comes bundled with local full-book source catalogs and raw chapter files for the current curriculum set: `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi`.
- Only `Da Xue` currently has the richer six-layer local annotation set; the other bundled texts currently read from bundled raw-source chapters by default.
- For books outside that bundled curriculum set, or when the learner wants an alternate source, Codex should search the web for plausible source pages, let the learner choose among multiple sources, then use the optional `the-big-learn` CLI to build a real full-book chapter menu, save raw chapters locally, and continue guided reading from saved reading units.
- If Codex cannot search or browse the web in the current environment, it should warn plainly instead of pretending source discovery succeeded.

## Install

From a local checkout:

```bash
git clone --single-branch --depth 1 https://github.com/geometer-jones/the-big-learn.git ~/.codex/skills/the-big-learn
cd ~/.codex/skills/the-big-learn
./setup
```

That installs the current checkout in editable mode and installs The Big Learn skills into `~/.codex/skills` by default. From any other checkout location, run `./setup codex`.

## Current Host Assets

- a Codex launcher skill for guided reading
- installed copies of the repo's internal skills under a `the-big-learn-` prefix
