# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Etage 4 - Resolve : deduplication et resolution des conflits de spans.

Responsabilites :
- Resoudre les chevauchements de spans (plusieurs recognizers ont matche la
  meme zone avec des types differents)
- Strategie : favoriser le span le plus englobant (plus long), puis le score,
  puis la priorite du recognizer

Entree : DetectedDocument
Sortie : ResolvedDocument
"""

from __future__ import annotations

from carnaval.core.span import Span
from carnaval.stages.documents import DetectedDocument, ResolvedDocument

# Priorite par recognizer. Plus haute = gagne en cas d'egalite de
# longueur et de score (cas rare).
DEFAULT_RECOGNIZER_PRIORITY = {
    "OrgSingleton": 100,
    "OrgSingletonLoose": 85,
    "OrganizationsDenyList": 90,
    "PeopleDenyList": 90,
    "OrganizationsLooseDenyList": 70,
    "HeaderSourceRegex": 95,
    "EmailRegex": 85,
    "IbanRegex": 85,
    "VatFrRegex": 85,
    "SiretRegex": 85,
    "SirenRegex": 75,
    "PhoneFrRegex": 80,
    "BicRegex": 60,
    "PostalCityFrRegex": 75,
    "ZoneFrRegex": 75,
    "StreetFrRegex": 70,
    "BpRegex": 75,
    # DE/AT/CH
    "PostalCityDeRegex": 75,
    "StreetDeRegex": 70,
    "PostfachDeRegex": 75,
    # EN (UK, US, CA, AU)
    "PostcodeUkRegex": 80,
    "ZipUsRegex": 70,
    "PostcodeCaRegex": 80,
    "StreetEnRegex": 70,
    "PoBoxRegex": 75,
    # ES
    "PostalCityEsRegex": 75,
    "StreetEsRegex": 70,
    "ApartadoEsRegex": 75,
    # IT
    "PostalCityItRegex": 75,
    "StreetItRegex": 70,
    "CasellaPostaleItRegex": 75,
    # Telephones par langue
    "PhoneDeRegex": 80,
    "PhoneUkRegex": 80,
    "PhoneUsRegex": 80,
    "PhoneOceRegex": 80,
    "PhoneEsRegex": 80,
    "PhoneLatamRegex": 80,
    "PhoneItRegex": 75,
    # Titres / civilites par langue
    "TitleDeRegex": 80,
    "ContextualPersonDeRegex": 75,
    "TitleEnRegex": 80,
    "ContextualPersonEnRegex": 75,
    "TitleEsRegex": 80,
    "ContextualPersonEsRegex": 75,
    "TitleItRegex": 80,
    "ContextualPersonItRegex": 75,
    # Dictionnaires bundled GeoNames / INSEE
    "CityDict_fr": 65,
    "CityDict_de": 65,
    "CityDict_en": 65,
    "CityDict_es": 65,
    "CityDict_it": 65,
    "FirstnameDict_fr": 55,
    "FirstnameDict_de": 55,
    "FirstnameDict_en": 55,
    "FirstnameDict_es": 55,
    "FirstnameDict_it": 55,
    "FirstnameDict_pt": 55,
    "CityDict_pt": 65,
    # PT regex
    "PostalCityPtRegex": 75,
    "CepBrRegex": 75,
    "StreetPtRegex": 70,
    "ApartadoPtRegex": 75,
    "PhonePtRegex": 75,
    "PhoneBrRegex": 75,
    "TitlePtRegex": 80,
    "ContextualPersonPtRegex": 75,
    # ORG par suffixe juridique
    "OrgSuffixRegex": 88,
    "NameCommaRegex": 75,
    "CiviliteRegex": 75,
    "PrenomNomRegex": 65,
    "PrenomNomGluedRegex": 40,
    "ContextualPersonRegex": 75,
    "StreetGluedRegex": 60,
    "PlacesDenyList": 92,
    "ContextualLocationRegex": 78,
    "UrlRegex": 50,
    "GLiNER": 30,
}


def _span_priority(span: Span, priority_map: dict[str, int]) -> int:
    return priority_map.get(span.recognizer, 0)


def resolve(
    doc: DetectedDocument,
    priority_map: dict[str, int] | None = None,
) -> ResolvedDocument:
    """Deduplique les Spans qui se chevauchent.

    Critere de tri (decroissant pour l'acceptation) :
        1. Longueur (le plus englobant gagne)
        2. Score
        3. Priorite du recognizer
        4. Position (gauche d'abord)
    """
    pmap = priority_map if priority_map is not None else DEFAULT_RECOGNIZER_PRIORITY

    # Trier pour l'acceptation
    sorted_spans = sorted(
        doc.spans,
        key=lambda s: (-s.length, -s.score, -_span_priority(s, pmap), s.start),
    )

    accepted: list[Span] = []
    for s in sorted_spans:
        if any(s.overlaps(a) for a in accepted):
            continue
        accepted.append(s)

    # Reordonner par position (debut croissant) pour la suite du pipeline
    accepted.sort(key=lambda s: s.start)

    return ResolvedDocument(
        source_path=doc.source_path,
        text=doc.text,
        language=doc.language,
        spans=tuple(accepted),
        metadata={
            **doc.metadata,
            "raw_spans_count": len(doc.spans),
            "resolved_spans_count": len(accepted),
        },
    )
