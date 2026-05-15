# Quickstart

Your first anonymization in five minutes. This page assumes Carnaval is already
installed - see [Installation](Installation.md) if not.

## The two-step workflow

```
inbox/doc.txt ──▶  anonymize.py  ──▶  outbox/...  ──▶  Cloud LLM  ──▶  response.json
                                                                            │
                                       reinject.py  ◀───────────────────────┘
                                            │
                                            ▼
                                    response_final.json
```

1. **Anonymize** a document before sending it to the LLM.
2. **Re-inject** the real values into the LLM's JSON / XML answer.

## 1. Anonymize from the command line

A sample fixture ships with the repository:

```bash
python anonymize.py profiles/acknowledge/fixtures/sample_ack_globex.txt \
    --profile acknowledge
```

Carnaval prints a summary and writes **8 output files** under `outbox/`:

```
============================================================
  carnaval - sample_ack_globex.txt
============================================================
  Langue          : fr
  Spans masques   : 7
  Par categorie   :
    EMAIL              : 1
    ORGANIZATION       : 2
    PERSON             : 2
    PHONE              : 1
    LOCATION           : 1
  Fichiers produits :
    TXT             : outbox/txt/sample_ack_globex_anonymise.txt
    JSON            : outbox/json/sample_ack_globex_anonymise.json
    JSONL           : outbox/jsonl/sample_ack_globex_entities.jsonl
    XML             : outbox/xml/sample_ack_globex_anonymise.xml
    CoNLL           : outbox/conll/sample_ack_globex_anonymise.conll
    HTML            : outbox/html/sample_ack_globex_anonymise.html
    Vault chiffre   : outbox/vault/sample_ack_globex_vault.enc
    Metadata        : outbox/meta/sample_ack_globex_meta.json
============================================================
```

The masked TXT file looks like this:

```
Hello [PERSON_1],
Your order with [ORG_1] has been confirmed.
Contact: [EMAIL_1]
```

### Common flags

| Flag | Effect |
|---|---|
| `--profile <name>` | Use a business profile (`acknowledge`, `invoice`, `email`) |
| `--private <name>` | Add a private profile from `profiles_private/` |
| `--no-gliner` | Disable the neural recognizer (faster, regex + deny lists only) |
| `--gliner-threshold 0.6` | Raise the neural confidence threshold |
| `--cleanup-pipes` | Strip stray `|` characters from broken PDF extraction |
| `--console` | Human-readable logs instead of JSON |
| `--log-level DEBUG` | More verbose logging |

## 2. Send the masked text to your LLM

Feed `outbox/txt/<doc>_anonymise.txt` to whatever LLM you use. The network call
is your responsibility - Carnaval never sends anything itself. Ask the LLM to
return **structured JSON or XML** and to keep the placeholders intact.

## 3. Re-inject the real values

Once you have the LLM's answer (e.g. `response.json`):

```bash
python reinject.py response.json --vault outbox/vault/sample_ack_globex_vault.enc
```

This writes `response_final.json` with every placeholder replaced by its
original value. The format (JSON vs XML) is auto-detected. See
[Reinjection](Reinjection.md) for details.

## Same thing with the Python API

Carnaval is equally usable as a library.

### Anonymize

```python
from pathlib import Path
from carnaval.pipeline import run_anonymization

masked, written, config = run_anonymization(
    input_path=Path("inbox/order.txt"),
    outbox_dir=Path("outbox"),
    vault_password="a-strong-randomly-generated-secret",
    profile="acknowledge",
    use_gliner=True,
)

print(masked.anonymized_text)   # text with placeholders
print(masked.by_category)       # {'PERSON': 2, 'ORGANIZATION': 1, ...}
print(written.json_path)        # path of the JSON output file
```

### Re-inject

```python
from carnaval.core.vault import Vault
from carnaval.stages.s7_reinject import reinject_json_data

vault = Vault(
    password="a-strong-randomly-generated-secret",
    path="outbox/vault/order_vault.enc",
)
vault.load()

llm_response = {"supplier": "[ORG_1]", "contact": "[PERSON_1]"}
restored = reinject_json_data(llm_response, vault)
# {"supplier": "Globex Inc.", "contact": "Jane Doe"}
```

### Anonymize without writing to disk

If you only want the masked text in memory (for an immediate LLM call):

```python
from carnaval.core.config_loader import load_config
from carnaval.core.vault import Vault
from carnaval.stages.s1_intake import intake
from carnaval.stages.s2_preprocess import preprocess
from carnaval.stages.s3_detect import detect
from carnaval.stages.s4_resolve import resolve
from carnaval.stages.s5_mask import mask

cfg = load_config(profile="acknowledge")
raw = intake("inbox/order.txt")
norm = preprocess(raw)
det = detect(norm, cfg, use_gliner=True)
res = resolve(det)

vault = Vault(password="a-strong-randomly-generated-secret")
masked = mask(res, vault)

print(masked.anonymized_text)   # placeholders text, nothing written to disk
# `vault` holds the mappings in memory; call vault.save() to persist them
```

## Next steps

- [Architecture](Architecture.md) - how the 7-stage pipeline works
- [Profiles](Profiles.md) - adapt Carnaval to your document type
- [Output Formats](Output-Formats.md) - the 8 files Carnaval produces
- [Reinjection](Reinjection.md) - the re-injection stage in depth
