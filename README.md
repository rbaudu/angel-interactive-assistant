# Angel Interactive Assistant

Assistant interactif basé sur Angel-server-capture qui propose des activités adaptées via un avatar humain.

## Description

Le projet Angel Interactive Assistant étend les capacités d'Angel-server-capture en ajoutant une couche d'interaction contextuelle. Le système analyse les activités détectées par Angel-server-capture et propose des activités complémentaires adaptées au contexte, comme diffuser de la musique pendant un repas ou raconter une histoire lors de moments d'inactivité.

L'interaction se fait à travers un avatar humain animé qui communique avec l'utilisateur.

## Fonctionnalités

- **Détection d'activités** : Utilise Angel-server-capture pour détecter ce que fait l'utilisateur
- **Recommandations contextuelles** : Suggère des activités adaptées au contexte
- **Avatar interactif** : Représentation humaine pour l'interaction
- **Génération de conversations** : Utilise des LLM pour créer des dialogues naturels
- **Narration d'histoires** : Génère et raconte des histoires adaptées aux préférences
- **Contrôle des appareils** : Gère télévision, lecteur de musique, lumières, etc.
- **Personnalisation** : Adapte les suggestions selon les préférences utilisateur

## Architecture

Le système est composé de plusieurs modules :

1. **Module de détection** (Angel-server-capture)
2. **Moteur de décision** pour analyser les activités et proposer des recommandations
3. **Générateur de contenu** pour créer conversations et histoires
4. **Interface avatar** pour l'interaction avec l'utilisateur
5. **Contrôleur d'appareils** pour piloter les systèmes externes

## Technologies utilisées

- **Backend** : Python avec FastAPI
- **Frontend** : HTML/CSS/JavaScript
- **Avatar 3D** : Three.js
- **Génération de contenu** : APIs Claude/GPT
- **Communication temps réel** : WebSockets
- **Base de données** : MongoDB pour stocker préférences et historique

## Installation

### Prérequis

- Python 3.8+
- Node.js 14+
- MongoDB

### Installation du backend

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp config/config.example.json config/config.json
# Éditer le fichier config.json avec vos paramètres
```

### Installation du frontend

```bash
cd frontend
npm install
```

## Démarrage

### Backend

```bash
cd backend
python -m python.api.main
```

### Frontend

```bash
cd frontend
npm start
```

## Structure du projet

```
angel-interactive-assistant/
│
├── config/
│   └── config.json                # Configuration centralisée
│
├── backend/
│   ├── python/
│   │   ├── decision_engine/       # Moteur de décision
│   │   ├── api/                   # API FastAPI
│   │   ├── content_generator/     # Génération de contenu
│   │   └── device_control/        # Contrôle des appareils
│   │
│   └── java/                      # Optionnel
│
├── frontend/
│   ├── html/                      # Pages HTML
│   ├── css/                       # Styles CSS
│   ├── javascript/                # Scripts JS
│   └── assets/                    # Ressources (modèles, animations)
│
└── docs/                          # Documentation
```

## Intégration avec Angel-server-capture

L'intégration avec Angel-server-capture se fait via une API. Le module Angel-server-capture doit être configuré pour envoyer les données d'activité détectées à l'endpoint `/angel-capture` de l'API d'Angel Interactive Assistant.

## Licence

Ce projet est sous licence MIT.
