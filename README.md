# LandGuard Neuro-Symbolic AI

> **Régulation foncière intelligente par Logique de Description, Prolog, ProbLog et DeepProbLog**

Projet de Master 1 — IA Symbolique, Probabiliste & Neuro-Symbolique

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du système](#architecture-du-système)
3. [Structure du dépôt](#structure-du-dépôt)
4. [Prérequis & Installation](#prérequis--installation)
5. [Lancement rapide](#lancement-rapide)
6. [Description des modules](#description-des-modules)
7. [Dataset](#dataset)
8. [Tests](#tests)
9. [Exemples de sortie](#exemples-de-sortie)

---

## Vue d'ensemble

LandGuard est un système hybride de **détection de fraudes foncières** combinant :

- **Logique de Description (DL)** — modélisation terminologique du domaine
- **SWI-Prolog** — moteur d'inférence déductif avec 15 règles métier
- **ProbLog** — raisonnement sous incertitude, calcul de probabilités de fraude
- **DeepProbLog + PyTorch** — fusion neuronale-symbolique pour la décision finale
- **XAI** — traces logiques explicables pour chaque alerte générée

Le système détecte automatiquement : accaparement foncier, spéculation, conflits d'intérêts, réseaux de prête-noms et circuits de blanchiment.

---

## Architecture du système

```
┌─────────────────────────────────────────────────────────┐
│                    dataset.csv (50 dossiers)             │
└──────────────────────────┬──────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
   ┌──────────────┐ ┌────────────┐ ┌─────────────┐
   │  PyTorch     │ │   Prolog   │ │   ProbLog   │
   │  (neural_    │ │ (rules.pl) │ │ (prob_      │
   │  model.py)   │ │            │ │  rules.pl)  │
   └──────┬───────┘ └─────┬──────┘ └──────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
              ┌───────────────────────┐
              │  DeepProbLog Fusion   │
              │ (deepproblog_model.pl)│
              └───────────┬───────────┘
                          ▼
              ┌───────────────────────┐
              │   XAI — Rapport       │
              │  rapport_landguard    │
              │  .json / .txt         │
              └───────────────────────┘
```

---

## Structure du dépôt

```
landguard/
│
├── README.md                    ← Ce fichier
│
├── Partie 1 — Logique de Description
│   ├── description_logic.md     ← 10 axiomes DL + 8 contraintes CI
│   ├── knowledge_base.pl        ← Base de connaissances Prolog (TBox + ABox)
│   └── diagramme_concepts.pdf   ← Hiérarchie des concepts
│
├── Partie 2 — Raisonnement Prolog
│   ├── rules.pl                 ← 15 règles (A1–D4)
│   ├── inference_engine.pl      ← Moteur d'inférence + scoring
│   └── explainability.pl        ← Module XAI (journalisation + traces)
│
├── Partie 3 — ProbLog
│   ├── probabilistic_rules.pl   ← Règles avec poids a priori
│   ├── queries.pl               ← Requêtes d'inférence probabiliste
│   └── rapport_inference_prob.txt ← Résultats ProbLog
│
├── Partie 4 — DeepProbLog
│   ├── neural_model.py          ← FraudDetectorNet (PyTorch)
│   ├── deepproblog_model.pl     ← Prédicats neuronaux + règles hybrides
│   └── model_weights.pth        ← Poids entraînés (97.5% précision)
│
├── Partie 5 — Pipeline & Validation
│   ├── main.py                  ← Orchestration complète
│   ├── dataset.csv              ← 50 dossiers synthétiques
│   └── test_landguard.py        ← 35 tests (16 Prolog + 6 ProbLog + 13 E2E)
│
└── rapport_landguard.pdf        ← Rapport scientifique (15–25 pages)
```

---

## Prérequis & Installation

### Dépendances système

- Python 3.9+
- SWI-Prolog 9.x (`swipl`)
- ProbLog 2.1+ (`problog`)

### Installation Python

```bash
# Cloner le dépôt
git clone https://github.com/<votre-repo>/landguard.git
cd landguard

# Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate        # Linux/macOS
# ou : venv\Scripts\activate    # Windows

# Installer les dépendances
pip install torch numpy pandas
```

### Installation SWI-Prolog

```bash
# Ubuntu / Debian
sudo apt install swi-prolog

# macOS (Homebrew)
brew install swi-prolog

# Vérification
swipl --version
```

### Installation ProbLog

```bash
pip install problog

# Vérification
problog --version
```

---

## Lancement rapide

### 1. Pipeline complet (recommandé)

```bash
python main.py
# ou avec un dataset personnalisé :
python main.py mon_dataset.csv
```

Produit :
- `rapport_landguard.json` — résultats structurés
- `rapport_landguard.txt`  — rapport lisible avec alertes XAI

### 2. Entraînement du modèle neuronal

```bash
python neural_model.py
# Génère model_weights.pth (100 epochs, ~30s)
```

### 3. Moteur Prolog seul

```bash
swipl -g "
  [knowledge_base, rules, inference_engine, explainability],
  rapport_global,
  halt
" -t halt
```

### 4. Inférence ProbLog

```bash
problog probabilistic_rules.pl queries.pl
```

### 5. Tests complets

```bash
python test_landguard.py
# Attendu : 35/35 tests OK
```

---

## Description des modules

### `knowledge_base.pl`
Base de connaissances principale. Définit la taxonomie (Acteur, Parcelle, Affectation, Dossier, LienSocial), les instances de démonstration, les transactions et les prédicats utilitaires (`nb_parcelles_urbaines/2`, `plus_value_ratio/3`, etc.).

### `rules.pl` — 15 règles réparties en 4 catégories

| Catégorie | Règles | Description |
|-----------|--------|-------------|
| **A — Accaparement** | A1, A2, A3, A4 | Concentration urbaine, familiale, rurale, mixte |
| **B — Spéculation** | B1, B2, B3 | Revente rapide, plus-value anormale, non-mise en valeur |
| **C — Conflits** | C1, C2, C3, C4 | Conflit direct/indirect, favoritisme, notaire lié |
| **D — Réseaux** | D1, D2, D3, D4 | Téléphone/adresse/IBAN partagés, circuit de blanchiment |

### `neural_model.py` — FraudDetectorNet

Réseau MLP 3 couches cachées (64→128→64), BatchNorm, Dropout.

| Feature | Description |
|---------|-------------|
| `nb_parcelles` | Nombre total de parcelles détenues |
| `frequence_revente` | Nb reventes / nb parcelles |
| `ratio_plus_value` | (prix_vente − prix_achat) / prix_achat |
| `nb_liens_reseau` | Nb de liens sociaux (famille, pro, financier) |
| `partage_telephone` | Binaire : téléphone partagé |
| `age_premier_achat` | Années depuis le premier achat |

Sortie : distribution sur `[standard, atypique, speculateur, fraude]`

### `deepproblog_model.pl` — Fusion hybride

```prolog
% Prédicat neuronal central
nn(fraud_model, [X], Classe, [standard, atypique, speculateur, fraude]).

% Exemple de règle hybride
fraude_hybride(X, Explication) :-
    neural_prediction(X, fraude),       % signal neuronal
    accaparement_urbain(X, _),          % contrainte symbolique
    ...
```

La décision finale est confirmée uniquement si le signal neuronal **et** au moins une règle symbolique convergent.

---

## Dataset

`dataset.csv` contient 50 dossiers synthétiques :

| Catégorie | Nb | Description |
|-----------|----|-------------|
| `standard` | 30 | Dossiers normaux, aucune anomalie |
| `speculation` | 5 | Reventes rapides + plus-values anormales |
| `accaparement` | 5 | Concentration urbaine dépassant CI-02 |
| `limite` | 5 | Cas complexes à la frontière des seuils |
| `fraude` | 5 | Fraudes sophistiquées (réseau, circuit, composite) |

Colonnes principales : `id`, `nom`, `type_acteur`, `nb_parcelles`, `nb_parcelles_urbaines`, `frequence_revente`, `ratio_plus_value`, `duree_detention_mois`, `partage_telephone`, `conflit_direct`, `nb_ventes_circulaires`, `label`.

---

## Tests

```
TestReglesProlog  (16 tests) — règles A1–D4, score, dossier standard
TestBornesProb    ( 6 tests) — bornes ProbLog, monotonie, classification
TestNeuronal      ( 6 tests) — architecture, softmax, batch, données
TestEndToEnd      ( 7 tests) — pipeline complet, JSON/TXT, fraude critique
─────────────────────────────
TOTAL             35 tests   — 35/35 ✓
```

---

## Exemples de sortie

### Alerte critique (D046 — Réseau Koné-Diallo)

```
🔴 [D046] Réseau Koné-Diallo
   neural       : fraude (confiance=0.91)
   P(fraude)    : 0.93 | Score sym : 35pts
   Convergence  : ✓
   ⚠ [CRITIQUE] Règle C1 — Conflit d'intérêt direct (CI-01 violée)
   ⚠ [CRITIQUE] Règle D3 — Circuit de blanchiment détecté (1 boucle)
   ⚠ [CRITIQUE] Règle D4 — IBAN partagé entre acteurs distincts
   ⚠ [HAUT]     Règle A1 — Accaparement urbain : 5 parcelles (seuil=3)
   ⚠ [HAUT]     Règle B1 — Revente rapide : 4 mois (seuil=12)
   ⚠ [HAUT]     Règle D1 — Téléphone partagé (CI-05 → suspicion prête-nom)
```

### Dossier standard (D001 — Fatou Kaboré)

```
🟢 [D001] Fatou Kaboré
   neural       : standard (confiance=0.87)
   P(fraude)    : 0.05 | Score sym : 0pts
   ✓ Aucune violation détectée.
```

---

*LandGuard Neuro-Symbolic AI — Master 1 Informatique*
