from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from the_big_learn.codex_host import default_codex_target, install_codex_skills, source_skill_dirs


class CodexHostTests(unittest.TestCase):
    def test_default_codex_target_looks_like_codex_skill_home(self) -> None:
        self.assertTrue(str(default_codex_target()).endswith(".codex/skills"))

    def test_source_skill_dirs_include_launcher_skill(self) -> None:
        names = {path.name for path in source_skill_dirs()}
        self.assertIn("the-big-learn-guided-reading", names)
        self.assertNotIn("deferred-answer", names)
        self.assertNotIn("question-queue", names)
        self.assertIn("explode-char", names)
        self.assertIn("flashcard-review", names)
        self.assertNotIn("map-dimension", names)
        self.assertNotIn("source-text-reader", names)
        self.assertIn("update", names)

    def test_install_codex_skills_copies_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installed = install_codex_skills(target=target)
            installed_names = {path.name for path in installed}

            self.assertIn("the-big-learn-guided-reading", installed_names)
            self.assertIn("the-big-learn-explode-char", installed_names)
            self.assertIn("the-big-learn-flashcard-review", installed_names)
            self.assertNotIn("the-big-learn-map-dimension", installed_names)
            self.assertNotIn("the-big-learn-question-queue", installed_names)
            self.assertNotIn("the-big-learn-source-text-reader", installed_names)
            self.assertIn("the-big-learn-update", installed_names)

            for path in installed:
                self.assertTrue((path / "SKILL.md").exists())

            launcher = target / "the-big-learn-guided-reading" / "SKILL.md"
            launcher_content = launcher.read_text(encoding="utf-8")
            self.assertNotIn("current reading path", launcher_content)
            self.assertIn("CURRICULUM.md", launcher_content)
            self.assertIn("annotations/da-xue/starter.annotations.json", launcher_content)
            self.assertIn("full curriculum books", launcher_content)
            self.assertIn("book number or the book name", launcher_content)
            self.assertIn("under each book title in the menu, render the title as a miniature reference line", launcher_content)
            self.assertIn("1. Da Xue", launcher_content)
            self.assertIn("2. Zhong Yong", launcher_content)
            self.assertIn("3. Lunyu", launcher_content)
            self.assertIn("4. Mengzi", launcher_content)
            self.assertIn("5. Sunzi Bingfa", launcher_content)
            self.assertIn("6. Daodejing", launcher_content)
            self.assertIn("7. San Zi Jing", launcher_content)
            self.assertIn("8. Qian Zi Wen", launcher_content)
            self.assertIn("9. Sanguo Yanyi", launcher_content)
            self.assertIn("designed curriculum", launcher_content)
            self.assertNotIn("Current locally annotated starter slice: `Opening outline`, 3 lines, about 58 Chinese characters", launcher_content)
            self.assertNotIn("locally annotated material for `Da Xue` is a starter slice", launcher_content)
            self.assertIn("if saved work already exists for a source-backed chapter, show it compactly inline", launcher_content)
            self.assertIn("Treat that label as progress metadata, not as a featured excerpt or substitute for the full book chapter menu", launcher_content)
            self.assertIn("chapter number or the chapter name", launcher_content)
            self.assertIn("use the same source-backed chapter path as the rest of the shipped curriculum", launcher_content)
            self.assertIn("chapter-001` through `chapter-007`", launcher_content)
            self.assertIn("reading-progress.json", launcher_content)
            self.assertIn("DESIGN.md", launcher_content)
            self.assertIn("source-store", launcher_content)
            self.assertIn("Do not read every bundled full-book catalog while rendering the opening book menu", launcher_content)
            self.assertIn("load only that book's catalog to build the chapter menu", launcher_content)
            self.assertIn("load only that chapter payload or source-backed chapter read for the reading pass", launcher_content)
            self.assertIn("run a web query for likely source pages", launcher_content)
            self.assertIn("prefer sources that expose the base text directly in reading order", launcher_content)
            self.assertIn("web search or browsing is unavailable", launcher_content)
            self.assertIn("throw a warning immediately", launcher_content)
            self.assertIn("multiple plausible source pages", launcher_content)
            self.assertIn("python3 -m the_big_learn source catalog --url <source-url>", launcher_content)
            self.assertIn("python3 -m the_big_learn source read --url <source-url> --chapter <chapter-number-or-id> --format json", launcher_content)
            self.assertIn("under each chapter title in the menu, render the title as a miniature reference line", launcher_content)
            self.assertIn("actual chapter count", launcher_content)
            self.assertIn("for books with more than 10 chapters, present the chapter menu in pages of 10 entries at a time", launcher_content)
            self.assertIn("reply with `+` to load 10 more chapters", launcher_content)
            self.assertIn("downloaded if needed, saved locally, and loaded into deterministic local reading units", launcher_content)
            self.assertIn("continue guided reading in raw-source mode", launcher_content)
            self.assertIn("for shipped `Da Xue` chapters 1 through 3, stay on the bundled source-backed chapter path", launcher_content)
            self.assertIn("supported through live source discovery and download-on-demand", launcher_content)
            self.assertIn("saved personal translation", launcher_content)
            self.assertIn("saved personal response", launcher_content)
            self.assertIn("Chapter 1 [translation saved] [response saved]", launcher_content)
            self.assertIn("[unsaved]", launcher_content)
            self.assertNotIn("recommended annotated excerpt rather than the full book chapter menu", launcher_content)
            self.assertIn("guided-reading purpose is to read the base text", launcher_content)
            self.assertIn("Do not open Chapter 1 with Zhu Xi's editorial preface", launcher_content)
            self.assertIn("Do not substitute the legacy `annotations/da-xue/starter.annotations.json` slice", launcher_content)
            self.assertIn("submit questions or comments as they arise", launcher_content)
            self.assertIn("stay in the same continuous pass of reading", launcher_content)
            self.assertIn("miniature reference line using the same order as regular line rendering", launcher_content)
            self.assertIn("do not offer or persist a separate reading-style mode switch", launcher_content)
            self.assertIn("let the learner defer a question to the stopping point without creating a visible queue", launcher_content)
            self.assertNotIn("learner_style.global.reading_style", launcher_content)
            self.assertNotIn("learner_style.work.reading_style", launcher_content)
            self.assertIn("guided reading centered on the base text", launcher_content)
            self.assertIn("This way you come to your questions when the answers are ready", launcher_content)
            self.assertIn("you do not disturb the flow of reading", launcher_content)
            self.assertIn("flagged, and they should keep reading while the reply arrives", launcher_content)
            self.assertIn("Continue reading", launcher_content)
            self.assertIn("Choose a chapter", launcher_content)
            self.assertIn("Your translation?", launcher_content)
            self.assertIn("Your response?", launcher_content)
            self.assertIn("keep the request in English", launcher_content)
            self.assertIn("Write all user-facing instructions, prompts, and action requests in English.", launcher_content)
            self.assertIn("Keep your prose responses in English even when discussing Chinese directly.", launcher_content)
            self.assertIn(
                "English phrase (简体词 (繁體詞, if different) pinyin (zhuyin) char-by-char English translation)",
                launcher_content,
            )
            self.assertIn("Those parenthetical vocabulary cues may introduce useful discussion vocabulary", launcher_content)
            self.assertIn("line location and identity", launcher_content)
            self.assertIn("if the learner asks about the current line or a phrase inside it, answer directly and then return to the translation, discussion, and response loop", launcher_content)
            self.assertIn("after the learner gives a personal translation, give brief, text-grounded feedback on it and invite discussion before advancing", launcher_content)
            self.assertIn("if that translation feedback discussion closes, pad `Your response?` with the same brief flow cue", launcher_content)
            self.assertIn("after the learner gives that line-level response, give brief, text-grounded feedback and invite discussion before advancing", launcher_content)
            self.assertIn("persist the current log immediately with `python3 -m the_big_learn progress-save --format json`", launcher_content)
            self.assertIn("another terminal session can see the saved line-by-line translation before chapter end", launcher_content)
            self.assertIn("Learner Response Log", launcher_content)
            self.assertIn("saved line-by-line response before chapter end", launcher_content)
            self.assertIn("automatically recommend at most one or two salient characters from the current line", launcher_content)
            self.assertIn("one or two salient characters or phrases worth saving as flashcards", launcher_content)
            self.assertIn(
                "convert every non-punctuation character row in that line shell into or update a character-index flashcard",
                launcher_content,
            )
            self.assertIn("append a citation showing work, chapter, line id, and character position", launcher_content)
            self.assertIn("`significance_flag_count`", launcher_content)
            self.assertIn("the-big-learn-explode-char", launcher_content)
            self.assertIn("return to the same reading spot", launcher_content)
            self.assertIn("Learner Translation Log", launcher_content)
            self.assertIn("keep learner questions tied to the visible line id or phrase under discussion", launcher_content)
            self.assertIn("separate question list, counter, or follow-up phase", launcher_content)
            self.assertIn("answer learner questions as soon as they are asked", launcher_content)
            self.assertIn("if the learner wants to leave a question for later, acknowledge it briefly, keep no visible queue", launcher_content)
            self.assertIn("do not block the next reading prompt on exploder latency", launcher_content)
            self.assertIn("full English translation for the chapter", launcher_content)
            self.assertIn("collected line-by-line personal translation", launcher_content)
            self.assertIn(
                "Chinese, Reading, English Definition, Chinese Phrase, English Phrase Translation",
                launcher_content,
            )
            self.assertIn("keeping simplified primary throughout the char-by-char table while appending traditional in parens only where it differs", launcher_content)
            self.assertIn("then the same full line again in English and simplified Hanzi", launcher_content)
            self.assertIn("stacked per-character list", launcher_content)
            self.assertIn("if the learner asks about the line, answer directly and then return to that loop", launcher_content)
            self.assertIn("do not claim stored pinyin, zhuyin, English gloss rows, or phrase tables", launcher_content)
            self.assertIn(
                "ignore commentary-only rows, chapter summaries, and commentary chapters in the main reading pass",
                launcher_content,
            )
            self.assertIn("title readings or glosses you provide are live assistant help", launcher_content)
            self.assertIn("collected line-by-line personal response", launcher_content)
            self.assertIn("Personal Summary", launcher_content)
            self.assertIn("Personal Response", launcher_content)
            self.assertIn("do not prompt for a separate saved chapter-end `Personal Translation` or `Personal Response`", launcher_content)
            self.assertIn("as soon as the learner gives the book-end `Personal Summary` or the book-end `Personal Response`", launcher_content)
            self.assertIn("discuss that summary as both a researcher and a philosopher", launcher_content)
            self.assertIn("discuss that response as both a researcher and a philosopher", launcher_content)
            self.assertIn("track chapter progress through the text over time", launcher_content)
            self.assertIn("`personal_book_summary_en` and `personal_book_response_en`", launcher_content)
            self.assertIn("`learner_response_log`", launcher_content)
            self.assertIn("python3 -m the_big_learn progress-save --format json", launcher_content)
            self.assertIn("[Save did not complete]", launcher_content)
            self.assertNotIn("translation + response saved", launcher_content)
            self.assertIn("python3 -m the_big_learn flashcard-save --format json", launcher_content)
            self.assertIn("~/.the-big-learn/flashcards/bank/", launcher_content)
            self.assertIn("~/.the-big-learn/flashcards/review-state.json", launcher_content)
            self.assertIn("increment that card's `significance_flag_count`", launcher_content)
            self.assertIn("as both a researcher and a philosopher", launcher_content)
            self.assertIn("textual grounding, evidence", launcher_content)
            self.assertIn("mark the matched choice plainly", launcher_content)
            self.assertIn("chapter menu for that book", launcher_content)
            self.assertIn("chapter menu covers the full book", launcher_content)
            self.assertIn("full book-level chapter catalog", launcher_content)
            self.assertIn("do not collapse the menu to only the chapters that were previously downloaded", launcher_content)
            self.assertIn("must contain all chapters of the chosen book", launcher_content)
            self.assertIn("keep those real chapter numbers on later pages instead of renumbering each 10-chapter slice", launcher_content)
            self.assertIn("If the learner replies with only `+` while a chapter menu page is open", launcher_content)
            self.assertIn("show each saved source-backed chapter with its saved-status indicators", launcher_content)
            self.assertIn("Do not invent synthetic starter chapters or progress labels for `Da Xue`", launcher_content)
            self.assertIn("Do not swap the shipped `Da Xue` chapter flow into the legacy starter annotations", launcher_content)
            self.assertIn("skip or defer that framing in the main reading pass and begin from the base text instead", launcher_content)
            self.assertIn("If the learner asks a question but also wants to keep momentum, answer it briefly, stay grounded in the current line, and then resume the reading pass from the same spot.", launcher_content)
            self.assertIn("translate the line, discuss that translation, respond to the line, discuss that response", launcher_content)
            self.assertIn("only move to the next line after the translation feedback discussion and the response feedback discussion have both naturally closed", launcher_content)
            self.assertIn("Use character explosion as a targeted aid, not a constant sidebar.", launcher_content)
            self.assertIn("Prefer recurring, semantically dense, or graphically teachable characters", launcher_content)
            self.assertIn("When the learner reaches the requested stopping point, return to any deferred questions and comments one by one in reading order", launcher_content)

            explode_char = target / "the-big-learn-explode-char" / "SKILL.md"
            explode_content = explode_char.read_text(encoding="utf-8")
            self.assertIn(
                "traditional Chinese form in parentheses only when it differs from the simplified form",
                explode_content,
            )
            self.assertIn(
                "keep it inline as `pinyin (zhuyin)` rather than splitting pinyin and zhuyin into separate lines",
                explode_content,
            )
            self.assertNotIn(
                "simplified Chinese form, even when it is identical to the traditional form",
                explode_content,
            )
            self.assertIn(
                "larger characters that contain the target symbol inside them",
                explode_content,
            )
            self.assertIn("If the user gives multiple characters, explode all of them in sequence", explode_content)
            self.assertIn("Preserve the original character order", explode_content)
            self.assertIn("If the invocation does not include a target character", explode_content)
            self.assertIn("ask the learner to confirm which character to explode", explode_content)
            self.assertIn("### Homophones", explode_content)
            self.assertIn("#### Same Tone", explode_content)
            self.assertIn("#### Different Tone", explode_content)
            self.assertIn("different-tone homophones", explode_content)
            self.assertIn("synonym-antonym meaning map", explode_content)
            self.assertIn("#### Synonyms", explode_content)
            self.assertIn("#### Antonyms", explode_content)
            self.assertIn("### Flashcard Candidates", explode_content)
            self.assertIn("offer exactly two concrete save options", explode_content)
            self.assertIn("If you want, I can save `语` (`語`) and `汉语` (`漢語`)", explode_content)
            self.assertIn("- `语` (`語`): `yu3 (ㄩˇ)` - language; speech", explode_content)
            self.assertIn("- `沉默`: `chen2 mo4 (ㄔㄣˊ ㄇㄛˋ)`", explode_content)

            synonyms_example = re.search(
                r"#### Synonyms\n\n(.*?)\n#### Antonyms",
                explode_content,
                re.DOTALL,
            )
            self.assertIsNotNone(synonyms_example)
            assert synonyms_example is not None
            self.assertIn("- `话语` (`話語`): `hua4 yu3 (ㄏㄨㄚˋ ㄩˇ)`", synonyms_example.group(1))
            self.assertNotIn("Traditional:", synonyms_example.group(1))
            self.assertNotIn("  - Simplified:", synonyms_example.group(1))

            flashcard_review = target / "the-big-learn-flashcard-review" / "SKILL.md"
            review_content = flashcard_review.read_text(encoding="utf-8")
            self.assertIn("python3 -m the_big_learn flashcard-review --format json", review_content)
            self.assertIn("weight = significance_flag_count + occurrence_count", review_content)
            self.assertIn("one randomly chosen face first", review_content)
            self.assertIn("the next review step, reveal both faces", review_content)

    def test_force_install_codex_skills_prunes_stale_the_big_learn_skill_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            stale = target / "the-big-learn-flashcard-variation-generator"
            stale.mkdir()
            (stale / "SKILL.md").write_text("stale\n", encoding="utf-8")
            third_party = target / "third-party-skill"
            third_party.mkdir()

            install_codex_skills(target=target, force=True)

            self.assertFalse(stale.exists())
            self.assertTrue(third_party.exists())
            self.assertTrue((target / "the-big-learn-flashcard-review" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
