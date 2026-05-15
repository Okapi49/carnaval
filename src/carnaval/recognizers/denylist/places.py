# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizer deny list de toponymes (noms de lieux specifiques).

Utile pour masquer des noms de villes / quartiers / sites qui ne sont
sensibles QUE dans un contexte client donne. Exemple : 'SPRINGFIELD'
n'est pas sensible en general, mais c'est l'adresse de votre
entreprise -> a masquer dans vos documents.
"""

from __future__ import annotations

from carnaval.core.span import Span
from carnaval.recognizers.base import build_alternation_pattern, regex_to_spans


def recognize_places(
    text: str,
    places: list[str],
    entity_type: str = "LOCATION",
    recognizer_name: str = "PlacesDenyList",
    score: float = 0.95,
    case_sensitive: bool = False,
    word_boundary: bool = True,
    tolerant_accents: bool = True,
) -> list[Span]:
    """Detecte les toponymes listes.

    tolerant_accents=True (defaut) permet de matcher 'Chambery' liste avec
    'Chambéry' dans le texte (et inversement). Indispensable car les listes
    d'origine GeoNames/INSEE ne sont pas systematiquement accentuees.
    """
    if not places:
        return []
    pattern = build_alternation_pattern(
        places,
        case_sensitive=case_sensitive,
        word_boundary=word_boundary,
        tolerant_accents=tolerant_accents,
    )
    return regex_to_spans(
        pattern,
        text,
        entity_type=entity_type,
        recognizer=recognizer_name,
        score=score,
    )
