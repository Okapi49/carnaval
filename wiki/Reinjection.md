# Reinjection

**Reinjection** is the inverse of anonymization. After your cloud LLM returns a
structured answer that still contains placeholders, Carnaval restores the
original values from the encrypted vault. This is stage **S7** of the pipeline.

```
LLM answer with placeholders  ──▶  S7 Reinject (+ vault)  ──▶  answer with real values
```

## Prerequisite: the vault

Reinjection needs the **same vault** that anonymization produced
(`outbox/vault/<stem>_vault.enc`) and the **same password**. If the password
differs, the vault cannot be decrypted - see [Troubleshooting](Troubleshooting.md).

## From the command line

```bash
python reinject.py response.json --vault outbox/vault/order_vault.enc
```

The output file defaults to `<input>_final.<ext>` - here `response_final.json`.
Override it with `--output`:

```bash
python reinject.py response.xml --vault outbox/vault/order_vault.enc \
    --output final/order.xml
```

The format (JSON vs XML) is auto-detected from the file content.

## Auto-detection

S7 looks at the first non-blank character of the input:

| First character | Treated as |
|---|---|
| `{` or `[` | JSON |
| `<` | XML |
| anything else | plain text |

## JSON reinjection

Carnaval walks the structure recursively and replaces placeholders **wherever
they appear** - keys are left untouched, only string values are processed.

Input `response.json`:

```json
{
  "supplier": "[ORG_1]",
  "contact": "[PERSON_1]",
  "amount": 1200
}
```

Result `response_final.json`:

```json
{
  "supplier": "Globex Inc.",
  "contact": "Jane Doe",
  "amount": 1200
}
```

Non-string values (numbers, booleans, null) pass through unchanged.

## XML reinjection

Element text, element tails and **attribute values** are all processed.

Input `response.xml`:

```xml
<order>
  <supplier>[ORG_1]</supplier>
  <contact email="[EMAIL_1]">[PERSON_1]</contact>
</order>
```

Result `response_final.xml`:

```xml
<order>
  <supplier>Globex Inc.</supplier>
  <contact email="jane@globex.example">Jane Doe</contact>
</order>
```

## Placeholder formats handled

The standard placeholder is `[TYPE_n]` (or `[ORG]` for the singleton). Some
LLMs drop the brackets, so S7 also recovers two degraded forms:

| Form | Example | Handled |
|---|---|---|
| Standard | `[PERSON_1]` | yes |
| Bracket-less, whole string | `PERSON_1` | yes |
| Bracket-less, inside a sentence | `Delivered to ADDR_2` | yes (word-boundary match) |

If a placeholder is not found in the vault, S7 leaves it untouched rather than
failing - so a partial answer still re-injects what it can.

## Python API

### Reinject a dict

```python
from carnaval.core.vault import Vault
from carnaval.stages.s7_reinject import reinject_json_data

vault = Vault(password="a-strong-secret", path="outbox/vault/order_vault.enc")
vault.load()

llm_response = {"supplier": "[ORG_1]", "contact": "[PERSON_1]"}
restored = reinject_json_data(llm_response, vault)
# {"supplier": "Globex Inc.", "contact": "Jane Doe"}
```

### Reinject a JSON string

```python
from carnaval.stages.s7_reinject import reinject_json_string

restored_str = reinject_json_string('{"x": "[PERSON_1]"}', vault)
```

### Reinject an XML string

```python
from carnaval.stages.s7_reinject import reinject_xml_string

restored = reinject_xml_string('<order supplier="[ORG_1]">[PERSON_1]</order>', vault)
```

### Auto-detecting helper

```python
from carnaval.stages.s7_reinject import reinject_string, reinject_file

# Accepts JSON, XML or plain text - auto-detected
restored = reinject_string(content, vault)

# Same, straight from a file path
restored = reinject_file("response.json", vault)
```

## End-to-end example

```python
from pathlib import Path
from carnaval.core.config_loader import load_config
from carnaval.core.vault import Vault
from carnaval.stages.s1_intake import intake
from carnaval.stages.s2_preprocess import preprocess
from carnaval.stages.s3_detect import detect
from carnaval.stages.s4_resolve import resolve
from carnaval.stages.s5_mask import mask
from carnaval.stages.s7_reinject import reinject_json_data


def process(path: Path, password: str) -> dict:
    # 1. Anonymize (in memory, nothing written to disk)
    cfg = load_config(profile="acknowledge")
    raw = intake(path)
    norm = preprocess(raw)
    det = detect(norm, cfg, use_gliner=True)
    res = resolve(det)
    vault = Vault(password=password)
    masked = mask(res, vault)

    # 2. Call your LLM with masked.anonymized_text
    response = call_my_llm(masked.anonymized_text)
    # response == {"supplier": "[ORG_1]", "contact": "[PERSON_1]"}

    # 3. Restore the real values
    return reinject_json_data(response, vault)
```

## See also

- [Architecture](Architecture.md) - stage S7
- [Vault and Security](Vault-and-Security.md) - the encrypted vault
- [Output Formats](Output-Formats.md) - formats produced by anonymization
- [Troubleshooting](Troubleshooting.md) - `VaultError` and reinjection issues
