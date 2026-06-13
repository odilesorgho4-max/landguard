% ============================================================
%  LandGuard — landguard_problog.pl
%  Fichier unique ProbLog (regles + requetes)
% ============================================================

% ============================================================
% FAITS DE BASE
% ============================================================

lien_familial(abdou, moussa).
lien_familial(mariama, aminata).

possede_urbain(abdou, 5).
possede_urbain(moussa, 2).
possede_urbain(mariama, 1).
possede_urbain(fatou, 1).

revente_rapide(mariama).
plus_value_anormale(mariama).

partage_tel(mariama, oumar).
partage_tel(oumar, aminata).
partage_adr(mariama, oumar).
partage_adr(oumar, aminata).
partage_iban_fact(oumar, delta_group).
conflit_direct(konate).

% ============================================================
% REGLES PROBABILISTES
% ============================================================

0.80::prete_nom(X,Y) :- partage_tel(X,Y).
0.65::prete_nom(X,Y) :- partage_adr(X,Y).
0.92::prete_nom_confirme(X,Y) :- partage_tel(X,Y), partage_adr(X,Y).
0.85::prete_nom_financier(X,Y) :- partage_iban_fact(X,Y).

0.60::speculateur(X) :- revente_rapide(X).
0.70::speculateur(X) :- plus_value_anormale(X).
0.88::speculateur_confirme(X) :- revente_rapide(X), plus_value_anormale(X).

0.95::accapareur(abdou) :- possede_urbain(abdou, N), N >= 4.
0.75::accapareur_reseau(abdou) :- lien_familial(abdou, moussa).

0.97::conflit_certain(konate) :- conflit_direct(konate).

0.99::fraude_probable(konate) :- conflit_certain(konate).
0.90::fraude_probable(mariama) :- prete_nom_confirme(mariama, oumar).
0.88::fraude_probable(mariama) :- speculateur_confirme(mariama).
0.85::fraude_probable(oumar) :- prete_nom_confirme(oumar, aminata).
0.80::fraude_probable(abdou) :- accapareur(abdou).
0.70::fraude_probable(oumar) :- prete_nom_financier(oumar, delta_group).
0.50::fraude_probable(moussa) :- accapareur_reseau(abdou).
0.25::fraude_probable(fatou).

% ============================================================
% REQUETES
% ============================================================

query(fraude_probable(konate)).
query(fraude_probable(mariama)).
query(fraude_probable(oumar)).
query(fraude_probable(abdou)).
query(fraude_probable(moussa)).
query(fraude_probable(fatou)).
query(prete_nom(mariama, oumar)).
query(prete_nom_confirme(mariama, oumar)).
query(speculateur_confirme(mariama)).
query(accapareur(abdou)).
query(conflit_certain(konate)).

% ============================================================
% FIN
% ============================================================
