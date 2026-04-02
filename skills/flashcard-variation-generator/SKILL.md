---
name: the-big-learn-flashcard-variation-generator
description: Generate flashcard prompt and answer directions across the six-layer model. Use when an existing bank entry should produce multiple review cards for recall from different angles.
---

# Flashcard Variation Generator

Use this skill to turn one canonical bank entry into many useful card directions.

Treat simplified and traditional Hanzi as one review unit. Display simplified first, and append the traditional form in parentheses when it differs.
Treat pinyin and zhuyin as one reading unit. Display pinyin first, and append the zhuyin form in parentheses.

## Startup

No startup command is required.

Read the bank entry and flashcard policy directly from the repository files already available in the workspace.

## Job

- choose prompt and answer layer pairs
- avoid same-layer cards
- prioritize the most useful early-stage recall paths first
- keep the generated card text faithful to the bank entry
- persist the generated variation set to disk instead of leaving it only in chat

## Default Priority

Start with:

1. hanzi -> reading
2. reading -> hanzi
3. hanzi -> gloss_en
4. translation_en -> hanzi
5. hanzi -> translation_en

Then expand as needed to the full any-layer-to-any-other-layer matrix.

## Rules

- Do not generate redundant cards.
- Do not treat simplified and traditional as separate card directions.
- Do not treat pinyin and zhuyin as separate card directions.
- Treat `gloss_en` and `translation_en` as one effective English direction when they render to the same text for a given entry, which is common for single-character cards.
- Keep one card focused on one answer target.
- Preserve line or segment references when available.
- If a layer is missing, skip that direction instead of fabricating it.
- When the variation set is ready, save it with `python3 -m the_big_learn flashcard-save --format json`.
- The saved variation set lives under `$THE_BIG_LEARN_STATE_DIR/flashcards/variations/` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/flashcards/variations/`.

## Output

Each generated card should include:

- source bank entry id
- prompt layer
- answer layer
- prompt text
- answer text
- optional hint
