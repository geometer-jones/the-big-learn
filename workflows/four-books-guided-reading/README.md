# Four Books Guided Reading

This workflow is the first implementation target for The Big Learn.

It is optimized for a learner reading in short idle intervals inside a coding-assistant environment.

Current repo note: the source-controlled workflow and host prompts describe the full intended loop, but the local Python fixture runner and saved progress store currently exercise the `Da Xue` starter slice first. Broader live reading across the full curriculum already depends on bundled source catalogs and host-side guided-reading behavior.

## Objective

Render a passage from the Four Books in the line-first format built from the six stored layers when local annotations exist, but still derive a full-book chapter menu from a live source whenever the repository does not already encode the entire book. Stop after each line to ask for the learner's own-English translation, answer any question about that line directly in the same discussion, give feedback on that translation and let a short discussion happen, then ask for a brief response to the line or claim, give feedback on that response, and only then move on. End the chapter with a whole-chapter English-first recap, a learner response prompt, and a researcher-philosopher evaluation of that response before creating review artifacts from durable confusion points.

## Primary Source

Start with `Da Xue`.

Future expansions can target the rest of the Four Books without changing the workflow shape.

## Components

- `the-big-learn-guided-reading`
- `the-big-learn-flashcard-bank-add`
- `the-big-learn-flashcard-review`

## Ordered Steps

1. Show the full curriculum menu from `CURRICULUM.md`.
2. If the chosen book already has a complete local chapter catalog, open the chapter menu from the repository annotation records.
3. If the chosen book does not already have a complete local chapter catalog, search the web for likely source pages, let the learner choose among plausible sources when needed, derive the real full-book chapter menu from the selected source, download the selected chapter, save it locally, and load it into raw-source reading units.
4. If web search is unavailable in the current host environment, warn the learner plainly instead of pretending source discovery succeeded.
5. Before the first line, tell the learner to ask questions as they arise, read the immediate answer, and then return to the text without losing their place.
6. Use `the-big-learn-guided-reading` to render the next line directly from the repository annotation records when six-layer annotations exist, or from saved raw-source reading units when they do not. For locally encoded lines, keep the fixed sequence explicit: full-line simplified Hanzi, full-line English, a five-column table with `Chinese`, `Reading`, `English Definition`, `Chinese Phrase`, and `English Phrase Translation`, then the same full line again in English and simplified Hanzi. Within that table, keep simplified primary and append traditional in parens only where the forms diverge, keep pinyin primary with zhuyin in parens, use semicolon-separated context-free character definitions in the `English Definition` column, and let the phrase columns span multiple character rows when a stored segment covers more than one character.
7. Prompt for a personal English translation of the current line in the learner's own voice.
8. If the learner asks about the line or a phrase inside it, answer directly in that same discussion and then return to the reading loop.
9. After each personal translation, give brief, text-grounded feedback and invite discussion before advancing.
10. If that translation discussion closes, ask for a brief personal response to the line or claim, then give brief, text-grounded feedback on that response and invite discussion before advancing.
11. Record the learner translation attempt with the line id, keep any revisions attached to that same line, and move to the next line only after the line-level discussion closes.
12. After each new or revised learner translation record, persist the current log immediately so the saved chapter `Personal Translation` stays current instead of waiting for chapter end.
13. Keep line-level questions grounded in the visible line id or phrase instead of creating a later review phase.
14. At the end of the chapter, present the full English translation, then the full Chinese text, then the collected line-by-line personal translation, and then prompt the learner for a response to the chapter.
15. Treat the collected line-by-line personal translation as the current `Personal Translation`, and do not wait for the chapter-end response to save it.
16. As soon as the learner gives the chapter-end `Personal Response`, persist it immediately before evaluation or continuation.
17. Evaluate the learner's chapter-end response as both a researcher and a philosopher, staying explicit about textual support versus extrapolation.
18. If the learner asks follow-up questions at the stopping point, answer them directly inside the same thread.
19. For durable confusion points, create bank entries with `the-big-learn-flashcard-bank-add`.
20. Review saved cards later with `the-big-learn-flashcard-review`.

## Required Records

- annotation line records from `annotations/`
- source catalogs derived from selected live source URLs
- raw chapter snapshots saved under the source store
- raw-source reading-unit payloads derived from saved source chapters
- learner translation records
- flashcard bank entries

## Stop Conditions

Stop the reading pass when:

- the learner reaches the requested line boundary
- the learner wants to end the session

## Quality Bar

- source text must stay canonical
- line ids must survive every handoff
- learner translation attempts must stay attached to the exact line id
- line-level questions must stay tied to the exact line or phrase
- answers must stay tied to the exact line or phrase
- flashcard entries must preserve all six layers when available
