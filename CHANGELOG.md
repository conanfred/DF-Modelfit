# Changelog

Les changements notables du projet sont documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [Non publié]

### Ajouté

- Interface bilingue (FR / EN) avec drapeaux et sauvegarde de la langue.
- Thème clair / sombre (fond noir ou blanc) avec sauvegarde du choix.
- Sauvegarde et chargement des réglages (filtres, scénario, tri, page, langue, thème) au chargement de la page.
- Mise à jour des modèles depuis Hugging Face (54 usages, max par usage configurable : 5, 10, 15, 20).
- Mise à jour automatique au démarrage si la dernière MAJ a plus d'un mois.
- Polling pendant le refresh pour mettre à jour la liste sans attendre la fin du POST.
- Historique des recommandations avec bouton de réinitialisation.
- Légende des 54 usages (pipeline tags) Hugging Face.

### Modifié

- Backend : fusion des modèles même en cas de réponse partielle de l'API HF.
- Timeout du refresh porté à 1 h pour laisser le temps au backend de terminer.

### Corrigé

- Compteur « Modèles » et liste mis à jour correctement après une mise à jour HF (succès ou polling).

---

## [1.0.0] — initial

- Détection matérielle (RAM, CPU, GPU).
- Calcul du fit (parfait, bon, marginal, trop juste).
- Scoring multi-critères (qualité, vitesse, fit, contexte).
- API : `/api/system`, `/api/models`, `/api/recommend`, `/api/refresh`.
- Interface : tableau filtrable, scénarios, comparaison avec graphiques, snippets Python.
- Données : chargement depuis `data/hf_models.json` ou `data/models.json`, mise à jour depuis l'API Hugging Face.

---

# Changelog (English)

Notable changes are documented in this file. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- Bilingual UI (FR / EN) with language selector and saved preference.
- Light / dark theme (black or white background) with saved preference.
- Save and load settings (filters, scenario, sort, page, language, theme) on page load.
- Model update from Hugging Face (54 usages, configurable max per usage: 5, 10, 15, 20).
- Auto-update on startup if last update was over a month ago.
- Polling during refresh to update the list without waiting for the POST to finish.
- Recommendation history with reset button.
- Legend for 54 Hugging Face pipeline tags.

### Changed

- Backend: merge models even when the HF API returns a partial response.
- Refresh timeout increased to 1 hour so the backend can complete.

### Fixed

- "Models" count and list now update correctly after an HF update (success or polling).

---

## [1.0.0] — initial

- Hardware detection (RAM, CPU, GPU).
- Fit calculation (perfect, good, marginal, too tight).
- Multi-criteria scoring (quality, speed, fit, context).
- API: `/api/system`, `/api/models`, `/api/recommend`, `/api/refresh`.
- UI: filterable table, scenarios, comparison with charts, Python snippets.
- Data: load from `data/hf_models.json` or `data/models.json`, update from Hugging Face API.
