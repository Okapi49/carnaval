# Multilingual support

Carnaval anonymizes documents in **6 languages**:

| Code | Language |
|---|---|
| `fr` | French |
| `en` | English |
| `de` | German |
| `es` | Spanish |
| `it` | Italian |
| `pt` | Portuguese |

Language handling is automatic - you rarely need to think about it - but
understanding the routing helps when you tune profiles or add recognizers.

## Language detection

During stage S2 (Preprocess), Carnaval detects the document's main language
with the `lingua` library. The result is stored on the `NormalizedDocument`
and shown in the CLI summary and every output file.

## Active-language routing

Detection of a single main language is not enough for real documents - a German
order acknowledgement may still quote the French address of its customer. So
stage S3 (Detect) computes a **set of active languages** by combining three
signals:

1. **The language detected by `lingua`** - the best single guess.
2. **The pipeline's primary language** - the customer's default language,
   taken from the profile / configuration.
3. **In-text linguistic markers** - unambiguous words found in the text itself.

The marker mechanism has two levels:

- **Strong markers** - a single hit is enough. These are unambiguous mentions
  such as a country name (`Deutschland` → German, `Portugal` → Portuguese,
  `France` → French).
- **Weak markers** - at least **two distinct hits** are required. These are
  commercial or legal tokens such as company suffixes (`GmbH`, `Ltd`, `SARL`,
  `Lda.`, `S.p.A.`) and closing formulas (`Sincerely`, `Cordialement`).

Every recognizer that is language-aware (address, phone, names, place deny
lists, contextual location, bundled dictionaries) then runs **once per active
language**. Universal recognizers (email, URL, IBAN, BIC) run regardless of
language.

## Forcing the language

You can override auto-detection from the CLI:

```bash
python anonymize.py inbox/doc.txt --profile acknowledge --language de
```

Or from the Python API, via the `language` argument of `run_anonymization`:

```python
run_anonymization(..., language="es")
```

When `language` is `None` (the default), auto-detection plus marker routing
decide.

## Per-language assets

Several resources are organized by language code:

- **Regex recognizers** - `src/carnaval/recognizers/regex/{address,phone,names}/`
  contain one module per language (`fr.py`, `de.py`, `en.py`, `es.py`, `it.py`,
  `pt.py`).
- **Bundled dictionaries** - `assets/dictionaries/cities/<lang>.txt` and
  `assets/dictionaries/firstnames/<lang>.txt`.
- **Place deny lists** - `profiles/<type>/deny_lists/places/<lang>.yaml`.

Only the files matching the active languages are loaded, which keeps each run
fast and focused.

## Language-specific entities

Some entities only exist in one country. French SIREN, SIRET and VAT numbers,
for example, are detected by French-specific recognizers that run only when
French is among the active languages. When you add a country-specific
recognizer, gate it on the relevant language in `s3_detect.py` - see
[Recognizers](Recognizers.md).

## See also

- [Architecture](Architecture.md) - stages S2 and S3
- [Recognizers](Recognizers.md) - how per-language recognizers are dispatched
- [Profiles](Profiles.md) - per-language place deny lists
