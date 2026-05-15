# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Type Span : un fragment detecte dans le texte.

Un Span represente une entite sensible localisee dans le texte source.
Utilise par tous les etages : produit par S3 (detect), consomme par S4 (resolve)
et S5 (mask).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Span:
    """Fragment detecte.

    Attributes:
        start: offset de debut dans le texte source (inclus)
        end: offset de fin dans le texte source (exclu)
        entity_type: type d'entite (PERSON, EMAIL, ORG_SINGLETON, ...)
        text: contenu textuel original capture
        score: confiance [0.0, 1.0]
        recognizer: nom du recognizer producteur (debug + arbitrage)
        metadata: cle/valeur libre (langue, pattern_name, ...)
    """

    start: int
    end: int
    entity_type: str
    text: str
    score: float = 1.0
    recognizer: str = ""
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(f"start negatif : {self.start}")
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) <= start ({self.start})")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score hors [0,1] : {self.score}")
        if not self.entity_type:
            raise ValueError("entity_type vide")

    @property
    def length(self) -> int:
        """Longueur du span en caracteres."""
        return self.end - self.start

    def overlaps(self, other: Span) -> bool:
        """True si les deux spans ont au moins un caractere en commun."""
        return not (self.end <= other.start or other.end <= self.start)

    def contains(self, other: Span) -> bool:
        """True si self englobe strictement other (ou egal)."""
        return self.start <= other.start and self.end >= other.end

    def shift(self, delta: int) -> Span:
        """Renvoie une copie decalee de delta caracteres."""
        return Span(
            start=self.start + delta,
            end=self.end + delta,
            entity_type=self.entity_type,
            text=self.text,
            score=self.score,
            recognizer=self.recognizer,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialisation pour JSON/audit (NB : contient le text original)."""
        return {
            "start": self.start,
            "end": self.end,
            "entity_type": self.entity_type,
            "text": self.text,
            "score": self.score,
            "recognizer": self.recognizer,
            "metadata": dict(self.metadata),
        }

    def to_dict_safe(self) -> dict[str, Any]:
        """Serialisation sans la valeur originale (pour logs/audit non confidentiels)."""
        return {
            "start": self.start,
            "end": self.end,
            "entity_type": self.entity_type,
            "length": self.length,
            "score": self.score,
            "recognizer": self.recognizer,
        }
