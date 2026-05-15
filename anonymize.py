#!/usr/bin/env python3
# Copyright 2026 Patrice AUBERT
# SPDX-License-Identifier: Apache-2.0
"""Lanceur local de la CLI d'anonymisation carnaval.

Permet d'executer l'outil sans installation (`python anonymize.py ...`).
La logique reelle vit dans `carnaval.cli.anonymize`. Une fois le paquet
installe, prefere la commande `carnaval-anonymize`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permettre l'execution sans installation : ajout de src/ au path.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from carnaval.cli.anonymize import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
