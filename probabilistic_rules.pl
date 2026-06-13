% ============================================================
%  LandGuard Neuro-Symbolic AI
%  probabilistic_rules.pl — Raisonnement probabiliste
%  ProbLog : regles avec poids a priori
% ============================================================

% ============================================================
% SECTION 1 : Faits de base
% ============================================================

% Instances acteurs
acteur(abdou). acteur(fatou). acteur(ibrahim).
acteur(mariama). acteur(oumar). acteur(aminata).
acteur(youssouf). acteur(moussa). acteur(konate).
acteur(delta_group).

% Liens sociaux
lien_familial(abdou, moussa).
lien_familial(mariama, aminata).

% Proprietes
possede_urbain(abdou, 5).
possede_urbain(mariama, 1).
possede_urbain(oumar, 1).
possede_urbain(moussa, 2).
possede_urbain(fatou, 1).

% Transactions
revente_rapide(mariama).
plus_value_anormale(mariama).
partage_tel(mariama, oumar).
partage_tel(oumar, aminata).
partage_adr(mariama, oumar).
partage_adr(oumar, aminata).
partage_iban_fact(oumar, delta_group).
conflit_direct(konate).
nb_parcelles_urbaines_fact(abdou, 5).
nb_parcelles_urbaines_fact(moussa, 2).

% ============================================================
% SECTION 2 : Regles probabilistes — Prete-nom
% ============================================================

0.80::prete_nom(X, Y) :- partage_tel(X, Y).
0.65::prete_nom(X, Y) :- partage_adr(X, Y).
0.92::prete_nom_confirme(X, Y) :- partage_tel(X, Y), partage_adr(X, Y).
0.85::prete_nom_financier(X, Y) :- partage_iban_fact(X, Y).

% ============================================================
% SECTION 3 : Regles probabilistes — Speculation
% ============================================================

0.60::speculateur(X) :- revente_rapide(X).
0.70::speculateur(X) :- plus_value_anormale(X).
0.88::speculateur_confirme(X) :- revente_rapide(X), plus_value_anormale(X).

% ============================================================
% SECTION 4 : Regles probabilistes — Accaparement
% ============================================================

0.95::accapareur(X) :- nb_parcelles_urbaines_fact(X, N), N >= 4.
0.75::accapareur_reseau(X) :- lien_familial(X, Y),
    nb_parcelles_urbaines_fact(X, N1),
    nb_parcelles_urbaines_fact(Y, N2),
    Total is N1 + N2, Total >= 5.

% ============================================================
% SECTION 5 : Regles probabilistes — Conflits
% ============================================================

0.97::conflit_certain(X) :- conflit_direct(X).

% ============================================================
% SECTION 6 : Fraude globale
% ============================================================

0.99::fraude_probable(X) :- conflit_certain(X).
0.90::fraude_probable(X) :- prete_nom_confirme(X, _), accapareur(X).
0.88::fraude_probable(X) :- speculateur_confirme(X), prete_nom_confirme(X, _).
0.80::fraude_probable(X) :- speculateur_confirme(X), accapareur(X).
0.70::fraude_probable(X) :- prete_nom_confirme(X, _).
0.60::fraude_probable(X) :- speculateur_confirme(X).
0.50::fraude_probable(X) :- accapareur_reseau(X).
0.40::fraude_probable(X) :- prete_nom(X, _).
0.25::fraude_probable(X) :- speculateur(X).

% ============================================================
% FIN probabilistic_rules.pl
% ============================================================
