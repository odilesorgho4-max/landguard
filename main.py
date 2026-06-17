"""
============================================================
 LandGuard Neuro-Symbolic AI
 main.py — Pipeline d'orchestration complet (Partie 5)
 Flux : CSV → PyTorch → ProbLog → Prolog → Rapport XAI
============================================================
"""

import json
import sys
import csv
import time
from pathlib import Path
from datetime import datetime

import torch
import torch.nn.functional as F
import numpy as np
import pandas as pd

# ── Import du module neuronal ──────────────────────────────
from neural_model import (
    FraudDetectorNet, CLASSES, FEATURE_NAMES,
    load_model, predict_actor, generate_synthetic_data
)

# ============================================================
# SECTION 1 : Configuration
# ============================================================

CONFIG = {
    "dataset_path":      "dataset.csv",
    "weights_path":      "model_weights.pth",
    "output_report":     "rapport_landguard.json",
    "output_txt":        "rapport_landguard.txt",
    "seuil_fraude":      0.60,   # P(fraude) neuronal → alerte
    "seuil_critique":    0.80,   # P(fraude) → niveau critique
}

NIVEAU_COULEUR = {
    "critique": "🔴",
    "eleve":    "🟠",
    "moyen":    "🟡",
    "faible":   "🟢",
}

# ============================================================
# SECTION 2 : Règles symboliques Python
# (portage léger des règles Prolog pour le pipeline Python)
# ============================================================

def eval_regles_symboliques(dossier: dict) -> list:
    """
    Évalue les règles logiques Prolog sur un dossier CSV.
    Retourne la liste des alertes déclenchées.
    """
    alertes = []
    nb_pu   = int(dossier.get("nb_parcelles_urbaines", 0))
    nb_p    = int(dossier.get("nb_parcelles", 0))
    freq_r  = float(dossier.get("frequence_revente", 0))
    ratio_pv = float(dossier.get("ratio_plus_value", 0))
    duree   = int(dossier.get("duree_detention_mois", 99))
    tel     = int(dossier.get("partage_telephone", 0))
    adr     = int(dossier.get("partage_adresse", 0))
    iban    = int(dossier.get("partage_iban", 0))
    circ    = int(dossier.get("nb_ventes_circulaires", 0))
    cd      = int(dossier.get("conflit_direct", 0))
    lf      = int(dossier.get("lien_familial_agent", 0))
    fav     = int(dossier.get("favoritisme", 0))
    nb_dos  = int(dossier.get("nb_dossiers_traites", 0))

    # Catégorie A — Accaparement
    if nb_pu >= 4:
        alertes.append({"regle":"A1","cat":"accaparement","niveau":"eleve",
            "desc":f"Accaparement urbain : {nb_pu} parcelles urbaines (seuil=3)"})
    if nb_p >= 5:
        alertes.append({"regle":"A4","cat":"accaparement","niveau":"moyen",
            "desc":f"Multipropriété mixte : {nb_p} parcelles au total"})

    # Catégorie B — Spéculation
    if duree < 12 and freq_r > 0:
        alertes.append({"regle":"B1","cat":"speculation","niveau":"eleve",
            "desc":f"Revente rapide : {duree} mois (seuil=12)"})
    if ratio_pv > 0.5:
        alertes.append({"regle":"B2","cat":"speculation","niveau":"eleve",
            "desc":f"Plus-value anormale : {ratio_pv*100:.0f}% (seuil=50%)"})

    # Catégorie C — Conflits
    if cd:
        alertes.append({"regle":"C1","cat":"conflit","niveau":"critique",
            "desc":"Conflit d'intérêt direct (CI-01 violée)"})
    if lf and nb_dos >= 2:
        alertes.append({"regle":"C2","cat":"conflit","niveau":"critique",
            "desc":"Conflit indirect : dossiers de proches familiaux"})
    if fav or nb_dos >= 3:
        alertes.append({"regle":"C3","cat":"conflit","niveau":"eleve",
            "desc":f"Favoritisme répétitif : {nb_dos} dossiers pour même acteur"})

    # Catégorie D — Réseaux
    if tel:
        alertes.append({"regle":"D1","cat":"reseau","niveau":"eleve",
            "desc":"Téléphone partagé (CI-05 → suspicion prête-nom)"})
    if adr and nb_p > 0:
        alertes.append({"regle":"D2","cat":"reseau","niveau":"eleve",
            "desc":"Adresse partagée entre propriétaires"})
    if circ >= 1:
        alertes.append({"regle":"D3","cat":"reseau","niveau":"critique",
            "desc":f"Circuit de blanchiment détecté ({circ} boucle(s))"})
    if iban:
        alertes.append({"regle":"D4","cat":"reseau","niveau":"critique",
            "desc":"IBAN partagé entre acteurs distincts"})

    return alertes


# ============================================================
# SECTION 3 : Calcul du score symbolique
# ============================================================

POIDS = {"critique": 10, "eleve": 5, "moyen": 2, "faible": 1}

def score_symbolique(alertes: list) -> int:
    return sum(POIDS.get(a["niveau"], 1) for a in alertes)

def niveau_risque_sym(score: int) -> str:
    if score >= 20: return "critique"
    if score >= 10: return "eleve"
    if score >= 4:  return "moyen"
    return "faible"


# ============================================================
# SECTION 4 : Probabilités ProbLog (simulation Python)
# ============================================================

PROB_RULES = {
    "prete_nom":     lambda d: 0.80 if d["partage_telephone"] else (0.65 if d["partage_adresse"] else 0.0),
    "speculateur":   lambda d: min(0.88, 0.60 + float(d["ratio_plus_value"])*0.15 + (0.1 if d["frequence_revente"]>0.4 else 0)),
    "accapareur":    lambda d: 0.95 if int(d["nb_parcelles_urbaines"])>=4 else (0.75 if int(d["nb_parcelles_urbaines"])>=3 else 0.05),
    "conflit":       lambda d: 0.97 if d["conflit_direct"] else (0.72 if d["lien_familial_agent"] else 0.0),
    "blanchiment":   lambda d: 0.93 if int(d["nb_ventes_circulaires"])>=1 else 0.0,
}

def niveau_prob(p: float) -> str:
    if p >= 0.80: return "critique"
    if p >= 0.60: return "eleve"
    if p >= 0.30: return "moyen"
    return "faible"

def calculer_probs(dossier: dict) -> dict:
    probs = {}
    for nom, fn in PROB_RULES.items():
        try:
            d = {k: float(v) if str(v).replace('.','').lstrip('-').isdigit() else v
                 for k,v in dossier.items()}
            probs[nom] = round(fn(d), 4)
        except:
            probs[nom] = 0.0
    # fraude globale = max pondéré
    p_fraude = min(0.99, max(
        probs["conflit"] * 0.99,
        probs["blanchiment"] * 0.93,
        probs["accapareur"] * probs["prete_nom"] * 0.85,
        probs["speculateur"] * probs["accapareur"] * 0.80,
        probs["speculateur"] * 0.60,
        probs["prete_nom"] * 0.40,
    ))
    probs["fraude_globale"] = round(p_fraude, 4)
    return probs


# ============================================================
# SECTION 5 : Inférence neuronale
# ============================================================

def preparer_features(dossier: dict, stats: dict) -> torch.Tensor:
    """Normalise les features d'un dossier avec les stats du dataset."""
    vals = []
    for feat in FEATURE_NAMES:
        v = float(dossier.get(feat, 0))
        m, s = stats.get(feat, (0, 1))
        vals.append((v - m) / (s + 1e-8))
    return torch.tensor([vals], dtype=torch.float32)

def infer_neural(dossier: dict, model: FraudDetectorNet, stats: dict) -> dict:
    x = preparer_features(dossier, stats)
    proba = model.predict_proba(x).squeeze().tolist()
    classe = CLASSES[int(np.argmax(proba))]
    return {
        "classe":        classe,
        "probabilites":  dict(zip(CLASSES, [round(p, 4) for p in proba])),
        "confiance":     round(max(proba), 4),
    }


# ============================================================
# SECTION 6 : Fusion neuro-symbolique
# ============================================================

def fusionner(neural: dict, alertes: list, probs: dict) -> dict:
    """Calcule le niveau hybride final et l'explication."""
    classe_n = neural["classe"]
    score_s  = score_symbolique(alertes)
    niveau_s = niveau_risque_sym(score_s)
    p_fraude = probs.get("fraude_globale", 0.0)
    niv_p    = niveau_prob(p_fraude)

    # Fusion : priorité aux signaux convergents
    votes = [niveau_s, niv_p]
    if classe_n in ["fraude", "speculateur"]:
        votes.append("eleve")
    if classe_n == "fraude" and score_s >= 10:
        votes.append("critique")

    ordre = ["critique", "eleve", "eleve", "moyen", "faible"]
    niveau_final = min(votes, key=lambda x: ordre.index(x)) if votes else "faible"

    regles_declenchees = [a["regle"] for a in alertes]
    convergence = (
        classe_n in ["fraude","speculateur"] and len(alertes) >= 2
    )

    explication = (
        f"Décision hybride : neural={classe_n} | "
        f"symbolique={niveau_s}({score_s}pts) | "
        f"problog=P(fraude)={p_fraude:.2f} | "
        f"niveau_final={niveau_final} | "
        f"règles={regles_declenchees} | "
        f"convergence={'OUI' if convergence else 'NON'}"
    )

    return {
        "niveau_final":  niveau_final,
        "convergence":   convergence,
        "explication":   explication,
        "score_sym":     score_s,
        "p_fraude":      p_fraude,
    }


# ============================================================
# SECTION 7 : Pipeline principal
# ============================================================

def run_pipeline(
    dataset_path: str = CONFIG["dataset_path"],
    weights_path: str = CONFIG["weights_path"],
    output_json:  str = CONFIG["output_report"],
    output_txt:   str = CONFIG["output_txt"],
    verbose:      bool = True,
) -> list:

    t0 = time.time()
    print("╔══════════════════════════════════════════════╗")
    print("║    LANDGUARD NEURO-SYMBOLIC AI — PIPELINE    ║")
    print("╚══════════════════════════════════════════════╝\n")

    # ── Chargement dataset ──────────────────────────────────
    if Path(dataset_path).exists():
        df = pd.read_csv(dataset_path)
    else:
        print("⚠ Dataset introuvable, génération synthétique...")
        df = generate_synthetic_data(50)
    print(f"📂 Dataset chargé : {len(df)} dossiers\n")

    # ── Calcul stats pour normalisation ─────────────────────
    num_cols = ["nb_parcelles","frequence_revente","ratio_plus_value",
                "nb_liens_reseau","age_premier_achat"]
    stats = {c: (df[c].mean(), df[c].std()) for c in num_cols if c in df.columns}

    # ── Chargement modèle neuronal ───────────────────────────
    if Path(weights_path).exists():
        model = load_model(weights_path)
    else:
        print("⚠ Poids introuvables — modèle non initialisé")
        model = FraudDetectorNet()
    model.eval()
    print()

    # ── Traitement dossier par dossier ───────────────────────
    resultats = []
    for _, row in df.iterrows():
        dossier = row.to_dict()
        id_dos  = dossier.get("id", "?")
        nom     = dossier.get("nom", "Inconnu")

        # 1. Inférence neuronale
        neural  = infer_neural(dossier, model, stats)

        # 2. Règles symboliques Prolog
        alertes = eval_regles_symboliques(dossier)

        # 3. Probabilités ProbLog
        probs   = calculer_probs(dossier)

        # 4. Fusion neuro-symbolique
        fusion  = fusionner(neural, alertes, probs)

        resultat = {
            "id":       id_dos,
            "nom":      nom,
            "label_gt": dossier.get("label","?"),
            "neural":   neural,
            "alertes":  alertes,
            "probs":    probs,
            "fusion":   fusion,
        }
        resultats.append(resultat)

        if verbose:
            emoji = NIVEAU_COULEUR.get(fusion["niveau_final"], "⚪")
            print(f"  {emoji} [{id_dos}] {nom:<30s} "
                  f"neural={neural['classe']:<12s} "
                  f"niveau={fusion['niveau_final']}")

    # ── Export JSON ──────────────────────────────────────────
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    # ── Export rapport texte ─────────────────────────────────
    generer_rapport_txt(resultats, output_txt)

    t1 = time.time()
    print(f"\n✅ Pipeline terminé en {t1-t0:.2f}s")
    print(f"   Rapport JSON : {output_json}")
    print(f"   Rapport TXT  : {output_txt}")

    _afficher_synthese(resultats)
    return resultats


# ============================================================
# SECTION 8 : Génération du rapport textuel
# ============================================================

def generer_rapport_txt(resultats: list, path: str):
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines += [
        "=" * 62,
        "  LANDGUARD NEURO-SYMBOLIC AI — RAPPORT CONSOLIDÉ",
        f"  Généré le : {ts}",
        "=" * 62, "",
    ]

    critiques = [r for r in resultats if r["fusion"]["niveau_final"] == "critique"]
    hauts     = [r for r in resultats if r["fusion"]["niveau_final"] == "eleve"]
    moyens    = [r for r in resultats if r["fusion"]["niveau_final"] == "moyen"]
    faibles   = [r for r in resultats if r["fusion"]["niveau_final"] == "faible"]

    lines += [
        f"SYNTHÈSE : {len(resultats)} dossiers analysés",
        f"  🔴 Critique : {len(critiques)}",
        f"  🟠 Élevé    : {len(hauts)}",
        f"  🟡 Moyen    : {len(moyens)}",
        f"  🟢 Faible   : {len(faibles)}", "",
    ]

    for niveau, groupe in [("CRITIQUE 🔴", critiques), ("ÉLEVÉ 🟠", hauts),
                           ("MOYEN 🟡", moyens), ("FAIBLE 🟢", faibles)]:
        if not groupe:
            continue
        lines += [f"── {niveau} ({'─'*(50-len(niveau))}", ""]
        for r in groupe:
            f = r["fusion"]
            n = r["neural"]
            lines += [
                f"  [{r['id']}] {r['nom']}",
                f"    Label réel   : {r['label_gt']}",
                f"    Neural       : {n['classe']} (confiance={n['confiance']:.2f})",
                f"    P(fraude)    : {f['p_fraude']:.2f} | Score sym : {f['score_sym']}pts",
                f"    Convergence  : {'✓' if f['convergence'] else '✗'}",
                f"    Explication  : {f['explication'][:80]}...",
                "",
            ]
            for a in r["alertes"]:
                lines.append(f"    ⚠ [{a['niveau'].upper()}] Règle {a['regle']} — {a['desc']}")
            lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _afficher_synthese(resultats: list):
    niveaux = [r["fusion"]["niveau_final"] for r in resultats]
    from collections import Counter
    counts = Counter(niveaux)
    print("\n┌─────────────────────────────────┐")
    print("│        SYNTHÈSE FINALE          │")
    print("├─────────────────────────────────┤")
    for niv, emoji in NIVEAU_COULEUR.items():
        print(f"│  {emoji} {niv:<10s} : {counts.get(niv,0):3d} dossiers       │")
    print("└─────────────────────────────────┘")

    # Précision vs label réel
    correct = sum(
        1 for r in resultats
if r["label_gt"] == r["neural"]["classe"] and True and
          r["fusion"]["niveau_final"] in ["critique","eleve","moyen"]
        or r["label_gt"] == "standard" and r["fusion"]["niveau_final"] == "faible"
    )
    acc = correct / len(resultats) if resultats else 0
    print(f"\n  Cohérence label réel : {correct}/{len(resultats)} ({acc:.0%})")


# ============================================================
# Point d'entrée
# ============================================================

if __name__ == "__main__":
    dataset = sys.argv[1] if len(sys.argv) > 1 else CONFIG["dataset_path"]
    run_pipeline(dataset_path=dataset)
