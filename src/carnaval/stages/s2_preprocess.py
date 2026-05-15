# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Etage 2 - Preprocess : detection langue + normalisation legere.

Responsabilites :
- Detecter la langue
- Normalisation minimale (espaces multiples, BOM)
- (Optionnel, desactive par defaut) nettoyage des barres verticales parasites
  qui apparaissent dans certains extracteurs PDF

Entree : RawDocument
Sortie : NormalizedDocument
"""

from __future__ import annotations

import re

from carnaval.core.language_detector import detect_language
from carnaval.stages.documents import NormalizedDocument, RawDocument

_BOM_PATTERN = re.compile(r"^﻿")
_MULTI_SPACES_PATTERN = re.compile(r"[ \t]{2,}")
# Barres verticales parasites au milieu des mots ("Chi | mieBERTAUX")
# On enleve "X | Y" -> "XY" ou "X Y" -> "XY" selon le contexte. Conservateur :
# on enleve seulement "alpha | alpha" colle a des lettres.
_PIPE_NOISE_PATTERN = re.compile(r"([A-Za-z]) \| ([A-Za-z])")


def preprocess(
    doc: RawDocument,
    *,
    language: str | None = None,
    normalize_spaces: bool = True,
    cleanup_pipes: bool = False,
) -> NormalizedDocument:
    """Prepare le texte pour la detection.

    Args:
        doc: RawDocument d'entree.
        language: force une langue ('fr', 'en', 'de', 'ja'). Auto si None.
        normalize_spaces: True -> compacte les espaces multiples.
        cleanup_pipes: True -> retire les `|` parasites style "Chi | mie".
            DEFAUT : False, car risque de toucher des contenus metier.

    Returns:
        NormalizedDocument.
    """
    text = doc.text

    # 1. BOM
    text = _BOM_PATTERN.sub("", text)

    # 2. Pipes parasites (optionnel)
    if cleanup_pipes:
        # Repete : "Chi | mie | BERTAUX" -> "ChimieBERTAUX"
        prev = None
        while prev != text:
            prev = text
            text = _PIPE_NOISE_PATTERN.sub(r"\1\2", text)

    # 3. Espaces multiples
    if normalize_spaces:
        text = _MULTI_SPACES_PATTERN.sub(" ", text)

    # 4. Detection langue
    lang = language or detect_language(text)

    return NormalizedDocument(
        source_path=doc.source_path,
        text=text,
        language=lang,
        encoding=doc.encoding,
        metadata={
            **doc.metadata,
            "normalize_spaces": normalize_spaces,
            "cleanup_pipes": cleanup_pipes,
        },
    )
