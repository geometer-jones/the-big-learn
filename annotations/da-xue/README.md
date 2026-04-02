# Da Xue

This directory holds the starter annotation spec and annotation data for `Da Xue`.

This is the repo's annotation store, not the full curriculum store.

`Da Xue` remains the first fully annotated local guided-reading text in the repository. The full current curriculum set now ships with the install as bundled source catalogs and raw chapter files, so `Zhong Yong`, `Lunyu`, `Mengzi`, `Sunzi Bingfa`, `Daodejing`, `San Zi Jing`, `Qian Zi Wen`, and `Sanguo Yanyi` are available locally without a post-install fetch even though their full six-layer annotations have not yet been added in-repo.

The current starter slice is `Opening outline`, 3 lines, about 58 Chinese characters. In the bundled `Da Xue` base-text catalog, those annotated lines map onto Chapters 1 through 3 of the core reading menu. The separate bundled commentary chapters for `Da Xue` are stored in the source-store data and should be treated as optional support, not as the default opening reading path.

## Source Choice

The starter line set currently follows the `四書章句集註/大學章句` textual line as a practical default for the project's first implementation pass.

Source:

- [四書章句集註/大學章句](https://zh.wikisource.org/wiki/%E5%9B%9B%E6%9B%B8%E7%AB%A0%E5%8F%A5%E9%9B%86%E8%A8%BB/%E5%A4%A7%E5%AD%B8%E7%AB%A0%E5%8F%A5)

Why this source:

- it is easy to cite
- it is widely recognized
- it exposes a standard line beginning with `在親民`, while also preserving the note that `親` is often taken as `新`

## Annotation Policy

- Pronunciation profile: modern Mandarin reading
- Status: starter draft, not final editorial canon
- Goal: provide a concrete machine-readable annotation target plus local teaching annotations

This matters because classical texts are not pronunciation-trivial, and some lines have real editorial variance.

## Files

- `starter.annotations.json`: source locators plus local annotations for the initial guided-reading loop
