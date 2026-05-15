# `profiles_private/` — Profils prives

Ce dossier accueille les profils d'anonymisation contenant vos **donnees
reelles** : vrais noms d'entreprise, contacts commerciaux, adresses de
sites, etc.

## Pourquoi un dossier separe

Ces deny lists sont sensibles : elles ne doivent jamais etre publiees dans
un repo public. Le `.gitignore` du projet ignore donc tout le contenu de
`profiles_private/`, **a l'exception** de ce `README.md` et du modele
`example_acknowledge/`.

```
profiles_private/
|-- README.md            <- ce fichier (versionne)
|-- example_acknowledge/ <- modele fictif a copier (versionne)
|-- ma_societe/          <- VOS profils reels (ignores par Git)
```

## Mode d'emploi

1. Copiez le modele : `example_acknowledge/` -> `ma_societe/` (nom libre).
2. Remplacez les valeurs fictives par vos vraies donnees dans les YAML.
3. Pointez le pipeline d'anonymisation sur votre profil prive.

Votre profil reel restera local : Git ne le suivra pas, aucune fuite
possible vers un repo public.

## Modele fourni

`example_acknowledge/` est un profil PRIVE EXEMPLE entierement fictif,
calque sur le profil public `profiles/acknowledge/`. Utilisez-le comme
point de depart. Voir `example_acknowledge/README.md` pour le detail.
