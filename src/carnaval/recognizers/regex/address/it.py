# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizers di indirizzi italiani.

Coperture :
    Via Roma 12, 20121 Milano
    Viale della Liberta 5
    Piazza Duomo 1
    Corso Vittorio Emanuele 100
    Casella Postale 1234
"""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

# CAP italien : 5 chiffres + ville
POSTAL_CITY_IT_PATTERN = re.compile(
    r"\b\d{5}[ \t]+" r"[A-Z][A-Za-zàèéìòùÀÈÉÌÒÙ \t\-'.]{2,60}"
)

# Rues IT : Via / Viale / Piazza / Corso / Vicolo / Largo / Strada / Lungomare
STREET_IT_PATTERN = re.compile(
    r"\b(?:Via|Viale|V\.le|Piazza|Pza|P\.za|Corso|C\.so|"
    r"Vicolo|V\.lo|Largo|L\.go|Strada|Lungomare|Lungotevere|"
    r"Riva|Salita|Calle)"
    r"\s+"
    r"(?:di\s|del\s|della\s|delle\s|degli\s|dei\s|d['’])?"
    r"[\w][\w \t\-'’.]{2,60}",
    re.IGNORECASE,
)

# Casella Postale (BP)
CASELLA_POSTALE_IT_PATTERN = re.compile(
    r"\b(?:Casella\s+Postale|C\.?\s?P\.?)\s+\d{1,6}\b",
    re.IGNORECASE,
)


def recognize_address_it(text: str, score: float = 0.85) -> list[Span]:
    spans: list[Span] = []
    for pat, name in (
        (POSTAL_CITY_IT_PATTERN, "PostalCityItRegex"),
        (STREET_IT_PATTERN, "StreetItRegex"),
        (CASELLA_POSTALE_IT_PATTERN, "CasellaPostaleItRegex"),
    ):
        spans.extend(
            regex_to_spans(
                pat,
                text,
                entity_type="LOCATION",
                recognizer=name,
                score=score,
            )
        )
    return spans
