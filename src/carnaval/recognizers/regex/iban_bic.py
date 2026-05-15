# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizers IBAN (avec checksum mod 97) et BIC (avec contexte requis)."""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

# IBAN compact : sans \b initial pour capturer "IBANFR76..." en textes parasites.
# Le checksum mod 97 filtre les faux positifs.
IBAN_COMPACT_PATTERN = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")

# IBAN avec espaces par blocs de 4
IBAN_SPACED_PATTERN = re.compile(
    r"\b[A-Z]{2}\d{2}(?:\s[A-Z0-9]{4}){2,7}(?:\s[A-Z0-9]{1,4})?\b"
)

# BIC ISO 9362
BIC_PATTERN = re.compile(r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b")

# Mots-cles imposes a proximite (50 chars) pour valider un BIC
BIC_CONTEXT = ("BIC", "SWIFT", "B.I.C")


def validate_iban_checksum(text: str) -> bool:
    """Validation IBAN par mod 97 = 1."""
    cleaned = "".join(c for c in text.upper() if c.isalnum())
    if len(cleaned) < 15 or len(cleaned) > 34:
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def recognize_iban(text: str, score: float = 0.85) -> list[Span]:
    """IBAN avec validation checksum. Filtre tout match qui ne passe pas mod 97."""
    spans = regex_to_spans(
        IBAN_COMPACT_PATTERN,
        text,
        entity_type="IBAN",
        recognizer="IbanRegex",
        score=score,
        validator=validate_iban_checksum,
    )
    spans += regex_to_spans(
        IBAN_SPACED_PATTERN,
        text,
        entity_type="IBAN",
        recognizer="IbanRegex",
        score=score,
        validator=validate_iban_checksum,
    )
    return spans


def _has_bic_context(text: str, start: int, end: int, window: int = 30) -> bool:
    """True si un mot-cle BIC/SWIFT est a proximite, ou si le match commence par BIC.

    Le cas "match commence par BIC" couvre les textes parasites colles
    type 'BICCOBAFRPXXXX' ou le mot-cle est absorbe dans le match.
    """
    matched = text[start:end].upper()
    if matched.startswith(("BIC", "SWIFT")):
        return True
    before = text[max(0, start - window) : start].upper()
    after = text[end : end + window].upper()
    return any(kw in before or kw in after for kw in BIC_CONTEXT)


def recognize_bic(text: str, score: float = 0.7) -> list[Span]:
    """BIC : ne produit un Span que si BIC/SWIFT est proche.

    Sans contexte, le pattern matcherait n'importe quel mot 8+ majuscules
    (STALINGRAD, ACTIVITES...).
    """
    spans: list[Span] = []
    for m in BIC_PATTERN.finditer(text):
        if not _has_bic_context(text, m.start(), m.end()):
            continue
        spans.append(
            Span(
                start=m.start(),
                end=m.end(),
                entity_type="BIC",
                text=m.group(0),
                score=score,
                recognizer="BicRegex",
            )
        )
    return spans
