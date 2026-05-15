# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizers d'adresses anglophones (UK, US, CA, AU).

Couvre :
    UK   123 High Street, London SW1A 1AA
         Flat 4, 25 King's Road
    US   1600 Pennsylvania Ave NW, Washington DC 20500
         123 Main St
    CA   M5V 3A8 Toronto
    AU   10 Smith St, Sydney NSW 2000
"""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

# UK postcode : LETTRES + chiffres (SW1A 1AA, EC1A 1BB, M1 1AA).
POSTCODE_UK_PATTERN = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?[ ]\d[A-Z]{2}\b")

# US ZIP : 5 chiffres + optionnel -4
ZIP_US_PATTERN = re.compile(r"\b\d{5}(?:-\d{4})?\b(?!\s*\d)")

# Code postal canadien : A1A 1A1
POSTCODE_CA_PATTERN = re.compile(r"\b[A-Z]\d[A-Z][ ]?\d[A-Z]\d\b")

# Rues EN : street / st. / avenue / ave / boulevard / blvd / drive / dr /
#           road / rd / lane / ln / way / court / ct / square / sq / place / pl
STREET_EN_PATTERN = re.compile(
    r"\b\d{1,5}[a-z]?\s+"
    r"(?:[A-Z][A-Za-z\-']+\s+){1,3}"
    r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Road|Rd|"
    r"Lane|Ln|Way|Court|Ct|Square|Sq|Place|Pl|Parkway|Pkwy|Terrace|Ter|"
    r"Highway|Hwy|Crescent|Cres)\b\.?",
    re.IGNORECASE,
)

# PO Box
PO_BOX_PATTERN = re.compile(
    r"\b(?:P\.?\s?O\.?\s?Box|Post\s?Office\s?Box)\s+\d{1,6}\b",
    re.IGNORECASE,
)


def recognize_address_en(text: str, score: float = 0.85) -> list[Span]:
    """Aggregateur EN (UK + US + CA + AU)."""
    spans: list[Span] = []
    for pat, name in (
        (POSTCODE_UK_PATTERN, "PostcodeUkRegex"),
        (ZIP_US_PATTERN, "ZipUsRegex"),
        (POSTCODE_CA_PATTERN, "PostcodeCaRegex"),
        (STREET_EN_PATTERN, "StreetEnRegex"),
        (PO_BOX_PATTERN, "PoBoxRegex"),
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
