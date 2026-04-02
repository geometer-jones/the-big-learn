# DESIGN

The Big Learn is a thread-native product. Its design system is mostly language, pacing, recurring turn shapes, and how much initiative the assistant takes. It is not a dashboard, a marketing site, or a settings-heavy app.

## Purpose

This file is the canonical design source for cross-host thread surfaces in Codex, Claude Code, and later Gemini. Use it to keep vocabulary, rhythm, and interaction shapes consistent across hosts.

## Principles

- Keep the text louder than the assistant.
- Preserve continuity. Reading should not shatter because help is available.
- One ritual, one steady support posture.

## Guided-Reading Posture

Guided reading uses one fixed posture:
- answer direct line-grounded questions immediately when the learner asks
- auto-recommend a very small number of salient character and phrase follow-ups for exploding and flashcards
- persist progress as soon as the relevant artifact exists
- as each learner translation is recorded, update and save the current `Personal Translation` immediately
- when a chapter closes, finalize and save the latest stitched `Personal Translation` without opening a separate chapter-end response checkpoint
- let the researcher/philosopher discussion follow the chapter-end `Personal Translation` and the book-end `Personal Response`
- when the learner provides the book-end `Personal Response`, save it immediately before final evaluation and Nostr drafting
- keep support labels explicit and factual

This posture does not change:

- the ritual order
- persistence behavior
- seriousness of textual engagement
- the learner's ability to ask for more help at any point

## Explode-Char Posture

Explode-char is a sidecar support surface, not a separate product mode.

- answer the requested character immediately instead of reopening the whole reading frame
- keep structural analysis compact, nested, and explicit about uncertainty
- use synthesis examples to make the target character usable right away
- end with exactly two concrete flashcard candidates
- if entered from guided reading, preserve the learner's place and make re-entry back into reading easy

This posture does not change:

- simplified-first Chinese display
- inline reading format as `pinyin (zhuyin)`
- preference for common, teachable examples over obscure or speculative ones
- explicit labels when a decomposition or containment claim is only graphical or uncertain

## Surface Vocabulary

Use the same small vocabulary across hosts:

- Saved-work tags: `[translation saved]`, `[response saved]`, `[unsaved]`
- Primary action prompts: `Continue reading`, `Choose a chapter`, `Your translation?`, `Your response?`, `Retry save`
- Failure state heading: `[Save did not complete]`
- Explode-char section labels: `Analysis`, `Synthesis`, `Phrase Use`, `Containing Characters`, `Homophones`, `Meaning Map`, `Flashcard Candidates`

Rules:

- Keep tags compact and factual.
- Keep primary actions short and imperative.
- Use `Your response?` for line-level reflection and book-end reflection, not as a chapter-transition gate.
- Secondary actions should be fewer and visually quieter than primary actions.
- Avoid emojis, decorative separators, and marketing-style headings in the reading flow.

## Turn Shapes

### Opening Turn

Hierarchy:

1. `Resume where you left off` block, if saved work exists
2. `Recommended next step`
3. Flat numbered curriculum menu
4. One-line instruction to reply with number or title

Tone:

- one calm sentence on what guided reading is
- one practical sentence on how to choose or continue
- no motivational fluff
- no apology for difficulty
- no wall of instructions before the menu

### Chapter Menu

Hierarchy:

1. Chapter title and short English framing
2. Title rendered as a miniature line shell
4. Saved-work tags
5. Length signal
6. Chapter choices

Title line shell:

- Render book and chapter titles in the same order as regular line rendering: see Line Shell.
- Titles do not open the learner translation and response loop. They are reference lines, not reading-pass lines.

### Line Shell

Default order:

0. Learner prompt
1. Simplified Chinese line
2. English line
3. Char-by-char support table
3.1 Chinese: simplified chinese character (traditional chinese character, if they differ)
3.2 Pronunciation: pinyin (zhuyin)
3.3 English character translation: <semi-colon separated list of context-free definitions of the character in 3.1 for that row>
3.4 Chinese phrase: simplified chinese characters grouped by semantic unit
3.5 English phrase translation: english translation grouped by semantic unit
4. English line
5. Simplified Chinese line
6. Line location/identity (e.g. line i of chapter k of book n)
7. Learner prompt

Rules:
- The Chinese line is the visual anchor.
- The char-by-char does most of the structural work.

### Explode-Char Turn

Hierarchy:

1. One brief bridge line if the learner arrived here from guided reading
2. `Analysis`
3. `Synthesis`
4. Direct save offer for exactly two flashcard candidates
5. Short return cue when the learner should resume the reading flow

Rules:

- `Analysis` uses nested bullets, not tables.
- Start with the full target character as the root node, then descend only as far as the decomposition stays teachable and honest.
- Keep simplified Chinese in the primary position and append traditional only when it differs. If simplified and traditional differ, then run two separate explosions, in the same style as if a phrase were exploded, and you explode each word in sequence.
- Render every reading inline as `pinyin (zhuyin)`.
- Keep `Synthesis` subsection order fixed: `Containing Characters, ie character that contain the exploded-char within its composition`, `Phrase Use, ie multi-character phrases that contain the exploded-char as one char`, `Homophones`, `Synonyms`, `Antonyms`, `Flashcard Candidates`.
- Try to divine the etymology, but be disciplined in qualifying the strength of your hunches

### Chapter End

Hierarchy:

1. Full English recap
2. Full Chinese recap
3. Learner's stitched `Personal Translation`
4. Save the current `Personal Translation` immediately if the latest stitched version is not already persisted
5. Discussion with LLM as a researcher and philosopher
6. One brief bridge line into the next chapter, or a compact stop marker if the learner asked to stop at that boundary

Rules:

- Chapter end is a continuity seam, not a separate reflection ritual.
- Do not prompt for a chapter-end `Personal Response`.
- If the learner is continuing the same book, move directly into the next chapter after the recap, save step, and chapter-end discussion.

### Book End

Hierarchy:

1. Book completion marker and short framing
2. Completed `Personal Translation` state, or a compact book-level completion recap when useful
3. Learner prompted for `Personal Response`
4. Save `Personal Response` immediately when it is provided
5. Discussion with LLM as a researcher and philosopher
6. Draft the end-of-book Nostr post and confirm or publish it

## States

- Keep automatic recommendations to one or two characters for exploding and one or two characters or phrases for flashcards at a time.

### Save Failure

- Keep the unsaved current `Personal Translation` and any active `Personal Response` visible in-thread.
- Show an explicit `unsaved` state block.
- Offer `Retry save` as the primary action.
- Do not continue past the current chapter or book boundary while the active artifact remains unsaved.

Example:

```text
[Save did not complete]
Your current translation and response are still visible in this thread, but they are not stored yet.
Primary action: Retry save
Secondary action: Stop here and keep this chapter open
```

## Responsive and Accessibility

- Default to the five-column char-by-char table when it renders clearly.
- Switch to a stacked per-character list when the host pane is narrow or table readability is poor.
- Do not mix both formats for the same rendered line.
- Preserve stable top-to-bottom order so the thread still works without visual scanning.
- Keep cue phrases consistent across turns.
- Default to compact prompts, but allow more explicit repeated cues when the host surface or learner needs stronger structure.

Stacked fallback:

```text
<simplified char> (traditional char, if different)
pinyin (zhuyin)
<char translation>
<Phras>
<Phrase translation>
```


## Not In Scope

- standalone web app or dashboard chrome
