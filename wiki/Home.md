<p align="center">
  <img src="../assets/carnaval-mask.svg" width="200" alt="Carnaval mask">
</p>

<h1 align="center">Carnaval Wiki</h1>

<p align="center"><em>The art of the mask &mdash; hide the identity, keep the meaning.</em></p>

Welcome! This wiki is the complete guide to **Carnaval**, the reversible
PII anonymization framework.

**New here?** In one sentence: Carnaval lets you use a cloud AI on your
documents *without* handing it the names, addresses or bank details they
contain — it puts a mask on the sensitive data, and lifts it once the AI has
answered. Curious? The **[Quickstart](Quickstart.md)** gets you running in
five minutes.

## What is Carnaval?

Carnaval lets you send text documents to a cloud LLM **without ever exposing
the personal or confidential data they contain**. It works in two moves:

1. **Anonymize** - sensitive entities (people, organizations, locations,
   emails, phone numbers, bank identifiers, tax numbers, URLs) are replaced
   with neutral placeholders such as `[PERSON_1]` or `[ORG]`. The mapping
   between each placeholder and its real value is stored in a local
   **AES-256-GCM encrypted vault**.
2. **Re-inject** - once the LLM returns a structured answer (JSON or XML), the
   original values are restored from the vault.

The LLM only ever sees masked text. The clear values never leave your machine.

```
RAW DOCUMENT  ──▶  Carnaval (anonymize)  ──▶  MASKED DOCUMENT  ──▶  Cloud LLM
                                                                        │
FINAL DOCUMENT  ◀──  Carnaval (re-inject)  ◀──  JSON / XML response  ◀──┘
```

## Pages

| Page | Topic |
|---|---|
| [Installation](Installation.md) | Requirements, dependencies, the optional `[ai]` extra, offline setup |
| [Quickstart](Quickstart.md) | Your first anonymization in 5 minutes - CLI and Python API |
| [Architecture](Architecture.md) | The 7-stage pipeline explained |
| [Vault and Security](Vault-and-Security.md) | The encrypted vault, AES-256-GCM, PBKDF2, GDPR notes |
| [Profiles](Profiles.md) | Business profiles, private profiles, deny lists and allow lists |
| [Recognizers](Recognizers.md) | Regex, deny lists, dictionaries, GLiNER - and how to add your own |
| [Multilingual](Multilingual.md) | The 6 supported languages and language routing |
| [Output Formats](Output-Formats.md) | The 8 output formats |
| [Reinjection](Reinjection.md) | Restoring values in the LLM's JSON / XML response |
| [Troubleshooting](Troubleshooting.md) | Common problems and fixes |
| [Contributing](Contributing.md) | How to contribute and run the test suite |

## Core concepts at a glance

- **Reversibility** - every masked value has a unique placeholder; the mapping
  is encrypted at rest.
- **Coherence** - the same original value always gets the same placeholder
  within a run, so the LLM can reason about references.
- **Locality** - anonymization makes no network calls. The optional neural
  model runs locally.
- **Stages** - the pipeline is 7 independent stages (S1–S7), each testable and
  replaceable in isolation.
- **Profiles** - a profile describes a *type of document* through editable YAML
  files; no code change required.
- **No magic** - each recognizer is a pure Python function: text in, spans out.

## What Carnaval does *not* do

- **No OCR** - the input is already-extracted text. Use a tool such as
  `pdfplumber` or `tesseract` upstream.
- **No LLM call** - Carnaval prepares and restores; the network call to the LLM
  is your responsibility.
- **No built-in batching** - one file at a time. Wrap `anonymize.py` in a loop
  to process a folder.

## Supported languages

French, English, German, Spanish, Italian, Portuguese. See
[Multilingual](Multilingual.md).

## License

Apache License 2.0.
