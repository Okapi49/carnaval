"""Tests d'integration sur les profils metier livres.

Verifie que chaque profil livre sait anonymiser sa fixture associee.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from carnaval.pipeline import run_anonymization

VALID_PWD = "test_password_long_enough_chars"
_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def outbox_dir(tmp_path: Path) -> Path:
    box = tmp_path / "outbox"
    for sub in ("txt", "json", "jsonl", "xml", "conll", "html", "vault", "meta"):
        (box / sub).mkdir(parents=True)
    return box


class TestAcknowledgeProfile:
    def test_masks_organization(self, outbox_dir: Path):
        fixture = (
            _REPO_ROOT
            / "profiles"
            / "acknowledge"
            / "fixtures"
            / "sample_ack_globex.txt"
        )
        masked, _, _ = run_anonymization(
            input_path=fixture,
            outbox_dir=outbox_dir,
            vault_password=VALID_PWD,
            profile="acknowledge",
            use_gliner=False,
            repo_root=_REPO_ROOT,
        )
        # Globex doit etre masque (deny list)
        assert "Globex Inc." not in masked.anonymized_text
        # Acme Corp doit etre masque (singleton)
        assert "Acme Corp" not in masked.anonymized_text
        # IBAN, TVA, telephone : masques par regex
        assert "FR7617629000010011369280060" not in masked.anonymized_text
        assert "FR66529268393" not in masked.anonymized_text
        # Reference produit preservee
        assert "KHZ-DA-032-0050-M" in masked.anonymized_text
        # Numero de commande preserve
        assert "ACM/4700001234" in masked.anonymized_text


class TestInvoiceProfile:
    def test_masks_emitter(self, outbox_dir: Path):
        fixture = (
            _REPO_ROOT
            / "profiles"
            / "invoice"
            / "fixtures"
            / "sample_invoice_initech.txt"
        )
        masked, _, _ = run_anonymization(
            input_path=fixture,
            outbox_dir=outbox_dir,
            vault_password=VALID_PWD,
            profile="invoice",
            use_gliner=False,
            repo_root=_REPO_ROOT,
        )
        # Initech doit etre masque
        assert "Initech" not in masked.anonymized_text
        # Acme Corp doit etre masque
        assert "Acme Corp" not in masked.anonymized_text
        # IBAN/BIC masques
        assert "FR1420041010050500013M02606" not in masked.anonymized_text
        # Numero facture preserve
        assert "FAC-2024-0892" in masked.anonymized_text
        # Montants preserves
        assert (
            "3000,00" in masked.anonymized_text or "3000.00" in masked.anonymized_text
        )


class TestEmailProfile:
    def test_masks_contacts(self, outbox_dir: Path):
        fixture = (
            _REPO_ROOT / "profiles" / "email" / "fixtures" / "sample_email_vandelay.txt"
        )
        masked, _, _ = run_anonymization(
            input_path=fixture,
            outbox_dir=outbox_dir,
            vault_password=VALID_PWD,
            profile="email",
            use_gliner=False,
            repo_root=_REPO_ROOT,
        )
        # Vandelay et emails masques
        assert "Vandelay" not in masked.anonymized_text
        assert "david.davis@vandelay.example" not in masked.anonymized_text
        assert "carol.carter@acme.example" not in masked.anonymized_text
        # Telephones masques
        assert "04.91.23.45.67" not in masked.anonymized_text
        # Reference commande preservee (champ metier)
        assert "ACM/2024/0438" in masked.anonymized_text
        # References produit preservees
        assert "KHZ-DA-032-0050-M" in masked.anonymized_text
