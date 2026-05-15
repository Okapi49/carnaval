# 03 - Deploiement production

## Principes

carnaval est un **outil de ligne de commande**, pas un service. Pour le
mettre en production :
1. Installer dans un dossier dedie (cf. [02_install.md](02_install.md))
2. Stocker le password du vault dans un coffre d'entreprise (Vault Hashicorp,
   AWS Secrets Manager, Azure Key Vault...)
3. Brancher en amont/aval d'un pipeline existant (cron, NiFi, Airflow,
   PowerShell scheduler...)

## Architecture deploiement type

```
+-----------+
| Extracteur|   (PDF -> TXT)
|   PDF     |
+-----+-----+
      |
      v
   inbox/<doc>.txt
      |
      v
+-----------+
| anonymize.py (carnaval)
+-----+-----+
      |
      v
   outbox/txt/<doc>_anonymise.txt
      |
      v
+-----------+
| Envoi LLM | (Sonnet via Bedrock, etc.)
+-----+-----+
      |
      v
   response.json
      |
      v
+-----------+
| reinject.py (carnaval)
+-----+-----+
      |
      v
   final.json --> consommateur metier
```

## Variables d'environnement

| Variable | Role | Critique |
|---|---|---|
| `CARNAVAL_VAULT_PASSWORD` | Mot de passe du vault | OUI |
| `CARNAVAL_LOG_LEVEL` | Niveau de log (DEBUG/INFO/WARNING/ERROR) | Non |

## Gestion du password en production

**Mauvais** : fichier `.env` sur le serveur en clair.

**Bon** :
- Linux : variable d'env injectee par systemd (`EnvironmentFile=/etc/secrets/carnaval`)
- Windows : variable systeme injectee par le service ou la tache planifiee
- Cloud : secret manager (Vault, AWS SM, Azure KV) recupere a chaque run

Exemple PowerShell :

```powershell
$env:CARNAVAL_VAULT_PASSWORD = (Get-VaultSecret -Path 'carnaval/vault-pwd').Value
python anonymize.py inbox\doc.txt --profile acknowledge
```

## Audit et logs

Les logs JSON structures (`--log-level INFO`) emettent par etage :

```json
{"event":"s5_mask_done","by_category":{"PERSON":2,"EMAIL":1},"timestamp":"..."}
```

**Aucune valeur en clair** dans les logs (filtre `_redact_sensitive` actif).

Pour integration SIEM :
```bash
python anonymize.py inbox/doc.txt --profile acknowledge \
    --log-level INFO 2>> /var/log/carnaval/audit.jsonl
```

## Performance attendue

| Configuration | Latence par document |
|---|---|
| GLiNER off (regex + denylist) | **<2 secondes** |
| GLiNER on, CPU x86 16 Go RAM | **15-20 secondes** |
| GLiNER on, GPU CUDA | **<5 secondes** (non teste) |

Le premier appel inclut le telechargement du modele HuggingFace
(~80-120s avec connexion correcte).

## Strategie de cycle de vie du vault

### Rotation

Le password du vault peut etre change : il faut alors re-chiffrer tous
les vaults actifs. Procedure :

```python
import os
from pathlib import Path
from carnaval.core.vault import Vault

old_pwd = os.environ["OLD_PASSWORD"]
new_pwd = os.environ["NEW_PASSWORD"]

for vault_file in Path("outbox/vault").glob("*.enc"):
    v = Vault(password=old_pwd, path=vault_file)
    v.load()
    v_new = Vault(password=new_pwd, path=vault_file)
    v_new.forward = v.forward
    v_new.backward = v.backward
    v_new.save()
```

### Purge

Les vaults peuvent etre purges apres N jours (apres que le LLM
downstream a fini son traitement et que la reinjection est faite).

```bash
find outbox/vault -name "*.enc" -mtime +30 -delete
```

## Securite reseau

carnaval n'ouvre **aucun port reseau**. Il lit un fichier, ecrit dans
`outbox/`. Pas de service, pas de bind. Plus simple a auditer.

## Surveillance

Metriques recommandees a remonter :
- Nombre de documents anonymises par heure
- Latence moyenne par etage
- Echecs (Spans=0, langue=unknown, vault save failure)
- Taille du dossier outbox/vault (alerter si > X Go)
