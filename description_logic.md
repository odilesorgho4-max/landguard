# LandGuard — Modélisation en Logique de Description

## 1. Taxonomie des Concepts (TBox)

### Concepts primitifs
```
Acteur, Parcelle, Affectation, Dossier, LienSocial
```

### Hiérarchie de subsomption
```
Citoyen       ⊑ Acteur
AgentPublic   ⊑ Acteur
Promoteur     ⊑ Acteur
Notaire       ⊑ Acteur

ParcelleUrbaine ⊑ Parcelle
ParcelleRurale  ⊑ Parcelle

Attribution ⊑ Affectation
Revente     ⊑ Affectation
Héritage    ⊑ Affectation

DossierActif    ⊑ Dossier
DossierSuspect  ⊑ Dossier

LienFamilial       ⊑ LienSocial
LienProfessionnel  ⊑ LienSocial
LienFinancier      ⊑ LienSocial
```

### Disjonction entre sous-classes
```
Citoyen ⊓ AgentPublic  ⊑ ⊥
Citoyen ⊓ Promoteur    ⊑ ⊥
Citoyen ⊓ Notaire      ⊑ ⊥
AgentPublic ⊓ Promoteur ⊑ ⊥
AgentPublic ⊓ Notaire   ⊑ ⊥

ParcelleUrbaine ⊓ ParcelleRurale ⊑ ⊥
DossierActif ⊓ DossierSuspect   ⊑ ⊥
```

---

## 2. Rôles (Object Properties)

| Rôle               | Domaine       | Portée        | Propriétés         |
|--------------------|---------------|---------------|--------------------|
| possede(X,Y)       | Acteur        | Parcelle      | —                  |
| traite(X,Y)        | AgentPublic   | Dossier       | —                  |
| beneficiaire(X,Y)  | Acteur        | Affectation   | —                  |
| lienFamilial(X,Y)  | Acteur        | Acteur        | symétrique         |
| vendA(X,Y)         | Acteur        | Acteur        | —                  |
| partageTelephone(X,Y) | Acteur     | Acteur        | symétrique         |
| partageAdresse(X,Y)   | Acteur     | Acteur        | symétrique         |
| concerneDossier(X,Y)  | Affectation | Dossier      | —                  |
| impliqueParcelle(X,Y) | Affectation | Parcelle     | —                  |

---

## 3. Axiomes DL (TBox — 10 axiomes complexes)

### AX-01 : Accaparement urbain
```
Citoyen ⊓ (≥ 4 possede.ParcelleUrbaine)  ⊑  AccapareurUrbain
```
*Tout citoyen détenteur d'au moins 4 parcelles urbaines est classé AccapareurUrbain.*

### AX-02 : Conflit d'intérêt direct
```
AgentPublic ⊓ ∃traite.Dossier ⊓ ∃beneficiaire.Affectation  ⊑  ConflitInteretDirect
```
*Un agent public qui traite un dossier dont il est bénéficiaire direct constitue un conflit d'intérêt.*

### AX-03 : Conflit d'intérêt indirect (famille)
```
AgentPublic ⊓ ∃traite.Dossier ⊓ ∃lienFamilial.(∃beneficiaire.Affectation)  ⊑  ConflitInteretIndirect
```
*Un agent public traitant un dossier bénéficiant à un membre de sa famille est en conflit d'intérêt indirect.*

### AX-04 : Spéculateur foncier
```
Acteur ⊓ ∃vendA.Acteur ⊓ ∃(reventeRapide ⊓ plusValueAnormale).Parcelle  ⊑  Speculateur
```
*Tout acteur ayant réalisé une revente rapide avec plus-value anormale est un spéculateur.*

### AX-05 : Prête-nom par téléphone
```
Acteur ⊓ ∃partageTelephone.Acteur  ⊑  SuspectPreteNom
```
*Deux acteurs distincts partageant le même numéro de téléphone sont suspects de prête-nom.*

### AX-06 : Réseau de prête-nom par adresse
```
Acteur ⊓ ∃partageAdresse.(∃possede.Parcelle)  ⊑  SuspectReseauFoncier
```
*Un acteur partageant son adresse avec un autre propriétaire actif est suspecté d'appartenir à un réseau.*

### AX-07 : Accaparement familial
```
Acteur ⊓ ∃lienFamilial.AccapareurUrbain ⊓ (≥ 2 possede.ParcelleUrbaine)  ⊑  AccapareurFamilial
```
*Un acteur lié familialement à un accapareur et détenant lui-même ≥ 2 parcelles urbaines contribue à l'accaparement familial.*

### AX-08 : Transaction circulaire (blanchiment)
```
Acteur ⊓ ∃vendA.(∃vendA.(∃vendA.(hasMeme.Acteur)))  ⊑  ReseauBlanchiment
```
*Un acteur qui vend à B qui vend à C qui revend au même A constitue un réseau circulaire de blanchiment.*

### AX-09 : Promoteur fantôme
```
Promoteur ⊓ ¬∃partageAdresse.⊤ ⊓ (≥ 3 possede.Parcelle) ⊓ ¬∃lienFamilial.⊤  ⊑  PromoteurFantome
```
*Un promoteur sans adresse stable, sans lien familial documenté mais détenant ≥ 3 parcelles est suspect d'identité fictive.*

### AX-10 : Dossier suspect composite
```
Dossier ⊓ ∃traite.(ConflitInteretDirect ⊔ ConflitInteretIndirect) ⊓ ∃concerneActeur.SuspectPreteNom  ⊑  DossierSuspect
```
*Un dossier traité en conflit d'intérêt ET impliquant un suspect de prête-nom est automatiquement classé DossierSuspect.*

---

## 4. Contraintes d'Intégrité (CI — 8 contraintes)

### CI-01 : Auto-traitement interdit
```
¬∃x : AgentPublic(x) ∧ traite(x, d) ∧ beneficiaire(x, a) ∧ concerneDossier(a, d)
```
*Un agent public ne peut pas être bénéficiaire d'une affectation liée au dossier qu'il traite.*

### CI-02 : Plafond de parcelles urbaines par citoyen
```
∀x : Citoyen(x) → |{y : possede(x,y) ∧ ParcelleUrbaine(y)}| ≤ 3
```
*Un citoyen ne peut détenir plus de 3 parcelles urbaines.*

### CI-03 : Unicité de traitement d'un dossier
```
∀d : Dossier(d) → |{a : AgentPublic(a) ∧ traite(a,d)}| ≤ 1
```
*Un dossier ne peut être traité que par un seul agent public.*

### CI-04 : Parcelle sans double propriété simultanée
```
∀p : Parcelle(p) → |{x : possede(x,p) ∧ Acteur(x)}| ≤ 1
```
*Une parcelle ne peut avoir qu'un seul propriétaire à un instant donné.*

### CI-05 : Téléphone partagé → suspicion de prête-nom
```
∀x,y : Acteur(x) ∧ Acteur(y) ∧ x ≠ y ∧ partageTelephone(x,y)
         → SuspectPreteNom(x) ∧ SuspectPreteNom(y)
```
*Deux acheteurs distincts partageant le même téléphone génèrent automatiquement une suspicion.*

### CI-06 : Délai minimal entre reventes
```
∀x,p : Acteur(x) ∧ Parcelle(p) ∧ possede(x,p) →
        dureeDetention(x,p) ≥ 12_mois ∨ FlagReventeRapide(x,p)
```
*Une revente en moins de 12 mois doit être signalée.*

### CI-07 : Notaire sans lien avec les parties
```
∀n,x,y : Notaire(n) ∧ vendA(x,y) ∧ traitePar(vendA(x,y), n) →
          ¬lienFamilial(n,x) ∧ ¬lienFamilial(n,y) ∧ ¬lienProfessionnel(n,x)
```
*Un notaire instrumentant une vente ne peut être lié aux parties (famille ou travail).*

### CI-08 : Plus-value plafonnée sans justification
```
∀x,p : revendParcelle(x,p) ∧
        ((prixVente - prixAchat) / prixAchat > 0.5) →
        RequiertJustificationPlusValue(x,p)
```
*Toute plus-value supérieure à 50% nécessite une justification documentée.*

---

## 5. Résumé de la TBox

| Catégorie          | Nombre |
|--------------------|--------|
| Concepts primitifs | 5      |
| Sous-concepts      | 13     |
| Rôles              | 9      |
| Axiomes complexes  | 10     |
| Contraintes CI     | 8      |
| Concepts dérivés   | 8      |

---

*LandGuard Neuro-Symbolic AI — Partie 1 : Logique de Description*
