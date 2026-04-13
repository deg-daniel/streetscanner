# Street Scanner 🛰️

Outil de processing StreetView et d'analyse d'images via VQA (Visual Question Answering). Ce projet permet de scanner un itinéraire, de récupérer les vues Google Street View perpendiculaires à la route et de détecter des objets ou scènes spécifiques via un modèle de vision (Gemma-4) en local.

## 🚀 Démo
Voici un aperçu de l'outil en action :

[![demo](video.gif)](video.gif)

## 🛠️ Installation
Utilise `uv` pour un setup ultra-rapide et déterministe :

```bash
# Clone le repo
git clone [https://github.com/deg-daniel/streetscanner.git](https://github.com/deg-daniel/streetscanner.git)
cd street-scanner

# Install dependencies et venv
uv sync

# Configure ta clé API Google Maps
export GOOGLE_MAPS_API_KEY="VOTRE_CLEF"