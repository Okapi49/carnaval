# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Contrat commun et helpers pour les recognizers.

Un recognizer est une fonction qui prend un texte et renvoie une liste de Span.
Pas de class, pas d'heritage, pas de framework.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable, Protocol

from carnaval.core.span import Span


class Recognizer(Protocol):
    """Contrat fonctionnel d'un recognizer."""

    def __call__(self, text: str) -> list[Span]: ...


# ----------------------------------------------------------------------
# Helpers regex -> Span
# ----------------------------------------------------------------------


def regex_to_spans(
    pattern: re.Pattern[str],
    text: str,
    *,
    entity_type: str,
    recognizer: str,
    score: float = 1.0,
    validator: Callable[[str], bool] | None = None,
    metadata: dict | None = None,
) -> list[Span]:
    """Itere sur les matches d'un pattern compile et produit des Spans.

    Args:
        pattern: regex compile.
        text: texte source.
        entity_type: type d'entite a attribuer au Span.
        recognizer: nom du recognizer producteur (debug, arbitrage).
        score: score [0,1] applique a chaque Span produit.
        validator: callable optionnel `(text) -> bool` qui filtre les matches
            (utile pour checksums : IBAN mod 97, Luhn, ...).
        metadata: dict optionnel ajoute aux Spans.

    Returns:
        Liste de Span (eventuellement vide).
    """
    spans: list[Span] = []
    for m in pattern.finditer(text):
        captured = m.group(0)
        if validator is not None and not validator(captured):
            continue
        spans.append(
            Span(
                start=m.start(),
                end=m.end(),
                entity_type=entity_type,
                text=captured,
                score=score,
                recognizer=recognizer,
                metadata=dict(metadata) if metadata else {},
            )
        )
    return spans


# ----------------------------------------------------------------------
# Helpers pour deny lists tolerantes
# ----------------------------------------------------------------------


# Voyelles francaises avec leurs variantes accentuees.
# Quand `tolerant_accents=True`, chaque voyelle d'un item devient une classe
# de caracteres qui matche aussi ses formes accentuees.
_ACCENT_CLASSES = {
    "a": "[aàáâäãåAÀÁÂÄÃÅ]",
    "e": "[eéèêëEÉÈÊË]",
    "i": "[iíìîïIÍÌÎÏ]",
    "o": "[oóòôöõOÓÒÔÖÕ]",
    "u": "[uúùûüUÚÙÛÜ]",
    "c": "[cçCÇ]",
    "n": "[nñNÑ]",
    "y": "[yýÿYÝŸ]",
}

# Classes de caracteres equivalents pour les separateurs et apostrophes.
# Le `*` (zero ou plus) accepte aussi les textes colles type "SampleCounty"
# ou "GLOBEXINDUSTRIESSAS". Combine au word_boundary externe, le risque
# de faux positif reste tres faible : on ne match qu'en debut/fin de mot.
_FLEX_SPACE_CLASS = r"[\s\-_]*"  # espace, tiret, underscore, ou rien
_FLEX_QUOTE_CLASS = r"['‘’]"  # apostrophe droite + courbes


_REGEX_SPECIAL_CHARS = set(r"\.^$*+?()[]{}|")
_SEPARATORS = (" ", "\t", "-", "_")
_APOSTROPHES = ("'", "‘", "’")


def _flexibilize_item(item: str, *, tolerant_accents: bool = False) -> str:
    """Transforme une chaine en regex tolerant aux variations courantes :

    - Espaces multiples / tabulations / tirets / underscores : equivalents
    - Apostrophes droites (`'`) et courbes (`U+2018`, `U+2019`) : equivalentes
    - (optionnel) Voyelles accentuees : classes de caracteres

    Exemple : "Sample County" produit un pattern qui matche :
        - Sample County
        - SAMPLE COUNTY
        - Sample-County
        - Sample_County
        - Sample  County
        - Sample county (mix de casse, via IGNORECASE en aval)

    Implementation : parcours char par char (pas de re.escape) pour eviter
    le piege ou re.escape() echappe les espaces dans Python recent et
    casse ensuite les substitutions.
    """
    result: list[str] = []
    i = 0
    n = len(item)
    while i < n:
        ch = item[i]

        # Sequence de separateurs (espaces, tabs, tirets, underscores) -> 1 classe
        if ch in _SEPARATORS:
            j = i
            while j < n and item[j] in _SEPARATORS:
                j += 1
            result.append(_FLEX_SPACE_CLASS)
            i = j
            continue

        # Apostrophe
        if ch in _APOSTROPHES:
            result.append(_FLEX_QUOTE_CLASS)
            i += 1
            continue

        # Voyelle accentuee (optionnel)
        if tolerant_accents and ch.lower() in _ACCENT_CLASSES:
            result.append(_ACCENT_CLASSES[ch.lower()])
            i += 1
            continue

        # Caractere normal : echapper si c'est un caractere regex special
        if ch in _REGEX_SPECIAL_CHARS:
            result.append("\\" + ch)
        else:
            result.append(ch)
        i += 1

    return "".join(result)


def build_alternation_pattern(
    items: Iterable[str],
    *,
    case_sensitive: bool = False,
    word_boundary: bool = True,
    flexible_separators: bool = True,
    tolerant_accents: bool = False,
) -> re.Pattern[str]:
    """Construit un regex d'alternation a partir d'une liste d'items.

    Le pattern produit est TOLERANT par defaut aux variations courantes :
    casse (IGNORECASE), separateurs (espace/tiret/underscore equivalents),
    apostrophes droites et courbes.

    Trie par longueur decroissante pour que la version la plus longue match
    en priorite (l'alternation regex n'est pas "longest match" par defaut).

    Args:
        items: liste de chaines a inclure.
        case_sensitive: True pour exiger une casse exacte (defaut False).
        word_boundary: True pour exiger des limites de mots (defaut True).
        flexible_separators: True (defaut) pour traiter espaces, tirets et
            underscores comme equivalents. Permet a "Sample County" de
            matcher aussi "Sample-County", "Sample_County", etc.
        tolerant_accents: True pour traiter les voyelles accentuees comme
            equivalentes a leur forme simple (defaut False car ca alourdit
            beaucoup le pattern et peut generer des faux positifs).

    Returns:
        Pattern compile.
    """
    items_sorted = sorted({i for i in items if i}, key=len, reverse=True)
    if not items_sorted:
        return re.compile(r"(?!x)x")

    if flexible_separators or tolerant_accents:
        parts = [
            _flexibilize_item(i, tolerant_accents=tolerant_accents)
            for i in items_sorted
        ]
    else:
        parts = [re.escape(i) for i in items_sorted]

    body = "|".join(parts)
    if word_boundary:
        body = rf"(?:{body})"
        body = rf"(?<![A-Za-z0-9_]){body}(?![A-Za-z0-9_])"
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(body, flags)
