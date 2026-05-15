# 06 - Etendre les recognizers (coder un nouveau detecteur)

Quand les deny lists ne suffisent pas (entite par pattern), il faut coder
un recognizer.

## Contrat

Un recognizer carnaval est **une fonction pure** :

```python
def my_recognizer(text: str) -> list[Span]:
    ...
```

C'est tout. Pas d'heritage, pas de framework, pas de hook a implementer.

## Exemple : reconnaitre un numero de securite sociale FR

```python
# src/carnaval/recognizers/regex/social_security_fr.py
"""Recognizer pour les numeros de securite sociale francais (NIR)."""

import re
from carnaval.core.span import Span
from carnaval.recognizers.base import regex_to_spans


# NIR : 1 chiffre (sexe) + 2 chiffres (annee) + 2 chiffres (mois) + 5 chiffres
# (commune naissance) + 3 chiffres (numero d'ordre) + 2 chiffres (cle)
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

## Brancher le nouveau recognizer

Editer `src/carnaval/stages/s3_detect.py`, ajouter l'import et la fonction
dans le tuple approprie :

```python
from carnaval.recognizers.regex.social_security_fr import recognize_nir_fr

_FR_REGEX_RECOGNIZERS = (
    recognize_phone_fr,
    recognize_all_fiscal_fr,
    recognize_address_fr,
    recognize_name_patterns,
    recognize_nir_fr,      # <-- ajout
)
```

## Ajouter le placeholder

Dans `src/carnaval/stages/s5_mask.py`, ajouter le mapping :

```python
DEFAULT_PLACEHOLDER_PREFIX = {
    ...,
    "NIR": "NIR",
}
```

Sans cette entree, le prefixe par defaut sera l'entity_type lui-meme, ce
qui peut aussi convenir.

## Ajouter la priorite dans le dedup

Dans `src/carnaval/stages/s4_resolve.py` :

```python
DEFAULT_RECOGNIZER_PRIORITY = {
    ...,
    "NirFrRegex": 85,
}
```

## Ajouter au pattern de re-injection

Dans `src/carnaval/stages/s7_reinject.py`, le pattern est generique :

```python
PLACEHOLDER_PATTERN = re.compile(
    r"\[([A-Z]+(?:_\d+)?)\]"
)
```

Il matche deja `[NIR_1]`, `[NIR_2]`, etc. **Aucune modification necessaire**.

## Tests obligatoires

Creer `tests/recognizers/test_nir.py` :

```python
import pytest
from carnaval.recognizers.regex.social_security_fr import recognize_nir_fr

class TestNirRecognizer:
    @pytest.mark.parametrize("text,expected", [
        ("NIR 1 85 04 75 116 089 25", True),
        ("Numero 1850475116089 25", True),
        ("Pas de NIR ici", False),
        ("Reference 12345", False),
    ])
    def test_match(self, text, expected):
        assert (len(recognize_nir_fr(text)) > 0) == expected
```

Et au moins un test d'integration :

```python
# tests/integration/test_nir_pipeline.py
def test_nir_masked_end_to_end(tmp_path):
    ...
```

## Lancer tous les tests

```bash
pytest -m "not slow"
```

Cible : tout reste vert apres l'ajout du recognizer.

## Recognizer IA (GLiNER zero-shot)

GLiNER detecte deja `person`, `email`, `address`, etc. Pour ajouter un
nouveau label :

```yaml
# config/pipeline.yaml
ai:
  gliner_labels:
    - person
    - email
    - ...
    - social security number    # <-- nouveau label
```

Et dans `src/carnaval/recognizers/ai/gliner_engine.py`, ajouter le
mapping :

```python
LABEL_TO_ENTITY_TYPE = {
    ...,
    "social security number": "NIR",
}
```

GLiNER essaiera de detecter le pattern en mode zero-shot, sans
re-entrainement.

## Recognizer base sur dictionnaire externe

Pour une liste tres longue (>1000 entrees) qui change souvent (ex: liste
d'employes synchronisee avec un Active Directory), vous pouvez :

1. Stocker la liste dans un fichier externe `data/employees.txt`
2. Charger paresseusement :

```python
@functools.lru_cache(maxsize=1)
def _load_employees() -> list[str]:
    path = Path(__file__).parent.parent.parent / "data" / "employees.txt"
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def recognize_employees(text: str) -> list[Span]:
    return recognize_people(text, _load_employees())
```

## Bonnes pratiques

- **Une responsabilite par recognizer** : un fichier = un type d'entite.
- **Tests positifs ET negatifs** : 5 cas True + 5 cas False minimum.
- **Pas d'effet de bord** : la fonction recoit `text`, renvoie `list[Span]`,
  rien d'autre.
- **Pattern compile au module-level** : evite la recompilation a chaque
  appel.
- **Score realiste** : 0.95+ pour regex tres specifiques avec checksum, 0.5-0.7
  pour regex generiques susceptibles de faux positifs.
