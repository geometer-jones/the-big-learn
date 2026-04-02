---
name: the-big-learn-flashcard-review
description: Review saved flashcards through a weighted random flow that alternates between one visible face and a full reveal on the next step.
---

# Flashcard Review

Use this skill when the learner wants to review saved flashcards.

## Startup

No startup command is required.

Work from the saved flashcard bank already on disk.

## Job

- sample one saved flashcard from the weighted distribution
- use `weight = significance_flag_count + occurrence_count`
- show only one randomly chosen face first
- on the next review step, reveal both faces for that same card
- then move on to a newly sampled card and repeat

## Review Loop

- Run `python3 -m the_big_learn flashcard-review --format json` to advance the review state.
- If the returned `phase` is `prompt`, show only the single visible face.
- If the returned `phase` is `reveal`, show both faces for that same card.
- If the learner wants to abandon the current pending card and start a fresh draw, run `python3 -m the_big_learn flashcard-review --format json --reset`.

## Card Faces

- Hanzi face: show the simplified form first and append the traditional form in parentheses only when it differs.
- Reading face: show `pinyin (zhuyin)` followed by the semicolon-separated English definitions from `gloss_en`.
- Do not split pinyin, zhuyin, and definitions into separate review faces.
- Do not generate alternate prompt-direction matrices.

## Rules

- Pull only from saved bank entries with positive review weight.
- Treat `occurrence_count` as the number of saved citations on the bank entry.
- Preserve the stored `significance_flag_count`; do not mutate it during review unless the learner explicitly flags the card separately.
- Keep the visible review step short and plain.
- When both faces are visible, preserve the order: Hanzi first, Reading plus definitions second.

## Storage

- Flashcard bank entries live under `$THE_BIG_LEARN_STATE_DIR/flashcards/bank/` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/flashcards/bank/`.
- The pending review-step state lives under `$THE_BIG_LEARN_STATE_DIR/flashcards/review-state.json` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/flashcards/review-state.json`.
