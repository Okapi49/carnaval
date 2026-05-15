# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizer email (RFC 5322 simplifie)."""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")


def recognize_email(text: str, score: float = 0.95) -> list[Span]:
    """Detecte les adresses email."""
    return regex_to_spans(
        EMAIL_PATTERN,
        text,
        entity_type="EMAIL",
        recognizer="EmailRegex",
        score=score,
    )
