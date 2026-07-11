# Boussole Politique — données personnelles et confidentialité MVP

- **Statut** : politique produit proposée ; ne remplace pas une revue juridique

## 1. Principe

Les positions politiques sont des données particulièrement sensibles. Le MVP les traite uniquement sur l'appareil pour fournir la fonctionnalité demandée. Boussole Politique ne crée pas de compte, ne synchronise pas les positions et ne publie pas d'agrégat citoyen.

## 2. Inventaire

| Donnée | Lieu | Finalité | Sortie réseau par défaut |
|---|---|---|---|
| positions et intensité | stockage local | calcul/reveal | non |
| sans avis / passer | local | état du parcours | non |
| version du résumé vu | local | exactitude/historique | non |
| phase pré/post reveal | local | préserver le jugement à froid | non |
| horodatage local | local | ordre et migration | non |
| circonscription choisie | local | reveal local | non |
| texte du miroir | local si activé | auto-contrôle | non |
| export | fichier choisi par l'usager | sauvegarde/portabilité | non, sauf action hors app de l'usager |
| votes et noms d'élus | public | comparaison | oui, dataset public |
| IP technique | hébergeur/CDN | transport/sécurité | inhérente au web, minimisée |

## 3. Garanties MVP

- aucun compte obligatoire ou facultatif ;
- aucun cookie d'identification applicatif ;
- aucune analytics tierce ou first-party ;
- aucune donnée citoyenne dans URL, requête, log, métrique ou rapport de crash ;
- fontes et assets locaux ;
- effacement local disponible ;
- export explicite après avertissement ;
- import local validé ;
- code de stockage et tests publics.

## 4. Transparence utilisateur

Avant la première réponse, afficher une explication courte :

> Tes réponses sont enregistrées sur cet appareil et comparées ici aux votes publics. Boussole Politique ne les reçoit pas. Sans export, elles peuvent être perdues si ton navigateur efface ses données.

Avant export :

> Ce fichier contient tes positions politiques. Toute personne qui y accède peut les lire. Conserve-le dans un emplacement sûr.

L'application ne doit pas affirmer que le stockage navigateur est chiffré ou durable sans preuve propre à la plateforme.

## 5. Élus et autres personnes publiques

Les votes sont publics, mais leur traitement reste soumis aux exigences d'exactitude, information et exercice des droits applicables. Prévoir quatre canaux distincts :

1. erreur de dérivation d'un fait ;
2. contestation éditoriale au regard de la charte ;
3. droit de réponse selon le cadre applicable ;
4. demande d'exercice de droits relatifs aux données personnelles.

Les mises au point officielles sont ingérées ; l'interface indique la position initiale et rectifiée. Le projet documente sa base juridique et ses procédures avant lancement public.

## 6. Rétention

### Appareil

Jusqu'à effacement par l'usager, le navigateur ou une migration. L'application fournit une commande d'effacement complet et ne conserve pas de copie distante.

### Hébergement

Pas de contenu citoyen. Pour les logs techniques d'accès aux artefacts publics, appliquer minimisation, rétention courte, contrôle d'accès et configuration documentée avec l'hébergeur. Ne pas joindre les logs à d'autres sources pour profiler les visiteurs.

### Preuves et issues

Aucune capture, export ou position réelle d'usager ne doit être jointe à une issue. Les fixtures utilisent des données synthétiques clairement marquées.

## 7. Export/import

Le format contient : version de schéma, version de dataset/sélection, positions, versions éditoriales et historique nécessaire. Il exclut tout secret serveur puisqu'il n'y en a pas dans le MVP.

Exigences :

- nom de fichier non révélateur par défaut ;
- pas de téléversement intermédiaire ;
- validation et aperçu avant import ;
- remplacement/fusion explicite ;
- import atomique ;
- option de chiffrement étudiée séparément, sans crypto artisanale.

## 8. Mesure et télémétrie

Le MVP ne collecte rien, même bruité. La télémétrie différentiellement privée de v0.5 est reportée car elle :

- ajoute un endpoint d'écriture ;
- complexifie la démonstration d'anonymisation ;
- ouvre un risque de qualification de sondage et d'auto-sélection ;
- n'est pas nécessaire pour prouver la boucle produit.

Une future proposition devra séparer les finalités, fournir AIPD/analyse statistique, budget de confidentialité, seuils, intervalles d'incertitude, non-jointure et opt-in granulaire.

## 9. Fonctionnalités futures

Sync, compte, push et LLM distant ne sont pas couverts. Le BYO-key en particulier transmettrait potentiellement une opinion en clair à un tiers choisi : il constitue une exception explicite au local-first, pas une variante silencieusement compatible.

Toute évolution exige : consentement/acte explicite lorsque pertinent, minimisation, modèle de menace, politique de clés, information fournisseur, tests et revue juridique avant activation.

## 10. Preuves attendues

- test Playwright qui intercepte tout trafic après saisie d'un canari ;
- inventaire automatique des endpoints et méthodes ;
- inspection du build pour trackers/URLs tierces ;
- test d'effacement IndexedDB ;
- round-trip export/import ;
- preuve que les logs applicatifs ne contiennent que des identifiants publics/techniques autorisés ;
- publication du schéma d'export et de la politique de migration.
