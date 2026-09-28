# TriageBot — PixelForge

Outil en ligne de commande (CLI) développé pour le studio indépendant PixelForge afin d'automatiser le tri, l'analyse et l'escalade des tickets de support du jeu *Dungeon Delivery*.
Le projet s'appuie sur un modèle de langage local via Ollama.

## Prérequis

- Python 3.10 ou supérieur (testé avec Python 3.14)
- Ollama installé et lancé en local (`ollama serve`)
- Modèle `llama3.2:3b` installé :
  ```bash
  ollama pull llama3.2:3b
  ```

## Installation

1. Cloner le dépôt et se placer dans le dossier du projet :
   ```bash
   git clone <URL_DU_DEPOT>
   cd TriageBot-Evaluation-Python-DFS
   ```

2. Créer l'environnement virtuel et l'activer :
   - Sous Linux / macOS / Git Bash :
     ```bash
     python -m venv .venv
     source .venv/Scripts/activate
     ```
   - Sous Windows (PowerShell / CMD) :
     ```cmd
     .venv\Scripts\activate.bat
     ```

3. Installer les dépendances nécessaires :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

Assurez-vous qu'Ollama est bien lancé en arrière-plan, puis lancez le script principal :

```bash
python triage.py
```

### Options

Il est possible de tester un autre modèle installé sans modifier le code grâce à la variable d'environnement `OLLAMA_MODEL` :
```bash
export OLLAMA_MODEL="gemma3:4b"
python triage.py
```

## Fichiers produits

- `results.json` : ensemble des tickets avec les données d'analyse brutes (catégorie, sévérité, sentiment, résumé, brouillon et règle d'escalade).
- `report.md` : rapport managérial au format Markdown présentant une synthèse chiffrée, la liste des tickets escaladés par équipe et les anomalies techniques éventuelles.
- Affichage direct d'un tableau de bord de synthèse dans le terminal à la fin du traitement.

## Fonctionnalités implémentées

### Niveau 1 : Analyse automatique
- Chargement des données depuis `tickets.json`.
- Interrogation du LLM avec prompt système strict et format JSON forcé.
- Extraction structurée : `category`, `severity` (1 à 5), `sentiment` et `summary`.
- Sauvegarde des résultats dans `results.json`.

### Niveau 2 : Fiabilité et robustesse
- **Validation stricte** : vérification de la présence de tous les champs, des types et des valeurs autorisées.
- **Gestion des retries** : 2 tentatives maximum en cas de réponse mal formée ; au-delà, bascule automatique du ticket en statut `to_check`.
- **Tolérance aux pannes** : détection et messages d'erreur clairs si Ollama n'est pas lancé, si `tickets.json` est manquant ou si le JSON est corrompu.
- **Optimisation des appels** : filtrage des messages vides en amont et détection des doublons (même joueur et même message) pour réutiliser les analyses existantes.
- **Tableau de bord console** : volume par catégorie, sévérité moyenne et top 3 des urgences.

### Niveau 3 : Outils support et aide à la décision
- **Brouillon de réponse (`draft`)** : proposition d'un message poli rédigé automatiquement dans la langue d'origine du joueur.
- **Règles d'escalade déterministes** : logique métier codée en pur Python sans dépendance au LLM :
  - Catégorie `toxicity` $\rightarrow$ Équipe modération
  - Catégorie `payment` avec urgence $\ge 4$ $\rightarrow$ Responsable support
  - Statut `to_check` $\rightarrow$ Relecture humaine obligatoire
  - Autres tickets $\rightarrow$ Traitement standard
- **Rapport de synthèse (`report.md`)** : génération automatique d'un document récapitulatif pour les managers non techniques.