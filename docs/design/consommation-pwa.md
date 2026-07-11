# Consommation future des assets dans la PWA

- **Statut** : contrat préparatoire ; aucun shell Dioxus métier n’est créé à ce stade.

## Fichiers

Les dérivés publics vivent dans `apps/web/assets/`. Les fichiers de `assets/brand/` restent les sources de marque. La génération s’exécute avec :

```sh
./scripts/generate-assets.sh
python3 scripts/test-assets.py
```

## Manifest web proposé

Quand le shell PWA sera créé, son manifest devra référencer au minimum :

```json
{
  "name": "Boussole Politique",
  "short_name": "Boussole",
  "description": "Compare tes positions aux votes, sans étiquette.",
  "icons": [
    { "src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/assets/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" },
    { "src": "/assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

Le `theme_color` et le `background_color` devront provenir du thème/tokens consommés depuis `client-kit`, pas d’une seconde source produit codée en dur. Les PNG exigent un fond opaque. `favicon.svg`, `favicon-32.png` et `apple-touch-icon.png` couvrent les navigateurs hors installation PWA.

## Dioxus 0.7

La future application pourra référencer les fichiers avec `asset!`, après instanciation du shell :

```rust,ignore
img {
    src: asset!("/assets/brand/wordmark-horizontal.svg"),
    alt: "Boussole Politique",
}
```

Le wordmark ne doit pas remplacer un titre textuel de page. Son `alt` est vide s’il est adjacent au même nom en texte.

## Cache et intégrité

- inclure `assets/brand/manifest.json` dans la preuve de release ;
- versionner les URLs ou invalider le service worker à chaque changement de hash ;
- ne jamais mettre en cache des données citoyennes avec ces assets publics ;
- vérifier les hashes avant publication ;
- ne pas annoncer ces fichiers comme icônes définitives App Store/Play avant revue produit.

## Fontes et thèmes

Les wordmarks déclarent Plus Jakarta Sans puis Inter. La PWA devra consommer les fontes locales et le bundle vérifié Libre IA Design System 2.0 depuis `client-kit`. Aucune fonte distante ne doit être ajoutée. L’icône opaque est identique en clair et sombre ; les wordmarks à `currentColor` s’adaptent au thème.
