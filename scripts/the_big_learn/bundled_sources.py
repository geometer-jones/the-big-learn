from __future__ import annotations


BUNDLED_SOURCES = {
    "da-xue": {
        "title": "Da Xue",
        "source_url": "https://ctext.org/si-shu-zhang-ju-ji-zhu/da-xue-zhang-ju?if=en",
        "chapter_count": 7,
        "source_chapter_count": 11,
        "commentary_chapter_count": 11,
    },
    "zhong-yong": {
        "title": "Zhong Yong",
        "source_url": "https://ctext.org/si-shu-zhang-ju-ji-zhu/zhong-yong-zhang-ju?if=en",
        "chapter_count": 33,
    },
    "lunyu": {
        "title": "Lunyu",
        "source_url": "https://ctext.org/si-shu-zhang-ju-ji-zhu/lun-yu-ji-zhu?if=en",
        "chapter_count": 20,
    },
    "mengzi": {
        "title": "Mengzi",
        "source_url": "https://ctext.org/si-shu-zhang-ju-ji-zhu/meng-zi-ji-zhu?if=en",
        "chapter_count": 14,
    },
    "sunzi-bingfa": {
        "title": "Sunzi Bingfa",
        "source_url": "https://ctext.org/art-of-war?if=en",
        "chapter_count": 13,
    },
    "daodejing": {
        "title": "Daodejing",
        "source_url": "https://ctext.org/dao-de-jing?if=en",
        "chapter_count": 81,
    },
    "san-zi-jing": {
        "title": "San Zi Jing",
        "source_url": "https://ctext.org/three-character-classic?if=en",
        "chapter_count": 1,
    },
    "qian-zi-wen": {
        "title": "Qian Zi Wen",
        "source_url": "https://zh.wikisource.org/wiki/%E5%8D%83%E5%AD%97%E6%96%87",
        "chapter_count": 1,
    },
    "sanguo-yanyi": {
        "title": "Sanguo Yanyi",
        "source_url": "https://zh.wikisource.org/wiki/%E4%B8%89%E5%9C%8B%E6%BC%94%E7%BE%A9",
        "chapter_count": 120,
    },
    "chengyu-catalog": {
        "title": "Chengyu Catalog",
        "source_url": "the-big-learn://chengyu-catalog",
        "chapter_count": 20,
    },
}


BUNDLED_SOURCE_URL_TO_WORK_ID = {
    spec["source_url"]: work_id
    for work_id, spec in BUNDLED_SOURCES.items()
}
