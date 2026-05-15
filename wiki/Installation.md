# Installation

This page covers installing Carnaval, its dependencies, the optional neural
recognizer, and an offline (air-gapped) setup.

## Requirements

| Item | Requirement |
|---|---|
| Python | 3.11 or newer (tested on 3.13) |
| OS | Windows, Linux, macOS |
| RAM | 2 GB minimum (the GLiNER model loads ~500 MB) |
| Disk | ~1 GB for the virtual environment and cached models |
| Network | Needed once, for the first GLiNER download - fully offline afterwards |

## Standard installation

### 1. Get the code

```bash
git clone <repository-url>
cd carnaval
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux / macOS / Git Bash
source .venv/bin/activate
```

### 3. Install the dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---|---|
| `pycryptodome` | AES-256-GCM vault encryption |
| `PyYAML` | YAML configuration loading |
| `python-dotenv` | `.env` loading |
| `structlog` | structured logging |
| `lingua-language-detector` | language detection |
| `gliner` | optional zero-shot neural PII recognizer (pulls in `torch` + `transformers`) |
| `pytest`, `pytest-cov` | test suite |

### 4. Configure the vault password

```bash
cp .env.example .env
```

Edit `.env` and set a strong secret (16 characters minimum, 32+ recommended):

```
CARNAVAL_VAULT_PASSWORD=a-strong-randomly-generated-secret
CARNAVAL_LOG_LEVEL=INFO
```

**Never commit `.env`** - it is already listed in `.gitignore`.

### 5. Verify the installation

```bash
pytest -m "not slow"
```

The slow tests are deselected because they require the GLiNER model download.

```bash
python -c "from carnaval.pipeline import run_anonymization; print('OK')"
```

### 6. Run a first live test

```bash
python anonymize.py profiles/acknowledge/fixtures/sample_ack_globex.txt \
    --profile acknowledge --no-gliner
```

Check that `outbox/txt/sample_ack_globex_anonymise.txt` was created.

## The neural recognizer (GLiNER)

GLiNER is the optional **AI recognizer** - a zero-shot Named Entity Recognition
model that catches free-form `PERSON`, `ORGANIZATION` and `LOCATION` mentions
that regex and deny lists miss.

It is part of `requirements.txt`. The model
(`urchade/gliner_multi_pii-v1`, ~500 MB) is downloaded from HuggingFace **on
first use only** - this takes a few minutes. Subsequent runs use the local
cache (`~/.cache/huggingface`).

To skip it entirely (faster, regex + deny lists only):

```bash
python anonymize.py inbox/doc.txt --profile acknowledge --no-gliner
```

> If your project packaging exposes an extra such as `pip install carnaval[ai]`,
> that extra corresponds exactly to this `gliner` dependency. With the plain
> `requirements.txt` install it is already present.

## Offline / air-gapped installation

To deploy on a machine with no internet access:

**On a connected machine:**

```bash
pip download -r requirements.txt -d wheels/
python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_multi_pii-v1')"
```

Then copy the `wheels/` folder and `~/.cache/huggingface/` to the target machine.

**On the target machine:**

```bash
pip install --no-index --find-links=wheels/ -r requirements.txt
```

Place the cached HuggingFace files in the same `~/.cache/huggingface/` location.

## Next steps

- [Quickstart](Quickstart.md) - run your first anonymization
- [Vault and Security](Vault-and-Security.md) - generate a strong password
- [Troubleshooting](Troubleshooting.md) - if something goes wrong
