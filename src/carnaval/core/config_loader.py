# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Chargement de la configuration en couches.

Strategie de merge :
    1. base    -> config/pipeline.yaml + sous-fichiers config/*/*.yaml
    2. profil  -> profiles/<type>/profile.yaml + sous-fichiers
    3. prive   -> profiles_private/<custom>/profile.yaml + sous-fichiers (optionnel)

Les listes sont CONCATENEES (deny_lists, allow_lists), les dicts sont MERGES
profondement. Les scalaires de la couche superieure ecrasent la couche
inferieure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Config:
    """Configuration applicative resolue par couches."""

    raw: dict[str, Any] = field(default_factory=dict)
    layers: list[str] = field(default_factory=list)  # noms des couches mergees

    # Acces rapides typiques
    @property
    def pipeline(self) -> dict[str, Any]:
        return self.raw.get("pipeline", {})

    @property
    def patterns(self) -> dict[str, Any]:
        return self.raw.get("patterns", {})

    @property
    def deny_lists(self) -> dict[str, list[str]]:
        return self.raw.get("deny_lists", {})

    @property
    def allow_lists(self) -> dict[str, list[str]]:
        return self.raw.get("allow_lists", {})

    @property
    def policies(self) -> dict[str, Any]:
        return self.raw.get("policies", {})

    @property
    def ai_models(self) -> dict[str, Any]:
        return self.raw.get("ai_models", {})

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Acces dotted-path : cfg.get('policies.priority_rules.DenylistRecognizer')."""
        parts = dotted_key.split(".")
        node: Any = self.raw
        for p in parts:
            if not isinstance(node, dict) or p not in node:
                return default
            node = node[p]
        return node


# ----------------------------------------------------------------------
# Merge utilities
# ----------------------------------------------------------------------


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge profond.

    Regles :
    - dict + dict  -> merge cle a cle (recursif)
    - list + list  -> concatenation (sans dedoublonnage : c'est le role du caller)
    - scalaire + scalaire -> overlay gagne
    - types mixtes -> overlay gagne (warning implicite)
    """
    result = dict(base)
    for key, val in overlay.items():
        if key in result:
            existing = result[key]
            if isinstance(existing, dict) and isinstance(val, dict):
                result[key] = _deep_merge(existing, val)
            elif isinstance(existing, list) and isinstance(val, list):
                result[key] = existing + val
            else:
                result[key] = val
        else:
            result[key] = val
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    """Charge un YAML, renvoie {} si fichier vide."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _load_directory_layer(dir_path: Path) -> dict[str, Any]:
    """Charge tous les YAML d'un dossier en un dict structure par sous-dossier.

    Pour un layout :
        layer/
            pipeline.yaml
            patterns/
                fiscal_fr.yaml      -> patterns.fiscal_fr.*
            deny_lists/
                organizations.yaml  -> deny_lists.organizations.*

    Le contenu du fichier remplace le sous-namespace correspondant.
    """
    if not dir_path.exists() or not dir_path.is_dir():
        return {}

    out: dict[str, Any] = {}

    # 1. fichiers .yaml directement a la racine de la couche (ex: pipeline.yaml, ai_models.yaml)
    for yml in sorted(dir_path.glob("*.yaml")):
        key = yml.stem
        data = _load_yaml(yml)
        # Si le YAML contient une cle racine du meme nom, on la fusionne
        # Sinon on stocke le contenu sous la cle key.
        if key in data and isinstance(data[key], dict):
            out[key] = _deep_merge(out.get(key, {}), data[key])
        else:
            out[key] = (
                _deep_merge(out.get(key, {}), data) if isinstance(data, dict) else data
            )

    # 2. sous-dossiers : patterns/, deny_lists/, allow_lists/, policies/
    #    + recursion limitee pour places/{fr,de,...}.yaml
    for sub in sorted(p for p in dir_path.iterdir() if p.is_dir()):
        sub_content: dict[str, Any] = {}
        # 2a. fichiers .yaml directs (ex: deny_lists/organizations.yaml)
        for yml in sorted(sub.glob("*.yaml")):
            sub_content[yml.stem] = _load_yaml(yml)
        # 2b. sous-sous-dossiers (ex: deny_lists/places/fr.yaml)
        #     -> deny_lists.places = {fr: [...], de: [...], ...}
        for subsub in sorted(p for p in sub.iterdir() if p.is_dir()):
            lang_dict: dict[str, Any] = {}
            for yml in sorted(subsub.glob("*.yaml")):
                lang_dict[yml.stem] = _load_yaml(yml)
            if lang_dict:
                sub_content[subsub.name] = _deep_merge(
                    sub_content.get(subsub.name, {}), lang_dict
                )
        if sub_content:
            out[sub.name] = _deep_merge(out.get(sub.name, {}), sub_content)

    return out


# ----------------------------------------------------------------------
# API publique
# ----------------------------------------------------------------------


def load_config(
    base_dir: Path | str | None = None,
    profile: str | None = None,
    private_profile: str | None = None,
    repo_root: Path | str | None = None,
) -> Config:
    """Charge la config en cascade base -> profile -> private_profile.

    Args:
        base_dir: chemin du dossier `config/` (defaut : <repo>/config).
        profile: nom du profil public a appliquer (ex: 'acknowledge').
        private_profile: nom du profil prive (sous profiles_private/).
        repo_root: racine du repo (auto-detection par defaut).

    Returns:
        Config resolu.
    """
    if repo_root is None:
        # racine = parent de src/carnaval/core/
        repo_root = Path(__file__).resolve().parents[3]
    repo_root = Path(repo_root)

    base_path = Path(base_dir) if base_dir else repo_root / "config"

    layers_loaded: list[str] = []
    merged: dict[str, Any] = {}

    # Couche 1 : base
    base_layer = _load_directory_layer(base_path)
    if base_layer:
        merged = _deep_merge(merged, base_layer)
        layers_loaded.append(f"base:{base_path}")

    # Couche 2 : profile public
    if profile:
        prof_path = repo_root / "profiles" / profile
        prof_layer = _load_directory_layer(prof_path)
        if not prof_layer:
            raise FileNotFoundError(f"Profil introuvable : {prof_path}")
        merged = _deep_merge(merged, prof_layer)
        layers_loaded.append(f"profile:{profile}")

    # Couche 3 : profil prive (optionnel)
    if private_profile:
        priv_path = repo_root / "profiles_private" / private_profile
        priv_layer = _load_directory_layer(priv_path)
        if not priv_layer:
            raise FileNotFoundError(f"Profil prive introuvable : {priv_path}")
        merged = _deep_merge(merged, priv_layer)
        layers_loaded.append(f"private:{private_profile}")

    return Config(raw=merged, layers=layers_loaded)
