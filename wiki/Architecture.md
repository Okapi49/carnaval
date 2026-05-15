# Architecture

Carnaval is built as a chain of **7 self-contained stages**. Stages S1 to S6
form the forward (anonymization) pipeline; S7 is the inverse (re-injection)
stage. Each stage has a clear input → output contract, so it can be tested,
debugged or replaced in isolation.

```
+---------+   +-----------+   +--------+   +---------+   +------+   +--------+
| S1      |──▶| S2        |──▶| S3     |──▶| S4      |──▶| S5   |──▶| S6     |
| Intake  |   | Preprocess|   | Detect |   | Resolve |   | Mask |   | Output |
+---------+   +-----------+   +--------+   +---------+   +------+   +--------+

(inverse stage)  S7 Reinject : JSON / XML with placeholders ──▶ JSON / XML restored
```

The orchestrator is `src/carnaval/pipeline.py`; it simply chains S1 → S6 and
contains no business logic of its own.

---

## S1 - Intake

**Reads the input file.**

- Input: a `Path` to a `.txt` file.
- Output: a `RawDocument` (raw text + metadata).

Responsibilities: check the file exists and is readable; read it as UTF-8 with
an automatic fallback to latin-1; reject empty or oversized files (default cap
50 MB); capture metadata such as size, mtime and encoding.

Code: `src/carnaval/stages/s1_intake.py`

---

## S2 - Preprocess

**Normalizes the text and detects the language.**

- Input: a `RawDocument`.
- Output: a `NormalizedDocument` (normalized text + detected language).

Responsibilities: detect the language with the `lingua` library; strip the BOM;
collapse multiple spaces; optionally remove stray `|` characters left by
faulty PDF extraction (the `cleanup_pipes` option, off by default because it
carries a small risk of altering business content).

Code: `src/carnaval/stages/s2_preprocess.py`

---

## S3 - Detect

**Runs every recognizer and collects raw spans.**

- Input: a `NormalizedDocument` plus a `Config`.
- Output: a `DetectedDocument` (a raw, *non-deduplicated* list of `Span`).

S3 first resolves the **set of active languages** by combining three signals:
the language detected by `lingua`, the pipeline's primary language, and
in-text linguistic markers (e.g. `GmbH` activates German, `SARL` activates
French). This lets a mixed-language document be detected correctly.

It then runs, without arbitration:

- **Universal regex recognizers** - email, URL, IBAN, BIC, header-source.
- **Legal-suffix organization recognizer** - multilingual (GmbH, AG, Ltd,
  SARL, Lda...).
- **Multilingual regex recognizers** - address, phone, names (dispatched
  internally per active language).
- **French-specific regex** - SIREN / SIRET / French VAT, when French is active.
- **Deny lists** - singleton organization, organizations, people.
- **Per-language deny lists** - place names.
- **Contextual location recognizer** - patterns like *"Agency in X"*.
- **Bundled dictionaries** - GeoNames cities and first names.
- **GLiNER** - the optional zero-shot neural recognizer.

Collecting overlapping or conflicting spans here is expected - sorting them out
is S4's job.

Code: `src/carnaval/stages/s3_detect.py` - see [Recognizers](Recognizers.md).

---

## S4 - Resolve

**Deduplicates overlapping spans.**

- Input: a `DetectedDocument`.
- Output: a `ResolvedDocument` (non-overlapping, ordered spans).

When several recognizers match the same region, S4 keeps exactly one span.
The selection criteria, in order:

1. **Length** - the longest (most enclosing) span wins.
2. **Score** - higher confidence wins.
3. **Recognizer priority** - a fixed priority table breaks remaining ties
   (deterministic recognizers outrank GLiNER).
4. **Position** - leftmost first.

> Why length before score? Consider an `EMAIL` span (score 0.95) that contains
> a sub-domain matched as a `URL` (score 0.70). The enclosing email span must
> win even though both scores are close, otherwise the email's integrity is
> lost.

Code: `src/carnaval/stages/s4_resolve.py`

---

## S5 - Mask

**Assigns placeholders and fills the vault.**

- Input: a `ResolvedDocument` plus a `Vault`.
- Output: a `MaskedDocument` (anonymized text + spans enriched with placeholders).

For each span S5 allocates a placeholder:

- A **singleton** type (`ORG_SINGLETON`) becomes `[ORG]` - no index.
- Any other type becomes `[TYPE_n]` with `n` incrementing per type.

**Coherence** is guaranteed: if a value already has a placeholder in the vault,
that placeholder is reused - every occurrence of the same value gets the same
tag. The anonymized text is rebuilt by substituting spans **right to left** so
that offsets stay valid. Every mapping is recorded in the vault.

Code: `src/carnaval/stages/s5_mask.py` - see [Vault and Security](Vault-and-Security.md).

---

## S6 - Output

**Writes the result in 8 formats.**

- Input: a `MaskedDocument`, a `Vault`, the outbox path.
- Output: a `WrittenOutput` with the 8 file paths.

Files written under `outbox/`:

| Folder | File | Content |
|---|---|---|
| `txt/` | `<stem>_anonymise.txt` | masked text |
| `json/` | `<stem>_anonymise.json` | text + entities + metadata |
| `jsonl/` | `<stem>_entities.jsonl` | one entity per line |
| `xml/` | `<stem>_anonymise.xml` | masked text in XML |
| `conll/` | `<stem>_anonymise.conll` | CoNLL-2003 BIO format |
| `html/` | `<stem>_anonymise.html` | colorized visualization |
| `vault/` | `<stem>_vault.enc` | AES-256-GCM encrypted vault |
| `meta/` | `<stem>_meta.json` | audit metadata, no sensitive data |

Code: `src/carnaval/stages/s6_output.py`, serializers in
`src/carnaval/core/serializers.py` - see [Output Formats](Output-Formats.md).

---

## S7 - Reinject (inverse stage)

**Restores the original values in the LLM's answer.**

- Input: JSON or XML containing placeholders, plus a `Vault`.
- Output: the same structure with original values restored.

The format is auto-detected from the first non-blank character: `{` or `[`
means JSON, `<` means XML, anything else falls back to plain text. S7 also
tolerates placeholders that lost their brackets (some LLMs drop them).

Code: `src/carnaval/stages/s7_reinject.py` - see [Reinjection](Reinjection.md).

---

## Orchestration

```python
from carnaval.pipeline import run_anonymization

masked, written, config = run_anonymization(
    input_path="inbox/doc.txt",
    outbox_dir="outbox",
    vault_password="a-strong-randomly-generated-secret",
    profile="acknowledge",
)
```

Each stage emits a structured log line. The logger redacts sensitive keys
automatically, so no clear value ever reaches the logs - see
[Vault and Security](Vault-and-Security.md).
