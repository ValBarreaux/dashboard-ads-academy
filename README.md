# Robot dashboard ads — Académie Excellence

Met à jour automatiquement, chaque jour à midi, le dashboard publicitaire publié sur
**https://academie-excellence-ads.netlify.app** — sans navigateur, sans intervention.

## Ce que fait le robot
1. `fetch_meta.py` : appelle l'API Meta Ads (token System User) → écrit `ads_meta.tsv` (lifetime) + `active_7d.tsv` (7 jours).
2. `analyze.py` : agrège par créative → `ads_analysis.json`.
3. `build_dashboard3.py` : génère `dashboard_ads.html` (benchmark + pilotage + KPI + superwinners + historique complet).
4. Déploiement Netlify du fichier sur le site existant (même URL).

Tout est piloté par `.github/workflows/refresh.yml` (GitHub Actions, cron quotidien + bouton manuel).

## Installation (une seule fois)

### 1. Créer le dépôt
- Sur github.com → **New repository** → nom au choix (ex. `dashboard-ads-academie`) → **Private** → Create.
- **Add file → Upload files** → glisser TOUT le contenu de ce dossier (y compris le dossier `.github`) → Commit.

### 2. Ajouter les 2 secrets
Dans le dépôt → **Settings → Secrets and variables → Actions → New repository secret** :
- `META_ACCESS_TOKEN` = ton token System User Meta (permission `ads_read`).
- `NETLIFY_AUTH_TOKEN` = un token personnel Netlify (app.netlify.com → **User settings → Applications → Personal access tokens → New access token**).

Les secrets ne sont visibles par personne (même pas dans les logs).

### 3. Lancer une première fois
- Onglet **Actions** → workflow **Refresh dashboard ads** → **Run workflow**.
- Si tout est vert ✅, le lien est à jour. Ensuite ça tourne tout seul chaque jour à ~12h Paris.

## Réglages utiles
- **Heure** : dans `refresh.yml`, ligne `cron: "0 10 * * *"` (10:00 UTC = 12:00 Paris l'été).
- **Compte pub / conversions RDV** : constantes en haut de `fetch_meta.py`.
- **Site Netlify cible** : `--site=...` dans `refresh.yml` (siteId `a7c6372a-aeb8-4749-9e8a-8b11e6a5a9f2`).
- **Taux AED→EUR** : `RATE` dans `analyze.py` et `build_dashboard3.py`.

Aucune dépendance à installer : tout tourne avec Python standard + Netlify CLI (via npx).
