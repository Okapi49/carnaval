# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Etage 3 - Detect : execute les recognizers et collecte les Spans.

Responsabilites :
- Charger les recognizers actifs selon la config
- Executer chaque recognizer sur le texte
- Collecter les Spans (sans dedup - c'est le role de S4)

Entree : NormalizedDocument + Config
Sortie : DetectedDocument
"""

from __future__ import annotations

from typing import Callable

from carnaval.core.config_loader import Config
from carnaval.core.span import Span
from carnaval.recognizers.denylist.organizations import (
    recognize_organizations,
    recognize_organizations_loose,
)
from carnaval.recognizers.denylist.people import recognize_people
from carnaval.recognizers.denylist.places import recognize_places
from carnaval.recognizers.denylist.singleton import (
    recognize_singleton,
    recognize_singleton_loose,
)
from carnaval.recognizers.dictionary import recognize_cities, recognize_firstnames
from carnaval.recognizers.regex.address import recognize_address
from carnaval.recognizers.regex.context_location import recognize_contextual_location
from carnaval.recognizers.regex.email import recognize_email
from carnaval.recognizers.regex.fiscal_fr import recognize_all_fiscal_fr
from carnaval.recognizers.regex.header_source import recognize_header_source
from carnaval.recognizers.regex.iban_bic import recognize_bic, recognize_iban
from carnaval.recognizers.regex.names import recognize_names
from carnaval.recognizers.regex.org_suffix import recognize_org_suffix
from carnaval.recognizers.regex.phone import recognize_phone
from carnaval.recognizers.regex.url import recognize_url
from carnaval.stages.documents import DetectedDocument, NormalizedDocument

# Recognizers regex universels (toutes langues)
_UNIVERSAL_REGEX_RECOGNIZERS: tuple[Callable[[str], list[Span]], ...] = (
    recognize_email,
    recognize_url,
    recognize_iban,
    recognize_bic,
    recognize_header_source,
)


# Recognizers regex specifiques FR (au-dela des dispatchers multilingues) :
# fiscal francais (SIREN/SIRET/TVA FR) qui n'a pas d'equivalent direct dans
# les autres langues. Pour DE/EN/ES/IT, le recognizer fiscal est branche
# explicitement dans detect() si la langue est active.
_FR_SPECIFIC_REGEX_RECOGNIZERS: tuple[Callable[[str], list[Span]], ...] = (
    recognize_all_fiscal_fr,
)


_SUPPORTED_LANGUAGES = frozenset({"fr", "en", "de", "es", "it", "pt", "nl"})

# Marqueurs linguistiques pour les documents hybrides.
# Deux niveaux :
#   STRONG = un seul hit suffit (mention non ambigue comme un nom de pays)
#   WEAK   = 2 hits distincts requis (suffixes orgs, mots commerciaux)
_LANGUAGE_MARKERS_STRONG: dict[str, tuple[str, ...]] = {
    "de": (
        r"\bDeutschland\b",
        r"\bÖsterreich\b",
        r"\bGeschäftsführer\b",
        r"\bSitz der Gesellschaft\b",
        r"\bRegistergericht\b",
        r"\bAufsichtsrat\w*\b",
    ),
    "en": (r"\bUnited Kingdom\b", r"\bUnited States\b"),
    "es": (r"\bEspaña\b",),
    "it": (r"\bItalia\b",),
    "pt": (r"\bPortugal\b", r"\bBrasil\b"),
    "fr": (r"\bFrance\b",),
}

_LANGUAGE_MARKERS_WEAK: dict[str, tuple[str, ...]] = {
    "de": (
        r"\bGmbH\b",
        r"\bAG\b",
        r"\bKG\b",
        r"\bSE\b",
        r"\bVorstand\b",
        r"\bAmtsgericht\b",
        r"\bUST-IdNr\.\b",
        r"\bUSt-IdNr\.\b",
        r"\bSchweiz\b",
    ),
    "en": (
        r"\bLtd\.?\b",
        r"\bLLC\b",
        r"\bInc\.\b",
        r"\bCorp\.\b",
        r"\bPLC\b",
        r"\bSincerely\b",
        r"\bRegards\b",
    ),
    "es": (r"\bS\.A\.\b", r"\bSociedad Anonima\b", r"\bSL\b", r"\bAtentamente\b"),
    "it": (r"\bS\.r\.l\.\b", r"\bS\.p\.A\.\b", r"\bCordiali saluti\b"),
    "pt": (
        r"\bLda\.?\b",
        r"\bSociedade\b",
        r"\bAvenida\b",
        r"\bAv\.\s*\d",
        r"\bRua\b",
        r"\bCNPJ\b",
    ),
    "fr": (
        r"\bSARL\b",
        r"\bSAS\b",
        r"\bS\.A\.S\.\b",
        r"\bSASU\b",
        r"\bcordialement\b",
        r"\bSiège social\b",
    ),
}

import re as _re

_STRONG_COMPILED: dict[str, list[_re.Pattern[str]]] = {
    lang: [_re.compile(p, _re.IGNORECASE) for p in patterns]
    for lang, patterns in _LANGUAGE_MARKERS_STRONG.items()
}
_WEAK_COMPILED: dict[str, list[_re.Pattern[str]]] = {
    lang: [_re.compile(p, _re.IGNORECASE) for p in patterns]
    for lang, patterns in _LANGUAGE_MARKERS_WEAK.items()
}


def _detect_languages_by_markers(text: str, weak_threshold: int = 2) -> set[str]:
    """Detecte les langues fortement presentes dans le texte par marqueurs.

    Une langue est activee si :
        - au moins un marqueur STRONG correspond (mention non ambigue), OU
        - au moins `weak_threshold` marqueurs WEAK distincts correspondent.
    """
    detected: set[str] = set()
    for lang in set(_LANGUAGE_MARKERS_STRONG) | set(_LANGUAGE_MARKERS_WEAK):
        strong_hit = any(p.search(text) for p in _STRONG_COMPILED.get(lang, []))
        if strong_hit:
            detected.add(lang)
            continue
        weak_hits = sum(1 for p in _WEAK_COMPILED.get(lang, []) if p.search(text))
        if weak_hits >= weak_threshold:
            detected.add(lang)
    return detected


def _extract_denylist(config: Config, name: str) -> list[str]:
    """Extrait une liste depuis config.deny_lists['<name>'].

    Conventions YAML supportees :
        deny_lists:
          organizations:
            organizations: [Acme, Globex]    # cle imbriquee
        ou bien :
        deny_lists:
          organizations: [Acme, Globex]       # liste directe
    """
    block = config.deny_lists.get(name, {})
    if isinstance(block, list):
        return list(block)
    if isinstance(block, dict):
        if name in block and isinstance(block[name], list):
            return list(block[name])
        for v in block.values():
            if isinstance(v, list):
                return list(v)
    return []


def _extract_denylist_multilang(
    config: Config,
    name: str,
    languages: set[str],
) -> list[str]:
    """Extrait une deny list multilingue.

    Layout YAML attendu :
        deny_lists/
          <name>/
            fr.yaml -> { <name>: [...] }
            de.yaml -> { <name>: [...] }
            ...

    Apres chargement :
        config.deny_lists[name] = {fr: {name: [...]}, de: {name: [...]}, ...}

    Args:
        config: Config charge.
        name: nom du bloc (ex: 'places').
        languages: ensemble des langues actives ({'fr'}, {'fr','de'}...).

    Returns:
        Liste concatenee de toutes les entrees pour les langues actives.
        Si le bloc est en ancien format (liste plate), fallback vers _extract_denylist.
    """
    block = config.deny_lists.get(name, {})

    # Compat ancien format : liste directe ou dict {name: [...]}
    if isinstance(block, list):
        return list(block)
    if not isinstance(block, dict):
        return []

    is_multilingual = any(k in _SUPPORTED_LANGUAGES for k in block.keys())
    if not is_multilingual:
        return _extract_denylist(config, name)

    result: list[str] = []
    for lang in languages:
        sub = block.get(lang, {})
        if not isinstance(sub, dict):
            continue
        # Cle imbriquee : sub = {name: [...]}
        if name in sub and isinstance(sub[name], list):
            result.extend(sub[name])
            continue
        # Fallback : prendre la premiere liste
        for v in sub.values():
            if isinstance(v, list):
                result.extend(v)
                break
    return result


def _resolve_active_languages(
    detected: str | None,
    primary: str | None,
    text: str = "",
) -> set[str]:
    """Calcule l'ensemble des langues actives.

    Combine plusieurs signaux :
        1. langue detectee par lingua (best-guess majoritaire)
        2. langue principale du pipeline (langue du client)
        3. marqueurs linguistiques forts dans le texte (GmbH -> de,
           SARL -> fr, Lda. -> pt...). Pour les documents hybrides.

    Fallback : {'fr'} si rien ne s'applique.
    """
    candidates: set[str] = set()
    for lang in (detected, primary):
        if lang and lang in _SUPPORTED_LANGUAGES:
            candidates.add(lang)
    if text:
        candidates |= _detect_languages_by_markers(text)
    return candidates or {"fr"}


def detect(
    doc: NormalizedDocument,
    config: Config,
    *,
    use_gliner: bool = True,
    gliner_threshold: float = 0.4,
    primary_language: str | None = None,
) -> DetectedDocument:
    """Lance tous les recognizers configures et collecte les Spans.

    Args:
        doc: document normalise.
        config: configuration carnaval (deny lists, patterns, policies).
        use_gliner: True pour activer le moteur GLiNER (lent au premier appel).
        gliner_threshold: seuil de confiance GLiNER.
        primary_language: langue principale du pipeline (langue du client /
            langue par defaut). Combinee avec doc.language pour determiner les
            recognizers et deny lists actifs. Cas d'usage : un AR allemand
            (doc.language='de') mentionne quand meme l'adresse FR du client
            (primary_language='fr') -> on active les deux jeux.

    Returns:
        DetectedDocument avec les Spans bruts (non deduplique).
    """
    text = doc.text
    spans: list[Span] = []

    # Resoudre les langues actives (doc.language + primary_language + marqueurs textuels)
    active_languages = _resolve_active_languages(
        detected=doc.language,
        primary=primary_language,
        text=text,
    )

    # 1. Regex universels (toutes langues)
    for reco in _UNIVERSAL_REGEX_RECOGNIZERS:
        spans.extend(reco(text))

    # 1bis. ORG par suffixe juridique (multilingue : GmbH, AG, Ltd, SARL, Lda.)
    spans.extend(recognize_org_suffix(text))

    # 2. Regex multilingues (dispatch interne selon active_languages)
    spans.extend(recognize_address(text, active_languages))
    spans.extend(recognize_phone(text, active_languages))
    spans.extend(recognize_names(text, active_languages))

    # 3. Regex specifiques a une langue (pas encore de dispatcher car
    #    pas d'equivalent dans les autres langues).
    if "fr" in active_languages:
        for reco in _FR_SPECIFIC_REGEX_RECOGNIZERS:
            spans.extend(reco(text))

    # 4. Deny lists multilingues par nature (organisations, personnes - noms propres)
    singletons = _extract_denylist(config, "organization_singleton")
    if singletons:
        spans.extend(
            recognize_singleton(
                text,
                singletons,
                entity_type="ORG_SINGLETON",
                recognizer_name="OrgSingleton",
            )
        )
        spans.extend(
            recognize_singleton_loose(
                text,
                singletons,
                entity_type="ORG_SINGLETON",
                recognizer_name="OrgSingletonLoose",
            )
        )

    organizations = _extract_denylist(config, "organizations")
    if organizations:
        spans.extend(recognize_organizations(text, organizations))
        spans.extend(recognize_organizations_loose(text, organizations))

    people = _extract_denylist(config, "people")
    if people:
        spans.extend(recognize_people(text, people))

    # 5. Deny lists par langue (toponymes : listes specifiques par langue)
    places = _extract_denylist_multilang(config, "places", active_languages)
    if places:
        spans.extend(recognize_places(text, places))

    # 6. Recognizer contextuel multilingue : "Agence de X", "Office in Y", etc.
    spans.extend(recognize_contextual_location(text, active_languages))

    # 7. Dictionnaires bundled (cities + firstnames). Active si les fichiers
    #    assets/dictionaries/{cities,firstnames}/{lang}.txt existent.
    spans.extend(recognize_cities(text, active_languages))
    spans.extend(recognize_firstnames(text, active_languages))

    # 8. GLiNER (lent)
    if use_gliner:
        try:
            from carnaval.recognizers.ai.gliner_engine import (
                recognize_with_gliner,
            )

            spans.extend(recognize_with_gliner(text, threshold=gliner_threshold))
        except ImportError:
            pass  # gliner non installe, on ignore silencieusement

    return DetectedDocument(
        source_path=doc.source_path,
        text=text,
        language=doc.language,
        spans=tuple(spans),
        metadata=doc.metadata,
    )
