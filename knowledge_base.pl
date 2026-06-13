% ============================================================
%  LandGuard Neuro-Symbolic AI
%  knowledge_base.pl — Base de connaissances (Partie 1)
% ============================================================

:- module(knowledge_base, [
    acteur/1, citoyen/1, agent_public/1, promoteur/1, notaire/1,
    parcelle/1, parcelle_urbaine/1, parcelle_rurale/1,
    dossier/1, dossier_actif/1, dossier_suspect/1,
    lien_familial/2, lien_professionnel/2, lien_financier/2,
    possede/2, traite/2, beneficiaire/2,
    partage_telephone/3, partage_adresse/3, partage_iban/3,
    concerne_dossier/2,
    prix_achat/3, prix_vente/3, date_achat/3, date_vente/3,
    nb_parcelles_urbaines/2, plus_value_ratio/3, duree_detention_mois/3
]).

:- discontiguous lien_familial/2.
:- discontiguous partage_telephone/3.
:- discontiguous partage_adresse/3.

% ============================================================
% SECTION 1 : Taxonomie
% ============================================================

acteur(X) :- citoyen(X).
acteur(X) :- agent_public(X).
acteur(X) :- promoteur(X).
acteur(X) :- notaire(X).

parcelle(X) :- parcelle_urbaine(X).
parcelle(X) :- parcelle_rurale(X).

dossier(X) :- dossier_actif(X).
dossier(X) :- dossier_suspect(X).

% ============================================================
% SECTION 2 : Instances
% ============================================================

% Citoyens
citoyen(abdou).
citoyen(fatou).
citoyen(ibrahim).
citoyen(mariama).
citoyen(oumar).
citoyen(aminata).
citoyen(youssouf).
citoyen(kadiatou).
citoyen(moussa).
citoyen(bintou).

% Agents publics
agent_public(konate).
agent_public(traore).
agent_public(diallo).

% Promoteurs
promoteur(immo_sarl).
promoteur(delta_group).
promoteur(fantome_x).

% Notaires
notaire(me_coulibaly).
notaire(me_ouedraogo).

% ============================================================
% SECTION 3 : Parcelles
% ============================================================

parcelle_urbaine(p1).  parcelle_urbaine(p2).  parcelle_urbaine(p3).
parcelle_urbaine(p4).  parcelle_urbaine(p5).  parcelle_urbaine(p6).
parcelle_urbaine(p7).  parcelle_urbaine(p8).  parcelle_urbaine(p9).
parcelle_urbaine(p10). parcelle_urbaine(p11). parcelle_urbaine(p12).
parcelle_urbaine(p13). parcelle_urbaine(p14).

parcelle_rurale(r1). parcelle_rurale(r2). parcelle_rurale(r3).
parcelle_rurale(r4). parcelle_rurale(r5).

% ============================================================
% SECTION 4 : Proprietes foncieres
% ============================================================

% Cas normal
possede(fatou,    p5).
possede(ibrahim,  r1).
possede(youssouf, p11).
possede(kadiatou, r2).
possede(bintou,   p14).

% Accaparement : abdou detient 5 parcelles urbaines
possede(abdou, p1).
possede(abdou, p2).
possede(abdou, p3).
possede(abdou, p4).
possede(abdou, p7).

% Accaparement familial : moussa = frere d'abdou
possede(moussa, p8).
possede(moussa, p9).

% Reseau prete-nom
possede(mariama,  p6).
possede(oumar,    p10).
possede(aminata,  p12).

% Promoteur
possede(delta_group, p13).

% ============================================================
% SECTION 5 : Transactions
% ============================================================

prix_achat(abdou,   p1, 5000000).
prix_achat(abdou,   p2, 4500000).
prix_achat(abdou,   p3, 6000000).
prix_achat(abdou,   p4, 5500000).
prix_achat(abdou,   p7, 4800000).
prix_achat(mariama, p6, 3000000).
prix_achat(oumar,   p10, 2800000).
prix_achat(delta_group, p13, 15000000).

% Mariama revend p6 avec +80% de plus-value
prix_vente(mariama, p6, 5400000).

date_achat(abdou,   p1,  2020-1).
date_achat(abdou,   p2,  2020-6).
date_achat(abdou,   p3,  2021-3).
date_achat(abdou,   p4,  2022-1).
date_achat(abdou,   p7,  2023-5).
date_achat(mariama, p6,  2023-1).
date_achat(oumar,   p10, 2023-2).
date_achat(aminata, p12, 2023-3).

% Mariama revend 4 mois apres achat
date_vente(mariama, p6, 2023-5).

% ============================================================
% SECTION 6 : Dossiers
% ============================================================

dossier_actif(d1). dossier_actif(d2). dossier_actif(d3).
dossier_actif(d4). dossier_actif(d5).
dossier_suspect(d6). dossier_suspect(d7).

concerne_dossier(d1, abdou).
concerne_dossier(d2, mariama).
concerne_dossier(d3, oumar).
concerne_dossier(d4, delta_group).
concerne_dossier(d5, fatou).
concerne_dossier(d6, abdou).
concerne_dossier(d7, mariama).

traite(konate, d1).
traite(konate, d2).
traite(traore, d3).
traite(traore, d4).
traite(diallo, d5).
traite(konate, d6).
traite(konate, d7).

% CI-01 viole : konate beneficiaire de d6 qu'il traite
beneficiaire(abdou,       d1).
beneficiaire(mariama,     d2).
beneficiaire(oumar,       d3).
beneficiaire(delta_group, d4).
beneficiaire(fatou,       d5).
beneficiaire(konate,      d6).

% ============================================================
% SECTION 7 : Liens sociaux
% ============================================================

lien_familial(abdou,  moussa).
lien_familial(moussa, abdou).
lien_familial(mariama, aminata).
lien_familial(aminata, mariama).
lien_familial(konate,  ibrahim).
lien_familial(ibrahim, konate).

lien_professionnel(me_coulibaly, konate).
lien_financier(oumar, delta_group).

% ============================================================
% SECTION 8 : Reseaux
% ============================================================

partage_telephone(mariama, oumar,   '0022670112233').
partage_telephone(oumar,   aminata, '0022670112233').

partage_adresse(mariama, oumar,   '12 rue Manga Ouaga').
partage_adresse(oumar,   aminata, '12 rue Manga Ouaga').

partage_iban(oumar, delta_group, 'BF0001234567890').

% ============================================================
% SECTION 9 : Predicats utilitaires
% ============================================================

nb_parcelles_urbaines(X, N) :-
    acteur(X),
    findall(P, (possede(X, P), parcelle_urbaine(P)), Ps),
    length(Ps, N).

duree_detention_mois(X, P, D) :-
    date_achat(X, P, YA-MA),
    date_vente(X, P, YV-MV),
    D is (YV - YA) * 12 + (MV - MA).

plus_value_ratio(X, P, Ratio) :-
    prix_achat(X, P, PA),
    prix_vente(X, P, PV),
    PA > 0,
    Ratio is (PV - PA) / PA.

% ============================================================
% FIN knowledge_base.pl
% ============================================================

% date_construction jamais definie = aucune parcelle construite
% (toutes les parcelles sont considerees non baties par defaut)
:- dynamic date_construction/3.

% Transactions de vente (vendeur, acheteur, parcelle)
:- dynamic vend_a/3.

% Mariama vend p6 a oumar
vend_a(mariama, oumar, p6).
