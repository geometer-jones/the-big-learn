---
name: the-big-learn-flashcard-bank-add
description: Turn learner questions or reviewed source segments into canonical flashcard bank entries across the six-layer model. Use when a Chinese word, phrase, or character should be saved for later review.
---

# Flashcard Bank Add

Use this skill to create a reusable bank entry.

## Startup

No startup command is required.

Use the repository files in the workspace to recover the source line, segment, and flashcard policy before drafting a bank entry.

## Job

- select the source line or segment
- preserve all six layers
- record why the card exists
- keep the bank entry canonical so multiple card directions can be generated later
- persist the final bank entry to disk instead of leaving it only in chat

## Required Fields

- bank entry id
- source work
- source line ids
- source segment ids when available
- origin kind
- six-layer payload
- eligible prompt layers
- status

## Rules

- Prefer phrase-level entries when the learner asked about a phrase.
- Prefer character-level entries only when the confusion is character-specific.
- Do not create duplicate bank entries if the same segment already exists.
- For single-character entries, `translation_en` may legitimately be identical to `gloss_en`; do not force a longer English translation just to make the two fields differ.
- Preserve the learner-origin note so future review can explain why this card matters.
- When the bank entry is ready, save it with `python3 -m the_big_learn flashcard-save --format json`.
- The saved bank entry lives under `$THE_BIG_LEARN_STATE_DIR/flashcards/bank/` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/flashcards/bank/`.

## Default Layer Policy

All six layers should be stored when available:

- traditional
- simplified
- zhuyin
- pinyin
- gloss_en
- translation_en

Storing zhuyin and pinyin does not make them separate prioritized review directions. That priority is defined separately by the flashcard variation policy.
