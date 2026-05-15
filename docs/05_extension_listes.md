# 05 - Etendre les listes (deny / allow) sans coder

C'est l'extension la plus frequente : ajouter un fournisseur, un nom, une
variante orthographique.

## Ajouter un fournisseur

Editer `profiles/<type>/deny_lists/organizations.yaml` :

```yaml
organizations:
  - "Globex Inc."
  - "Initech"
  - "Mon Nouveau Fournisseur SAS"     # <-- ajout
  - "MonNouveauFournisseur"           # variante orthographique
```

Lancer une anonymisation -> le nouveau nom est detecte immediatement.
Pas de redemarrage, pas de recompilation, pas de rebuild d'index.

## Ajouter une variante du singleton

L'entreprise mere unique du client :

```yaml
# profiles/<type>/deny_lists/organization_singleton.yaml
organization_singleton:
  - "Acme Corp"
  - "Acme Corporation"
  - "ACME CORP."         # variante avec point
  - "Acme  Corp"         # variante avec double espace
  - "ACMECORP"           # sans espace
```

Toutes les variantes -> meme placeholder `[ORG]`.

## Ajouter un nom de personne recurrent

```yaml
# profiles/<type>/deny_lists/people.yaml
people:
  - "Alice Anderson"
  - "Bob Brown"
  - "John Doe"           # <-- ajout
  - "Jane Doe"
```

NB : ce sont les **noms complets**. Pour les noms detectes par contexte
(M. NOM Prenom, NOM, Prenom), pas besoin de les lister : les regex
`name_patterns` les attrapent.

## Ajouter un domaine email

```yaml
supplier_domains:
  - "globex.example"
  - "mondomaine.com"     # <-- ajout
```

Sera detecte par UrlRecognizer / EmailRecognizer.

## Specifique a un client (profil prive)

Pour ne **pas** exposer vos donnees reelles dans le repo public :

1. Creer `profiles_private/mon_client_acknowledge/`
2. Y reproduire la structure minimale :

```
profiles_private/mon_client_acknowledge/
|-- profile.yaml
`-- deny_lists/
    `-- organizations.yaml
```

```yaml
# profiles_private/mon_client_acknowledge/profile.yaml
profile:
  name: mon_client_acknowledge
  extends: acknowledge       # informatif
  description: "Profil prive client X"
```

```yaml
# profiles_private/mon_client_acknowledge/deny_lists/organizations.yaml
organizations:
  - "Mon Fournisseur Reel 1"
  - "Mon Fournisseur Reel 2"
```

Le merge **ajoute** les fournisseurs prives a ceux du profil public.

Lancement :

```bash
python anonymize.py doc.txt \
    --profile acknowledge \
    --private mon_client_acknowledge
```

## Verifier la couverture d'une liste

Pour tester qu'une nouvelle variante est bien detectee, lancer sur un
texte d'exemple :

```bash
echo "Test : Mon Nouveau Fournisseur SAS livre demain" > /tmp/test.txt
python anonymize.py /tmp/test.txt --profile acknowledge --no-gliner --console
cat outbox/txt/test_anonymise.txt
# Doit afficher : "Test : [ORG_1] livre demain"
```

## Pieges courants

- **Casse sensible ?** Non, par defaut les deny lists matchent en
  ignorant la casse. `acme corp` matche aussi.
- **Variantes avec accents** ? L'IGNORECASE Python ne supporte pas
  l'unicode folding par defaut. Pour `Stephanie`, ajoutez aussi
  `Stéphanie` dans la liste.
- **Sous-string risk ?** Le pattern utilise des word boundaries, donc
  `Acme` ne matchera pas a l'interieur de `acmeic`. La variante
  "loose" sans word boundary est disponible si necessaire (cf
  `organizations.py:recognize_organizations_loose`).

## Validation : tests de profil

Si vous etendez beaucoup, ajoutez un test :

```python
# tests/integration/test_my_profile.py
def test_my_new_supplier_masked(outbox_dir, tmp_path):
    text = "Commande chez Mon Nouveau Fournisseur SAS"
    inbox = tmp_path / "in.txt"
    inbox.write_text(text, encoding="utf-8")

    masked, _, _ = run_anonymization(
        input_path=inbox,
        outbox_dir=outbox_dir,
        vault_password="test_password_long_enough",
        profile="acknowledge",
        use_gliner=False,
    )
    assert "Mon Nouveau Fournisseur" not in masked.anonymized_text
```
