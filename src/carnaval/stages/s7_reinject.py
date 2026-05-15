# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Etage 7 - Reinject : restauration des valeurs originales dans JSON/XML.

Etage INVERSE du pipeline. Le LLM cloud retourne une structure (JSON ou XML)
contenant des placeholders `[TYPE_n]` ou `[TYPE]`. Cette etape parcourt
recursivement la structure et restitue les valeurs reelles depuis le Vault.

Entrees supportees :
    - dict / list / str (objets Python deja parses)
    - str JSON (auto-detection si commence par '{' ou '[')
    - str XML  (auto-detection si commence par '<')
    - Path vers un fichier .json ou .xml
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from carnaval.core.vault import Vault

# Pattern qui matche tout placeholder produit par S5 :
#   [PERSON_1], [EMAIL_42], [ORG], [VAT_3], etc.
PLACEHOLDER_PATTERN = re.compile(r"\[([A-Z]+(?:_\d+)?)\]")


# Liste des prefixes de placeholders qu'on accepte de matcher bare.
_BARE_PLACEHOLDER_TYPES = (
    r"ORG|"
    r"SUPPLIER_\d+|PERSON_\d+|EMAIL_\d+|PHONE_\d+|ADDR_\d+|LOCATION_\d+|"
    r"SIREN_\d+|SIRET_\d+|VAT_\d+|IBAN_\d+|BIC_\d+|URL_\d+|ORG_\d+|NRP_\d+"
)

# Pattern : placeholder sans crochets, mais SEUL dans la chaine (anchors).
PLACEHOLDER_PATTERN_BARE = re.compile(rf"^({_BARE_PLACEHOLDER_TYPES})$")

# Pattern : placeholder sans crochets, INLINE (au milieu d'une phrase).
# Certains LLMs droppent les crochets meme quand le placeholder est inclus
# dans une phrase ("Rendu a ADDR_2", "2-ADDR_4 communication interface").
# Word boundaries strictes pour ne pas matcher de sous-chaines.
PLACEHOLDER_PATTERN_BARE_INLINE = re.compile(rf"\b({_BARE_PLACEHOLDER_TYPES})\b")


def _restore_in_string(text: str, vault: Vault) -> str:
    """Remplace tous les placeholders d'une chaine par leur valeur originale.

    Gere trois formats :
    - `[TYPE_n]` standard
    - `TYPE_n`   bare-only (chaine = placeholder unique)
    - `... TYPE_n ...` bare-inline (placeholder dans une phrase)
    """

    def repl_standard(match: re.Match) -> str:
        ph = match.group(0)
        original = vault.get_original(ph)
        return original if original is not None else ph

    out = PLACEHOLDER_PATTERN.sub(repl_standard, text)

    # Fallback 1 : la valeur COMPLETE est un placeholder bare ("ORG_1")
    if out and PLACEHOLDER_PATTERN_BARE.match(out):
        wrapped = f"[{out}]"
        original = vault.get_original(wrapped)
        if original is not None:
            return original

    # Fallback 2 : placeholder bare au milieu d'une phrase
    # ("Rendu a ADDR_2", "2-ADDR_4 communication...")
    def repl_bare_inline(match: re.Match) -> str:
        ph_bare = match.group(0)
        wrapped = f"[{ph_bare}]"
        original = vault.get_original(wrapped)
        return original if original is not None else ph_bare

    out = PLACEHOLDER_PATTERN_BARE_INLINE.sub(repl_bare_inline, out)

    return out


# ----------------------------------------------------------------------
# JSON
# ----------------------------------------------------------------------


def reinject_json_data(data: Any, vault: Vault) -> Any:
    """Parcours recursif d'une structure JSON-like et restitution.

    Args:
        data: dict, list, str, ou scalaire.
        vault: Vault charge.

    Returns:
        Structure de meme forme, avec les placeholders remplaces.
    """
    if isinstance(data, str):
        return _restore_in_string(data, vault)
    if isinstance(data, dict):
        return {k: reinject_json_data(v, vault) for k, v in data.items()}
    if isinstance(data, list):
        return [reinject_json_data(item, vault) for item in data]
    if isinstance(data, tuple):
        return tuple(reinject_json_data(item, vault) for item in data)
    return data


def reinject_json_string(json_str: str, vault: Vault) -> str:
    """Parse un JSON, restaure, re-serialise. Conserve l'indentation 2."""
    parsed = json.loads(json_str)
    restored = reinject_json_data(parsed, vault)
    return json.dumps(restored, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------
# XML
# ----------------------------------------------------------------------


def _restore_in_element(elem: ET.Element, vault: Vault) -> None:
    """Restitution recursive d'un noeud XML (mute l'arbre)."""
    if elem.text:
        elem.text = _restore_in_string(elem.text, vault)
    if elem.tail:
        elem.tail = _restore_in_string(elem.tail, vault)
    # Attributs
    for attr_key, attr_val in list(elem.attrib.items()):
        elem.attrib[attr_key] = _restore_in_string(attr_val, vault)
    # Enfants
    for child in elem:
        _restore_in_element(child, vault)


def reinject_xml_string(xml_str: str, vault: Vault) -> str:
    """Parse un XML, restaure, re-serialise."""
    root = ET.fromstring(xml_str)
    _restore_in_element(root, vault)
    return ET.tostring(root, encoding="unicode")


# ----------------------------------------------------------------------
# Auto-detection + entry point
# ----------------------------------------------------------------------


def reinject_file(input_path: Path | str, vault: Vault) -> str:
    """Auto-detecte JSON vs XML d'apres l'extension OU le contenu.

    Args:
        input_path: fichier .json ou .xml.
        vault: Vault charge.

    Returns:
        Contenu restitue, sous forme de chaine.
    """
    p = Path(input_path)
    content = p.read_text(encoding="utf-8")
    return reinject_string(content, vault)


def reinject_string(content: str, vault: Vault) -> str:
    """Restitue dans une chaine en auto-detectant JSON vs XML."""
    stripped = content.lstrip()
    if not stripped:
        return content
    first = stripped[0]
    if first in ("{", "["):
        return reinject_json_string(content, vault)
    if first == "<":
        return reinject_xml_string(content, vault)
    # Fallback : traiter comme texte brut
    return _restore_in_string(content, vault)
