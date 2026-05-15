# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Moteur GLiNER : NER zero-shot pour les entites PII.

Wrapper minimaliste autour de la lib `gliner`. Pas de Presidio entre les deux.

Premier appel : telechargement du modele depuis HuggingFace (~500 Mo).
Appels suivants : modele cache en RAM (~1 Go).
"""

from __future__ import annotations

from typing import Optional

from carnaval.core.span import Span

DEFAULT_MODEL = "urchade/gliner_multi_pii-v1"

# Labels par defaut a chercher (le modele est zero-shot, on lui passe les
# noms d'entites qu'on veut detecter).
DEFAULT_LABELS = (
    "person",
    "email",
    "phone number",
    "address",
    "street address",
    "postal code",
    "city",
    "organization",
    "company",
)

# Mapping labels GLiNER -> entity_type carnaval
LABEL_TO_ENTITY_TYPE = {
    "person": "PERSON",
    "email": "EMAIL",
    "phone number": "PHONE",
    "address": "LOCATION",
    "street address": "LOCATION",
    "postal code": "LOCATION",
    "city": "LOCATION",
    "organization": "ORGANIZATION",
    "company": "ORGANIZATION",
}


_MODEL: Optional[object] = None


def _load_model(model_name: str = DEFAULT_MODEL):
    """Charge le modele paresseusement (premier appel = telechargement)."""
    global _MODEL
    if _MODEL is None:
        try:
            from gliner import GLiNER  # type: ignore
        except ImportError as e:
            raise ImportError(
                "Le package 'gliner' n'est pas installe. " "Lance : pip install gliner"
            ) from e
        _MODEL = GLiNER.from_pretrained(model_name)
    return _MODEL


def is_available() -> bool:
    """Verifie si la lib gliner est installable. N'instancie pas le modele."""
    try:
        import gliner  # noqa: F401

        return True
    except ImportError:
        return False


def recognize_with_gliner(
    text: str,
    labels: tuple[str, ...] | list[str] = DEFAULT_LABELS,
    threshold: float = 0.4,
    model_name: str = DEFAULT_MODEL,
) -> list[Span]:
    """Lance GLiNER et convertit la sortie en Spans carnaval.

    Args:
        text: texte source.
        labels: noms des entites a chercher (zero-shot, modifiable a la volee).
        threshold: seuil de confiance minimal [0,1].
        model_name: nom du modele HuggingFace.

    Returns:
        Liste de Span (eventuellement vide).
    """
    if not text or not text.strip():
        return []

    model = _load_model(model_name)
    raw_entities = model.predict_entities(text, list(labels), threshold=threshold)

    spans: list[Span] = []
    for ent in raw_entities:
        label = ent["label"]
        entity_type = LABEL_TO_ENTITY_TYPE.get(label, label.upper())
        spans.append(
            Span(
                start=int(ent["start"]),
                end=int(ent["end"]),
                entity_type=entity_type,
                text=str(ent["text"]),
                score=float(ent["score"]),
                recognizer="GLiNER",
                metadata={"gliner_label": label},
            )
        )
    return spans
