# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Recognizers d'adresses francaises.

Complement de GLiNER : capture les adresses isolees que GLiNER rate.
"""

from __future__ import annotations

import re

from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

# Code postal 5 chiffres + ville (majuscules OU mixed case).
# - 1er char apres l'espace : DOIT etre majuscule (filtre faux positifs)
# - Suite : minuscules + accentues + tirets + apostrophes acceptes pour
#   couvrir "Le Bourget-du-Lac", "Saint-Etienne", "Cédex"...
# - [ \t]* (pas \s) pour ne pas franchir un retour ligne
POSTAL_CITY_PATTERN = re.compile(
    r"\b\d{5}[ \t]*[A-Z]" r"[A-Za-zéèêëàâäîïôöùûüçÉÈÊËÀÂÄÎÏÔÖÙÛÜÇ \t\-'.]{2,60}"
)

# Boite postale (BP, B.P., CS)
BP_PATTERN = re.compile(
    r"\b(?:B\.?P\.?|C\.?S\.?)\s+\d{2,6}\b",
    re.IGNORECASE,
)

# Zones d'activite francaises - accepte Z.I., Z.I, ZAC, etc.
# Inclut aussi les noms de technopoles connues (Technolac, Sophia-Antipolis...)
ZONE_PATTERN = re.compile(
    r"(?:\b(?:PARC[ \t]D['']ACTIVITES?|PARC[ \t]ACTIVITES?|"
    r"Z\.?\s?A\.?\s?C\.?|Z\.?\s?I\.?|ZONE[ \t]INDUSTRIELLE|"
    r"ZONE[ \t]D['']ACTIVITES?|IMMEUBLE|TECHNOPOLE|TECHNOPARC)"
    r"[ \t]*-?[ \t]*"
    r"[A-Z\d][\w \t\-'/.]{2,80})"
    r"|"
    # Technopoles nommees (Savoie Technolac, Sophia-Antipolis, etc.)
    # Pattern: [Mot capitalise] (espace [mot capitalise])? + suffixe technopole
    r"(?:\b[A-Z][A-Za-zéèêëàâäîïôöùûüç]{2,20}"
    r"(?:[\s\-][A-Z][A-Za-zéèêëàâäîïôöùûüç]{2,20})?"
    r"[\s\-]Technolac\b)"
    r"|(?:\bSophia[\s\-]Antipolis\b)",
    re.IGNORECASE,
)

# Rue / boulevard / avenue ... + nom : matche les adresses isolees sans code postal.
# Numero + (virgule ou espace) + type voie + nom de la rue.
# Exemples couverts :
#   126 RUE DE STALINGRAD
#   30 Boulevard de la Republique
#   155, avenue du Faucigny
#   126,RUE DE STALINGRAD       (sans espace apres virgule)
STREET_PATTERN_WITH_NUMBER = re.compile(
    r"\b\d{1,4}\s*,?\s*(?:bis|ter|quater)?\s*"
    r"(?:rue|boulevard|bd|avenue|av|impasse|allée|allee|"
    r"chemin|route|place|quai|cours)\s+"
    r"(?:de\s|du\s|des\s|d['’]|la\s|le\s|l['’])?"
    r"[\w][\w \t\-'’./]{2,60}",
    re.IGNORECASE,
)

# Cas ou la rue est sur une ligne SEULE (sans numero precedent) :
#   Rue de la Gare
#   Boulevard de la Republique
#   Avenue des Champs-Elysees
STREET_PATTERN_WITHOUT_NUMBER = re.compile(
    r"\b(?:Rue|Boulevard|Avenue|Impasse|Allée|Allee|Chemin|Route|"
    r"Place|Quai|Cours)\s+"
    r"(?:(?:de|du|des|la|le|l['’]|d['’])\s+){0,2}"
    r"[A-Z][\w \t\-'’./]{2,60}"
)

# Cas particulier : texte parasite ou tous les mots sont colles.
# Exemples : "126RUEDESTALINGRAD", "RuedelaGare".
STREET_GLUED_PATTERN = re.compile(
    r"\b\d{0,4}\s*"
    r"(?:rue|boulevard|bd|avenue|impasse|allee|chemin|route|place|quai|cours)"
    r"(?:de|du|des|d[a-z]?|la|le|l[a-z]?)?"
    r"[a-z]{2,40}",
    re.IGNORECASE,
)


def recognize_postal_city_fr(text: str, score: float = 0.85) -> list[Span]:
    return regex_to_spans(
        POSTAL_CITY_PATTERN,
        text,
        entity_type="LOCATION",
        recognizer="PostalCityFrRegex",
        score=score,
    )


def recognize_bp(text: str, score: float = 0.85) -> list[Span]:
    """Detecte les references de boite postale (BP 70226, B.P. 100, CS 12345)."""
    return regex_to_spans(
        BP_PATTERN,
        text,
        entity_type="LOCATION",
        recognizer="BpRegex",
        score=score,
    )


def recognize_zone_fr(text: str, score: float = 0.85) -> list[Span]:
    return regex_to_spans(
        ZONE_PATTERN,
        text,
        entity_type="LOCATION",
        recognizer="ZoneFrRegex",
        score=score,
    )


def recognize_street_fr(text: str, score: float = 0.85) -> list[Span]:
    spans = regex_to_spans(
        STREET_PATTERN_WITH_NUMBER,
        text,
        entity_type="LOCATION",
        recognizer="StreetFrRegex",
        score=score,
    )
    spans += regex_to_spans(
        STREET_PATTERN_WITHOUT_NUMBER,
        text,
        entity_type="LOCATION",
        recognizer="StreetFrRegex",
        score=score - 0.05,
    )
    spans += regex_to_spans(
        STREET_GLUED_PATTERN,
        text,
        entity_type="LOCATION",
        recognizer="StreetGluedRegex",
        score=score - 0.05,
    )
    return spans


def recognize_address_fr(text: str) -> list[Span]:
    """Aggregateur."""
    return (
        recognize_postal_city_fr(text)
        + recognize_zone_fr(text)
        + recognize_street_fr(text)
        + recognize_bp(text)
    )
