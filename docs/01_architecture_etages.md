# 01 - Architecture en etages

Le pipeline carnaval est decoupe en **7 etages** autonomes.

```
+---------+    +----------+    +--------+    +---------+    +------+    +--------+
| S1      |--->| S2       |--->| S3     |--->| S4      |--->| S5   |--->| S6     |
| Intake  |    | Preproc. |    | Detect |    | Resolve |    | Mask |    | Output |
+---------+    +----------+    +--------+    +---------+    +------+    +--------+

(etage inverse) S7 Reinject : JSON/XML avec balises -> JSON/XML restitue
```

## S1 - Intake : lecture du fichier

**Entree** : `Path` vers un fichier `.txt`
**Sortie** : `RawDocument` (texte brut + metadata)

**Responsabilites** :
- Verifier l'existence et l'accessibilite
- Lire en UTF-8 (fallback latin-1 si echec)
- Refuser fichiers vides ou trop gros (`max_size_bytes`)
- Capturer metadata : taille, mtime, encodage

**Code** : `src/carnaval/stages/s1_intake.py`

**Tests** : `tests/unit/test_s1_intake.py`

---

## S2 - Preprocess : normalisation + langue

**Entree** : `RawDocument`
**Sortie** : `NormalizedDocument` (texte normalise + langue detectee)

**Responsabilites** :
- Detecter la langue (lingua : FR/EN/DE/JA)
- Retirer le BOM
- Normaliser les espaces multiples (option `normalize_spaces`)
- Nettoyer les `|` parasites au milieu des mots (option `cleanup_pipes`,
  desactivee par defaut car risque metier)

**Code** : `src/carnaval/stages/s2_preprocess.py`

---

## S3 - Detect : execution des recognizers

**Entree** : `NormalizedDocument` + `Config`
**Sortie** : `DetectedDocument` (liste de `Span` brute, non deduplique)

**Responsabilites** :
- Charger les deny lists depuis la config
- Executer chaque recognizer :
  - **Universels** : email, URL, IBAN, BIC, header_source
  - **FR** (si langue fr) : phone, fiscal, address, name_patterns
  - **Deny lists** : organization_singleton, organizations, people
  - **AI** : GLiNER (zero-shot multi-langue)
- Collecter tous les Spans sans arbitrer (S4 fera le tri)

**Code** : `src/carnaval/stages/s3_detect.py`

---

## S4 - Resolve : deduplication des chevauchements

**Entree** : `DetectedDocument`
**Sortie** : `ResolvedDocument` (Spans non chevauchants, ordonnes)

**Responsabilites** :
- Pour chaque groupe de Spans qui se chevauchent, garder un seul.
- Critere de selection (decroissant) :
  1. **Longueur** : le span le plus long gagne (englobant)
  2. **Score** : plus eleve gagne
  3. **Priorite recognizer** : `OrgSingleton` > `OrganizationsDenyList` > ... > `GLiNER`

**Pourquoi pas "score d'abord ?"** Parce qu'un EMAIL (score 0.95) qui contient un
sous-domaine (URL score 0.7) doit prevaloir : le span englobant gagne meme
si son score est legerement inferieur, sinon on perd l'integrite de
l'email.

**Code** : `src/carnaval/stages/s4_resolve.py`

---

## S5 - Mask : placeholders + alimentation du vault

**Entree** : `ResolvedDocument` + `Vault`
**Sortie** : `MaskedDocument` (texte anonymise + Spans enrichis du placeholder)

**Responsabilites** :
- Pour chaque Span, allouer un placeholder :
  - Singleton (`ORG_SINGLETON`) -> `[ORG]` (pas d'index)
  - Autre -> `[TYPE_n]` avec n incremental par type
- Garantir la **coherence** : si une valeur a deja un placeholder dans le
  vault, on le reutilise (toutes les occurrences -> meme balise).
- Construire le texte anonymise (substitution **de droite a gauche** pour
  ne pas casser les offsets).
- Enregistrer chaque mapping dans le vault.

**Code** : `src/carnaval/stages/s5_mask.py`

---

## S6 - Output : ecriture multi-format

**Entree** : `MaskedDocument` + `Vault` + chemin outbox
**Sortie** : `WrittenOutput` (chemins de 8 fichiers ecrits)

**Responsabilites** : ecrire dans `outbox/` :
- `txt/<stem>_anonymise.txt`
- `json/<stem>_anonymise.json` (text + entities + meta)
- `jsonl/<stem>_entities.jsonl` (1 entite par ligne)
- `xml/<stem>_anonymise.xml`
- `conll/<stem>_anonymise.conll` (BIO)
- `html/<stem>_anonymise.html` (visualisation)
- `vault/<stem>_vault.enc` (AES-256-GCM)
- `meta/<stem>_meta.json` (audit, **sans donnees sensibles**)

**Code** : `src/carnaval/stages/s6_output.py`
**Serializers** : `src/carnaval/core/serializers.py`

---

## S7 - Reinject : restauration (etage inverse)

**Entree** : JSON ou XML avec placeholders + Vault
**Sortie** : JSON ou XML avec valeurs originales restituees

**Auto-detection** du format par le premier caractere :
- `{` ou `[` -> JSON
- `<` -> XML
- autre -> fallback texte brut

**Code** : `src/carnaval/stages/s7_reinject.py`

---

## Orchestration : pipeline.py

Le module `src/carnaval/pipeline.py` enchaine S1->S6 :

```python
masked, written, config = run_anonymization(
    input_path=...,
    outbox_dir=...,
    vault_password=...,
    profile="acknowledge",
)
```

Chaque etage emet un log structure (sans donnees sensibles, grace au
filtre `_redact_sensitive` du logger).
