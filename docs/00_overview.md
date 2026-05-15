# 00 - Vue d'ensemble

## Quel probleme resout carnaval

Vous voulez utiliser un LLM cloud (Sonnet, GPT, Mistral...) pour traiter
des documents textes contenant des donnees personnelles ou confidentielles :
- Accuses de reception fournisseurs
- Factures
- Emails professionnels
- Contrats, CV, dossiers medicaux, ...

**Probleme** : ces documents contiennent des entites sensibles (noms,
emails, IBAN, adresses) qui ne doivent pas etre transmises en clair a
un service externe.

**Solution carnaval** :

```
DOCUMENT BRUT --> [carnaval] --> DOCUMENT BALISE --> LLM cloud
                                                          |
DOCUMENT FINAL <-- [carnaval] <-- JSON/XML reponse <------+
```

1. **Avant l'envoi** : remplacer les entites sensibles par des balises
   `[PERSON_1]`, `[EMAIL_2]`, `[ORG]`, etc. Stocker les mappings dans un
   vault chiffre local.
2. **Apres la reponse** : restaurer les valeurs originales dans la
   structure JSON ou XML retournee.

## Principes

### 1. Reversibilite

Chaque entite masquee est associee a un placeholder unique. Le mapping
est stocke chiffre (AES-256-GCM) sur le disque local. Sans le password,
impossible de remonter aux valeurs originales.

### 2. Coherence

La meme valeur originale recoit toujours le **meme** placeholder dans un
run. Exemple : "Alice Doe" apparait 5 fois dans le texte ? -> 5 fois
`[PERSON_1]`. Le LLM peut donc raisonner sur les references.

### 3. Locality

Aucun appel reseau pour anonymiser. GLiNER tourne localement (modele
~500 Mo telecharge une fois). Lingua pour la langue. Tout est sur votre
machine.

### 4. Multi-format

Une seule passe d'anonymisation produit le resultat dans 6 formats
courants :
- **TXT** : texte brut avec balises (pour pipe vers LLM)
- **JSON** : structure exploitable (text + entities)
- **JSONL** : streaming (1 entite par ligne)
- **XML** : integration SI legacy / EDI
- **CoNLL** : entrainement de modeles NER
- **HTML** : visualisation colorisee pour debug

### 5. Modularite par etages

Le pipeline est compose de 7 etages autonomes. Chaque etage a un contrat
clair (entree -> sortie) et peut etre teste, remplace ou debuge en
isolation.

### 6. Profils metier

Un profil decrit un **type de document** (acknowledge, invoice, email...)
avec ses entites typiques, ses listes negatives, ses regles d'arbitrage.
Les profils sont des YAML editables sans toucher au code.

### 7. Pas de magie

Aucun framework opaque entre l'utilisateur et le pipeline. Chaque
recognizer est une **fonction pure** Python qui prend un texte et renvoie
des Spans. Pas d'heritage, pas de class hierarchy, pas de hook
implicite.

## Ce que carnaval ne fait pas

- **Pas d'OCR** : entree = texte deja extrait. Pour extraire d'un PDF,
  utiliser un outil amont (pdfplumber, pypdf, tesseract...).
- **Pas d'envoi au LLM** : carnaval prepare et restaure, l'appel reseau
  est de votre responsabilite.
- **Pas de batch built-in** : un fichier a la fois. Pour traiter en lot,
  ecrire une boucle shell ou Python autour de `anonymize.py`.

## Pour aller plus loin

- [01_architecture_etages.md](01_architecture_etages.md) - le pipeline
  en detail
- [04_configuration.md](04_configuration.md) - configuration et profils
- [07_securite.md](07_securite.md) - le vault et le password
