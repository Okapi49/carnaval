# Profiles

A **profile** describes a *type of document* - its typical entities, the
business fields to preserve, and its lists of values to mask or keep. Profiles
are plain YAML files: you adapt Carnaval to a new document type without
touching the code.

## The three configuration layers

When Carnaval loads its configuration it merges three layers in order:

```
1. config/              technical defaults (universal regex settings)
        │
        ▼
2. profiles/<type>/      document type - acknowledge, invoice, email...
        │
        ▼
3. profiles_private/     real client data - GIT-IGNORED
        │
        ▼
   resolved Config
```

Merge rules:

- `dict + dict` → merged recursively, key by key
- `list + list` → concatenated (deny lists accumulate)
- `scalar + scalar` → the upper layer wins

## Bundled profiles

| Profile | Document type | Use case |
|---|---|---|
| `acknowledge` | Supplier order acknowledgement | Order / delivery confirmation |
| `invoice` | Invoice or fee note | Accounting, payment |
| `email` | Business email | B2B communication |

Use one with the `--profile` flag:

```bash
python anonymize.py inbox/doc.txt --profile acknowledge
python anonymize.py inbox/doc.txt --profile invoice --no-gliner
```

## Profile layout

```
profiles/<name>/
├── profile.yaml           # description: name, language, expected entities
├── deny_lists/            # values to MASK
│   ├── organizations.yaml
│   ├── organization_singleton.yaml
│   └── people.yaml
├── allow_lists/           # values to KEEP (false-positive guards)
│   └── product_refs.yaml
├── patterns/              # type-specific regex (rare)
├── policies/              # arbitration rules (rare)
└── fixtures/              # fictitious sample documents for tests
```

### `profile.yaml`

```yaml
profile:
  name: acknowledge
  description: |
    Anonymization of supplier order acknowledgements.
  language: fr
  expected_entities:
    - PERSON
    - ORGANIZATION
    - EMAIL
    - PHONE
    - LOCATION
    - IBAN
    - BIC
    - VAT
    - SIRET
    - SIREN
  preserve:
    - order_numbers       # the customer's order number - keep it!
    - product_references
    - amounts
    - dates
```

## Deny lists - values to mask

A deny list is a YAML file with a single top-level key. Anything listed there
is masked.

### Organizations

```yaml
# profiles/<type>/deny_lists/organizations.yaml
organizations:
  - "Globex Inc."
  - "Initech"
  - "Vandelay Industries"
```

### Singleton organization

The customer's own company appears in *every* one of their documents, so it
receives **one placeholder with no index** - `[ORG]`. List every spelling
variant:

```yaml
# profiles/<type>/deny_lists/organization_singleton.yaml
organization_singleton:
  - "Acme Corp"
  - "Acme Corporation"
  - "ACME CORP."
  - "ACMECORP"
```

All of those map to the same `[ORG]`.

### People

```yaml
# profiles/<type>/deny_lists/people.yaml
people:
  - "Jane Doe"
  - "John Smith"
```

These are *full names*. Names that appear with a recognizable pattern
(title + name, etc.) are caught by the name regex recognizers - no need to list
them. See [Recognizers](Recognizers.md).

### Place names

Place deny lists can be split per language:

```
deny_lists/places/
├── fr.yaml
├── de.yaml
├── en.yaml
└── ...
```

Each file uses the same `places:` key. Only the files for the active languages
are loaded - see [Multilingual](Multilingual.md).

## Allow lists - informative guards

Allow lists are **documentary**. The pipeline does not consult them directly;
they record which values must *not* be masked, and that intent is enforced by
well-scoped regex, the GLiNER score threshold, and the S4 dedup favouring
deterministic recognizers.

```yaml
# profiles/<type>/allow_lists/product_refs.yaml
product_ref_patterns:
  - "[A-Z]{2,4}-[A-Z0-9]{2,8}-\\d{2,4}"
```

## Private profiles

To keep your real client data out of a public repository, put it in
`profiles_private/` (git-ignored):

```
profiles_private/my_client_acknowledge/
├── profile.yaml
└── deny_lists/
    └── organizations.yaml
```

```yaml
# profiles_private/my_client_acknowledge/profile.yaml
profile:
  name: my_client_acknowledge
  extends: acknowledge
  description: "Private profile for client X"
```

```yaml
# profiles_private/my_client_acknowledge/deny_lists/organizations.yaml
organizations:
  - "Real Supplier One"
  - "Real Supplier Two"
```

Run with both:

```bash
python anonymize.py inbox/doc.txt \
    --profile acknowledge \
    --private my_client_acknowledge
```

The private organizations are *added* to the public profile's list.

## Creating a new profile

1. Copy an existing profile: `cp -r profiles/acknowledge profiles/my_profile`
2. Edit `profiles/my_profile/profile.yaml` (name, language, description).
3. Adapt the YAML files under `deny_lists/`, `allow_lists/`, etc.
4. Add a fictitious fixture under `fixtures/` and an integration test.

## Inspecting the resolved config

```python
from carnaval.core.config_loader import load_config

cfg = load_config(profile="acknowledge", private_profile="my_client")
print(cfg.layers)                       # the layers that were merged
print(cfg.deny_lists)                   # the resolved deny lists
print(cfg.get("pipeline.use_gliner"))   # dotted-path access
```

## See also

- [Recognizers](Recognizers.md) - adding deny-list entries vs coding a recognizer
- [Multilingual](Multilingual.md) - per-language lists
- [Quickstart](Quickstart.md) - running with a profile
