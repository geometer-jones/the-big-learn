# The Big Learn

The Big Learn is an open-source Chinese learning system designed to run inside coding assistants. Its primary interface is a set of host-native skills and commands for Codex, Claude Code, and Gemini. The Python package in this repository is a host-support layer for installation, bundled source access, live source cataloging, learner-artifact persistence, and local flashcard state.

## Approach

The project is built around a small number of explicit ideas:

- Start with canonical source texts instead of situation-specific phrase packs.
- Encode each source line in six stored layers: simplified Chinese, traditional Chinese, pinyin, zhuyin, English char-by-char translation, and English holistic translation.
- Render each annotated line in a fixed learner-facing sequence: full-line simplified Chinese, full-line English, a char-by-char breakdown table with `Chinese`, `Reading`, `English Definition`, `Chinese Phrase`, and `English Phrase Translation`, then the same full line again in English and simplified Chinese before any learner translation or notes.
- In that table, keep simplified primary and append traditional in parens only where it differs, keep pinyin primary with zhuyin in parens, use semicolon-separated context-free English definitions in the `English Definition` column, and let the phrase columns span multiple character rows when a stored segment covers more than one character.
- Keep reading continuous: let the learner keep moving, ask line-grounded questions as they arise, and answer them in the same discussion.
- Turn durable confusion points into flashcards and review them through a weighted random prompt-and-reveal loop.
- Keep prompts, curriculum data, fixtures, and policies in the repository so the behavior is inspectable and editable.

The current curriculum spine starts with the Four Books and begins with `Da Xue`. The guided-reading menu now reflects the full curriculum in `CURRICULUM.md`, while keeping `Da Xue` as the recommended starting point. The install bundle now ships with prepackaged local source catalogs and chapter payloads with precomputed reading units for the current curriculum set: `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi`. Guided reading now uses that bundled source-backed chapter path across the shipped curriculum, with live assistant support during the reading pass and saved generated help available on reread.

## Learning Loop

1. Choose a curriculum book from the guided-reading menu.
2. If the selected book already has a complete local chapter catalog or bundled raw-source chapter store, load it from local package data and continue from those saved files.
3. Continue from bundled or saved raw-source reading units, and reuse any saved generated help on reread before generating new line support.
4. If the selected book does not already ship with a complete local chapter catalog, search the web for likely source pages, let the learner choose among plausible sources when needed, derive the full book chapter menu from the chosen source, download the selected chapter, and continue from saved local reading units.
5. Let the learner translate each line and ask grounded questions without leaving the reading flow.
6. Answer those line-level questions against the exact line or phrase in the same discussion.
7. Create flashcard entries from the learner's real confusion points.
8. Save chapter progress for later sessions.

## System Shape

- `skills/`: reusable learning skills
- `hosts/`: host-specific assets for Codex, Claude Code, and Gemini
- `books/`: bundled and saved full-book source catalogs plus raw chapter payloads
- `scripts/the_big_learn/`: optional Python host-support CLI for installers, source cataloging, progress storage, flashcard storage, and browsable learner-artifact mirrors
- `flashcards/`: bundled static flashcard assets only. The repo currently carries `schema/bank-entry.schema.json` and `templates/default-variation-policy.json` here; saved flashcards and review state live under the runtime state dir, not in the repository.
- `scripts/`: Python package source plus any local development helpers
- `evals/` and `tests/`: fixtures and regression coverage

## Quick Start

The main product surface is the host assets. For a Claude-style clone-and-setup install:

```bash
git clone --single-branch --depth 1 https://github.com/geometer-jones/the-big-learn.git ~/.claude/skills/the-big-learn
cd ~/.claude/skills/the-big-learn
./setup
```

That bootstrap installs the current checkout in editable mode and installs the Claude host assets into `~/.claude/skills`. To target a different host from the same checkout:

```bash
./setup codex
./setup gemini
./setup all
```

If you want the helper runtime without the bootstrap, you can still install it manually:

```bash
python3 -m pip install -e .
```

A normal install now comes bundled with the full text of the current curriculum set under the local `books/`, so `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi` are available immediately after install without a post-install fetch.

Optional verification commands:

```bash
python3 -m the_big_learn claude install --force
python3 -m the_big_learn codex install --force
python3 -m the_big_learn gemini install --force
python3 -m the_big_learn source catalog --url 'https://ctext.org/si-shu-zhang-ju-ji-zhu/zhong-yong-zhang-ju1?if=en'
python3 -m the_big_learn source read --url 'https://ctext.org/si-shu-zhang-ju-ji-zhu/zhong-yong-zhang-ju1?if=en' --chapter 1
python3 -m unittest discover -s tests
```

## Current Scope

- Guided-reading menu: full curriculum from `CURRICULUM.md`
- Bundled curriculum source text: prepackaged full-book chapter catalogs and chapter payloads with precomputed reading units for `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi` in `books/`
- Repository content starts from bundled `books/` chapter data, while richer line-shell help is generated and saved locally as users read
- Live source support beyond the bundled curriculum set: full-book source catalogs, saved raw chapter downloads, and raw-source reading units from selected source URLs
- Supported workflow: guided reading with line-grounded question handling for bundled or download-on-demand source texts
- Saved progress and learner artifacts: host flows persist chapter-level and book-level state into `reading-progress.json`, with a browsable mirror of learner artifacts under `reading/`
- Flashcards: bank entry creation and weighted review
- Supported hosts: Codex, Claude Code, and Gemini
- Runtime: Python 3.9+, `setuptools`, and the standard library

If guided reading needs live source discovery and the host environment cannot search the web, the host asset should warn the learner plainly instead of pretending source discovery succeeded.

## Related Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DESIGN.md](./DESIGN.md)
- [PRODUCT.md](./PRODUCT.md)
- [CURRICULUM.md](./CURRICULUM.md)
- [README_RUNTIME.md](./README_RUNTIME.md)
- [hosts/codex/README.md](./hosts/codex/README.md)
- [hosts/claude/README.md](./hosts/claude/README.md)
- [hosts/gemini/README.md](./hosts/gemini/README.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
