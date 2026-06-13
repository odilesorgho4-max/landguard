% ============================================================
%  LandGuard — rules.pl (sans module, version corrigee)
% ============================================================

:- dynamic date_construction/3.
:- dynamic vend_a/3.

% Ajout vente pour les tests
vend_a(mariama, oumar, p6).

% ============================================================
% CATEGORIE A — ACCAPAREMENT
% ============================================================

accaparement_urbain(X, N) :-
    acteur(X),
    findall(P, (possede(X,P), parcelle_urbaine(P)), Ps),
    length(Ps, N),
    N >= 4.

accaparement_familial(X, Famille, Total) :-
    acteur(X),
    findall(M, (lien_familial(X,M) ; lien_familial(M,X)), ProchesRep),
    sort([X|ProchesRep], Famille),
    findall(P, (member(F,Famille), possede(F,P), parcelle_urbaine(P)), ToutesPs),
    sort(ToutesPs, PsUniques),
    length(PsUniques, Total),
    Total >= 6.

accaparement_rural(X, N) :-
    acteur(X),
    findall(P, (possede(X,P), parcelle_rurale(P)), Ps),
    length(Ps, N),
    N >= 3.

multipropriete_mixte(X, Total) :-
    acteur(X),
    findall(P, (possede(X,P), parcelle_urbaine(P)), Pu),
    findall(R, (possede(X,R), parcelle_rurale(R)), Pr),
    length(Pu, Nu), length(Pr, Nr),
    Total is Nu + Nr,
    Total >= 5.

% ============================================================
% CATEGORIE B — SPECULATION
% ============================================================

speculation_revente_rapide(X, P, Duree) :-
    acteur(X), parcelle(P),
    duree_detention_mois(X, P, Duree),
    Duree < 12.

speculation_plus_value(X, P, Ratio) :-
    acteur(X), parcelle(P),
    plus_value_ratio(X, P, Ratio),
    Ratio > 0.5.

speculation_non_mise_en_valeur(X, P) :-
    acteur(X), parcelle_urbaine(P),
    possede(X, P),
    date_achat(X, P, YA-_),
    \+ date_construction(X, P, _),
    YA =< 2022.

% ============================================================
% CATEGORIE C — CONFLITS D'INTERETS
% ============================================================

conflit_interet_direct(Agent, Dossier) :-
    agent_public(Agent),
    dossier(Dossier),
    traite(Agent, Dossier),
    beneficiaire(Agent, Dossier).

conflit_interet_indirect(Agent, Proche, Dossier) :-
    agent_public(Agent),
    dossier(Dossier),
    traite(Agent, Dossier),
    concerne_dossier(Dossier, Proche),
    lien_familial(Agent, Proche),
    Proche \= Agent.

conflit_favoritisme(Agent, Acteur, NbDossiers) :-
    agent_public(Agent),
    acteur(Acteur),
    Agent \= Acteur,
    findall(D, (dossier(D), traite(Agent,D), concerne_dossier(D,Acteur)), Ds),
    length(Ds, NbDossiers),
    NbDossiers >= 3.

conflit_notaire_lie(Notaire, Vendeur, Acheteur, TypeLien) :-
    notaire(Notaire),
    acteur(Vendeur), acteur(Acheteur),
    vend_a(Vendeur, Acheteur, _),
    (   lien_familial(Notaire, Vendeur)      -> TypeLien = familial_vendeur
    ;   lien_familial(Notaire, Acheteur)     -> TypeLien = familial_acheteur
    ;   lien_professionnel(Notaire, Vendeur) -> TypeLien = professionnel_vendeur
    ;   lien_professionnel(Notaire, Acheteur)-> TypeLien = professionnel_acheteur
    ).

% ============================================================
% CATEGORIE D — RESEAUX
% ============================================================

reseau_telephone(X, Y, Tel) :-
    acteur(X), acteur(Y),
    X \= Y,
    partage_telephone(X, Y, Tel).

reseau_adresse(X, Y, Adresse) :-
    acteur(X), acteur(Y),
    X \= Y,
    partage_adresse(X, Y, Adresse),
    possede(X, _), possede(Y, _).

reseau_circulaire(X, Y, Z) :-
    acteur(X), acteur(Y), acteur(Z),
    X \= Y, Y \= Z, X \= Z,
    vend_a(X, Y, _),
    vend_a(Y, Z, _),
    vend_a(Z, X, _).

reseau_iban(X, Y, IBAN) :-
    acteur(X), acteur(Y),
    X \= Y,
    partage_iban(X, Y, IBAN).

% ============================================================
% SCORING
% ============================================================

poids_niveau(critique, 10).
poids_niveau(haut,      5).
poids_niveau(moyen,     2).
poids_niveau(faible,    1).

score_risque(X, Score) :-
    acteur(X),
    findall(W, (
        violation(X, _, _, Niveau),
        poids_niveau(Niveau, W)
    ), Poids),
    sumlist(Poids, Score).

niveau_risque(Score, critique) :- Score >= 20, !.
niveau_risque(Score, haut)     :- Score >= 10, !.
niveau_risque(Score, moyen)    :- Score >= 4,  !.
niveau_risque(_, faible).

% ============================================================
% VIOLATIONS (point d'entree unifie)
% ============================================================

violation(X, accaparement, 'A1', haut) :-
    accaparement_urbain(X, _).
violation(X, accaparement, 'A2', critique) :-
    accaparement_familial(X, _, _).
violation(X, accaparement, 'A3', moyen) :-
    accaparement_rural(X, _).
violation(X, accaparement, 'A4', moyen) :-
    multipropriete_mixte(X, _).
violation(X, speculation, 'B1', haut) :-
    possede(X,P), parcelle(P),
    speculation_revente_rapide(X, P, _).
violation(X, speculation, 'B2', haut) :-
    possede(X,P), parcelle(P),
    speculation_plus_value(X, P, _).
violation(X, speculation, 'B3', moyen) :-
    speculation_non_mise_en_valeur(X, _).
violation(X, conflit, 'C1', critique) :-
    conflit_interet_direct(X, _).
violation(X, conflit, 'C2', critique) :-
    conflit_interet_indirect(X, _, _).
violation(X, conflit, 'C3', haut) :-
    conflit_favoritisme(X, _, _).
violation(X, conflit, 'C4', haut) :-
    conflit_notaire_lie(X, _, _, _).
violation(X, reseau, 'D1', haut) :-
    reseau_telephone(X, _, _).
violation(X, reseau, 'D2', haut) :-
    reseau_adresse(X, _, _).
violation(X, reseau, 'D3', critique) :-
    reseau_circulaire(X, _, _).
violation(X, reseau, 'D4', critique) :-
    reseau_iban(X, _, _).

% ============================================================
% RAPPORT
% ============================================================

rapport_acteur(X) :-
    acteur(X),
    findall(v(Cat,R,N), violation(X,Cat,R,N), Vs),
    sort(Vs, VsUniq),
    (   VsUniq \= []
    ->  findall(W, (member(v(_,_,Niv), VsUniq), poids_niveau(Niv,W)), Poids),
        sumlist(Poids, Score),
        niveau_risque(Score, Niveau),
        format("~n[~w] ~w | Score: ~w | Niveau: ~w~n", [Niveau, X, Score, Niveau]),
        forall(member(v(Cat,R,Niv), VsUniq),
               format("  ⚠ [~w] Regle ~w (~w)~n", [Niv, R, Cat]))
    ;   true
    ).

rapport_global :-
    format("~n=== LANDGUARD — RAPPORT GLOBAL ===~n~n"),
    forall(acteur(X), rapport_acteur(X)),
    format("~n=== FIN RAPPORT ===~n").

% ============================================================
% FIN rules.pl
% ============================================================
