# 09 - Troubleshooting

## VaultError: Mauvais password ou vault corrompu

**Cause** : le `CARNAVAL_VAULT_PASSWORD` utilise pour `reinject.py` ne
correspond pas a celui utilise pour `anonymize.py`.

**Fix** :
- Verifier la variable d'environnement
- Si le password a ete change entre les deux runs, on ne peut plus
  dechiffrer le vault. Soit on regenere le vault (re-anonymiser le texte),
  soit on retrouve l'ancien password.

## VaultError: Password trop court

**Cause** : moins de 16 caracteres.

**Fix** : utiliser un password >= 16 chars, idealement >= 32.

```bash
openssl rand -base64 48
```

## IntakeError: Fichier introuvable / vide / trop gros

- **Introuvable** : verifier le chemin (relatif vs absolu)
- **Vide** : carnaval refuse les fichiers de 0 octet. Verifier l'extraction
  amont du PDF.
- **Trop gros** : taille max par defaut 50 Mo. Augmenter via :
  ```python
  intake(path, max_size_bytes=100 * 1024 * 1024)
  ```

## GLiNER : telechargement bloque

**Symptome** : lors du premier appel, hangs sur "Fetching files...".

**Cause** : firewall/proxy bloque huggingface.co.

**Fix** :
- Verifier acces a `huggingface.co` / `cdn-lfs.huggingface.co`
- Configurer un proxy HTTPS : `HTTPS_PROXY=...`
- Telecharger sur une autre machine et copier `~/.cache/huggingface/` sur
  la machine cible

Alternative : desactiver GLiNER (`--no-gliner`) - le pipeline se replie sur
regex + denylist uniquement.

## Performance lente

| Symptome | Cause probable | Fix |
|---|---|---|
| Premier appel >60s | Telechargement modele HF | Normal, attendre |
| Chaque appel >15s | GLiNER sur CPU | Acceptable, ou GPU si dispo |
| Avec `--no-gliner` toujours lent | Texte tres long | Verifier la taille (gros document = nombreux Spans) |

## Trop de faux positifs

**Symptome** : des mots non sensibles sont masques (ex: "PARC" devient `[BIC_1]`).

**Causes possibles** :
- Seuil GLiNER trop bas : augmenter via `--gliner-threshold 0.6`
- Un recognizer custom mal calibre

**Fix** :
- Inspecter le JSON de sortie : voir quel `recognizer` produit le faux positif
- Ajuster le regex en cause, ou augmenter le score threshold

## Pas assez de detection (fuite)

**Symptome** : un nom evident n'est pas masque.

**Causes** :
- GLiNER desactive (`--no-gliner`) : il manque la detection PERSON contextuelle
- Le nom n'est pas dans les deny lists et n'est pas matchable par regex
- Le seuil GLiNER est trop haut

**Fix** :
- Activer GLiNER, baisser le seuil a 0.3
- Ajouter le nom aux `deny_lists/people.yaml`

## Texte parasite (caracteres `|` au milieu des mots)

**Symptome** : extraction PDF defaillante, texte comme `Chi | mieBERTAUX`.

**Fix** : activer `--cleanup-pipes` :

```bash
python anonymize.py inbox/doc.txt --profile acknowledge --cleanup-pipes
```

Attention : risque de modifier des contenus metier (rare mais possible).

## Encoding latin-1 dans la sortie

**Cause** : le fichier source etait en latin-1 (le fallback s'est active).

**Fix** : aucun. Le contenu est preserve. Si vous voulez forcer UTF-8 en
amont, convertir le fichier avant : `iconv -f latin1 -t utf8 in.txt > out.txt`.

## ImportError: No module named 'carnaval'

**Cause** : execution sans le venv active, ou hors du dossier projet.

**Fix** :
- Activer le venv : `.\.venv\Scripts\activate`
- Lancer depuis la racine du projet : `python anonymize.py ...`

## Erreur de checksum IBAN

**Symptome** : un IBAN valide n'est pas detecte.

**Cause** : le validateur exige mod 97 = 1. Verifier sur
[iban.com/iban-checker](https://www.iban.com/iban-checker) que l'IBAN est
formel.

Si l'IBAN est valide mais non detecte, ouvrir une issue avec un exemple
anonymise (sans la vraie valeur, masque toi-meme avant !).

## Tests echouent apres un changement

**Fix** : isoler par etage.

```bash
pytest tests/unit/test_s3_detect.py -v       # un seul fichier
pytest tests/unit/test_s3_detect.py::TestDetect::test_email_only -v   # un seul test
pytest --lf                                    # uniquement les tests qui ont echoue
```

Lire la trace d'erreur, le message d'assertion donne souvent la valeur
attendue vs recue.

## Logs invisibles / vide

**Cause** : niveau log eleve.

**Fix** :
```bash
python anonymize.py inbox/doc.txt --profile acknowledge \
    --log-level DEBUG --console
```

`--console` rend les logs lisibles (mode JSON par defaut pour
machine-readability).

## Symptomes plus rares

Si rien dans cette liste ne correspond a votre cas :
1. Reproduire avec un texte minimal
2. Lancer avec `--log-level DEBUG --console`
3. Capturer la trace complete
4. Ouvrir une issue avec :
   - Version Python
   - OS
   - Texte d'entree (anonymise !)
   - Commande exacte
   - Output complet
   - Trace d'erreur
