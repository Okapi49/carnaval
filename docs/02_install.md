# 02 - Installation

## Pre-requis

- **Python** : 3.11 ou superieur (teste sur 3.13)
- **OS** : Windows, Linux, macOS
- **RAM** : 2 Go minimum (GLiNER charge un modele de ~500 Mo)
- **Disque** : ~1 Go (pour le venv + modeles HuggingFace caches)
- **Reseau** : necessaire au premier lancement (telechargement GLiNER).
  Apres ca, tout fonctionne offline.

## Installation

### 1. Cloner ou recuperer le code

```bash
git clone <url>
cd carnaval
```

### 2. Creer un environnement virtuel

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux / macOS / Git Bash
source .venv/bin/activate
```

### 3. Installer les dependances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Dependances installees :
- `pycryptodome` : chiffrement AES-256-GCM
- `PyYAML`, `python-dotenv` : config
- `structlog` : logs
- `lingua-language-detector` : detection de langue
- `gliner` : NER PII (tire torch + transformers)
- `pytest`, `pytest-cov` : tests

### 4. Configurer le password du vault

```bash
cp .env.example .env
```

Editer `.env` :

```
CARNAVAL_VAULT_PASSWORD=un_secret_fort_de_32_caracteres_minimum
```

**Important** : ne **jamais** commiter `.env`. Le `.gitignore` l'exclut deja.

### 5. Verifier l'installation

```bash
pytest -m "not slow"
```

Resultat attendu : `179 passed, 2 deselected` (les 2 slow tests
necessitent le telechargement du modele GLiNER ~500 Mo).

### 6. Lancer un test live

```bash
python anonymize.py profiles/acknowledge/fixtures/sample_ack_globex.txt \
    --profile acknowledge --no-gliner
```

Verifier que `outbox/txt/sample_ack_globex_anonymise.txt` est cree.

## Activer GLiNER (premier appel)

Le modele est telecharge automatiquement depuis HuggingFace au premier
appel. Ceci prend **~2-5 minutes** selon votre connexion (~500 Mo).

```bash
python anonymize.py profiles/acknowledge/fixtures/sample_ack_globex.txt \
    --profile acknowledge
```

Les appels suivants utilisent le cache local (~/.cache/huggingface).

## Installation offline (sans reseau)

Pour deployer en environnement sans internet :

1. Sur une machine connectee :
   ```bash
   pip download -r requirements.txt -d wheels/
   python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_multi_pii-v1')"
   ```
2. Copier `wheels/` et `~/.cache/huggingface/` sur la machine cible.
3. Sur la machine cible :
   ```bash
   pip install --no-index --find-links=wheels/ -r requirements.txt
   ```

## Verification finale

```bash
python -c "from carnaval.pipeline import run_anonymization; print('OK')"
```

Si OK affichage, l'installation est complete.
