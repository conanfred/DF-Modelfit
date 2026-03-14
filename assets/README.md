# Assets

## Créer DEMO.gif à partir de DEMO.mp4

Pour que la démo s’affiche directement dans le README sur GitHub, générez un fichier **DEMO.gif** à la racine du projet à partir de **DEMO.mp4**.

### Avec ffmpeg (recommandé)

À la racine du projet :

```bash
ffmpeg -i DEMO.mp4 -vf "fps=10,scale=720:-1:flags=lanczos" -c:v gif DEMO.gif
```

- `fps=10` : 10 images par seconde (réduit la taille du GIF).
- `scale=720:-1` : largeur 720 px (hauteur automatique). Vous pouvez mettre `480` pour un GIF plus léger.

### Variante plus légère (moins de couleurs)

```bash
ffmpeg -i DEMO.mp4 -vf "fps=8,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 DEMO.gif
```

Une fois **DEMO.gif** créé à la racine, le README l’affichera à la place du poster.
