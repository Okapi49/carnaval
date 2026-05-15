# Recognizers

A **recognizer** is what finds sensitive entities in the text. Carnaval uses
four kinds, all run during stage S3 (Detect). This page explains each kind and
shows how to add your own.

## The recognizer contract

Every recognizer is a **pure Python function**:

```python
def my_recognizer(text: str) -> list[Span]:
    ...
```

Text in, a list of `Span` objects out. No inheritance, no framework, no hooks.
A `Span` records the start/end offsets, the entity type, the matched text, a
confidence score and the recognizer name.

## The four kinds of recognizer

### 1. Regex recognizers

Pattern-based detection for entities with a recognizable shape.

- **Universal** (all languages): email, URL, IBAN, BIC, header-source.
- **Legal-suffix organizations**: multilingual - GmbH, AG, Ltd, Inc., SARL,
  Lda., S.p.A., etc.
- **Multilingual dispatchers**: address, phone and name recognizers that route
  internally to the right per-language patterns.
- **French-specific**: SIREN, SIRET and French VAT numbers (no direct
  equivalent in the other languages).

Regex recognizers are deterministic and get high priority in the S4 dedup.
Recognizers with a checksum (IBAN, for instance) score very high; generic
patterns score lower because they are more prone to false positives.

### 2. Deny lists

Exact-value lists declared in profile YAML files. Anything listed is masked.
There are three deny-list recognizers - organizations, singleton organization,
people - plus per-language place lists. Matching is **case-insensitive** and
uses word boundaries by default (`Acme` will not match inside `acmeic`); a
"loose" variant without word boundaries is also available.

Adding a deny-list entry requires **no code** - see [Profiles](Profiles.md).

### 3. Bundled dictionaries

Large reference lists shipped with the project under `assets/dictionaries/`:

- **cities** - GeoNames-derived city names, one file per language
- **firstnames** - common first names, one file per language, with a
  `_stoplist.txt` to suppress ambiguous entries

These give per-language baseline coverage of `LOCATION` and `PERSON` even when
GLiNER is disabled. They are loaded lazily and only for the active languages.

### 4. GLiNER - the optional neural recognizer

GLiNER is a **zero-shot Named Entity Recognition** model. It catches free-form
`PERSON`, `ORGANIZATION` and `LOCATION` mentions that regex and deny lists
cannot anticipate.

- Model: `urchade/gliner_multi_pii-v1` (~500 MB, downloaded on first use).
- Zero-shot: you pass it the entity labels you want, no retraining needed.
- Configurable confidence threshold (default `0.4`, raise it to reduce false
  positives).
- Disable it with `--no-gliner` for a faster, fully deterministic run.
- Lowest priority in the S4 dedup, so a deterministic match always wins a tie.

Default GLiNER labels are mapped to Carnaval entity types in
`src/carnaval/recognizers/ai/gliner_engine.py`:

| GLiNER label | Entity type |
|---|---|
| `person` | `PERSON` |
| `email` | `EMAIL` |
| `phone number` | `PHONE` |
| `address`, `street address`, `postal code`, `city` | `LOCATION` |
| `organization`, `company` | `ORGANIZATION` |

## How S3 combines them

Stage S3 runs **every** recognizer and collects all spans, including
overlapping ones. The arbitration happens later, in S4 (Resolve), which keeps
the longest / highest-scoring / highest-priority span for each region. See
[Architecture](Architecture.md).

## Adding a recognizer

When deny lists are not enough - you need to detect a *pattern*, not a fixed
list - you code a recognizer. Example: a French social-security number.

### 1. Write the function

```python
# src/carnaval/recognizers/regex/social_security_fr.py
import re
from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans

NIR_PATTERN = re.compile(
    r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2,5}\s?\d{3}\s?\d{2}\b"
)

def recognize_nir_fr(text: str, score: float = 0.85) -> list[Span]:
    return regex_to_spans(
        NIR_PATTERN, text,
        entity_type="NIR",
        recognizer="NirFrRegex",
        score=score,
    )
```

Compile the pattern at module level, not inside the function.

### 2. Wire it into S3

In `src/carnaval/stages/s3_detect.py`, import the function and add it to the
appropriate recognizer tuple:

```python
from carnaval.recognizers.regex.social_security_fr import recognize_nir_fr

_FR_SPECIFIC_REGEX_RECOGNIZERS = (
    recognize_all_fiscal_fr,
    recognize_nir_fr,      # <-- added
)
```

### 3. Declare the placeholder prefix

In `src/carnaval/stages/s5_mask.py`:

```python
DEFAULT_PLACEHOLDER_PREFIX = {
    ...,
    "NIR": "NIR",
}
```

If you skip this, the placeholder prefix defaults to the entity type itself,
which is often fine.

### 4. Set the dedup priority

In `src/carnaval/stages/s4_resolve.py`:

```python
DEFAULT_RECOGNIZER_PRIORITY = {
    ...,
    "NirFrRegex": 85,
}
```

### 5. Re-injection - nothing to do

The S7 placeholder pattern is generic and already matches `[NIR_1]`, `[NIR_2]`,
etc. No change is needed.

### 6. Add tests

Create `tests/recognizers/test_nir.py` with positive *and* negative cases
(at least 5 of each), plus at least one end-to-end integration test. See
[Contributing](Contributing.md).

```bash
pytest -m "not slow"
```

## Adding a GLiNER label

GLiNER is zero-shot, so a new entity type just needs a label and a mapping:

```yaml
# config/pipeline.yaml
ai:
  gliner_labels:
    - person
    - email
    - social security number    # <-- new label
```

```python
# src/carnaval/recognizers/ai/gliner_engine.py
LABEL_TO_ENTITY_TYPE = {
    ...,
    "social security number": "NIR",
}
```

## Good practice

- One responsibility per recognizer - one file, one entity type.
- Positive and negative tests for every recognizer.
- No side effects - `text` in, `list[Span]` out, nothing else.
- Realistic scores - 0.95+ for specific patterns with a checksum, 0.5–0.7 for
  generic patterns that may produce false positives.

## See also

- [Architecture](Architecture.md) - stages S3 and S4
- [Profiles](Profiles.md) - extending deny lists without code
- [Multilingual](Multilingual.md) - per-language recognizers
