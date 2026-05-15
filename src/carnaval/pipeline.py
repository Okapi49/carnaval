# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Orchestrateur du pipeline carnaval.

Compose les etages S1 -> S6 en un appel unique. Ne contient PAS de logique
metier, juste l'enchainement.
"""

from __future__ import annotations

import time
from pathlib import Path

from carnaval.core.config_loader import Config, load_config
from carnaval.core.logger import get_logger
from carnaval.core.vault import Vault
from carnaval.stages.documents import MaskedDocument, WrittenOutput
from carnaval.stages.s1_intake import intake
from carnaval.stages.s2_preprocess import preprocess
from carnaval.stages.s3_detect import detect
from carnaval.stages.s4_resolve import resolve
from carnaval.stages.s5_mask import mask
from carnaval.stages.s6_output import output


def run_anonymization(
    input_path: Path | str,
    outbox_dir: Path | str,
    vault_password: str,
    *,
    profile: str | None = None,
    private_profile: str | None = None,
    use_gliner: bool = True,
    gliner_threshold: float = 0.4,
    cleanup_pipes: bool = False,
    language: str | None = None,
    repo_root: Path | str | None = None,
) -> tuple[MaskedDocument, WrittenOutput, Config]:
    """Pipeline complet S1 -> S6.

    Args:
        input_path: chemin du fichier .txt a anonymiser.
        outbox_dir: dossier de sortie (les sous-dossiers txt/json/... seront crees).
        vault_password: password du vault chiffre (min 16 chars).
        profile: nom du profil metier (ex: 'acknowledge').
        private_profile: nom du profil prive (sous profiles_private/).
        use_gliner: True pour activer la detection IA (lent au premier appel).
        gliner_threshold: seuil de confiance GLiNER.
        cleanup_pipes: True pour retirer les `|` parasites entre les mots.
        language: force la langue ('fr', 'en', 'de', 'ja'). Auto si None.
        repo_root: racine du repo (auto si None).

    Returns:
        (MaskedDocument, WrittenOutput, Config)
    """
    log = get_logger()
    t0 = time.time()

    # Chargement config
    config = load_config(
        profile=profile,
        private_profile=private_profile,
        repo_root=repo_root,
    )
    log.info("config_loaded", layers=config.layers)

    # S1 - Intake
    raw_doc = intake(input_path)
    log.info("s1_intake_done", size_bytes=raw_doc.length)

    # S2 - Preprocess
    norm_doc = preprocess(raw_doc, language=language, cleanup_pipes=cleanup_pipes)
    log.info("s2_preprocess_done", language=norm_doc.language)

    # S3 - Detect
    det_doc = detect(
        norm_doc,
        config,
        use_gliner=use_gliner,
        gliner_threshold=gliner_threshold,
    )
    log.info("s3_detect_done", raw_spans=len(det_doc.spans))

    # S4 - Resolve
    res_doc = resolve(det_doc)
    log.info(
        "s4_resolve_done",
        resolved_spans=len(res_doc.spans),
        dropped=len(det_doc.spans) - len(res_doc.spans),
    )

    # S5 - Mask
    vault = Vault(password=vault_password)
    masked_doc = mask(res_doc, vault)
    log.info(
        "s5_mask_done",
        anonymized_chars=len(masked_doc.anonymized_text),
        by_category=masked_doc.by_category,
    )

    # S6 - Output
    duration = time.time() - t0
    written = output(masked_doc, vault, outbox_dir, duration_seconds=duration)
    log.info(
        "s6_output_done",
        duration_seconds=round(duration, 2),
        outbox=str(outbox_dir),
    )

    return masked_doc, written, config
