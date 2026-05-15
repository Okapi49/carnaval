# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizer telephones France (+33 / 0X).

Formats couverts :
    02.41.34.85.15
    +33 2 41 33 75 75
    06.08.60.12.23
    0241414242
"""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

# (?<![\w]) : pas precede d'un caractere word (evite de matcher au milieu
# d'une reference type 0810822010647).
PHONE_FR_PATTERN = re.compile(r"(?<![\w])(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}\b")


def recognize_phone_fr(text: str, score: float = 0.85) -> list[Span]:
    return regex_to_spans(
        PHONE_FR_PATTERN,
        text,
        entity_type="PHONE",
        recognizer="PhoneFrRegex",
        score=score,
    )
