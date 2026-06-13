% ============================================================
%  LandGuard Neuro-Symbolic AI
%  explainability.pl — Module XAI (Partie 2)
%  Journalisation, traces logiques et explications textuelles
% ============================================================

:- module(explainability, [
    log_inference/5,
    expliquer_alerte/3,
    generer_rapport_xai/2,
    afficher_trace/1,
    sauvegarder_traces/1,
    vider_journal/0
]).

:- use_module(library(lists)).

% ============================================================
% SECTION 1 : Journal dynamique des inférences
% ============================================================

% Structure : journal_entry(RegleID, Predicat, Acteur, Tokens, Niveau, Timestamp)
:- dynamic journal_entry/6.

% Compteur global d'inférences
:- dynamic compteur_inference/1.
compteur_inference(0).

% Niveaux de criticité
niveau_valide(critique).
niveau_valide(haut).
niveau_valide(moyen).
niveau_valide(faible).

% ============================================================
% log_inference(+RegleID, +Predicat, +Acteur, +Tokens, +Niveau)
% Point d'entrée principal pour journaliser une inférence
% ============================================================
log_inference(RegleID, Predicat, Acteur, Tokens, Niveau) :-
    (niveau_valide(Niveau) -> true ; Niveau = faible),
    get_time(TS),
    retract(compteur_inference(N)),
    N1 is N + 1,
    assert(compteur_inference(N1)),
    assertz(journal_entry(RegleID, Predicat, Acteur, Tokens, Niveau, TS)).

% ============================================================
% SECTION 2 : Génération d'explications textuelles
% ============================================================

% expliquer_alerte(+RegleID, +Acteur, -ExplicationTexte)
expliquer_alerte('A1', X, Texte) :-
    nb_parcelles_urbaines(X, N),
    format(atom(Texte),
        "L'acteur ~w détient ~w parcelles urbaines, soit ~w de plus que le maximum légal \c
         fixé à 3 (Contrainte CI-02). Cela constitue un accaparement urbain caractérisé.",
        [X, N, N-3]).

expliquer_alerte('A2', X, Texte) :-
    accaparement_familial(X, Famille, Total),
    format(atom(Texte),
        "Le réseau familial de ~w (~w) cumule ~w parcelles urbaines. \c
         Le seuil d'alerte pour un accaparement familial coordonné est de 6.",
        [X, Famille, Total]).

expliquer_alerte('A3', X, Texte) :-
    accaparement_rural(X, N),
    format(atom(Texte),
        "L'acteur ~w détient ~w parcelles rurales, dépassant le seuil d'alerte (3). \c
         Risque de monopole foncier rural.",
        [X, N]).

expliquer_alerte('A4', X, Texte) :-
    multipropriete_mixte(X, Total),
    format(atom(Texte),
        "L'acteur ~w détient ~w parcelles au total (urbaines + rurales). \c
         Ce cumul mixte est atypique et justifie une investigation.",
        [X, Total]).

expliquer_alerte('B1', X, Texte) :-
    findall(P-D, (possede(X,P), speculation_revente_rapide(X,P,D)), Cases),
    Cases = [P-D|_],
    format(atom(Texte),
        "La parcelle ~w a été revendue ~w mois après son acquisition par ~w. \c
         Le délai légal minimal est de 12 mois (CI-06). \c
         Cette revente ultra-rapide est un indicateur de spéculation.",
        [P, D, X]).

expliquer_alerte('B2', X, Texte) :-
    findall(P-R, (possede(X,P), speculation_plus_value(X,P,R)), Cases),
    Cases = [P-R|_],
    Pct is round(R * 100),
    format(atom(Texte),
        "La plus-value réalisée sur ~w par ~w est de ~w%%, \c
         largement au-dessus du seuil d'alerte de 50%% (CI-08). \c
         Une justification documentée est requise.",
        [P, X, Pct]).

expliquer_alerte('B3', X, Texte) :-
    findall(P, speculation_non_mise_en_valeur(X,P), Ps),
    Ps = [P|_],
    format(atom(Texte),
        "La parcelle ~w appartenant à ~w n'a connu aucune construction \c
         depuis plus de 3 ans. Ce comportement est caractéristique de la \c
         rétention spéculative qui empêche le développement urbain.",
        [P, X]).

expliquer_alerte('C1', X, Texte) :-
    conflit_interet_direct(X, D),
    format(atom(Texte),
        "VIOLATION CRITIQUE — L'agent public ~w a traité le dossier ~w \c
         dont il est lui-même le bénéficiaire. Ceci constitue une violation \c
         directe de la Contrainte d'Intégrité CI-01 (auto-attribution interdite).",
        [X, D]).

expliquer_alerte('C2', X, Texte) :-
    conflit_interet_indirect(X, Proche, D),
    format(atom(Texte),
        "L'agent public ~w a traité le dossier ~w concernant ~w, \c
         qui lui est lié familialement. Ce conflit d'intérêt indirect \c
         est couvert par l'Axiome AX-03 et représente un risque de favoritisme.",
        [X, D, Proche]).

expliquer_alerte('C3', X, Texte) :-
    conflit_favoritisme(X, Acteur, N),
    format(atom(Texte),
        "L'agent ~w a traité ~w dossiers consécutifs pour le même acteur ~w. \c
         Ce schéma répétitif dépasse le seuil de 3 (règle C3) et constitue \c
         un fort indicateur de favoritisme systémique.",
        [X, N, Acteur]).

expliquer_alerte('C4', X, Texte) :-
    conflit_notaire_lie(X, V, A, Lien),
    format(atom(Texte),
        "Le notaire ~w instrumentant la vente entre ~w et ~w présente \c
         un lien de type '~w' avec l'une des parties. \c
         Ceci viole la Contrainte CI-07 (neutralité du notaire).",
        [X, V, A, Lien]).

expliquer_alerte('D1', X, Texte) :-
    reseau_telephone(X, Y, Tel),
    format(atom(Texte),
        "Les acteurs ~w et ~w partagent le même numéro de téléphone (~w). \c
         Selon la CI-05, ceci constitue une suspicion forte de prête-nom. \c
         Les transactions foncières des deux acteurs doivent être auditées conjointement.",
        [X, Y, Tel]).

expliquer_alerte('D2', X, Texte) :-
    reseau_adresse(X, Y, Adr),
    format(atom(Texte),
        "Les propriétaires ~w et ~w déclarent la même adresse (~w). \c
         Cette coïncidence, combinée à des achats fonciers distincts, \c
         suggère une structure de prête-nom avec adresse relais.",
        [X, Y, Adr]).

expliquer_alerte('D3', X, Texte) :-
    reseau_circulaire(X, Y, Z),
    format(atom(Texte),
        "ALERTE CRITIQUE — Circuit de transactions détecté : ~w → ~w → ~w → ~w. \c
         Ce schéma circulaire est un indicateur classique de blanchiment foncier. \c
         L'origine réelle des fonds doit être tracée (AX-08).",
        [X, Y, Z, X]).

expliquer_alerte('D4', X, Texte) :-
    reseau_iban(X, Y, IBAN),
    format(atom(Texte),
        "Les acteurs ~w et ~w utilisent le même compte bancaire (~w) \c
         pour des transactions foncières distinctes. Ce flux financier \c
         partagé est un marqueur de réseau coordonné.",
        [X, Y, IBAN]).

% Explication générique (fallback)
expliquer_alerte(RegleID, X, Texte) :-
    format(atom(Texte),
        "Violation de la règle ~w détectée pour l'acteur ~w. \c
         Consultez le journal d'inférence pour les détails.",
        [RegleID, X]).

% ============================================================
% SECTION 3 : Affichage et export des traces
% ============================================================

% afficher_trace(+Acteur) — affiche toutes les entrées du journal pour un acteur
afficher_trace(X) :-
    format("~n--- TRACE XAI : ~w ---~n", [X]),
    findall(
        entry(RegleID, Niveau, TS),
        journal_entry(RegleID, _, X, _, Niveau, TS),
        Entries
    ),
    (   Entries = []
    ->  format("  Aucune inférence enregistrée.~n")
    ;   forall(
            member(entry(R, N, T), Entries),
            (
                format_time(atom(TSFmt), '%H:%M:%S', T),
                format("  [~w] Règle ~w — Niveau : ~w~n", [TSFmt, R, N])
            )
        )
    ).

% generer_rapport_xai(+Acteur, -RapportAtom)
generer_rapport_xai(X, Rapport) :-
    findall(
        ligne(R, N, Expl),
        (
            journal_entry(R, _, X, _, N, _),
            expliquer_alerte(R, X, Expl)
        ),
        Lignes
    ),
    sort(Lignes, LignesUniques),
    with_output_to(atom(Rapport), (
        format("=== RAPPORT XAI — ~w ===~n~n", [X]),
        forall(
            member(ligne(R, N, Expl), LignesUniques),
            format("[~w] RÈGLE ~w~n~w~n~n", [N, R, Expl])
        )
    )).

% sauvegarder_traces(+FichierSortie)
sauvegarder_traces(Fichier) :-
    findall(entry(R, P, A, Tok, N, TS), journal_entry(R, P, A, Tok, N, TS), Entries),
    open(Fichier, write, Stream),
    format(Stream, "% LandGuard — Journal d'inférence XAI~n~n", []),
    forall(
        member(entry(R, P, A, Tok, N, TS), Entries),
        (
            format_time(atom(TSFmt), '%Y-%m-%d %H:%M:%S', TS),
            format(Stream, "entry(~q, ~q, ~q, ~q, ~q, '~w').~n",
                   [R, P, A, Tok, N, TSFmt])
        )
    ),
    close(Stream),
    format("Journal sauvegardé dans ~w (~w entrées)~n", [Fichier, Entries]).

% vider_journal/0 — remet à zéro le journal
vider_journal :-
    retractall(journal_entry(_, _, _, _, _, _)),
    retract(compteur_inference(_)),
    assert(compteur_inference(0)),
    format("Journal XAI vidé.~n").

% ============================================================
% SECTION 4 : Résumé statistique des inférences
% ============================================================

stats_journal :-
    findall(N, journal_entry(_, _, _, _, N, _), Niveaux),
    length(Niveaux, Total),
    include(=(critique), Niveaux, Critiques),
    include(=(haut),     Niveaux, Hauts),
    include(=(moyen),    Niveaux, Moyens),
    include(=(faible),   Niveaux, Faibles),
    length(Critiques, NC), length(Hauts, NH),
    length(Moyens, NM),    length(Faibles, NF),
    format("~n=== STATISTIQUES XAI ===~n"),
    format("  Total inférences : ~w~n", [Total]),
    format("  Critique : ~w | Haut : ~w | Moyen : ~w | Faible : ~w~n",
           [NC, NH, NM, NF]).

% ============================================================
% FIN explainability.pl
% ============================================================
