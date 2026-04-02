from __future__ import annotations

from .bundled_sources import BUNDLED_SOURCES

FOUR_BOOK_IDS = ("da-xue", "zhong-yong", "lunyu", "mengzi")

FOUR_BOOKS = {work_id: BUNDLED_SOURCES[work_id] for work_id in FOUR_BOOK_IDS}
