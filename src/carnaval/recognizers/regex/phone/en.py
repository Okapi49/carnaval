# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizer telephones anglophones (UK, US, CA, AU, IE, NZ).

Formats couverts :
    +44 20 7946 0958          UK
    020 7946 0958
    (415) 555-0132            US
    +1 415-555-0132
    1-800-555-0199
    +61 2 9876 5432           AU
"""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

# UK : +44 puis 10 chiffres avec separateurs optionnels, ou 0X local.
PHONE_UK_PATTERN = re.compile(
    r"(?<![\w])"
    r"(?:\+44\s?|0)"
    r"\(?\d{2,5}\)?"
    r"[\s\-]?\d{3,4}[\s\-]?\d{3,4}"
    r"(?![\w])"
)

# US/CA : (XXX) XXX-XXXX, XXX-XXX-XXXX, +1 XXX XXX XXXX
PHONE_US_PATTERN = re.compile(
    r"(?<![\w])"
    r"(?:\+1[\s\-.]?)?"
    r"\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
    r"(?![\w])"
)

# AU/IE/NZ : +XX prefixe + numero
PHONE_OCE_PATTERN = re.compile(
    r"(?<![\w])"
    r"\+(?:61|353|64)\s?"
    r"\d{1,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}"
    r"(?![\w])"
)


def recognize_phone_en(text: str, score: float = 0.8) -> list[Span]:
    spans: list[Span] = []
    for pat, name in (
        (PHONE_UK_PATTERN, "PhoneUkRegex"),
        (PHONE_US_PATTERN, "PhoneUsRegex"),
        (PHONE_OCE_PATTERN, "PhoneOceRegex"),
    ):
        spans.extend(
            regex_to_spans(
                pat,
                text,
                entity_type="PHONE",
                recognizer=name,
                score=score,
            )
        )
    return spans
