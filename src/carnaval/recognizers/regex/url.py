# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizer URL et domaines."""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

URL_PATTERN = re.compile(
    r"\b(?:https?://)?(?:www\.)?"
    r"[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}"
    r"(?:\.[a-zA-Z]{2,})+"
    r"(?:/[^\s]*)?",
)


def recognize_url(text: str, score: float = 0.7) -> list[Span]:
    return regex_to_spans(
        URL_PATTERN,
        text,
        entity_type="URL",
        recognizer="UrlRegex",
        score=score,
    )
