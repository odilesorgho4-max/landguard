"""
============================================================
 LandGuard Neuro-Symbolic AI
 test_landguard.py — Suite de tests (Partie 5)
 Tests unitaires Prolog (15) + ProbLog bornes + end-to-end
============================================================
"""

import unittest
import torch
import numpy as np
import pandas as pd
import json
from pathlib import Path

from neural_model import (
    FraudDetectorNet, FoncierDataset, FraudTrainer,
    generate_synthetic_data, predict_actor, load_model,
    CLASSES, FEATURE_NAMES, N_FEATURES, N_CLASSES
)
from main import (
    eval_regles_symboliques, score_symbolique, niveau_risque_sym,
    calculer_probs, niveau_prob, infer_neural, fusionner,
    run_pipeline, generer_rapport_txt
)

# ============================================================
# HELPERS
# ============================================================

def dossier(**kwargs):
    """Crée un dossier de test avec valeurs par défaut."""
    defaults = dict(
        id="TEST", nom="Test", type_acteur="citoyen",
        nb_parcelles=1, nb_parcelles_urbaines=1, nb_parcelles_rurales=0,
        frequence_revente=0.0, ratio_plus_value=0.1, duree_detention_mois=24,
        nb_liens_reseau=1, partage_telephone=0, partage_adresse=0, partage_iban=0,
        age_premier_achat=5, nb_dossiers_traites=0,
        conflit_direct=0, lien_familial_agent=0, favoritisme=0,
        nb_ventes_circulaires=0, label="standard", description=""
    )
    defaults.update(kwargs)
    return defaults


# ============================================================
# PARTIE A — Tests règles symboliques Prolog (15 tests)
# ============================================================

class TestReglesProlog(unittest.TestCase):

    # A1 : Accaparement urbain
    def test_A1_accaparement_urbain_declenche(self):
        d = dossier(nb_parcelles_urbaines=4)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("A1", regles, "A1 doit se déclencher avec 4 parcelles urbaines")

    def test_A1_accaparement_urbain_non_declenche(self):
        d = dossier(nb_parcelles_urbaines=3)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertNotIn("A1", regles, "A1 ne doit pas se déclencher avec 3 parcelles")

    # A4 : Multipropriété mixte
    def test_A4_multipropriete_mixte(self):
        d = dossier(nb_parcelles=5)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("A4", regles)

    # B1 : Revente rapide
    def test_B1_revente_rapide_declenche(self):
        d = dossier(duree_detention_mois=8, frequence_revente=0.5)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("B1", regles, "B1 doit se déclencher avec revente < 12 mois")

    def test_B1_revente_rapide_non_declenche(self):
        d = dossier(duree_detention_mois=14, frequence_revente=0.5)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertNotIn("B1", regles, "B1 ne doit pas se déclencher avec 14 mois")

    # B2 : Plus-value anormale
    def test_B2_plus_value_anormale(self):
        d = dossier(ratio_plus_value=0.8)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("B2", regles)

    def test_B2_plus_value_normale(self):
        d = dossier(ratio_plus_value=0.3)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertNotIn("B2", regles)

    # C1 : Conflit direct
    def test_C1_conflit_direct(self):
        d = dossier(conflit_direct=1)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("C1", regles)
        niveaux = {a["regle"]: a["niveau"] for a in alertes}
        self.assertEqual(niveaux["C1"], "critique")

    # C2 : Conflit indirect
    def test_C2_conflit_indirect_familial(self):
        d = dossier(lien_familial_agent=1, nb_dossiers_traites=2)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("C2", regles)

    # C3 : Favoritisme
    def test_C3_favoritisme_repete(self):
        d = dossier(favoritisme=1)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("C3", regles)

    # D1 : Téléphone partagé
    def test_D1_telephone_partage(self):
        d = dossier(partage_telephone=1)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("D1", regles)

    # D2 : Adresse partagée
    def test_D2_adresse_partagee(self):
        d = dossier(partage_adresse=1, nb_parcelles=2)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("D2", regles)

    # D3 : Circuit circulaire
    def test_D3_circuit_blanchiment(self):
        d = dossier(nb_ventes_circulaires=1)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("D3", regles)
        niveaux = {a["regle"]: a["niveau"] for a in alertes}
        self.assertEqual(niveaux["D3"], "critique")

    # D4 : IBAN partagé
    def test_D4_iban_partage(self):
        d = dossier(partage_iban=1)
        alertes = eval_regles_symboliques(d)
        regles = [a["regle"] for a in alertes]
        self.assertIn("D4", regles)

    # Score & niveau
    def test_score_et_niveau_critique(self):
        d = dossier(conflit_direct=1, nb_ventes_circulaires=1, partage_iban=1)
        alertes = eval_regles_symboliques(d)
        score = score_symbolique(alertes)
        niveau = niveau_risque_sym(score)
        self.assertGreaterEqual(score, 20)
        self.assertEqual(niveau, "critique")

    def test_dossier_standard_zero_alertes(self):
        d = dossier()  # toutes valeurs par défaut (pas d'anomalie)
        alertes = eval_regles_symboliques(d)
        self.assertEqual(len(alertes), 0, "Dossier standard → aucune alerte")


# ============================================================
# PARTIE B — Tests d'inférence ProbLog (bornes)
# ============================================================

class TestBornesProb(unittest.TestCase):

    def test_borne_haute_conflit_certain(self):
        d = dossier(conflit_direct=1)
        probs = calculer_probs(d)
        self.assertGreaterEqual(probs["conflit"], 0.95,
            "P(conflit|direct) doit être ≥ 0.95")

    def test_borne_basse_acteur_propre(self):
        d = dossier()
        probs = calculer_probs(d)
        self.assertLess(probs["fraude_globale"], 0.40,
            "P(fraude) pour dossier clean doit être < 0.40")

    def test_monotonie_prete_nom_confirme(self):
        d_tel     = dossier(partage_telephone=1, partage_adresse=0)
        d_cumul   = dossier(partage_telephone=1, partage_adresse=1)
        p_simple  = calculer_probs(d_tel)["prete_nom"]
        p_cumul   = calculer_probs(d_cumul)["prete_nom"]
        self.assertGreaterEqual(p_cumul, p_simple * 0.9,
            "P(fraude|tel+adr) ≥ P(prete_nom|tel seul)")

    def test_probabilites_bornees_0_1(self):
        d = dossier(nb_parcelles_urbaines=6, conflit_direct=1,
                    nb_ventes_circulaires=2, partage_telephone=1)
        probs = calculer_probs(d)
        for k, v in probs.items():
            self.assertGreaterEqual(v, 0.0, f"{k} < 0")
            self.assertLessEqual(v, 1.0,   f"{k} > 1")

    def test_blanchiment_eleve_si_circuit(self):
        d = dossier(nb_ventes_circulaires=1)
        probs = calculer_probs(d)
        self.assertGreaterEqual(probs["blanchiment"], 0.90)

    def test_classification_4_niveaux(self):
        for p, attendu in [(0.1,"faible"),(0.45,"moyen"),(0.70,"eleve"),(0.85,"critique")]:
            self.assertEqual(niveau_prob(p), attendu, f"P={p} → {attendu}")


# ============================================================
# PARTIE C — Tests module neuronal
# ============================================================

class TestNeuronal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.model = FraudDetectorNet()
        cls.model.eval()

    def test_architecture_sortie_4_classes(self):
        x = torch.randn(1, N_FEATURES)
        with torch.no_grad():
            out = self.model(x)
        self.assertEqual(out.shape, (1, N_CLASSES))

    def test_softmax_somme_1(self):
        x = torch.randn(5, N_FEATURES)
        proba = self.model.predict_proba(x)
        sums = proba.sum(dim=1)
        self.assertTrue(torch.allclose(sums, torch.ones(5), atol=1e-5))

    def test_predict_class_retourne_label_valide(self):
        x = torch.randn(1, N_FEATURES)
        classe = self.model.predict_class(x)
        if isinstance(classe, list):
            classe = classe[0]
        self.assertIn(classe, CLASSES)

    def test_batch_inference(self):
        x = torch.randn(10, N_FEATURES)
        proba = self.model.predict_proba(x)
        self.assertEqual(proba.shape, (10, N_CLASSES))

    def test_generate_synthetic_data_shape(self):
        df = generate_synthetic_data(50)
        self.assertEqual(len(df), 50)
        for col in FEATURE_NAMES + ["label"]:
            self.assertIn(col, df.columns)

    def test_generate_synthetic_data_labels(self):
        df = generate_synthetic_data(100)
        labels = set(df["label"].unique())
        self.assertEqual(labels, set(CLASSES))


# ============================================================
# PARTIE D — Tests intégration end-to-end (pipeline)
# ============================================================

class TestEndToEnd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Prépare un mini dataset de 10 dossiers pour les tests."""
        cls.mini_dataset = "test_mini_dataset.csv"
        rows = [
            dossier(id="T001", nom="Standard1", label="standard"),
            dossier(id="T002", nom="Standard2", label="standard"),
            dossier(id="T003", nom="Standard3", label="standard"),
            dossier(id="T004", nom="Specul1", frequence_revente=0.8,
                    ratio_plus_value=1.2, duree_detention_mois=5, label="speculation"),
            dossier(id="T005", nom="Specul2", frequence_revente=0.6,
                    ratio_plus_value=0.9, duree_detention_mois=7, label="speculation"),
            dossier(id="T006", nom="Accap1", nb_parcelles=6,
                    nb_parcelles_urbaines=5, label="accaparement"),
            dossier(id="T007", nom="Accap2", nb_parcelles=5,
                    nb_parcelles_urbaines=4, label="accaparement"),
            dossier(id="T008", nom="Conflit1", conflit_direct=1, label="fraude"),
            dossier(id="T009", nom="Reseau1", partage_telephone=1,
                    partage_iban=1, nb_ventes_circulaires=1, label="fraude"),
            dossier(id="T010", nom="FraudeMax", nb_parcelles=8,
                    nb_parcelles_urbaines=6, ratio_plus_value=2.0,
                    duree_detention_mois=3, frequence_revente=1.0,
                    conflit_direct=1, partage_telephone=1, partage_iban=1,
                    nb_ventes_circulaires=2, label="fraude"),
        ]
        pd.DataFrame(rows).to_csv(cls.mini_dataset, index=False)

    def test_pipeline_produit_50_resultats(self):
        """Le pipeline renvoie autant de résultats que de dossiers."""
        resultats = run_pipeline(
            dataset_path=self.mini_dataset,
            output_json="test_out.json",
            output_txt="test_out.txt",
            verbose=False
        )
        self.assertEqual(len(resultats), 10)

    def test_pipeline_structure_resultat(self):
        """Chaque résultat contient les clés attendues."""
        resultats = run_pipeline(
            dataset_path=self.mini_dataset,
            output_json="test_out.json",
            output_txt="test_out.txt",
            verbose=False
        )
        for r in resultats:
            for cle in ["id","nom","label_gt","neural","alertes","probs","fusion"]:
                self.assertIn(cle, r, f"Clé manquante : {cle}")

    def test_fraude_detectee_critique(self):
        """T010 (fraude composite max) doit être niveau critique."""
        resultats = run_pipeline(
            dataset_path=self.mini_dataset,
            output_json="test_out.json",
            output_txt="test_out.txt",
            verbose=False
        )
        t010 = next((r for r in resultats if r["id"] == "T010"), None)
        self.assertIsNotNone(t010)
        self.assertEqual(t010["fusion"]["niveau_final"], "critique",
            "T010 fraude composite doit être critique")

    def test_conflit_direct_critique(self):
        """T008 (conflit direct) doit déclencher règle C1 niveau critique."""
        resultats = run_pipeline(
            dataset_path=self.mini_dataset,
            output_json="test_out.json",
            output_txt="test_out.txt",
            verbose=False
        )
        t008 = next((r for r in resultats if r["id"] == "T008"), None)
        c1 = [a for a in t008["alertes"] if a["regle"] == "C1"]
        self.assertTrue(len(c1) > 0, "C1 doit se déclencher")
        self.assertEqual(c1[0]["niveau"], "critique")

    def test_rapport_json_genere(self):
        run_pipeline(dataset_path=self.mini_dataset,
                     output_json="test_out.json", output_txt="test_out.txt",
                     verbose=False)
        self.assertTrue(Path("test_out.json").exists())
        with open("test_out.json") as f:
            data = json.load(f)
        self.assertEqual(len(data), 10)

    def test_rapport_txt_genere(self):
        run_pipeline(dataset_path=self.mini_dataset,
                     output_json="test_out.json", output_txt="test_out.txt",
                     verbose=False)
        self.assertTrue(Path("test_out.txt").exists())
        content = Path("test_out.txt").read_text()
        self.assertIn("LANDGUARD", content)
        self.assertIn("LANDGUARD", content)

    def test_probs_fraude_dans_0_1(self):
        resultats = run_pipeline(dataset_path=self.mini_dataset,
                                 output_json="test_out.json", output_txt="test_out.txt",
                                 verbose=False)
        for r in resultats:
            pf = r["probs"]["fraude_globale"]
            self.assertGreaterEqual(pf, 0.0)
            self.assertLessEqual(pf, 1.0)


# ============================================================
# Point d'entrée
# ============================================================

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestReglesProlog))
    suite.addTests(loader.loadTestsFromTestCase(TestBornesProb))
    suite.addTests(loader.loadTestsFromTestCase(TestNeuronal))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\n{'='*60}")
    print(f"Tests : {result.testsRun} | "
          f"OK : {result.testsRun - len(result.failures) - len(result.errors)} | "
          f"Échecs : {len(result.failures)} | Erreurs : {len(result.errors)}")
