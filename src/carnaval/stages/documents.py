# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Documents intermediaires echanges entre les etages.

Tous les documents sont immuables (frozen dataclass). Chaque etage produit
un nouveau document a partir du document d'entree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from carnaval.core.span import Span


@dataclass(frozen=True)
class RawDocument:
    """Document brut tel que lu depuis le disque (sortie S1)."""

    source_path: Path
    text: str
    encoding: str = "utf-8"
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @property
    def length(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class NormalizedDocument:
    """Document apres preprocessing (sortie S2).

    Le texte peut avoir ete normalise (espaces, parasites optionnels supprimes).
    La langue detectee est attachee.
    """

    source_path: Path
    text: str
    language: str  # 'fr', 'en', 'de', 'ja', 'unknown'
    encoding: str = "utf-8"
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class DetectedDocument:
    """Document avec les Spans bruts (sortie S3)."""

    source_path: Path
    text: str
    language: str
    spans: tuple[Span, ...]  # tuple pour immutabilite
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class ResolvedDocument:
    """Document apres dedup/resolution des conflits (sortie S4)."""

    source_path: Path
    text: str
    language: str
    spans: tuple[Span, ...]  # spans ordonnes, non chevauchants
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class MaskedDocument:
    """Document apres masquage (sortie S5).

    Contient le texte anonymise et les Spans enrichis du placeholder attribue.
    """

    source_path: Path
    original_text: str  # texte d'entree
    anonymized_text: str  # texte avec placeholders
    language: str
    spans: tuple[Span, ...]  # avec metadata["placeholder"] alimente
    by_category: dict[str, int] = field(default_factory=dict, compare=False, hash=False)
    metadata: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class WrittenOutput:
    """Inventaire des fichiers ecrits (sortie S6)."""

    txt_path: Path
    json_path: Path
    jsonl_path: Path
    xml_path: Path
    conll_path: Path
    html_path: Path
    vault_path: Path
    meta_path: Path
