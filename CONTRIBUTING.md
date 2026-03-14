# Contribuer à DF Modelfit

Merci de votre intérêt pour contribuer à **DF Modelfit**. Ce document décrit comment proposer des correctifs, des améliorations ou des idées.

## Licence et usage

- **Usage gratuit** pour le public (particuliers, usage non commercial).
- Les sociétés et l’usage en recherche doivent Entreprises et laboratoires : seule une **licence écrite et signée de la main** de l'auteur est acceptée. Contacter **DF AI Research** : [contact@dfairesearch.com](mailto:contact@dfairesearch.com) — [https://dfairesearch.com/](https://dfairesearch.com/).
- En contribuant, vous acceptez que vos contributions soient distribuées sous la même licence.

## Comment contribuer

### Signaler un bug

1. Vérifiez qu’une [issue](/issues) similaire n’existe pas déjà.
2. Ouvrez une **nouvelle issue** en utilisant le template « Bug report ».
3. Décrivez le problème, les étapes pour le reproduire, votre environnement (OS, Python, navigateur) et le comportement attendu.

### Proposer une fonctionnalité

1. Ouvrez une **issue** avec le template « Feature request ».
2. Expliquez le cas d’usage, l’objectif et éventuellement une idée de solution.

### Proposer une modification du code

1. **Fork** du dépôt sur GitHub.
2. Créez une **branche** à partir de `main` (ex. `fix/typo-readme` ou `feat/new-filter`).
3. Effectuez vos modifications (code, tests, doc si besoin).
4. **Commit** avec un message clair (ex. `fix: correction du calcul du fit`, `feat: filtre par fournisseur`).
5. Ouvrez une **Pull Request** vers la branche `main` du dépôt original.
6. Remplissez le template de PR et décrivez les changements.

## Conventions

- **Code** : style cohérent avec le projet (Python avec type hints, JS avec les patterns existants).
- **Messages de commit** : de préférence en français ou en anglais, explicites (ex. `fix:`, `feat:`, `docs:`).
- **Documentation** : mettre à jour le README ou les commentaires si vous changez un comportement visible.

## Structure du projet

- `main.py` — point d’entrée FastAPI.
- `api/` — logique métier (système, fit, Hugging Face).
- `static/` — interface web (HTML, CSS, JS).
- `data/` — fichiers JSON des modèles (générés ou de secours).

## Lancer en local

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
# ou lance.bat sous Windows
```

Puis ouvrir http://localhost:5050.

---

# Contributing to DF Modelfit (English)

Thank you for your interest in contributing. This document describes how to suggest fixes, improvements, or ideas.

## License and use

- **Free use** for the public (individuals, personal and non-commercial use).
- **Companies and laboratories**: only a **written license signed by hand** by the author is accepted — no other form (email, click-wrap, verbal). Contact **DF AI Research**: [contact@dfairesearch.com](mailto:contact@dfairesearch.com) — [https://dfairesearch.com/](https://dfairesearch.com/).
- By contributing, you agree that your contributions are distributed under the same terms.

## How to contribute

### Report a bug

1. Check that a similar [issue](/issues) does not already exist.
2. Open a **new issue** using the "Bug report" template.
3. Describe the problem, steps to reproduce, your environment (OS, Python, browser), and expected behaviour.

### Suggest a feature

1. Open an **issue** with the "Feature request" template.
2. Explain the use case, goal, and optionally a solution idea.

### Propose a code change

1. **Fork** the repository on GitHub.
2. Create a **branch** from `main` (e.g. `fix/typo-readme`, `feat/new-filter`).
3. Make your changes (code, tests, docs if needed).
4. **Commit** with a clear message (e.g. `fix: fit calculation`, `feat: provider filter`).
5. Open a **Pull Request** to the `main` branch of the original repo.
6. Fill in the PR template and describe the changes.

## Conventions

- **Code**: style consistent with the project (Python with type hints, JS with existing patterns).
- **Commit messages**: preferably in French or English, explicit (e.g. `fix:`, `feat:`, `docs:`).
- **Documentation**: update README or comments if you change visible behaviour.

## Project structure

- `main.py` — FastAPI entry point.
- `api/` — business logic (system, fit, Hugging Face).
- `static/` — web UI (HTML, CSS, JS).
- `data/` — model JSON files (generated or fallback).

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

Then open http://localhost:5050.

## Questions

Pour toute question sur la licence, l’usage professionnel ou la recherche, contactez **DF AI Research**.

For any question about the license, professional use, or research, contact **DF AI Research**.
