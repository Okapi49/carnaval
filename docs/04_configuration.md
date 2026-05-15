# 04 - Configuration

## Couches de configuration

carnaval applique 3 couches successives au chargement :

```
+-----------------------+
| 1. config/            |  (defaut technique - regex universels)
+-----------------------+
            |
            v
+-----------------------+
| 2. profiles/<type>/   |  (type de document - acknowledge, invoice, email...)
+-----------------------+
            |
            v
+-----------------------+
| 3. profiles_private/  |  (donnees client reelles - GIT IGNORE)
+-----------------------+
            |
            v
       Config resolu
```

Strategie de merge :
- `dict + dict` : recursion (cle par cle)
- `list + list` : concatenation (les deny lists s'enrichissent)
- `scalaire + scalaire` : la couche superieure gagne

## Layout d'un profil

```
profiles/<nom>/
|-- profile.yaml           # description (nom, langue, entites attendues)
|-- deny_lists/            # listes a MASQUER
|   |-- organizations.yaml
|   |-- organization_singleton.yaml
|   `-- people.yaml
|-- allow_lists/           # listes a PRESERVER (anti faux positifs)
|   `-- product_refs.yaml
|-- patterns/              # regex specifiques au type (rare)
|-- policies/              # regles d'arbitrage (rare)
`-- fixtures/              # exemples fictifs pour tests
    `-- sample.txt
```

## Fichier `config/pipeline.yaml`

```yaml
pipeline:
  default_language: fr
  use_gliner: true
  gliner_threshold: 0.4
  cleanup_pipes: false
  score_threshold: 0.4

placeholder:
  format: "[{prefix}_{index}]"
  singleton_format: "[{prefix}]"

ai:
  gliner_model: "urchade/gliner_multi_pii-v1"
  gliner_labels:
    - person
    - email
    - phone number
    - address
    - organization
```

## Deny lists

Format simple - une cle a la racine du YAML :

```yaml
# config/deny_lists/organizations.yaml ou profiles/<type>/deny_lists/organizations.yaml
organizations:
  - "Globex Inc."
  - "Initech"
  - "Vandelay"
```

Pour les domaines email/web :

```yaml
supplier_domains:
  - "globex.example"
  - "initech.example"
```

## Singleton organization

L'entreprise du client (qui apparait dans tous ses documents) recoit
**un seul placeholder** sans index :

```yaml
# profiles/<type>/deny_lists/organization_singleton.yaml
organization_singleton:
  - "Acme Corp"
  - "Acme Corporation"
  - "ACME CORP"
  - "ACMECORP"
```

Toutes les variantes ci-dessus produiront `[ORG]` (unique).

## People

```yaml
# profiles/<type>/deny_lists/people.yaml
people:
  - "Alice Anderson"
  - "Bob Brown"
```

## Allow lists (informatives)

Les allow lists sont **documentaires**. Le pipeline ne les utilise pas
explicitement - leur respect est garanti par :
- Les regex specifiques qui ne matchent que les bonnes formes
- Le seuil de score GLiNER
- Le dedup qui privilegie les recognizers deterministes

```yaml
# profiles/<type>/allow_lists/product_refs.yaml
product_ref_patterns:
  - "[A-Z]{2,4}-[A-Z0-9]{2,8}-\\d{2,4}"
```

## Lancer avec un profil

```bash
python anonymize.py doc.txt --profile acknowledge
python anonymize.py doc.txt --profile invoice --no-gliner
python anonymize.py doc.txt --profile acknowledge --private mon_client
```

## Inspecter la config resolue

```python
from carnaval.core.config_loader import load_config

cfg = load_config(profile="acknowledge", private_profile="mon_client")
print(cfg.layers)            # ['base:...', 'profile:acknowledge', 'private:mon_client']
print(cfg.deny_lists)         # dict resolu
print(cfg.get("pipeline.use_gliner"))   # acces dotted-path
```
