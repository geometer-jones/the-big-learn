---
name: the-big-learn-explode-char
description: Break one or more Chinese characters into nested component trees, then show short phrases, larger characters that use them, homophones across tones, and a synonym-antonym meaning map for each chosen sense. Use when the learner asks to "explode" a Hanzi, inspect its parts, and see pinyin with zhuyin in parentheses plus English meaning for each component and synthesis example.
---

# Explode Char

Use this skill when the learner gives one or more Chinese characters and wants both structural analysis and practical synthesis through phrases, larger containing characters, homophones, and a compact meaning map for each chosen sense. Treat explode-char as a sidecar support surface: answer the requested character immediately without reopening the full guided-reading frame.

## Startup

No startup command is required.

Stay inside the host thread and work directly from the repository context already loaded in the workspace.

## Job

- accept one or more Chinese characters and handle them one at a time in the order given
- show the simplified form in the primary position and append the traditional form in parentheses only when it differs
- make `## Definition` the first visible section of the explosion so the learner gets the chosen reading and sense before the structural breakdown
- follow `## Definition` immediately with `## Etymology` so the learner gets the historical note before any script comparison or structural teaching breakdown
- keep that simplified-primary display rule throughout `## Analysis`, including component nodes, and do not add redundant traditional parentheses when the scripts match
- if the request came from guided reading, use one brief bridge line to signal that this is a quick sidecar answer and keep the learner's reading place intact
- when the simplified and traditional forms differ, show a short `## Simplified | Traditional` block before `## Analysis` so both forms are visible without duplicating the whole turn
- break components into smaller components only when the split is plausible and useful
- give each node its Chinese form, a reading rendered as `pinyin (zhuyin)` when available, and a short English meaning or function
- separate visual teaching decomposition from historical etymology when those differ
- follow the analysis with synthesis examples that use the full target character in phrases, show larger characters that contain the target form inside them, list common homophones for the chosen reading across both same-tone and different-tone matches, and map the chosen meaning through nearby and opposite Chinese expressions
- whenever you show a reading anywhere in the answer, keep it inline as `pinyin (zhuyin)` rather than splitting pinyin and zhuyin into separate lines
- do not end the exploder with flashcard save suggestions or candidate lists
- if the learner came from guided reading, end with a short return cue that makes it easy to resume the same reading spot

## Inputs

- one or more target Chinese characters
- optional preferred reading or meaning if the character is polyphonic
- optional phrase count, otherwise default to 5 short phrases
- optional homophone count, otherwise default to 5 items
- optional synonym or antonym count, otherwise default to 5 items per cluster

If the invocation does not include a target character, look back through the recent conversation for Chinese characters the learner mentioned most recently.
Propose a short candidate list and ask the learner to confirm which character to explode, or to type a different character if none of the suggestions are right.
Do not silently choose a target character when the user has not confirmed it.
If the user gives multiple characters, explode all of them in sequence instead of asking them to narrow to a single target.
Preserve the original character order.
Do not collapse multiple adjacent characters into a word-level analysis unless the learner explicitly asks for that.

## Output Shape

For a single target character, keep the turn compact and use visible blocks in this order:

1. one brief bridge line when the learner arrived from guided reading
2. `## Definition`
3. `## Etymology`
4. `## Simplified | Traditional` only when the scripts differ
5. `## Analysis`
6. `## Synthesis`
7. `## Meaning Map`
8. a short return cue when the learner should resume guided reading

For multiple target characters, repeat the same order for each character before moving to the next one. Use:

1. one brief bridge line only when it helps preserve guided-reading continuity
2. `## Definition: <character>`
3. `## Etymology: <character>`
4. `## Simplified | Traditional: <character>` only when the scripts differ
5. `## Analysis: <character>`
6. `## Synthesis: <character>`
7. `## Meaning Map: <character>`

Do not add extra top-level headings beyond `## Definition`, `## Etymology`, the optional `## Simplified | Traditional` block, `## Analysis`, `## Synthesis`, and `## Meaning Map`.

Do not use tables for the main answer. Use nested bullet lists so the structure reads like a tree.

### Definition

Lead with a compact definition block before any etymology note, script note, or decomposition so the learner sees the selected reading and meaning first.

Include:

- the target character in simplified Chinese, with traditional in parentheses only when it differs
- the chosen reading as `pinyin (zhuyin)`
- a short learner-facing English definition for the intended sense
- one short note only when the character is polyphonic, sense-specific, or not normally used standalone

Preferred pattern:

- `语` (`語`): `yu3 (ㄩˇ)` - language; speech

### Etymology

Place this section immediately after `## Definition`.

Keep it concise and historical:

- explain the most useful historical origin or character-formation note for the chosen sense
- distinguish that historical note from the learner-facing decomposition you will use later in `## Analysis`
- if the history is uncertain, disputed, or only partially recoverable, say that plainly instead of overstating it

Preferred pattern:

- Historically, `語` is treated as a speech-related character built with `言` plus `吾`, where `吾` mainly helps cue the older sound; the modern teaching breakdown is still useful, but it is not the whole historical story.

### Analysis

Start with the full target character as the root node in simplified-primary display. Expand the components in the script form that best explains the structure, and briefly note when the traditional form makes the decomposition clearer.

Each bullet should include:

- simplified Chinese form in the primary position
- traditional Chinese form in parentheses only when it differs from the simplified form
- a reading rendered as `pinyin (zhuyin)`, or `non-standalone` / `unknown` when that is more honest
- short English meaning, role, or function

Preferred pattern:

- `简体` (`傳統`): `pinyin (zhuyin)` - short English meaning
  - `component`: `pinyin (zhuyin)` - meaning or function
    - `subcomponent`: `pinyin (zhuyin)` - meaning or function

When useful, add a brief note such as:

- `semantic hint`
- `phonetic hint`
- `graphical part only`
- `historical form differs`

Stop descending once the next split would be speculative, historically dubious, or no longer helpful to the learner.

### Simplified | Traditional

Use this block only when the target character's simplified and traditional forms differ.

Keep it short:

- show the simplified form first and the traditional form second
- add one short note only when the alternate script materially changes or clarifies the decomposition
- if the forms are identical, omit this block entirely
- if the learner supplied the traditional form, still keep the simplified form in the primary position inside this block and throughout the rest of the answer
- do not duplicate the full explosion under both script forms unless the learner explicitly asks for a separate script-by-script comparison

### Synthesis

List all of these synthesis outputs:

- short multi-character phrases that use the full target character
- larger characters that contain the target symbol inside them as a visible component or subshape
- a homophone list for the chosen reading of the target character

Include all three synthesis sections when honest examples exist. If one content category is sparse, say so briefly instead of stretching.

For phrase examples, include:

- the full phrase in simplified Chinese, with traditional in parentheses only when it differs
- the phrase reading as `pinyin (zhuyin)`
- the phrase's full English translation
- a nested breakdown of the individual characters in the phrase with their own simplified form, traditional form when it differs, `pinyin (zhuyin)`, and standalone English meanings

Preferred pattern:

- `简体词` (`繁體詞`): `phrase pinyin (zhuyin)` - full phrase translation
  - `char 1 simplified` (`char 1 traditional`): `pinyin (zhuyin)` - standalone meaning
  - `char 2 simplified` (`char 2 traditional`): `pinyin (zhuyin)` - standalone meaning
  - `char 3 simplified` (`char 3 traditional`): `pinyin (zhuyin)` - standalone meaning

For containing-character examples, include:

- the larger character in simplified Chinese, with traditional in parentheses only when it differs
- the larger character reading as `pinyin (zhuyin)`
- the larger character's English meaning
- a short note saying how the target appears inside it and whether the link is semantic, phonetic, graphical-only, or uncertain
- a nested breakdown that includes the target symbol and the other major part or parts

Preferred pattern:

- `简体大字` (`繁體大字`): `pinyin (zhuyin)` - meaning; contains target as a component or visible subshape
  - `target`: `pinyin (zhuyin)` - role inside the larger character
  - `other part`: `pinyin (zhuyin)` - meaning or function

Prefer short, common, teachable phrases and common containing characters over obscure compounds or graph variants.

For the synthesis portion, use these subsection headers inside `## Synthesis` in this order:

1. `### Containing Characters`
2. `### Phrase Use`
3. `### Homophones`

For the homophone portion, list common characters or short words that share the same syllable as the target under the chosen reading, including both same-tone and different-tone matches when honest examples exist. Do not stop after same-tone matches when honest different-tone homophones are available.

Use these subsection headers inside `### Homophones` in this order:

1. `#### Same Tone`
2. `#### Different Tone`

For each homophone item, include:

- the homophone in simplified Chinese, with traditional in parentheses only when it differs
- the homophone reading as `pinyin (zhuyin)`
- a short English meaning
- a brief note on whether the pronunciation match is exact for initial, final, and tone
- if the tone differs, name the target tone and the homophone tone plainly

Preferred pattern:

- `简体同音字` (`繁體同音字`): `pinyin (zhuyin)` - short meaning; exact homophone

For different-tone items, prefer this pattern:

- `简体变调同音字` (`繁體變調同音字`): `pinyin (zhuyin)` - short meaning; same syllable, different tone from target

Prefer exact same-syllable matches first. Then include different-tone homophones for the same syllable before falling back to looser sound-alikes. If you include near-homophones because common same-syllable items are sparse, label them clearly as near-homophones instead of mixing them in silently.

### Meaning Map

Place the meaning map after structural analysis and synthesis so the learner gets the semantic neighborhood once the decomposition and examples are already on the page.

Use exactly these subsection headers inside `## Meaning Map` in this order:

1. `#### Synonyms`
2. `#### Antonyms`

Render each synonym item as a single bullet line, similar to the homophone list, with zhuyin kept inline in parentheses after the pinyin.

For each synonym item, include:

- the synonym in simplified Chinese, with traditional in parentheses only when it differs
- the synonym reading as `pinyin (zhuyin)`
- the English word-by-word gloss
- the English holistic translation

Render each antonym item as a single bullet line in the same compact reading format:

- Simplified Chinese
- Traditional Chinese, in parentheses only when it differs
- Pinyin with zhuyin in parentheses
- English word-by-word gloss
- English holistic translation

Preferred patterns:

- `传统` (`傳統`): `chuan2 tong3 (ㄔㄨㄢˊ ㄊㄨㄥˇ)` - `transmit; pass down + rule; system`; tradition

If the target character is not normally used as a standalone word for the intended sense, use short Chinese words or phrases that stay tightly anchored to that sense instead of forcing isolated single-character items.

## Rules

- Be explicit about uncertainty. If a decomposition is only a teaching convenience, say so.
- Do not invent deep etymology or oracle-bone history from shape alone.
- If a component is not normally used as an independent character, label it clearly instead of forcing a fake gloss.
- If the target character has multiple readings, lead with the reading that matches the chosen meaning and note the others briefly if they matter.
- Keep English meanings short and learner-friendly.
- Keep phrase translations idiomatic, but keep single-character glosses literal enough to show composition.
- When decomposition depends on the written form, reason from the script that best explains the structure, but keep the displayed output simplified-first.
- If simplified and traditional forms differ in a way that affects decomposition, mention that briefly.
- If no target character is provided, mine only the recent thread context for plausible Hanzi candidates, then stop and get confirmation before doing the full explosion.
- In `## Definition`, state the chosen reading and sense plainly before the decomposition starts.
- In `## Etymology`, keep the historical note brief and place it immediately after `## Definition`.
- In `## Analysis`, keep simplified primary at every node and append traditional in parentheses only when it differs.
- In `## Synthesis`, include phrase-use examples, larger containing-character examples, and a homophone list.
- In `## Meaning Map`, put `#### Synonyms` and `#### Antonyms` after `## Analysis` and `## Synthesis`.
- Keep every displayed reading inline as `pinyin (zhuyin)` instead of splitting pinyin and zhuyin into separate lines.
- If multiple target characters are provided, finish the full analysis-and-synthesis block for one character before moving to the next.
- Preserve the input order for multi-character requests unless the learner explicitly asks for a different order.
- Do not treat every visual resemblance as a real component relation. Mark graphical-only or uncertain containment honestly.
- Build the homophone list for the same chosen reading used elsewhere in the answer.
- Prefer exact same-syllable matches first, then different-tone homophones, then loose sound-alikes only if needed.
- Keep different-tone homophones in their own subgroup instead of mixing them into the same-tone list.
- Include a `#### Different Tone` subgroup whenever honest same-syllable different-tone homophones are available.
- Do not print separate pinyin or Zhuyin lines in the synthesis subsections.
- Do not use nested bullets under `#### Synonyms`.
- Keep synonym items close in part of speech, register, and semantic scope when possible.
- Use genuine antonyms when possible; when Chinese uses a contrast pair rather than a perfect opposite, pick the most standard contrast and say so briefly.
- If the target character has multiple meanings, build the meaning map for one sense only and keep that sense aligned with the reading used in `## Analysis`.
- Do not end the exploder with flashcard candidate recommendations or save prompts.

## Example Skeleton

```markdown
## Definition

- `语` (`語`): `yu3 (ㄩˇ)` - language; speech

## Etymology

- Historically, `語` is a speech-related character built with `言` plus `吾`, with `吾` mainly helping cue the older sound.
- The learner-facing decomposition below is still useful, but it is a teaching breakdown rather than a full etymology.

## Simplified | Traditional

- `语` | `語` - the traditional form preserves the fuller `言` component, which makes the historical structure easier to see.

## Analysis

- `语` (`語`): `yu3 (ㄩˇ)` - language; speech
  - `言`: `yan2 (ㄧㄢˊ)` - speech; words
  - `吾`: `wu2 (ㄨˊ)` - I; my
    - `五`: `wu3 (ㄨˇ)` - five
    - `口`: `kou3 (ㄎㄡˇ)` - mouth

## Synthesis

### Containing Characters

- `悟`: `wu4 (ㄨˋ)` - realize; understand; contains `吾` as a visible component
  - `吾`: `wu2 (ㄨˊ)` - I; my
  - `忄`: `non-standalone` - heart semantic hint

### Phrase Use

- `语言` (`語言`): `yu3 yan2 (ㄩˇ ㄧㄢˊ)` - language
  - `语` (`語`): `yu3 (ㄩˇ)` - speech; language
  - `言`: `yan2 (ㄧㄢˊ)` - speech; words
- `汉语` (`漢語`): `han4 yu3 (ㄏㄢˋ ㄩˇ)` - Chinese language
  - `汉` (`漢`): `han4 (ㄏㄢˋ)` - Han; Chinese
  - `语` (`語`): `yu3 (ㄩˇ)` - speech; language

### Homophones

#### Same Tone

- `雨`: `yu3 (ㄩˇ)` - rain; exact homophone
- `与` (`與`): `yu3 (ㄩˇ)` - with; and; exact homophone

#### Different Tone

- `鱼` (`魚`): `yu2 (ㄩˊ)` - fish; same syllable, different tone from target
- `玉`: `yu4 (ㄩˋ)` - jade; same syllable, different tone from target

## Meaning Map

#### Synonyms

- `话语` (`話語`): `hua4 yu3 (ㄏㄨㄚˋ ㄩˇ)` - `speech + language`; speech; utterance

#### Antonyms

- `沉默`: `chen2 mo4 (ㄔㄣˊ ㄇㄛˋ)` - `sink; deep + silent`; silent; silence

## Handoff

If the learner arrived from guided reading, end with a short return cue such as: `When you're ready, go back to the same line and keep reading from there.`
