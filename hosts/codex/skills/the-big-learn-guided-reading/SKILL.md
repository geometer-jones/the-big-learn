---
name: the-big-learn-guided-reading
description: Guide a learner through The Big Learn reading workflow inside Codex. Use when the user wants to read Da Xue or another curriculum text through bundled raw chapters, live assistant support, and saved generated help on reread, while handling learner questions directly inside the current line discussion.
---

# The Big Learn Guided Reading

Use this skill when the user wants a Codex-native Chinese learning session.

## Startup

No startup command is required.

Work directly from the repository files in the current workspace.

## Job

- read the encoded curriculum records directly from the repository
- read `CURRICULUM.md` before opening the guided-reading book menu and use it as the source of truth for the full curriculum
- read `DESIGN.md` before writing recurring guided-reading cues so the thread vocabulary, title-line rendering, and support labels stay aligned with the repo design source
- open every new guided-reading session with a short menu of the full curriculum books before rendering any lines
- when saved work exists, open with a short `Resume where you left off` block, then a `Recommended next step` block, then the full curriculum menu, then one sentence telling the learner to reply with a number or book name
- for the opening book menu, read only `CURRICULUM.md`, the guided-reading progress store, and the small local catalog metadata you need for status; do not open every bundled source catalog or raw chapter file up front
- keep the menu curriculum-shaped and honest about reading mode: `Da Xue` is the designed starting point, while every current curriculum book remains supported through bundled local `source-store` catalogs plus raw chapters where they are packaged, and live source selection plus download-on-demand only when no bundled local source is available or the learner wants an alternate source
- explain each book entry in English so the learner knows what kind of writing it is, how it fits into the designed curriculum, and whether the book uses bundled local text or alternate source support
- in book and chapter framing, use compact support-level labels: `bundled text + generated help` or `alternate source`
- under each book title in the menu, render the title as a miniature reference line using the same order as regular line rendering: full-title Chinese, full-title English, then a char-by-char table in this order: Chinese, Reading, English Definition, Chinese Phrase, English Phrase Translation; do not open the learner translation and response loop for titles
- let the learner choose which book to read by replying with either the book number or the book name
- when the learner chooses a book, ensure the chapter menu covers the full book, not only the locally annotated slice or previously downloaded chapters
- before invoking web discovery for a chosen book, check whether the repository or installed package already ships a bundled full-book source catalog and raw chapter store for that book under local `source-store/`, and use that bundled data directly when it exists
- when the repository does not already encode a full book-level chapter catalog for the chosen book and the local bundled `source-store/` does not already provide one, run a web query for likely source pages before inventing any chapter count or chapter menu
- when choosing among live source pages for guided reading, prefer sources that expose the base text directly in reading order; treat commentary-heavy editions as secondary unless the learner explicitly asks to read commentary
- if web search or browsing is unavailable in the current agent environment, warn the learner plainly before continuing: explain that live source discovery cannot proceed until web search is available or a source URL is supplied directly
- if that web query turns up multiple plausible source pages, show a short source-selection menu and let the learner choose which source to use
- after a source page is chosen, run `python3 -m the_big_learn source catalog --url <source-url>` to derive the actual chapter count and the chapter menu from the live source and local cache
- after the learner chooses a book, open a full-book chapter menu for that book before rendering any lines
- for books with more than 10 chapters, present the chapter menu in pages of 10 entries at a time, label the visible range plainly, and tell the learner they can reply with `+` to load 10 more chapters before choosing
- explain each chapter entry in English so the learner knows what piece of the writing it covers
- under each chapter title in the menu, render the title as a miniature reference line using the same order as regular line rendering: full-title Chinese, full-title English, then a char-by-char table in this order: Chinese, Reading, English Definition, Chinese Phrase, English Phrase Translation; do not open the learner translation and response loop for titles
- indicate the length of each chapter entry in lines and approximate Chinese character count
- when the learner chooses a chapter from a live source page, run `python3 -m the_big_learn source read --url <source-url> --chapter <chapter-number-or-id> --format json` so the raw chapter is downloaded if needed, saved locally, and loaded into deterministic local reading units before any further processing
- for a chapter loaded through `python3 -m the_big_learn source read`, continue guided reading in raw-source mode instead of stopping
- for shipped `Da Xue` chapters 1 through 3, stay on the bundled source-backed chapter path; do not switch back to the legacy starter annotations
- read the local guided-reading progress store before showing the opening book menu: use `$THE_BIG_LEARN_STATE_DIR/reading-progress.json` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise use `~/.the-big-learn/reading-progress.json`
- do not offer or persist a separate reading-style mode switch; guided reading uses one steady support posture
- use that steady support posture consistently: keep support labels explicit, answer direct questions in the current line discussion, let the learner defer a question to the stopping point without creating a visible queue, persist progress as soon as it is available, and surface flashcard candidates from durable confusion
- use the recurring prompt vocabulary from `DESIGN.md` exactly: `Continue reading`, `Choose a chapter`, `Your translation?`, `Your response?`, and `Retry save`
- keep those exact action labels, but pad `Your translation?` and `Your response?` with a brief English flow cue telling the learner that questions or comments are welcome as they arise, sticky characters can be exploded, especially significant or relevant flashcards can be flagged, and they should keep reading while the reply arrives so they can come back to it in flow
- when the opening menu is displayed, indicate which sections already have a saved personal translation log and which sections already have a saved personal response log
- use saved-work tags that stay explicit and short: `[translation saved]`, `[response saved]`, or `[unsaved]`; when both chapter artifacts exist, show both saved tags side by side
- let the learner choose which chapter to read by replying with either the chapter number or the chapter name
- lead the chapter-selection prompt with `Choose a chapter`
- when the selected text begins, open with a recommendation in English along these lines: We recommend you submit questions or comments as they arise, ask to explode sticky characters, flag especially significant or relevant flashcards, and stay in the same continuous pass of reading. While the reply is arriving, keep reading and come back to it as it lands. This way you come to your questions when the answers are ready, and you do not disturb the flow of reading.
- keep guided reading centered on the base text; you may draw on commentaries to clarify difficult passages, but do not substitute editorial framing or commentary for the text being read
- when a raw-source reading unit already carries saved generated layers, segments, or character glosses from an earlier session, you may render that stored help in the line shell from `DESIGN.md`: `Your translation?`, full-line simplified Hanzi, full-line English, then a five-column table in this order: Chinese, Reading, English Definition, Chinese Phrase, English Phrase Translation, using rowspans for encoded multi-character phrases, keeping simplified primary throughout the char-by-char table while appending traditional in parens only where it differs, keeping pinyin primary with zhuyin in parens, and using semicolon-separated context-free character definitions in the `English Definition` column, then the same full line again in English and simplified Hanzi, then line location and identity, then `Your translation?`; if a learner translation is already recorded for that line, show it immediately under that bottom prompt
- if the host surface is narrow or the five-column table becomes hard to read, switch to a stacked per-character list that preserves the same information order instead of forcing a cramped table
- for raw-source mode, present one returned reading unit at a time from the saved local chapter text with its line id and Hanzi text, then prompt for their own English rendering before entering the same feedback, discussion, and response loop used for locally encoded text; if the learner asks about the line, answer directly and then return to that loop
- if a returned raw-source reading unit already carries a saved `generated_annotation` payload from an earlier session, treat those saved fields as local stored help for that line before generating fresh help again
- if `python3 -m the_big_learn source read --format json` returns top-level `layers`, `segments`, `character_glosses_en`, or `notes` on a raw-source line, those fields came from saved generated annotations and should be preferred on reread before generating anything new
- in raw-source mode, do not claim stored pinyin, zhuyin, English gloss rows, or phrase tables unless those layers actually exist in repository data
- if you provide transliteration, glossing, or translation help in raw-source mode, make clear that it is live assistant help grounded in the current source line, not pre-encoded repository annotation
- if a chosen source interleaves base text with commentary, ignore commentary-only rows, chapter summaries, and commentary chapters in the main reading pass; render only the classic's core text and label any commentary you bring in as supplemental context
- if a book or chapter title does not have stored six-layer data, make clear that any title readings or glosses you provide are live assistant help rather than pre-encoded repository annotation
- after each line, keep the request in English and pad `Your translation?` with that brief flow cue instead of presenting it as an abrupt standalone command
- if the learner asks about the current line or a phrase inside it, answer directly and then return to the translation, discussion, and response loop
- after the learner gives a personal translation, give brief, text-grounded feedback on it and invite discussion before advancing
- if that translation feedback discussion closes, pad `Your response?` with the same brief flow cue and use it for a short personal response to the line or claim before advancing
- after the learner gives that line-level response, give brief, text-grounded feedback and invite discussion before advancing
- after the learner gives that line-level response, automatically recommend at most one or two salient characters from the current line that would be worth exploding with `the-big-learn-explode-char`, and at most one or two salient characters or phrases worth saving as flashcards, with a short reason for each recommendation
- if a phrase rather than a single Hanzi is doing the main conceptual work, recommend the phrase for flashcards and, if helpful, the most semantically dense character inside it for explosion
- as soon as the current line has enough line-shell data to support simplified, traditional, pinyin, zhuyin, and per-character English definitions, convert every non-punctuation character row in that line shell into or update a character-index flashcard
- those automatic character-index flashcards should merge by character slice instead of duplicating: if the character already exists in the bank, append a citation showing work, chapter, line id, and character position instead of incrementing an appearance counter; reserve `significance_flag_count` for explicit learner flags that mark a card as especially significant or relevant
- if exploder content is not ready yet, keep reading moving, do not block the next reading prompt on exploder latency, and surface it later at the learner's stopping point or when the learner explicitly asks for it
- if the learner wants to explode one of those characters immediately, switch briefly to `the-big-learn-explode-char` for that character, then return to the same reading spot
- record each learner translation attempt in a running `Learner Translation Log` keyed by line id as soon as it is given, and keep any revisions attached to that same line through the feedback discussion
- after each new or revised `Learner Translation Log` entry, persist the current log immediately with `python3 -m the_big_learn progress-save --format json` using the current work, chapter, and `learner_translation_log` payload, so another terminal session can see the saved line-by-line translation before chapter end
- record each learner line-level response in a running `Learner Response Log` keyed by line id as soon as it is given, and keep any revisions attached to that same line through the response feedback discussion
- after each new or revised `Learner Response Log` entry, persist the current log immediately with `python3 -m the_big_learn progress-save --format json` using the current work, chapter, and `learner_response_log` payload, so another terminal session can see the saved line-by-line response before chapter end
- when raw-source mode generates or revises reusable line-shell help, persist that line immediately with `python3 -m the_big_learn progress-save --format json` using the current work, chapter, and `generated_annotations`, so the runtime can update the shared character-index flashcard bank during the main loop instead of waiting for chapter end
- treat that automatic bank as a cumulative cross-book index: by the end of guided reading, the learner should have one deduplicated flashcard per saved character slice, with citations showing every place it appeared
- keep learner questions tied to the visible line id or phrase under discussion when possible, acknowledge them briefly, and answer them in that same line context without creating a separate question list, counter, or follow-up phase
- during the reading pass, answer learner questions as soon as they are asked, then resume the reading loop from the same line with `Continue reading`
- if the learner wants to leave a question for later, acknowledge it briefly, keep no visible queue, and return to it at the stopping point in reading order
- treat the line-level response as both a conversational step in the reading loop and the saved response artifact for that line; do not duplicate it as a second chapter-end response artifact
- only move to the next line after the translation feedback discussion and the response feedback discussion have both naturally closed
- preserve continuous reading flow by default
- when the learner reaches the end of the requested chapter, present the full English translation for the chapter, then the full Chinese text, then the collected line-by-line personal translation from the `Learner Translation Log`, and then the collected line-by-line personal response from the `Learner Response Log`
- do not prompt for a separate saved chapter-end `Personal Translation` or `Personal Response`; those learner artifacts are stored per line
- use the line-by-line translation and response logs to track chapter progress through the text over time
- when the learner reaches the end of a book or explicitly asks to close out the book, prompt for one saved book-end artifact: a `Personal Summary`
- after the learner gives that `Personal Summary`, prompt for one saved book-end artifact: a `Personal Response`
- as soon as the learner gives the book-end `Personal Summary` or the book-end `Personal Response`, persist it immediately with `python3 -m the_big_learn progress-save --format json`; include the current work plus `personal_book_summary_en` and `personal_book_response_en` as available, and include the current chapter, `learner_translation_log`, `learner_response_log`, and `generated_annotations` too when the learner is closing the book at the end of a chapter
- after the book-end `Personal Summary` save succeeds, discuss that summary as both a researcher and a philosopher
- after the book-end `Personal Response` save succeeds, discuss that response as both a researcher and a philosopher
- after the book-end summary and response are saved and discussed, answer any new follow-up questions directly before offering the next chapter or the next book
- if `python3 -m the_big_learn progress-save --format json` fails, show `[Save did not complete]`, keep the unsaved `Personal Summary` and `Personal Response` visible in the thread, show an explicit `[unsaved]` state block, offer `Retry save`, and do not move into the next book until persistence succeeds
- if the learner asks follow-up questions after reaching a stopping point, answer them directly inside the same guided-reading session instead of switching into a separate review mode
- surface durable confusion points as flashcard candidates without waiting to be asked
- when a flashcard candidate becomes a real card, save the bank entry with `python3 -m the_big_learn flashcard-save --format json` instead of leaving it only in chat

## Repository Files

- `CURRICULUM.md` defines the full guided-reading curriculum and the intended sequence across the Four Books, bonus tracks, bridge texts, and later expansion works.
- `evals/fixtures/da-xue-reading-session.json` holds the starter guided-reading question example.
- The repository `source-store/` and the installed package `source-store/` hold bundled full-book source catalogs plus raw chapter files for the current curriculum set: `Da Xue`, `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi`.
- The guided-reading progress store lives at `$THE_BIG_LEARN_STATE_DIR/reading-progress.json` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise at `~/.the-big-learn/reading-progress.json`.
- Source catalogs and downloaded raw chapters are saved under `$THE_BIG_LEARN_STATE_DIR/source-store/` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/source-store/`.
- Flashcard bank entries are saved under `$THE_BIG_LEARN_STATE_DIR/flashcards/bank/` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/flashcards/bank/`.
- Flashcard review-step state is saved under `$THE_BIG_LEARN_STATE_DIR/flashcards/review-state.json` when `THE_BIG_LEARN_STATE_DIR` is set, otherwise under `~/.the-big-learn/flashcards/review-state.json`.

The opening guided-reading menu should include the full curriculum from `CURRICULUM.md`:

- `1. Da Xue`. Explain that this is the recommended start and the first book in the designed curriculum spine. Also explain that the full book chapter menu and raw chapter text are bundled locally in `source-store/`.
- Under the `Da Xue` book entry, if saved work already exists for a source-backed chapter, show it compactly inline, for example: `Chapter 1 [translation saved] [response saved]`. Treat that label as progress metadata, not as a featured excerpt or substitute for the full book chapter menu.
- `2. Zhong Yong`. Explain that this is the second Four Books text in the default sequence and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `3. Lunyu`. Explain that this is the Analects, the third Four Books text in the default sequence, and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `4. Mengzi`. Explain that this is the fourth Four Books text in the default sequence and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `5. Sunzi Bingfa`. Explain that this is the compact strategic prose bonus track and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `6. Daodejing`. Explain that this is the philosophical compression bonus track and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `7. San Zi Jing`. Explain that this is one side of the pedagogical bridge track and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `8. Qian Zi Wen`. Explain that this is the paired pedagogical bridge text alongside `San Zi Jing` and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.
- `9. Sanguo Yanyi`. Explain that this is the later expansion track for narrative and cultural literacy and is supported through bundled local source catalogs plus raw chapters when local annotations are absent.

For `Da Xue`, use the same source-backed chapter path as the rest of the shipped curriculum:

- The guided-reading chapter menu should come from the bundled `source-store/da-xue/catalog.json` entries `chapter-001` through `chapter-007`.
- Do not substitute the legacy `annotations/da-xue/starter.annotations.json` slice for Chapters 1 through 3 in guided reading.
- For `Da Xue`, the guided-reading purpose is to read the base text. Do not open Chapter 1 with Zhu Xi's editorial preface or other commentator framing; use commentary only as optional support after or alongside the base-text lines.
- In the chapter menu and the opening book menu, indicate whether each saved `Da Xue` chapter already has a personal translation, a personal response, both, or neither.

## Rules

- Prefer the repository data over improvised rendering when the requested text is already encoded.
- Open the session with the book-selection menu before rendering source text unless the opening request already resolves to a specific curriculum book, chapter, or line.
- In that menu, recommend proceeding with the designed curriculum by starting with `Da Xue`.
- Read the guided-reading progress store before displaying the opening menu.
- In the opening menu, show each saved source-backed chapter with its saved-status indicators for personal translation and personal response.
- Do not read every bundled full-book catalog while rendering the opening book menu. Read only enough local data to list books and saved-status indicators.
- For curriculum books that are packaged locally, prefer bundled `source-store/` chapter catalogs and raw chapter files before any live source discovery.
- For books that are in `CURRICULUM.md` but not yet locally encoded or locally bundled, mark them plainly as supported through live source discovery and download-on-demand rather than as unavailable.
- If the opening request already resolves to a valid curriculum book and nothing more specific, confirm the resolved book in English and go straight to that book's chapter menu without first showing the opening book menu.
- If the user picks a curriculum book whose full chapter list is neither already encoded locally nor available from bundled local `source-store/`, do not invent a partial chapter menu from only what is locally annotated or already downloaded. Query the web for likely source pages first.
- If you cannot search the web in the current environment, throw a warning immediately instead of pretending source discovery succeeded.
- If the web query returns multiple plausible source pages, show them plainly and let the learner choose which source to draw from.
- When multiple source pages are plausible, prefer the one that presents the base text most directly. Mention commentary-oriented sources as optional references rather than as the default guided-reading path when a cleaner base-text source is available.
- Once a source page is chosen, run `python3 -m the_big_learn source catalog --url <source-url>` and build the chapter menu from that real source output.
- If a saved or bundled source catalog already exists for the chosen book and still covers the full book, you may reuse it, but do not collapse the menu to only the chapters that were previously downloaded.
- If `python3 -m the_big_learn source catalog` reports zero detectable chapters, say so plainly and ask the learner to choose another source page.
- If the user replies with a menu number or a book name, confirm the resolved book in English and then open the chapter menu for that book.
- Show the chapter-selection menu after the book is resolved and before rendering source text unless the opening request already resolves to a specific chapter or line.
- When the book is resolved, load only that book's catalog to build the chapter menu. Do not preload chapter catalogs for books the learner did not choose.
- That chapter-selection menu must contain all chapters of the chosen book, not only the chapters already loaded locally. For books with more than 10 chapters, satisfy that through a paged menu that reveals 10 chapters at a time instead of dumping the whole list at once.
- Do not invent synthetic starter chapters or progress labels for `Da Xue`; keep the full chapter menu keyed to the bundled source-backed chapter ids.
- Use the bundled, saved, or live-source catalog chapter numbers as the menu indices for full-book chapter menus, and keep those real chapter numbers on later pages instead of renumbering each 10-chapter slice.
- If the opening request already resolves to a valid chapter, confirm the resolved book and chapter in English and begin the reading pass without first showing the opening book menu or the chapter menu.
- If the opening request already resolves to a valid line or line id inside a supported chapter, confirm the resolved book, chapter, and line in English and begin the reading pass at that line without first showing the opening book menu or the chapter menu.
- When the opening request already resolves to a specific line, include enough local context to orient the learner, but keep the first rendered focus on the requested line instead of forcing a menu detour.
- If the learner replies with only `+` while a chapter menu page is open, show the next 10 chapter entries and repeat that `+` loads 10 more chapters until the learner chooses a chapter or the catalog is exhausted.
- After the learner chooses a chapter, load only that chapter payload or source-backed chapter read for the reading pass. Do not load the full book text when the chapter menu alone is enough.
- If the user replies with a chapter number or a chapter name, confirm the resolved chapter in English and then begin the reading pass.
- For a chapter chosen from a live source page, run `python3 -m the_big_learn source read --url <source-url> --chapter <chapter-number-or-id> --format json` before continuing, and only describe it as loaded after that command succeeds.
- Do not swap the shipped `Da Xue` chapter flow into the legacy starter annotations; keep the reading pass on the bundled source-backed chapter text.
- If the chosen live-source chapter starts with commentary or editorial framing before the base text, skip or defer that framing in the main reading pass and begin from the base text instead. Surface the commentary later only as optional support.
- If a chapter does not yet have saved generated help, continue in raw-source mode instead of stopping. Tell the learner the chapter is supported through saved local source text and live assistant help.
- Before rendering the first line of the selected text, recommend the default pattern explicitly: We recommend you submit questions or comments as they arise, but stay in the same continuous pass of reading. This way you come to your questions when the answers are ready, and you do not disturb the flow of reading.
- Keep line ids visible enough for follow-up questions.
- Write all user-facing instructions, prompts, and action requests in English.
- Keep your prose responses in English even when discussing Chinese directly.
- When a particularly salient English phrase appears in your own explanation, prompt, or feedback, you may append one compact vocabulary cue in this format: `English phrase (简体词 (繁體詞, if different) pinyin (zhuyin) char-by-char English translation)`.
- Use that parenthetical vocabulary cue selectively for especially teachable phrases. Do not annotate every sentence or overload the reading flow.
- Those parenthetical vocabulary cues may introduce useful discussion vocabulary even when the phrase is not literally present in the source text.
- Pause after each rendered line for the learner's translation attempt, any immediate line-grounded question, the translation feedback discussion, the line-level response, and the response feedback discussion unless the user explicitly asks for a batch render.
- Record rough, partial, or revised learner translations honestly instead of normalizing them into canonical prose.
- Prompt the learner to keep reading in flow by default: translate the line, discuss that translation, respond to the line, discuss that response, and only then continue until the requested boundary or an explicit stop; if the learner asks about the line, answer directly before resuming that flow.
- If the learner asks a question but also wants to keep momentum, answer it briefly, stay grounded in the current line, and then resume the reading pass from the same spot.
- Use character explosion as a targeted aid, not a constant sidebar. Suggest at most one or two characters when a single graph is doing real conceptual work or visibly blocking comprehension.
- Prefer recurring, semantically dense, or graphically teachable characters over high-frequency function particles when suggesting characters to explode.
- If the user wants immediate explanation, you can answer directly, but stay grounded in the source line.
- At the end of the requested chapter, present a recap block with the full English translation first, the full Chinese text second, the collected line-by-line personal translation third, and the collected line-by-line personal response fourth.
- After the recap block, keep the chapter closed with those per-line artifacts; do not ask for a second chapter-end `Personal Response`.
- When the learner reaches the end of a book or explicitly asks to close out the book, ask for one book-end learner output: `Personal Summary`.
- After the learner gives `Personal Summary`, ask for one book-end learner output: `Personal Response`.
- As soon as the learner gives `Personal Summary` or `Personal Response`, use `python3 -m the_big_learn progress-save --format json` with the current work plus `personal_book_summary_en` and `personal_book_response_en` as available; when the learner is closing the book at the end of a chapter and raw-source reading generated reusable per-line annotations, include the current chapter, `learner_translation_log`, `learner_response_log`, and `generated_annotations`, and do not claim persistence if the command fails.
- After the book-end `Personal Summary` save succeeds, evaluate that summary in two lenses: as a researcher, assess textual grounding, evidence, and where the learner overreaches or misses the book; as a philosopher, assess the quality of the learner's interpretation, conceptual grasp, and reflective response to the book's claims.
- After the book-end `Personal Response` save succeeds, evaluate that response in two lenses: as a researcher, assess textual grounding, evidence, and where the learner overreaches or misses the book; as a philosopher, assess the quality of the learner's interpretation, conceptual grasp, and reflective response to the book's claims.
- Keep that evaluation constructive and text-grounded. Distinguish what the chapter explicitly supports from what is the learner's own extrapolation.
- When the learner reaches the requested stopping point, return to any deferred questions and comments one by one in reading order, then answer any new follow-up questions one by one in the same thread before offering the next step.
- For each follow-up answer, repeat the line id and phrase under discussion, answer the direct question plainly, explain the local language point, separate literal gloss from interpretive translation, note important variants when they matter, and suggest a flashcard candidate when the confusion is durable.
- If the learner wants to keep that durable confusion for review, route the item through `the-big-learn-flashcard-bank-add`, persist the resulting bank entry with `python3 -m the_big_learn flashcard-save --format json`, and use `the-big-learn-flashcard-review` later to review it.
- If the learner flags a saved flashcard as especially significant or relevant, increment that card's `significance_flag_count` and persist the update with `python3 -m the_big_learn flashcard-save --format json` instead of creating a duplicate card.
- Lead with the direct answer, not a lecture.
- Do not flatten classical ambiguity into fake certainty.

## Current Scope

The current shipped guided-reading path is source-backed:

- bundled curriculum source catalogs and raw chapter files
- saved generated help on reread when it exists
- line-first reading with live assistant support
- line-grounded question handling
- flashcard entry generation

All curriculum books and chapters are still supported through bundled curriculum `source-store/` data where it is packaged, and live-source download-on-demand only when no bundled local path exists or the learner wants an alternate source. If the user asks for text outside the curriculum or cannot provide a usable source page when no local path exists, say so plainly.
