# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Etage 1 - Intake : lecture du fichier source.

Responsabilites :
- Verifier l'existence du fichier
- Lire le contenu en UTF-8 (fallback latin-1 si echec)
- Capturer metadata : taille, encodage, mtime
- Refuser fichiers vides ou trop gros (configurable)

Entree : Path
Sortie : RawDocument
"""

from __future__ import annotations

from pathlib import Path

from carnaval.stages.documents import RawDocument


class IntakeError(Exception):
    """Erreur d'entree (fichier introuvable, illisible, trop gros, ...)."""


def intake(
    path: Path | str,
    max_size_bytes: int = 50 * 1024 * 1024,  # 50 Mo
) -> RawDocument:
    """Lit un fichier .txt en RawDocument.

    Args:
        path: chemin du fichier.
        max_size_bytes: taille max acceptee.

    Returns:
        RawDocument peuple.

    Raises:
        IntakeError: si le fichier est absent, vide, trop gros ou illisible.
    """
    p = Path(path)
    if not p.exists():
        raise IntakeError(f"Fichier introuvable : {p}")
    if not p.is_file():
        raise IntakeError(f"Pas un fichier : {p}")

    size = p.stat().st_size
    if size == 0:
        raise IntakeError(f"Fichier vide : {p}")
    if size > max_size_bytes:
        raise IntakeError(f"Fichier trop gros : {size} bytes > {max_size_bytes}")

    # Lecture avec fallback d'encodage
    encoding_used = "utf-8"
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        encoding_used = "latin-1"
        text = p.read_text(encoding="latin-1")

    return RawDocument(
        source_path=p,
        text=text,
        encoding=encoding_used,
        metadata={
            "size_bytes": size,
            "mtime": p.stat().st_mtime,
            "filename": p.name,
        },
    )
