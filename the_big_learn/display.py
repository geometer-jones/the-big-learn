from __future__ import annotations

from collections.abc import Mapping


SCRIPT_LAYER_KEYS = frozenset({"traditional", "simplified"})
SCRIPT_LAYER_NAME = "hanzi"
PHONETIC_LAYER_KEYS = frozenset({"zhuyin", "pinyin"})
PHONETIC_LAYER_NAME = "reading"


def format_hanzi_pair(traditional: str, simplified: str) -> str:
    if simplified == traditional:
        return simplified
    return f"{simplified}({traditional})"


def format_hanzi_layers(layers: Mapping[str, str]) -> str:
    return format_hanzi_pair(layers["traditional"], layers["simplified"])


def format_reading_pair(zhuyin: str, pinyin: str) -> str:
    if pinyin == zhuyin:
        return pinyin
    return f"{pinyin}({zhuyin})"


def format_reading_layers(layers: Mapping[str, str]) -> str:
    return format_reading_pair(layers["zhuyin"], layers["pinyin"])


def format_layer_value(layers: Mapping[str, str], layer_key: str) -> str:
    if layer_key in SCRIPT_LAYER_KEYS or layer_key == SCRIPT_LAYER_NAME:
        return format_hanzi_layers(layers)
    if layer_key in PHONETIC_LAYER_KEYS or layer_key == PHONETIC_LAYER_NAME:
        return format_reading_layers(layers)
    return str(layers[layer_key])


def canonical_layer_name(layer_key: str) -> str:
    if layer_key in SCRIPT_LAYER_KEYS or layer_key == SCRIPT_LAYER_NAME:
        return SCRIPT_LAYER_NAME
    if layer_key in PHONETIC_LAYER_KEYS or layer_key == PHONETIC_LAYER_NAME:
        return PHONETIC_LAYER_NAME
    return layer_key
