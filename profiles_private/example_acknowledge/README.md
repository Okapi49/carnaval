# Profil prive : `example_acknowledge`

Modele de profil **prive** entierement fictif. Il montre la structure
attendue d'un profil contenant vos donnees reelles (deny lists), sans
exposer la moindre information sensible.

## A quoi ca sert

Le profil public `profiles/acknowledge/` ne contient que des donnees
fictives Apache 2.0. Pour anonymiser vos vrais accuses de reception, vous
avez besoin de deny lists avec vos vrais noms d'entreprise, contacts et
adresses. Ces listes ne doivent jamais finir dans un repo public : on les
place donc dans `profiles_private/`, ignore par Git.

## Mode d'emploi

1. Copiez ce dossier sous un nom parlant :
   `profiles_private/example_acknowledge/` -> `profiles_private/ma_societe/`
2. Editez les fichiers YAML et remplacez les valeurs fictives
   (`Acme Corp`, `Globex`, `Jane Doe`, `Springfield`, `Main Street`...)
   par vos vraies valeurs.
3. Pointez le pipeline sur votre profil prive lors de l'anonymisation.

## Structure

```
example_acknowledge/
|-- profile.yaml                              <- metadonnees du profil
|-- allow_lists/
|   |-- product_refs.yaml                     <- references produit a preserver
|-- deny_lists/
    |-- organization_singleton.yaml           <- VOTRE entreprise -> [ORG]
    |-- organizations.yaml                    <- fournisseurs a masquer
    |-- people.yaml                           <- contacts a masquer
    |-- places/
        |-- fr.yaml                           <- toponymes a masquer
```

Toutes les valeurs livrees ici sont **fictives** et servent uniquement
d'illustration.
