# 08 - Formats d'entree et de sortie

## Entree

### Fichier .txt brut

- Encodage : UTF-8 (fallback latin-1 automatique)
- Taille max : 50 Mo par defaut (configurable)
- Pas de structure imposee : texte brut

Exemple :
```
Bonjour Alice Anderson,
Votre commande chez Globex Inc. est confirmee.
Contact : alice@globex.example
```

## Sorties simultanees

Une seule passe d'anonymisation produit **6 formats** dans `outbox/` :

### 1. TXT - `outbox/txt/<stem>_anonymise.txt`

Texte avec balises, prets a piper vers un LLM.

```
Bonjour [PERSON_1],
Votre commande chez [ORG_1] est confirmee.
Contact : [EMAIL_1]
```

### 2. JSON - `outbox/json/<stem>_anonymise.json`

Structure exploitable pour les API.

```json
{
  "anonymized_text": "Bonjour [PERSON_1]...",
  "language": "fr",
  "entities": [
    {
      "start": 8,
      "end": 22,
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

### 3. JSONL - `outbox/jsonl/<stem>_entities.jsonl`

Une entite par ligne, streaming-friendly.

```jsonl
{"start": 8, "end": 22, "type": "PERSON", "placeholder": "[PERSON_1]", "score": 0.95, "recognizer": "GLiNER"}
{"start": 40, "end": 51, "type": "ORGANIZATION", "placeholder": "[ORG_1]", "score": 1.0, "recognizer": "OrganizationsDenyList"}
```

### 4. XML - `outbox/xml/<stem>_anonymise.xml`

Integration legacy / EDI.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<carnavalResult>
  <anonymizedText>Bonjour [PERSON_1]...</anonymizedText>
  <language>fr</language>
  <source>/path/inbox/doc.txt</source>
  <byCategory>
    <category name="PERSON">1</category>
    <category name="ORGANIZATION">1</category>
  </byCategory>
  <entities>
    <entity start="8" end="22" type="PERSON" placeholder="[PERSON_1]" .../>
  </entities>
</carnavalResult>
```

### 5. CoNLL - `outbox/conll/<stem>_anonymise.conll`

Format CoNLL-2003 BIO pour entrainement de modeles NER.

```
Bonjour O

Alice B-PERSON
Anderson I-PERSON

Votre O
commande O
chez O
Globex B-ORGANIZATION
Inc. I-ORGANIZATION
```

### 6. HTML - `outbox/html/<stem>_anonymise.html`

Visualisation interactive avec spans colorises. Utile pour le debug et
les revues fonctionnelles.

## Vault et metadata

### Vault - `outbox/vault/<stem>_vault.enc`

Fichier binaire chiffre AES-256-GCM. Indispensable pour la reinjection.

### Meta - `outbox/meta/<stem>_meta.json`

Audit non sensible.

```json
{
  "source": "/path/inbox/doc.txt",
  "language": "fr",
  "num_spans": 3,
  "by_category": {"PERSON": 1, "ORGANIZATION": 1, "EMAIL": 1},
  "outputs": {
    "txt": "...",
    "json": "...",
    "...": "..."
  },
  "timestamp": 1715680000.0,
  "duration_seconds": 12.5
}
```

## Re-injection : formats supportes en entree

S7 accepte JSON et XML. Auto-detection par le premier caractere :

| Premier char | Format detecte |
|---|---|
| `{` ou `[` | JSON |
| `<` | XML |
| Autre | Texte brut |

### Exemple JSON

```bash
# Reponse Sonnet
cat > response.json <<EOF
{
  "supplier": "[ORG_1]",
  "contact": "[PERSON_1]",
  "amount": 1200
}
EOF

python reinject.py response.json --vault outbox/vault/doc_vault.enc
```

Produit `response_final.json` :
```json
{
  "supplier": "Globex Inc.",
  "contact": "Alice Anderson",
  "amount": 1200
}
```

### Exemple XML

```bash
cat > response.xml <<EOF
<order>
  <supplier>[ORG_1]</supplier>
  <contact email="[EMAIL_1]">[PERSON_1]</contact>
</order>
EOF

python reinject.py response.xml --vault outbox/vault/doc_vault.enc
```

Produit `response_final.xml` :
```xml
<order>
  <supplier>Globex Inc.</supplier>
  <contact email="alice@globex.example">Alice Anderson</contact>
</order>
```

Les attributs XML, le texte des elements et les tail sont tous traites.

## Ajouter un format de sortie custom

Editer `src/carnaval/core/serializers.py`, ajouter une fonction
`to_<format>(doc: MaskedDocument) -> str`. Brancher dans
`stages/s6_output.py`.

Idees de formats additionnels :
- **Markdown** avec annotations
- **YAML** pour configuration
- **CSV** pour tableur (1 ligne = 1 entite)
- **OWL/RDF** pour graphe de connaissances
