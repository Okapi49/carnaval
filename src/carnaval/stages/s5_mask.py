# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Etage 5 - Mask : application des placeholders + alimentation du vault.

Responsabilites :
- Attribuer un placeholder a chaque Span
- Garantir la coherence : la meme valeur originale -> meme placeholder
- Types singleton (`ORG_SINGLETON`) -> placeholder sans index
- Autres types -> placeholder indexe `[TYPE_n]`
- Construire le texte anonymise (substitution from-end-to-start pour ne
  pas casser les offsets)

Entree : ResolvedDocument + Vault
Sortie : MaskedDocument
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from typing import Any

from carnaval.core.span import Span
from carnaval.core.vault import Vault
from carnaval.stages.documents import MaskedDocument, ResolvedDocument

# Types pour lesquels on emet un placeholder sans index (singleton).
DEFAULT_SINGLETON_TYPES = frozenset({"ORG_SINGLETON"})


# Mapping entity_type -> prefixe utilise dans le placeholder.
# Le suffixe `_n` est ajoute pour les types non-singleton.
DEFAULT_PLACEHOLDER_PREFIX = {
    "ORG_SINGLETON": "ORG",
    "ORGANIZATION": "ORG",
    "PERSON": "PERSON",
    "EMAIL": "EMAIL",
    "PHONE": "PHONE",
    "LOCATION": "ADDR",
    "ADDRESS": "ADDR",
    "SIRET": "SIRET",
    "SIREN": "SIREN",
    "VAT": "VAT",
    "IBAN": "IBAN",
    "BIC": "BIC",
    "URL": "URL",
    "NRP": "NRP",
}


class PlaceholderAllocator:
    """Distribue les placeholders en garantissant la coherence via Vault."""

    def __init__(
        self,
        vault: Vault,
        prefix_map: dict[str, str] | None = None,
        singleton_types: frozenset[str] | None = None,
    ):
        self._vault = vault
        self._prefix_map = prefix_map or DEFAULT_PLACEHOLDER_PREFIX
        self._singletons = singleton_types or DEFAULT_SINGLETON_TYPES
        self._counters: dict[str, int] = {}

    def allocate(self, entity_type: str, original: str) -> str:
        """Renvoie le placeholder pour une valeur originale.

        Si la valeur est deja dans le vault, on renvoie le placeholder existant
        (assure la coherence). Sinon on en alloue un nouveau et on l'enregistre.
        """
        existing = self._vault.get_placeholder(original)
        if existing:
            return existing

        prefix = self._prefix_map.get(entity_type, entity_type)
        if entity_type in self._singletons:
            placeholder = f"[{prefix}]"
        else:
            self._counters[prefix] = self._counters.get(prefix, 0) + 1
            placeholder = f"[{prefix}_{self._counters[prefix]}]"

        self._vault.store(placeholder, original)
        return placeholder


def mask(
    doc: ResolvedDocument,
    vault: Vault,
    *,
    prefix_map: dict[str, str] | None = None,
    singleton_types: frozenset[str] | None = None,
) -> MaskedDocument:
    """Applique les placeholders au texte resolu.

    Strategie de substitution : on remplace les spans **de droite a gauche**
    pour ne pas invalider les offsets des spans suivants.

    Args:
        doc: ResolvedDocument (spans non chevauchants, ordonnes).
        vault: Vault qui sera alimente.
        prefix_map: override du mapping entity_type -> prefixe.
        singleton_types: override de l'ensemble des types singleton.

    Returns:
        MaskedDocument avec text anonymise et spans enrichis de placeholder.
    """
    allocator = PlaceholderAllocator(
        vault=vault,
        prefix_map=prefix_map,
        singleton_types=singleton_types,
    )

    # Construire le placeholder pour chaque span (ordre des positions)
    enriched_spans: list[Span] = []
    for s in doc.spans:
        ph = allocator.allocate(s.entity_type, s.text)
        new_meta: dict[str, Any] = {**s.metadata, "placeholder": ph}
        enriched_spans.append(dc_replace(s, metadata=new_meta))

    # Substitution de droite a gauche
    text = doc.text
    for s in sorted(enriched_spans, key=lambda x: x.start, reverse=True):
        ph = s.metadata["placeholder"]
        text = text[: s.start] + ph + text[s.end :]

    by_category: dict[str, int] = {}
    for s in enriched_spans:
        by_category[s.entity_type] = by_category.get(s.entity_type, 0) + 1

    return MaskedDocument(
        source_path=doc.source_path,
        original_text=doc.text,
        anonymized_text=text,
        language=doc.language,
        spans=tuple(enriched_spans),
        by_category=by_category,
        metadata=doc.metadata,
    )
