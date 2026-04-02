from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def _load_build_source_store_module():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "build_four_books_source_store.py"
    spec = importlib.util.spec_from_file_location("build_four_books_source_store", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load build_four_books_source_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_source_store = _load_build_source_store_module()


class BuildSourceStoreTests(unittest.TestCase):
    def test_store_dir_for_bundled_work_uses_readable_name(self) -> None:
        self.assertEqual(
            build_source_store._store_dir_for_url(
                build_source_store.BUNDLED_SOURCES["lunyu"]["source_url"]
            ).name,
            "lunyu",
        )

    def test_curate_da_xue_catalog_extracts_core_text_and_commentary(self) -> None:
        raw_catalog = {
            "provider": "ctext-html",
            "source_url": "https://ctext.org/si-shu-zhang-ju-ji-zhu/da-xue-zhang-ju?if=en",
            "title": "四書章句集注 : 大學章句",
            "chapter_count": 11,
            "chapters": [
                {
                    "id": "chapter-001",
                    "order": 1,
                    "title": "右經一章",
                    "summary": "，蓋孔子之言，而曾子述之",
                    "character_count": 0,
                    "text": "\n".join(
                        [
                            "大學之書，古之大學所以教人之法也。",
                            "淳熙己酉春二月申子，新安朱熹序",
                            "大學之道，在明明德，在親民，在止於至善。",
                            "知止而后有定，定而后能靜，靜而后能安，安而后能慮，慮而后能得。",
                            "物有本末，事有終始，知所先後，則近道矣。",
                            "古之欲明明德於天下者，先治其國；欲治其國者，先齊其家；欲齊其家者，先脩其身；欲脩其身者，先正其心；欲正其心者，先誠其意；欲誠其意者，先致其知；致知在格物。",
                            "物格而后知至，知至而后意誠，意誠而后心正，心正而后身脩，身脩而后家齊，家齊而后國治，國治而后天下平。",
                            "自天子以至於庶人，壹是皆以脩身為本。",
                            "其本亂而末治者否矣，其所厚者薄，而其所薄者厚，未之有也！",
                        ]
                    ),
                    "supplemental_text": "程子曰：「大學，孔氏之遺書，而初學入德之門也。」",
                },
                *[
                    {
                        "id": f"chapter-{index:03d}",
                        "order": index,
                        "title": title,
                        "summary": summary,
                        "character_count": len(text),
                        "text": text,
                        "supplemental_text": f"{title} 補註",
                    }
                    for index, (title, summary, text) in enumerate(
                        [
                            ("右傳之首章", "釋明明德", "康誥曰：「克明德。」"),
                            ("右傳之二章", "釋新民", "湯之盤銘曰：「苟日新，日日新，又日新。」"),
                            ("右傳之三章", "釋止於至善", "詩云：「邦畿千里，惟民所止。」"),
                            ("右傳之四章", "釋本末", "子曰：「聽訟，吾猶人也，必也使無訟乎！」"),
                            ("右傳之五章", "，蓋釋格物、致知之義，而今亡矣", "此謂知本，此謂知之至也。"),
                            ("右傳之六章", "釋誠意", "所謂誠其意者：毋自欺也。"),
                            ("右傳之七章", "釋正心脩身", "所謂脩身在正其心者。"),
                            ("右傳之八章", "釋脩身齊家", "所謂齊其家在脩其身者。"),
                            ("右傳之九章", "釋齊家治國", "所謂治國必先齊其家者。"),
                            ("右傳之十章", "釋治國平天下", "所謂平天下在治其國者。"),
                        ],
                        start=2,
                    )
                ],
            ],
        }

        curated = build_source_store._curate_da_xue_catalog(raw_catalog)

        self.assertEqual(curated["chapter_count"], 7)
        self.assertEqual(
            [chapter["title"] for chapter in curated["chapters"]],
            [spec["title"] for spec in build_source_store.DA_XUE_CORE_CHAPTER_SPECS],
        )
        self.assertEqual(curated["chapters"][0]["text"], "大學之道，在明明德，在親民，在止於至善。")
        self.assertEqual(curated["chapters"][3]["summary"], "先治其國；欲治其國者，先齊其家")
        self.assertEqual(curated["commentary_chapter_count"], 11)
        self.assertEqual(curated["commentary_chapters"][0]["id"], "commentary-introduction")
        self.assertEqual(curated["commentary_chapters"][0]["title"], "朱熹序與總說")
        self.assertEqual(curated["commentary_chapters"][0]["text"], "大學之書，古之大學所以教人之法也。\n淳熙己酉春二月申子，新安朱熹序")
        self.assertEqual(
            curated["commentary_chapters"][0]["supplemental_text"],
            "程子曰：「大學，孔氏之遺書，而初學入德之門也。」",
        )
        self.assertEqual(curated["commentary_chapters"][1]["id"], "commentary-chapter-001")
        self.assertEqual(curated["commentary_chapters"][1]["title"], "右傳之首章")
        self.assertIn("should not be presented", curated["core_text_note"])


if __name__ == "__main__":
    unittest.main()
