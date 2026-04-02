# Runtime

This file describes the optional support layer, not the primary user interface.

The primary interface for The Big Learn is host-native skills inside Codex, Claude Code, and Gemini. Those host assets now read the local starter annotations directly from the repository, and a normal install also comes bundled with local source catalogs plus chapter payloads whose reading units are precomputed for the current curriculum set: `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi`. The Python CLI can still derive live full-book chapter catalogs, save source chapters, load saved reading units, inspect local progress, and manage update-check configuration whenever the repository does not already ship with the needed chapter menu or when the learner wants an alternate source. The Python CLI is optional support for local verification and installer helpers.

The current runtime layer is a tiny Python CLI with no external dependencies.

## Install

For a clone-and-setup install modeled after a Claude skill pack:

```bash
git clone --single-branch --depth 1 https://github.com/geometer-jones/the-big-learn.git ~/.claude/skills/the-big-learn
cd ~/.claude/skills/the-big-learn
./setup
```

That bootstrap installs the current checkout in editable mode and installs the Claude host assets into `~/.claude/skills`. You can target another host from the same checkout with `./setup codex`, `./setup gemini`, or `./setup all`.

If you only want the runtime helper without the bootstrap, from the repo root run:

```bash
python3 -m pip install -e .
```

The installed package also includes bundled curriculum source data under its local `source-store/`, so those nine texts are present immediately on install even outside a git checkout. A manual package install also registers the `the-big-learn` console command, but the bootstrap and host assets use `python3 -m the_big_learn` so they do not depend on `PATH` setup.

Show the installed version:

```bash
python3 -m the_big_learn version
```

Install the Codex skills into `~/.codex/skills`:

```bash
python3 -m the_big_learn codex install
```

Install the Claude Code skills into `~/.claude/skills`:

```bash
python3 -m the_big_learn claude install
```

Install the Gemini CLI commands into `~/.gemini/commands`:

```bash
python3 -m the_big_learn gemini install
```

If you do not want to install it yet, you can still run:

```bash
python3 -m the_big_learn
```

## Commands

Render the starter `Da Xue` lines:

```bash
python3 -m the_big_learn render --work da-xue --start 1 --end 3
```

Run the starter guided-reading fixture end to end:

```bash
python3 -m the_big_learn session
```

Show saved guided-reading progress for the current local `Da Xue` starter slice:

```bash
python3 -m the_big_learn progress
```

Inspect local runtime configuration:

```bash
python3 -m the_big_learn config list
python3 -m the_big_learn config get update_check
python3 -m the_big_learn config get remote_version_url
```

Build a chapter catalog from a live source URL and save it locally when you want an alternate source or a non-bundled curriculum text:

```bash
python3 -m the_big_learn source catalog --url 'https://ctext.org/si-shu-zhang-ju-ji-zhu/zhong-yong-zhang-ju1?if=en'
```

Download one chapter from a live source URL and save it locally when you want an alternate source or need text beyond the bundled curriculum set:

```bash
python3 -m the_big_learn source download --url 'https://ctext.org/si-shu-zhang-ju-ji-zhu/zhong-yong-zhang-ju1?if=en' --chapter 1
```

Load one saved live-source chapter into raw reading units:

```bash
python3 -m the_big_learn source read --url 'https://ctext.org/si-shu-zhang-ju-ji-zhu/zhong-yong-zhang-ju1?if=en' --chapter 1
```

If a host cannot search the web for live source discovery, it should warn the learner plainly and ask for a direct source URL instead of guessing.

Show the default Codex skill install path:

```bash
python3 -m the_big_learn codex path
```

Show the default Claude Code skill install path:

```bash
python3 -m the_big_learn claude path
```

Show the default Gemini CLI command install path:

```bash
python3 -m the_big_learn gemini path
```

Emit JSON instead of Markdown:

```bash
python3 -m the_big_learn session --format json
```

Step through weighted flashcard review:

```bash
python3 -m the_big_learn flashcard-review --format json
```

Check whether a newer upstream version is available:

```bash
python3 -m the_big_learn update-check
```

Force a fresh update check, ignoring cache and snooze state:

```bash
python3 -m the_big_learn update-check --force
```

Snooze prompts for a specific remote version:

```bash
python3 -m the_big_learn update-snooze --version 0.2.0 --level 1
```

Disable update checks entirely:

```bash
python3 -m the_big_learn config set update_check false
```

If your install does not come from a git checkout with an `origin` remote, set the upstream `VERSION` URL explicitly:

```bash
python3 -m the_big_learn config set remote_version_url https://raw.githubusercontent.com/<owner>/<repo>/main/VERSION
```

## State And Environment

The CLI stores local state under `~/.the-big-learn/` by default. That state directory currently holds:

- `config.json` for `update_check` and `remote_version_url`
- `last-update-check.json` for update-check cache state
- `update-snoozed.json` for snoozed upgrade prompts
- `installed-version` for `JUST_UPGRADED` detection
- `reading-progress.json` for saved chapter-level line translation and line response logs plus book-level summary and response progress
- `source-store/` for cached live source catalogs, HTML snapshots, downloaded chapter payloads, and any saved generated line annotations for raw-source reading units
- `flashcards/review-state.json` for the pending flashcard-review step when a card has been shown but not yet revealed

Supported environment overrides:

- `THE_BIG_LEARN_STATE_DIR` relocates the local state directory
- `THE_BIG_LEARN_ROOT` points the runtime at a different repo root when loading repository-backed assets
- `THE_BIG_LEARN_REMOTE_VERSION_URL` overrides the inferred upstream `VERSION` URL for update checks

## Test

Run runtime tests:

```bash
python3 -m unittest discover -s tests
```

There is also a targeted starter-data audit script in `scripts/verify_starter_data.py`, but it currently lags the combined `hanzi` and `reading` flashcard policy and is not the main passing verification path.

## What It Does

- loads local annotation records from `annotations/`
- ships with bundled curriculum source catalogs and chapter payloads with precomputed reading units under `source-store/`
- uses locally stored starter source text so the host loop does not need a separate runtime app
- derives real full-book chapter catalogs from selected external source URLs and saves those catalogs locally when the bundled data is not enough
- downloads selected raw chapters from live sources and saves them locally under the source store
- loads saved source chapters into deterministic local reading units for raw-source guided reading
- can persist generated per-line annotations back into saved source chapter payloads so later raw-source sessions can reuse them
- gives host launchers a deterministic way to open bundled curriculum chapter menus immediately or turn a chosen external source URL into a real full-book chapter menu and a saved local chapter file
- renders the line-first reading pass from the six stored layers
- reports saved chapter-level line translation and line response progress plus book-level summary and response status
- answers learner questions from the starter fixture
- emits deterministic line-grounded answers
- creates flashcard bank entries
- steps through weighted flashcard review with alternating prompt and reveal states

The host loop can run directly from the repository files. The CLI remains useful when you want repeatable rendering, fixture playback, installer commands, or alternate source ingestion beyond the bundled curriculum set.

This is not the main product surface. It is the executable support layer behind the skill-driven experience.
