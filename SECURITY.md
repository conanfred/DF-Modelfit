# Politique de sécurité

## Versions supportées

Nous nous efforçons de corriger les vulnérabilités de sécurité pour la dernière version majeure du projet.

## Signaler une vulnérabilité

Si vous découvrez un problème de sécurité (ex. fuite de données, exécution de code, exposition de chemins ou de tokens), merci de **ne pas** ouvrir une issue publique.

- **Contact** : [contact@dfairesearch.com](mailto:contact@dfairesearch.com) ou [https://dfairesearch.com/](https://dfairesearch.com/).
- Décrivez le problème de manière suffisante pour qu’il puisse être reproduit, sans publier de code d’exploitation.
- Nous nous engageons à vous répondre et à traiter les rapports de bonne foi dans un délai raisonnable.

## Périmètre

- Code de ce dépôt (backend FastAPI, frontend, scripts).
- Données et fichiers générés localement (`data/`) ne doivent pas contenir de secrets ; l’usage d’un token Hugging Face (`HF_TOKEN`) est optionnel et reste côté serveur.

## Bonnes pratiques

- Ne commitez jamais de clés API, mots de passe ou jetons dans le dépôt.
- Utilisez des variables d’environnement pour les secrets (ex. `HF_TOKEN`).
- Gardez les dépendances à jour (`pip install -r requirements.txt`, mise à jour régulière des paquets).

---

# Security Policy (English)

## Supported versions

We aim to fix security vulnerabilities for the latest major version of the project.

## Reporting a vulnerability

If you discover a security issue (e.g. data leak, code execution, path or token exposure), please **do not** open a public issue.

- **Contact**: [contact@dfairesearch.com](mailto:contact@dfairesearch.com) or [https://dfairesearch.com/](https://dfairesearch.com/).
- Describe the issue in enough detail to reproduce it, without publishing exploit code.
- We will respond and handle good-faith reports in a reasonable time.

## Scope

- Code in this repository (FastAPI backend, frontend, scripts).
- Locally generated data and files (`data/`) must not contain secrets; use of a Hugging Face token (`HF_TOKEN`) is optional and remains server-side.

## Best practices

- Never commit API keys, passwords, or tokens to the repository.
- Use environment variables for secrets (e.g. `HF_TOKEN`).
- Keep dependencies up to date (`pip install -r requirements.txt`, regular package updates).
