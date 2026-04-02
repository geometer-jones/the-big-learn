# Product

This file captures the current product thesis for The Big Learn.

It is intentionally opinionated. The project does not need a vague mission statement right now. It needs a sharp wedge.

## Who This Is For

The first user is not "everyone learning Chinese."

The first user is:

- a software vibe-coder
- already working inside coding assistants
- waiting for threads, tests, deploys, or reviews to come back
- wants a meaningful Chinese-learning loop during that waiting time

This matters because the product should fit the rhythm of that person's day.

Short bursts. High context. Low setup cost. Strong continuity between sessions.

## Position In The Stack

The right comparison is not a generic tutoring chatbot.

The right comparison is `gstack`, but for Chinese learning.

That means:

- explicit skills instead of one mushy tutor prompt
- explicit workflows instead of one-off chat sessions
- reusable content primitives
- host-native packaging for coding assistants
- open source behavior that people can inspect and modify

## Teaching Thesis

Many Chinese apps begin from the leaves:

- restaurant words
- airport words
- shopping words
- phrases tied to immediate situations

That can help with survival tasks, but it often does not give the learner a framework.

The Big Learn starts closer to the root.

The initial curriculum wedge is the Four Books:

1. `Da Xue`
2. `Zhong Yong`
3. `Lunyu`
4. `Mengzi`

We start with `Da Xue`.

The bet is simple: foundational texts plus strong agent workflows can teach structure, pattern recognition, and conceptual grounding better than disconnected phrase packs.

The broader initial canon is defined in [CURRICULUM.md](./CURRICULUM.md):

- Four Books
- `Sunzi Bingfa`
- `Daodejing`
- `San Zi Jing` / `Qian Zi Wen`
- `Sanguo Yanyi`

The guided-reading menu should show that full curriculum, not just the locally annotated subset. When a learner chooses a curriculum book that is not yet fully encoded, the product should search for likely source pages, let the learner choose a source when there are multiple plausible candidates, derive the real chapter count from that source, and save the selected raw chapter locally.

## Core Learning Primitive

Each line is stored in six layers:

1. Simplified Chinese
2. Traditional Chinese
3. Pinyin
4. Zhuyin
5. English character-by-character translation
6. English holistic translation

Learner-facing reading views collapse those into four display units:

1. Hanzi, with simplified primary and traditional in parens when it differs
2. Reading, with pinyin primary and zhuyin in parens
3. English character-by-character translation
4. English holistic translation

The six-layer line record is the atomic storage unit of the system, and the combined Hanzi and Reading views are the atomic learner-facing units.

Everything should build on top of it:

- reading views
- explanations
- question answering
- flashcards
- review drills

## Reading Philosophy

Reading should feel continuous.

The learner is encouraged to:

1. read from start to finish
2. submit questions one by one as they arise
3. get the answer immediately in the current line discussion
4. return to the line and keep going with discipline

The point is to avoid constant context-switching.

Questions are still welcomed. Curiosity is preserved. But the reading flow depends on the learner returning to the text after each answer instead of turning the session into an endless aside.

## Flashcard Thesis

When a learner asks about a word, phrase, or character, that is strong evidence of relevance.

Those items should be eligible for automatic insertion into the flashcard bank.

The bank should support mappings between the learner-facing units derived from the six stored layers.

Examples:

- Hanzi -> Reading
- Reading -> Hanzi
- Hanzi -> English gloss
- English gloss -> Hanzi
- holistic translation -> original phrase
- Hanzi -> holistic translation

The project should not assume one fixed flashcard direction. Different recall paths train different kinds of competence.

## First Skills To Build

The first skill set should stay narrow:

- source-text reader
- guided-reading launcher with built-in line-grounded question handling
- flashcard bank inserter
- flashcard review

That is enough to prove the loop.

## Product Constraints

- Start text-first.
- Do not build a standalone app first.
- Do not spread into every Chinese-learning use case.
- Do not chase gamification before the learning loop works.
- Do not lose the root-first thesis.

## What Success Looks Like

A user can sit in a coding-assistant environment, open the guided-reading menu, see the full curriculum, and choose any curriculum book without getting a fake or partial chapter menu. The system should fetch or reuse a real full-book source catalog, show all chapters of the book, and keep the reading pass on source-backed chapter text rather than synthetic starter excerpts. If the host cannot search the web for that source-backed path, it should warn plainly instead of bluffing. Once a chapter is chosen, the system should download it, save it locally, load it into reading units, and continue guided reading rather than treating it as unsupported. The learner should still be able to ask line-grounded questions without breaking flow, get direct answers in the same discussion, and automatically accumulate useful flashcards from what actually confused them.

That is the first believable version.
