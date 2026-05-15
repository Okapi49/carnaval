# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizer pour une liste d'organisations (fournisseurs, partenaires).

Chaque organisation distincte recoit un index numerique : [ORGANIZATION_1],
[ORGANIZATION_2], etc. (l'attribution se fait a l'etage de masquage,
ce module produit juste des Spans tagges ORGANIZATION).
"""

from __future__ import annotations

from carnaval.core.span import Span
from carnaval.recognizers.base import build_alternation_pattern, regex_to_spans


def recognize_organizations(
    text: str,
    organizations: list[str],
    entity_type: str = "ORGANIZATION",
    recognizer_name: str = "OrganizationsDenyList",
    score: float = 1.0,
    case_sensitive: bool = False,
    word_boundary: bool = True,
) -> list[Span]:
    """Detecte les organisations listees."""
    if not organizations:
        return []
    pattern = build_alternation_pattern(
        organizations,
        case_sensitive=case_sensitive,
        word_boundary=word_boundary,
    )
    return regex_to_spans(
        pattern,
        text,
        entity_type=entity_type,
        recognizer=recognizer_name,
        score=score,
    )


def recognize_organizations_loose(
    text: str,
    organizations: list[str],
    entity_type: str = "ORGANIZATION",
    recognizer_name: str = "OrganizationsLooseDenyList",
    score: float = 0.75,
    min_len: int = 4,
) -> list[Span]:
    """Variante 'tolerante' sans word boundary, pour les textes parasites
    ou les noms colles a d'autres mots ("venteexamplecorpdisponible").

    Filtre les variantes < min_len chars pour limiter les faux positifs.
    """
    candidates = [o for o in organizations if len(o) >= min_len]
    if not candidates:
        return []
    pattern = build_alternation_pattern(
        candidates,
        case_sensitive=False,
        word_boundary=False,
    )
    return regex_to_spans(
        pattern,
        text,
        entity_type=entity_type,
        recognizer=recognizer_name,
        score=score,
    )
