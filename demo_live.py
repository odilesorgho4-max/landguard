"""
============================================================
 LandGuard Neuro-Symbolic AI
 demo_live.py — Interface de démonstration en direct
 Usage : python demo_live.py
============================================================
"""

import torch
import numpy as np
from neural_model import FraudDetectorNet, CLASSES, FEATURE_NAMES, load_model
from main import eval_regles_symboliques, score_symbolique, niveau_risque_sym, calculer_probs

# ── Chargement du modele ──────────────────────────────────────
def charger_modele():
    try:
        model = load_model("model_weights.pth")
        return model
    except:
        print("  Modele non trouve, initialisation...")
        return FraudDetectorNet()

# ── Prediction neuronale ──────────────────────────────────────
def predict(features, model):
    x = torch.tensor([[features[f] for f in FEATURE_NAMES]], dtype=torch.float32)
    model.eval()
    with torch.no_grad():
        proba = torch.softmax(model(x), dim=-1).squeeze().tolist()
    classe = CLASSES[int(np.argmax(proba))]
    return classe, dict(zip(CLASSES, [round(p*100, 1) for p in proba])), round(max(proba)*100, 1)

# ── Interface principale ──────────────────────────────────────
def demo_live():
    print("\n" + "="*60)
    print("   LANDGUARD AI -- INTERFACE DE SIMULATION EN DIRECT")
    print("="*60)

    model = charger_modele()

    # Acteurs connus dans la base
    acteurs_connus = {
        "abdou":       {"nb_parcelles":5,"frequence_revente":0.0,"ratio_plus_value":0.0,
                        "nb_liens_reseau":3,"partage_telephone":0,"age_premier_achat":4,
                        "conflit_direct":0,"lien_familial_agent":0,"favoritisme":0,
                        "nb_ventes_circulaires":0,"partage_adresse":0,"partage_iban":0,
                        "nb_parcelles_urbaines":5,"duree_detention_mois":99,"label":"accaparement"},
        "mariama":     {"nb_parcelles":1,"frequence_revente":1.0,"ratio_plus_value":0.8,
                        "nb_liens_reseau":2,"partage_telephone":1,"age_premier_achat":3,
                        "conflit_direct":0,"lien_familial_agent":0,"favoritisme":0,
                        "nb_ventes_circulaires":0,"partage_adresse":1,"partage_iban":0,
                        "nb_parcelles_urbaines":1,"duree_detention_mois":4,"label":"speculation"},
        "konate":      {"nb_parcelles":2,"frequence_revente":0.0,"ratio_plus_value":0.0,
                        "nb_liens_reseau":3,"partage_telephone":0,"age_premier_achat":6,
                        "conflit_direct":1,"lien_familial_agent":1,"favoritisme":1,
                        "nb_ventes_circulaires":0,"partage_adresse":0,"partage_iban":0,
                        "nb_parcelles_urbaines":2,"duree_detention_mois":99,"label":"fraude"},
        "fatou":       {"nb_parcelles":1,"frequence_revente":0.0,"ratio_plus_value":0.1,
                        "nb_liens_reseau":1,"partage_telephone":0,"age_premier_achat":5,
                        "conflit_direct":0,"lien_familial_agent":0,"favoritisme":0,
                        "nb_ventes_circulaires":0,"partage_adresse":0,"partage_iban":0,
                        "nb_parcelles_urbaines":1,"duree_detention_mois":99,"label":"standard"},
    }

    while True:
        print("\n" + "-"*60)
        nom = input("Entrez le nom de l'acteur a analyser (ou 'quitter') : ").strip().lower()

        if nom in ["quitter", "q", "exit"]:
            print("\nFin de la demonstration. Au revoir !")
            break

        # Verifier si acteur connu
        if nom in acteurs_connus:
            print(f"  --> [CADASTRE] Acteur connu ! Antecedent : {acteurs_connus[nom]['label']}")
            features = acteurs_connus[nom]
        else:
            print(f"  --> [CADASTRE] Nouvel acteur inconnu terrain. Saisie manuelle requise.")
            features = saisir_features()

        print("\nAnalyse en cours...\n")

        # 1. Inference neuronale
        feat_neural = {k: features[k] for k in FEATURE_NAMES}
        classe_n, probas, confiance = predict(feat_neural, model)

        # 2. Regles symboliques
        alertes = eval_regles_symboliques(features)
        score_s = score_symbolique(alertes)
        niveau_s = niveau_risque_sym(score_s)

        # 3. Probabilites ProbLog
        probs = calculer_probs(features)
        p_fraude = probs["fraude_globale"]

        # 4. Fusion hybride
        votes = [niveau_s]
        if classe_n in ["fraude"]:      votes.append("eleve")
        if classe_n == "fraude" and score_s >= 10: votes.append("critique")
        if classe_n == "speculation" and score_s >= 4: votes.append("eleve")
        if classe_n == "accaparement" and score_s >= 4: votes.append("eleve")
        if p_fraude >= 0.80: votes.append("critique")
        elif p_fraude >= 0.60: votes.append("eleve")

        ordre = ["critique", "eleve", "moyen", "faible"]
        niveau_final = min(votes, key=lambda x: ordre.index(x)) if votes else "faible"
        convergence = classe_n in ["fraude","accaparement","speculation"] and len(alertes) >= 2

        # ── Affichage du verdict ──────────────────────────────
        print("="*60)
        print(f"   VERDICT : {nom.upper()}")
        print("="*60)
        print(f"\n[NEURONAL]")
        print(f"  Classe predite  : {classe_n.upper()} ({confiance}%)")
        print(f"  Distribution    : ", end="")
        for c, p in probas.items():
            print(f"{c}={p}%", end="  ")
        print()

        print(f"\n[SYMBOLIQUE]")
        if alertes:
            for a in alertes:
                print(f"  [{a['niveau'].upper()}] Regle {a['regle']} -- {a['desc']}")
        else:
            print("  Aucune regle declenchee")
        print(f"  Score total : {score_s} pts | Niveau : {niveau_s}")

        print(f"\n[PROBLOG]")
        print(f"  P(fraude globale) = {p_fraude:.2f}")

        print(f"\n[DECISION FINALE]")
        emoji = {"critique":"[!!!]","eleve":"[!!]","moyen":"[!]","faible":"[OK]"}
        print(f"  Niveau de risque : {emoji.get(niveau_final,'')} {niveau_final.upper()}")
        print(f"  Convergence neural+symbolique : {'OUI' if convergence else 'NON'}")

        print(f"\n[EXPLICATION XAI]")
        if niveau_final == "critique":
            print(f"  ALERTE MAJEURE : Fraude confirmee par regles metier et reseau neuronal.")
            print(f"  Action recommandee : BLOCAGE IMMEDIAT + Saisine Parquet.")
        elif niveau_final == "eleve":
            print(f"  Suspicion forte detectee. Investigation approfondie requise.")
            print(f"  Action recommandee : Audit complet du dossier.")
        elif niveau_final == "moyen":
            print(f"  Signaux faibles detectes. Surveillance renforcee recommandee.")
        else:
            print(f"  Profil conforme aux reglementations du cadastre.")
        print("="*60)

        continuer = input("\nAnalyser un autre acteur ? (o/n) : ").strip().lower()
        if continuer != "o":
            print("\nFin de la demonstration. Bonne soutenance !")
            break


def saisir_features():
    """Saisie interactive des caracteristiques d'un acteur inconnu."""
    print("\nSaisissez les caracteristiques :")

    def ask(label, default, typ=float):
        val = input(f"  - {label} [Defaut: {default}] : ").strip()
        return typ(val) if val else default

    nb_p    = ask("Nombre de parcelles", 1, int)
    nb_pu   = ask("Dont parcelles urbaines", min(nb_p,1), int)
    freq_r  = ask("Frequence de revente (0=jamais, 1=souvent)", 0.0, float)
    ratio   = ask("Ratio plus-value (ex: 0.8 = +80%)", 0.0, float)
    duree   = ask("Duree detention mois (si revente)", 99, int)
    nb_l    = ask("Nombre de liens reseau (complices)", 0, int)
    tel     = ask("Partage telephone (1=Oui, 0=Non)", 0, int)
    adr     = ask("Partage adresse (1=Oui, 0=Non)", 0, int)
    iban    = ask("Partage IBAN (1=Oui, 0=Non)", 0, int)
    age     = ask("Age premier achat (annees)", 5, float)
    cd      = ask("Conflit direct (1=Oui, 0=Non)", 0, int)
    lf      = ask("Lien familial agent (1=Oui, 0=Non)", 0, int)
    fav     = ask("Favoritisme (1=Oui, 0=Non)", 0, int)
    circ    = ask("Nb ventes circulaires", 0, int)

    return {
        "nb_parcelles": nb_p,
        "nb_parcelles_urbaines": nb_pu,
        "frequence_revente": freq_r,
        "ratio_plus_value": ratio,
        "duree_detention_mois": duree,
        "nb_liens_reseau": nb_l,
        "partage_telephone": tel,
        "partage_adresse": adr,
        "partage_iban": iban,
        "age_premier_achat": age,
        "conflit_direct": cd,
        "lien_familial_agent": lf,
        "favoritisme": fav,
        "nb_ventes_circulaires": circ,
        "label": "inconnu"
    }


if __name__ == "__main__":
    demo_live()
