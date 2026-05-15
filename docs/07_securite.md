# 07 - Securite

## Le vault chiffre

### Algorithme

| Element | Valeur |
|---|---|
| Chiffrement symetrique | AES-256-GCM |
| Derivation de cle | PBKDF2-HMAC-SHA256, 600 000 iterations |
| Sel | 16 octets aleatoires par fichier |
| Nonce GCM | 16 octets aleatoires par fichier |
| Tag d'authentification | 16 octets (verification d'integrite) |
| Format binaire | `[salt 16][nonce 16][tag 16][ciphertext N]` |

### Force

- Mode AES-256-GCM : chiffrement authentifie. Toute alteration du fichier
  est detectee a la lecture (VaultError).
- PBKDF2 600k iterations : ralentit les attaques par dictionnaire/brute force
  (delai non-trivial meme avec GPU).
- Nonce aleatoire par fichier : pas de reuse, pas de fuite par comparaison
  de chiffres.

### Limitation

- Le password doit etre fort. 16 caracteres minimum, idealement >32, genere
  aleatoirement.
- Le password en RAM pendant l'execution. Si la machine est compromise au
  niveau OS, les valeurs en clair sont accessibles. **Ce n'est pas un HSM**.

## Le password

### Generer un password fort

Linux/macOS :
```bash
openssl rand -base64 48
```

Windows PowerShell :
```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
```

### Stockage

**A NE PAS FAIRE** :
- Commit dans le repo (`.env` est git-ignore par defaut, garder).
- Logger meme partiellement.
- Passer en argument de ligne de commande (visible dans `ps`, history).
- Hardcoder dans le code.

**A FAIRE** :
- Variable d'environnement `CARNAVAL_VAULT_PASSWORD`, injectee par :
  - Systemd : `EnvironmentFile=/etc/secrets/carnaval` (mode 600)
  - Windows : variable systeme du service / tache planifiee
  - Cloud : secret manager (Vault, AWS SM, Azure KV) lu au demarrage

### Rotation

Cf. [03_deploiement_production.md](03_deploiement_production.md#rotation).

## Anti-fuite dans les logs

Le logger structlog (`carnaval/core/logger.py`) embarque un processor
`_redact_sensitive` qui interdit toute valeur sous les cles suivantes :

```python
SENSITIVE_KEYS = frozenset({
    "original", "raw_text", "raw", "text",
    "mapping", "vault", "vault_contents",
    "password", "secret",
    "forward", "backward",
})
```

Si un appelant tente `log.info("event", original="Alice")`, le log emis sera :
`{"event":"event","original":"<REDACTED>"}`.

C'est un **garde-fou par defaut**. Si vous ajoutez des cles dans le code,
n'oubliez pas d'enrichir cette frozenset.

## Aucune fuite reseau

carnaval n'ouvre **aucun port reseau** et ne fait **aucun appel sortant**
apres le telechargement initial du modele GLiNER. Vous pouvez :
- Tester avec `tcpdump` / wireshark
- Deployer dans un container sans interface reseau
- Bloquer toute sortie firewall pour le user qui execute carnaval

## Surface d'attaque

### Fichier vault.enc compromis

Sans le password, le contenu est illisible (AES-256-GCM). Avec le password,
toutes les valeurs originales sont accessibles.

**Mitigation** :
- Stocker `outbox/vault/` dans une partition chiffree au repos
- Purger les vaults apres traitement (cron : `find ... -mtime +30 -delete`)
- Rotation du password (cf. doc deploiement)

### Fichier d'entree inbox/

Le fichier d'entree contient les donnees sensibles **en clair**. Il faut :
- Restreindre les droits POSIX (chmod 600)
- Le supprimer apres anonymisation
- Stocker sur partition chiffree

### Metadata meta.json

Le fichier `outbox/meta/<stem>_meta.json` contient :
- Nb d'entites par categorie (statistique, non sensible)
- Chemin source (peut etre sensible si le nom du fichier reflete le client)

Aucune **valeur originale** n'est dans le meta.

## Audit

Pour traces SOC :

```bash
python anonymize.py inbox/doc.txt --profile acknowledge \
    --log-level INFO 2>> /var/log/carnaval/audit.jsonl
```

Format de chaque ligne :
```json
{"event":"s5_mask_done","by_category":{"PERSON":2,"EMAIL":1},"timestamp":"..."}
```

Tracabilite : on sait combien d'entites de chaque type ont ete masquees,
mais on ne sait jamais LESQUELLES (zero fuite).

## Conformite RGPD

carnaval permet de mettre en oeuvre la **pseudonymisation** au sens du
RGPD (art. 4.5) :
- Donnees personnelles remplacees par des identifiants ne permettant
  plus l'identification sans donnees supplementaires
- Les donnees supplementaires (vault) sont conservees separement
  et techniquement protegees

**Attention** : carnaval n'est pas un certificat RGPD. C'est un outil
technique qui aide a la conformite. La conformite globale depend du
contexte d'usage, des durees de retention, des contrats DPA avec les
LLM externes, etc.
