# Output formats

A single run of `anonymize.py` produces **8 output files** under `outbox/`,
each in its own sub-folder. You pick whichever ones your downstream tooling
needs - they are all written in one pass.

## Input

Carnaval reads a single **`.txt`** file:

- Encoding: UTF-8, with automatic fallback to latin-1.
- Maximum size: 50 MB by default (configurable).
- No imposed structure - plain text.

```
Hello Jane Doe,
Your order with Globex Inc. has been confirmed.
Contact: jane@globex.example
```

Carnaval does **not** do OCR. To process a PDF, extract its text upstream
(`pdfplumber`, `pypdf`, `tesseract`...).

## The 8 outputs

| # | Format | Path | Purpose |
|---|---|---|---|
| 1 | TXT | `outbox/txt/<stem>_anonymise.txt` | masked text to feed an LLM |
| 2 | JSON | `outbox/json/<stem>_anonymise.json` | structured result for APIs |
| 3 | JSONL | `outbox/jsonl/<stem>_entities.jsonl` | one entity per line, streaming |
| 4 | XML | `outbox/xml/<stem>_anonymise.xml` | legacy / EDI integration |
| 5 | CoNLL | `outbox/conll/<stem>_anonymise.conll` | NER model training |
| 6 | HTML | `outbox/html/<stem>_anonymise.html` | colorized visualization |
| 7 | Vault | `outbox/vault/<stem>_vault.enc` | encrypted placeholder mapping |
| 8 | Meta | `outbox/meta/<stem>_meta.json` | audit metadata (no sensitive data) |

### 1. TXT

Plain masked text, ready to pipe to an LLM.

```
Hello [PERSON_1],
Your order with [ORG_1] has been confirmed.
Contact: [EMAIL_1]
```

### 2. JSON

Structured result for programmatic use.

```json
{
  "anonymized_text": "Hello [PERSON_1]...",
  "language": "en",
  "entities": [
    {
      "start": 6,
      "end": 14,
      "type": "PERSON",
      "placeholder": "[PERSON_1]",
      "score": 0.95,
      "recognizer": "GLiNER"
    }
  ],
  "by_category": {"PERSON": 1, "ORGANIZATION": 1, "EMAIL": 1},
  "source": "/path/inbox/doc.txt"
}
```

### 3. JSONL

One entity object per line - friendly for streaming and log pipelines.

```jsonl
{"start": 6, "end": 14, "type": "PERSON", "placeholder": "[PERSON_1]", "score": 0.95, "recognizer": "GLiNER"}
{"start": 30, "end": 41, "type": "ORGANIZATION", "placeholder": "[ORG_1]", "score": 1.0, "recognizer": "OrganizationsDenyList"}
```

### 4. XML

For legacy systems and EDI integration.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<carnavalResult>
  <anonymizedText>Hello [PERSON_1]...</anonymizedText>
  <language>en</language>
  <source>/path/inbox/doc.txt</source>
  <byCategory>
    <category name="PERSON">1</category>
    <category name="ORGANIZATION">1</category>
  </byCategory>
  <entities>
    <entity start="6" end="14" type="PERSON" placeholder="[PERSON_1]" .../>
  </entities>
</carnavalResult>
```

### 5. CoNLL

CoNLL-2003 BIO format, for training or evaluating NER models.

```
Hello O

Jane B-PERSON
Doe I-PERSON

Your O
order O
with O
Globex B-ORGANIZATION
Inc. I-ORGANIZATION
```

### 6. HTML

An interactive page with colorized spans - handy for debugging and functional
reviews.

### 7. Vault

The AES-256-GCM encrypted file holding the placeholder ↔ value mapping. It is
**required** for re-injection. See [Vault and Security](Vault-and-Security.md).

### 8. Meta

Non-sensitive audit data.

```json
{
  "source": "/path/inbox/doc.txt",
  "language": "en",
  "num_spans": 3,
  "by_category": {"PERSON": 1, "ORGANIZATION": 1, "EMAIL": 1},
  "outputs": {"txt": "...", "json": "..."},
  "timestamp": 1715680000.0,
  "duration_seconds": 12.5
}
```

No original value is ever written here - only counts and paths.

## Re-injection input formats

Stage S7 accepts JSON or XML and auto-detects the format from the first
non-blank character:

| First character | Detected format |
|---|---|
| `{` or `[` | JSON |
| `<` | XML |
| anything else | plain text |

See [Reinjection](Reinjection.md).

## Using the serializers directly

The serializers live in `src/carnaval/core/serializers.py` and can be called on
a `MaskedDocument` independently of the file-writing stage:

```python
from carnaval.core.serializers import to_txt, to_json, to_html

txt = to_txt(masked)
json_str = to_json(masked)
html = to_html(masked)
```

## Adding a custom output format

Add a `to_<format>(doc: MaskedDocument) -> str` function in
`src/carnaval/core/serializers.py`, then wire it into
`src/carnaval/stages/s6_output.py`. Possible additions: Markdown, YAML, CSV
(one row per entity), RDF.

## See also

- [Architecture](Architecture.md) - stage S6
- [Reinjection](Reinjection.md) - feeding JSON/XML back through Carnaval
- [Quickstart](Quickstart.md) - a full run end to end
