# DESIGN

The Big Learn is a thread-native product. Its design system is mostly language, pacing, recurring turn shapes. It is not a dashboard, a marketing site, or a settings-heavy app.

## Purpose

This file is the canonical design source for cross-host thread surfaces in Codex, Claude Code, and later Gemini. Use it to keep vocabulary, rhythm, and interaction shapes consistent across hosts.

## Language Default

- The LLM should communicate primarily in English across all host surfaces.
- Keep framing, prompts, explanations, save-state messaging, and discussion in English unless the learner explicitly asks for another language.
- Use Chinese where the product requires it: source lines, character and phrase examples, flashcard faces, quoted learner input, and direct analysis of Chinese text.

## Guided-Reading Posture

Guided reading uses one fixed posture:
- answer direct line-grounded questions immediately when the learner asks
- auto-recommend a very small number of salient character and phrase follow-ups for exploding and flashcards
- as each line shell is completed, fold every non-punctuation character row into the persistent character-index flashcard bank
- merge repeated characters into the existing flashcard instead of creating duplicates, store citations of each appearance, and keep a separate `significance_flag_count` for the number of times the learner explicitly flags that card as significant or relevant
- let those saved cards feed a later weighted review loop instead of generating a separate variation matrix
- persist progress as soon as the relevant artifact exists
- as each learner translation is recorded, update and save the current `Personal Translation` immediately
- when a chapter closes, finalize and save the latest stitched `Personal Translation` without opening a separate chapter-end response checkpoint
- let the researcher/philosopher discussion follow the chapter-end `Personal Translation` and the book-end `Personal Response`
- when the learner provides the book-end `Personal Response`, save it immediately before final evaluation and Nostr drafting
- keep support labels explicit and factual

This posture does not change:

- the reading order
- persistence behavior
- seriousness of textual engagement
- the learner's ability to ask for more help at any point

## Explode-Char Posture

Explode-char is a sidecar support surface, not a separate product mode.

- answer the requested character immediately instead of reopening the whole reading frame
- keep structural analysis compact, nested, and explicit about uncertainty
- use synthesis examples to make the target character usable right away
- do not turn the exploder into a flashcard-saving surface
- if entered from guided reading, preserve the learner's place and make re-entry back into reading easy

This posture does not change:
- inline reading format as `pinyin (zhuyin)`
- usage of common, teachable examples, as well as obscure or speculative ones if they are interesting
- explicit labels when a decomposition or containment claim is only graphical or uncertain

## Flashcard-Review Posture

Flashcard review is a lightweight recall loop, not a deck-builder.

- sample saved cards from a weighted distribution
- use `weight = 10 * significance_flag_count + occurrence_count`
- treat `occurrence_count` as the number of saved citations on that card
- show exactly one randomly chosen face first
- on the next step, reveal both faces for that same card
- then move directly to the next weighted random card
- do not generate alternate prompt-direction sets for the same entry

This posture does not change:

- simplified-first Hanzi display, with traditional in parentheses only when it differs
- reading display as `pinyin (zhuyin)`
- reading face definitions rendered from the saved semicolon-separated English definitions
- reveal order fixed as Hanzi first, then Reading plus definitions

## Surface Vocabulary

Use the same small vocabulary across hosts:

- Saved-work tags: `[translation saved]`, `[response saved]`, `[unsaved]`
- Primary action prompts: `Continue reading`, `Choose a chapter`, `Your translation?`, `Your response?`, `Retry save`
- Flow cue prefix: a brief English lead-in ahead of `Your translation?` or `Your response?` as a philosopher and researcher, inviting questions and comments
- Failure state heading: `[Save did not complete]`
- Explode-char section labels: `Definition`, `Simplified | Traditional`, `Meaning Map`, `Analysis`, `Synthesis`, `Containing Characters`, `Phrase Use`, `Homophones`

Rules:

- Keep tags compact and factual.
- Keep primary actions short and imperative.
- Use `Your response?` for line-level reflection and book-end reflection, not as a chapter-transition gate.
- Keep the exact action labels unchanged even when a flow cue prefix is added ahead of them.
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

0. Flow cue + learner prompt
1. Simplified Chinese line
2. English line
3. Char-by-char support table
3.1 Index: character position in the line, numbered from 1 to k where k is the number of characters in the line
3.2 Chinese: simplified chinese character (traditional chinese character, if they differ)
3.3 Pronunciation: pinyin (with zhuyin in parens after)
3.4 English character translation: <semi-colon separated list of context-free definitions of the character in 3.2 for that row>
3.5 Chinese phrase: simplified chinese characters grouped by semantic unit, or empty space to pad for extra character rows
3.6 English phrase translation: english translation grouped by semantic unit, or empty space to pad for extra character rows
4. English line
5. Simplified Chinese line
6. Line location/identity (e.g. line i of chapter k of book n)
7. Flow cue + learner prompt

Rules:
- The Chinese line is the visual anchor.
- The char-by-char does most of the structural work.
- The first table column is `Index`, and every character row in the line shell, including punctuation rows, gets a stable number so the learner can refer to any visible position directly.
- The flow cue should say engage with the text as a philosopher and researcher and linguist, hilighting an interesting lead or two
- The current line shell is also the extraction surface for character-index flashcards: simplified, traditional, pinyin, zhuyin, and semicolon-separated English definitions should be recoverable from it for each saved character row.

### Explode-Char Turn

Hierarchy:

0. One brief bridge line if the learner arrived here from guided reading
1. `Definition`
2. `Simplified | Traditional`
3. `Analysis`
4. `Synthesis`
5. `Meaning Map`
6. Short return cue when the learner should resume the reading flow

Rules:
- `Simplified | Traditional` displays the simplified version if the exploded char is traditional and vice-versa; if the traditional and simplified are the same, this section is absent
- `Analysis` uses nested bullets, not tables.
- Start with the full target character as the root node, then descend only as far as the decomposition stays teachable and honest.
- Keep simplified Chinese in the primary position and append traditional only when it differs. If simplified and traditional differ, then run two separate explosions, in the same style as if a phrase were exploded, and you explode each word in sequence.
- Render every reading inline as `pinyin (zhuyin)`.
- Keep `Synthesis` subsection order fixed: `Containing Characters, ie character that contain the exploded-char within its composition`, `Phrase Use, ie multi-character phrases that contain the exploded-char as one char`, `Homophones`.
- Inside `Homophones`, include both `Same Tone` and `Different Tone` subgroups when honest same-syllable examples exist, and do not stop after same-tone matches.
- `Meaning Map` comes after structural analysis and synthesis; keep its subsection order fixed as `Synonyms`, then `Antonyms`
- Do not end the exploder with flashcard candidate recommendations or save prompts.
- Try to divine the etymology, but be disciplined in qualifying the strength of your hunches

### Flashcard-Review Turn

Hierarchy:

1. One visible review face
2. Short prompt to recall the hidden face
3. On the next step, both faces visible
4. Short bridge into the next card

Card faces:

- Hanzi face: simplified Chinese, with traditional in parentheses only when it differs
- Reading face: `pinyin (zhuyin)` followed by the semicolon-separated saved English definitions

Rules:

- The prompt step shows only one face.
- The reveal step shows both faces in a fixed order: Hanzi first, then Reading plus definitions.
- After the reveal step, the next advance should draw a fresh weighted random card instead of lingering on the previous one.
- The review turn should stay compact and non-discursive unless the learner explicitly asks for explanation.

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

- Keep explicit recommendations to one or two characters for exploding and one or two characters or phrases for optional study cards at a time.
- The automatic character-index flashcards are separate infrastructure: they update silently as lines are processed and should accumulate into a full cross-book character index.
- Text appearances still accumulate through citations; explicit learner flags increment a separate `significance_flag_count`.
- Those two signals together determine later review frequency through the weighted review loop.

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

- Default to the six-column char-by-char table when it renders clearly.
- Switch to a stacked per-character list when the host pane is narrow or table readability is poor.
- Do not mix both formats for the same rendered line.
- Preserve stable top-to-bottom order so the thread still works without visual scanning.
- Keep cue phrases consistent across turns.
- Default to compact prompts, but allow more explicit repeated cues when the host surface or learner needs stronger structure.

Stacked fallback:

```text
Index: n
<simplified char> (traditional char, if different)
pinyin (zhuyin)
<char translation>
<Phrase>
<Phrase translation>
```


## Not In Scope

- standalone web app or dashboard chrome
