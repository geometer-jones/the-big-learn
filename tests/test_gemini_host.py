from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from the_big_learn.gemini_host import default_gemini_target, install_gemini_commands


class GeminiHostTests(unittest.TestCase):
    def test_default_gemini_target_looks_like_gemini_commands_home(self) -> None:
        self.assertTrue(str(default_gemini_target()).endswith(".gemini/commands"))

    def test_install_gemini_commands_copies_command_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            installed = install_gemini_commands(target=target)

            self.assertEqual({path.name for path in installed}, {"the-big-learn"})
            self.assertTrue((target / "the-big-learn" / "guided-reading.toml").exists())
            self.assertTrue((target / "the-big-learn" / "explode-char.toml").exists())
            self.assertTrue((target / "the-big-learn" / "flashcard-review.toml").exists())
            self.assertFalse((target / "the-big-learn" / "deferred-answer.toml").exists())
            guided_reading = (target / "the-big-learn" / "guided-reading.toml").read_text(encoding="utf-8")
            self.assertNotIn("current reading path", guided_reading)
            self.assertIn(
                "CURRICULUM.md",
                guided_reading,
            )
            self.assertIn(
                "DESIGN.md",
                guided_reading,
            )
            self.assertIn(
                "annotations/da-xue/starter.annotations.json",
                guided_reading,
            )
            self.assertIn(
                "bundled local `source-store/` for the shipped curriculum set",
                guided_reading,
            )
            self.assertIn(
                "Do not open every bundled source catalog or raw chapter file up front.",
                guided_reading,
            )
            self.assertIn(
                "load only that chosen book's catalog to render the chapter menu",
                guided_reading,
            )
            self.assertIn(
                "full curriculum books",
                guided_reading,
            )
            self.assertIn(
                "book number or the book name",
                guided_reading,
            )
            self.assertIn(
                "Under each book title in the menu, render the title as a miniature reference line",
                guided_reading,
            )
            self.assertIn(
                "1. Da Xue",
                guided_reading,
            )
            self.assertIn(
                "2. Zhong Yong",
                guided_reading,
            )
            self.assertIn(
                "3. Lunyu",
                guided_reading,
            )
            self.assertIn(
                "4. Mengzi",
                guided_reading,
            )
            self.assertIn(
                "5. Sunzi Bingfa",
                guided_reading,
            )
            self.assertIn(
                "6. Daodejing",
                guided_reading,
            )
            self.assertIn(
                "7. San Zi Jing",
                guided_reading,
            )
            self.assertIn(
                "8. Qian Zi Wen",
                guided_reading,
            )
            self.assertIn(
                "9. Sanguo Yanyi",
                guided_reading,
            )
            self.assertIn(
                "designed curriculum",
                guided_reading,
            )
            self.assertNotIn(
                "Current locally annotated starter slice: `Opening outline`, 3 lines, about 58 Chinese characters",
                guided_reading,
            )
            self.assertIn(
                "full `Da Xue` chapter menu and raw chapter text are bundled locally in `source-store/`",
                guided_reading,
            )
            self.assertIn(
                "If saved work already exists for a source-backed chapter, show it compactly under that book entry",
                guided_reading,
            )
            self.assertIn(
                "treat that label as progress metadata rather than as a featured excerpt or substitute for the full book chapter menu",
                guided_reading,
            )
            self.assertIn(
                "supported through bundled local source catalogs plus raw chapters when local annotations are absent",
                guided_reading,
            )
            self.assertIn(
                "web query for likely source pages",
                guided_reading,
            )
            self.assertIn(
                "Before web discovery, check whether the repository or installed package already ships a bundled full-book source catalog",
                guided_reading,
            )
            self.assertIn(
                "preferring sources that expose the base text directly in reading order",
                guided_reading,
            )
            self.assertIn(
                "web search or browsing is unavailable",
                guided_reading,
            )
            self.assertIn(
                "warn the learner plainly before continuing",
                guided_reading,
            )
            self.assertIn(
                "multiple plausible source pages",
                guided_reading,
            )
            self.assertIn(
                "python3 -m the_big_learn source catalog --url <source-url>",
                guided_reading,
            )
            self.assertIn(
                "python3 -m the_big_learn source read --url <source-url> --chapter <chapter-number-or-id> --format json",
                guided_reading,
            )
            self.assertIn(
                "Under each chapter title in the menu, render the title as a miniature reference line",
                guided_reading,
            )
            self.assertIn(
                "actual chapter count",
                guided_reading,
            )
            self.assertIn(
                "For books with more than 10 chapters, present that menu in pages of 10 entries at a time",
                guided_reading,
            )
            self.assertIn(
                "reply with `+` to load 10 more chapters",
                guided_reading,
            )
            self.assertIn(
                "saved local source text",
                guided_reading,
            )
            self.assertIn(
                "downloaded if needed, saved locally, and loaded into deterministic local reading units",
                guided_reading,
            )
            self.assertIn(
                "chapter number or the chapter name",
                guided_reading,
            )
            self.assertIn(
                "use the same source-backed chapter path as the rest of the shipped curriculum",
                guided_reading,
            )
            self.assertIn(
                "saved or bundled source catalog already exists",
                guided_reading,
            )
            self.assertIn(
                "reading-progress.json",
                guided_reading,
            )
            self.assertIn(
                "Resume where you left off",
                guided_reading,
            )
            self.assertNotIn(
                "stored annotation",
                guided_reading,
            )
            self.assertIn(
                "bundled text + generated help",
                guided_reading,
            )
            self.assertIn(
                "saved personal translation",
                guided_reading,
            )
            self.assertIn(
                "saved personal response",
                guided_reading,
            )
            self.assertIn(
                "Chapter 1 [translation saved] [response saved]",
                guided_reading,
            )
            self.assertIn(
                "[unsaved]",
                guided_reading,
            )

            self.assertIn(
                "persist the current log immediately with `python3 -m the_big_learn progress-save --format json`",
                guided_reading,
            )
            self.assertIn(
                "another terminal session can see the saved line-by-line translation before chapter end",
                guided_reading,
            )
            self.assertIn(
                "Learner Response Log",
                guided_reading,
            )
            self.assertIn(
                "saved line-by-line response before chapter end",
                guided_reading,
            )
            self.assertNotIn(
                "recommended annotated excerpt rather than the full book chapter menu",
                guided_reading,
            )
            self.assertIn(
                "you should not invent a synthetic starter chapter for guided reading",
                guided_reading,
            )
            self.assertIn(
                "guided-reading purpose is to read the base text",
                guided_reading,
            )
            self.assertIn(
                "Do not open Chapter 1 with Zhu Xi's editorial preface",
                guided_reading,
            )
            self.assertIn(
                "submit questions or comments as they arise",
                guided_reading,
            )
            self.assertIn(
                "Continue reading",
                guided_reading,
            )
            self.assertIn(
                "Choose a chapter",
                guided_reading,
            )
            self.assertIn(
                "Your translation?",
                guided_reading,
            )
            self.assertIn(
                "Your response?",
                guided_reading,
            )
            self.assertIn(
                "miniature reference line using the same order as regular line rendering",
                guided_reading,
            )
            self.assertIn(
                "Do not offer or persist a separate reading-style mode switch",
                guided_reading,
            )
            self.assertIn(
                "let the learner defer a question to the stopping point without creating a visible queue",
                guided_reading,
            )
            self.assertNotIn("learner_style.global.reading_style", guided_reading)
            self.assertNotIn("learner_style.work.reading_style", guided_reading)
            self.assertIn(
                "guided reading centered on the base text",
                guided_reading,
            )
            self.assertIn(
                "stay in the same continuous pass of reading",
                guided_reading,
            )
            self.assertIn(
                "This way you come to your questions when the answers are ready",
                guided_reading,
            )
            self.assertIn(
                "flagged, and they should keep reading while the reply arrives",
                guided_reading,
            )
            self.assertIn(
                "pad `Your translation?` with that brief flow cue",
                guided_reading,
            )
            self.assertIn(
                "Write all user-facing instructions, prompts, and action requests in English.",
                guided_reading,
            )
            self.assertIn(
                "Keep your prose responses in English even when discussing Chinese directly.",
                guided_reading,
            )
            self.assertIn(
                "English phrase (简体词 (繁體詞, if different) pinyin (zhuyin) char-by-char English translation)",
                guided_reading,
            )
            self.assertIn(
                "Those parenthetical vocabulary cues may introduce useful discussion vocabulary",
                guided_reading,
            )
            self.assertIn(
                "`significance_flag_count`",
                guided_reading,
            )
            self.assertIn(
                "If the learner instead asks about the current line or a phrase inside it, answer directly and then return to the translation, discussion, and response loop.",
                guided_reading,
            )
            self.assertIn(
                "After the learner gives a personal translation, give brief, text-grounded feedback on it and invite discussion before advancing.",
                guided_reading,
            )
            self.assertIn(
                "If that translation feedback discussion closes, pad `Your response?` with the same brief flow cue",
                guided_reading,
            )
            self.assertIn(
                "After the learner gives that line-level response, give brief, text-grounded feedback and invite discussion before advancing.",
                guided_reading,
            )
            self.assertIn(
                "automatically recommend at most one or two salient characters from the current line",
                guided_reading,
            )
            self.assertIn("one or two salient characters or phrases worth saving as flashcards", guided_reading)
            self.assertIn(
                "convert every non-punctuation character row in that line shell into or update a character-index flashcard",
                guided_reading,
            )
            self.assertIn("append a citation showing work, chapter, line id, and character position", guided_reading)
            self.assertIn("increment that card's `significance_flag_count`", guided_reading)
            self.assertIn(
                "/the-big-learn:explode-char",
                guided_reading,
            )
            self.assertIn(
                "keep learner questions tied to the visible line id or phrase under discussion",
                guided_reading,
            )
            self.assertIn(
                "separate question list, counter, or follow-up phase",
                guided_reading,
            )
            self.assertIn(
                "answer learner questions as soon as they are asked",
                guided_reading,
            )
            self.assertIn(
                "keep no visible queue",
                guided_reading,
            )
            self.assertIn(
                "do not block the next reading prompt on exploder latency",
                guided_reading,
            )
            self.assertIn(
                "full English translation for the chapter",
                guided_reading,
            )
            self.assertIn(
                "collected line-by-line personal translation",
                guided_reading,
            )
            self.assertIn(
                "collected line-by-line personal response",
                guided_reading,
            )
            self.assertIn(
                "Chinese, Reading, English Definition, Chinese Phrase, English Phrase Translation",
                guided_reading,
            )
            self.assertIn(
                "keeping simplified primary throughout the char-by-char table while appending traditional in parens only where it differs",
                guided_reading,
            )
            self.assertIn(
                "then the same full line again in English and simplified Hanzi",
                guided_reading,
            )
            self.assertIn(
                "stacked per-character list",
                guided_reading,
            )
            self.assertIn(
                "continue in raw-source mode instead of stopping",
                guided_reading,
            )
            self.assertIn(
                "stay on the bundled source-backed chapter path",
                guided_reading,
            )
            self.assertIn(
                "Do not substitute `annotations/da-xue/starter.annotations.json` for the bundled `chapter-001` through `chapter-003` flow",
                guided_reading,
            )
            self.assertIn(
                "If the learner asks about that line, answer directly and then return to that loop.",
                guided_reading,
            )
            self.assertIn(
                "do not claim stored pinyin, zhuyin, English gloss rows, or phrase tables",
                guided_reading,
            )
            self.assertIn(
                "ignore commentary-only rows, chapter summaries, and commentary chapters in the main reading pass",
                guided_reading,
            )
            self.assertIn(
                "title readings or glosses you provide are live assistant help",
                guided_reading,
            )
            self.assertIn(
                "Prompt the learner to keep reading in flow by default: translate the line, discuss that translation, respond to the line, discuss that response, and only then continue until the requested boundary or an explicit stop. If the learner asks about the line, answer directly before resuming that flow.",
                guided_reading,
            )
            self.assertIn(
                "Only move to the next line after the translation feedback discussion and the response feedback discussion have both naturally closed.",
                guided_reading,
            )
            self.assertIn(
                "prompt for one saved book-end artifact: `Personal Summary`",
                guided_reading,
            )
            self.assertIn(
                "Personal Summary",
                guided_reading,
            )
            self.assertIn(
                "Personal Response",
                guided_reading,
            )
            self.assertIn(
                "Do not prompt for a separate saved chapter-end `Personal Translation` or `Personal Response`",
                guided_reading,
            )
            self.assertIn(
                "As soon as the learner gives the book-end `Personal Summary` or the book-end `Personal Response`, persist it immediately",
                guided_reading,
            )
            self.assertIn(
                "After the book-end `Personal Summary` save succeeds, evaluate that summary in two lenses",
                guided_reading,
            )
            self.assertIn(
                "After the book-end `Personal Response` save succeeds, evaluate that response in two lenses",
                guided_reading,
            )
            self.assertIn(
                "`personal_book_summary_en` and `personal_book_response_en`",
                guided_reading,
            )
            self.assertIn(
                "`learner_response_log`",
                guided_reading,
            )
            self.assertIn(
                "python3 -m the_big_learn progress-save --format json",
                guided_reading,
            )
            self.assertIn(
                "[Save did not complete]",
                guided_reading,
            )
            self.assertIn(
                "python3 -m the_big_learn flashcard-save --format json",
                guided_reading,
            )
            self.assertIn(
                "~/.the-big-learn/flashcards/bank/",
                guided_reading,
            )
            self.assertIn(
                "~/.the-big-learn/flashcards/review-state.json",
                guided_reading,
            )
            self.assertIn(
                "bundled curriculum `source-store/` data where it is packaged",
                guided_reading,
            )
            self.assertIn(
                "as a researcher, assess textual grounding, evidence",
                guided_reading,
            )
            self.assertIn(
                "as a philosopher, assess interpretation quality, conceptual grasp",
                guided_reading,
            )
            self.assertIn(
                "mark the matched choice plainly",
                guided_reading,
            )
            self.assertIn(
                "chapter menu",
                guided_reading,
            )
            self.assertIn(
                "chapter menu covers the full book",
                guided_reading,
            )
            self.assertIn(
                "full book-level chapter catalog",
                guided_reading,
            )
            self.assertIn(
                "do not collapse the menu to only the chapters that were previously downloaded",
                guided_reading,
            )
            self.assertIn(
                "must contain all chapters of the chosen book",
                guided_reading,
            )
            self.assertIn(
                "If the learner replies with only `+` while a chapter menu page is open",
                guided_reading,
            )
            self.assertIn(
                "stay on the bundled source-backed chapter path",
                guided_reading,
            )
            self.assertIn(
                "skip or defer that framing in the main reading pass and begin from the base text instead",
                guided_reading,
            )
            self.assertIn(
                "If the learner asks a question but also wants to keep momentum, answer it briefly, stay grounded in the current line, and then resume the reading pass from the same spot.",
                guided_reading,
            )
            self.assertIn(
                "Use character explosion as a targeted aid, not a constant sidebar.",
                guided_reading,
            )
            self.assertIn(
                "When the user reaches the requested stopping point, return to any deferred questions and comments one by one in reading order",
                guided_reading,
            )
            self.assertIn(
                "answer any new follow-up questions directly before offering the next chapter",
                guided_reading,
            )
            explode_char = (target / "the-big-learn" / "explode-char.toml").read_text(encoding="utf-8")
            self.assertIn("skills/explode-char/SKILL.md", explode_char)
            self.assertIn("look back through the recent thread for likely Hanzi candidates", explode_char)
            flashcard_review = (target / "the-big-learn" / "flashcard-review.toml").read_text(encoding="utf-8")
            self.assertIn("skills/flashcard-review/SKILL.md", flashcard_review)
            self.assertIn("python3 -m the_big_learn flashcard-review --format json", flashcard_review)

    def test_force_install_gemini_commands_replaces_existing_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            existing = target / "the-big-learn"
            existing.mkdir(parents=True)
            (existing / "stale-command.toml").write_text("stale\n", encoding="utf-8")

            install_gemini_commands(target=target, force=True)

            self.assertFalse((existing / "stale-command.toml").exists())
            self.assertTrue((existing / "guided-reading.toml").exists())
            self.assertTrue((existing / "flashcard-review.toml").exists())


if __name__ == "__main__":
    unittest.main()
