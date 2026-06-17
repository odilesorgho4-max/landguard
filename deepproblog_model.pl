% ============================================================
%  LandGuard Neuro-Symbolic AI
%  deepproblog_model.pl — Couche Neuro-Symbolique (Partie 4)
%  Fusion : prédictions PyTorch + contraintes Prolog
% ============================================================

:- module(deepproblog_model, [
    neural_prediction/2,
    fraude_hybride/2,
    speculateur_hybride/2,
    accapareur_hybride/2,
    conflit_hybride/2,
    reseau_hybride/2,
    score_hybride/3,
    expliquer_decision_hybride/3
]).

:- use_module(knowledge_base).
:- use_module(rules).
:- use_module(explainability).

% ============================================================
% SECTION 1 : Prédicat neuronal DeepProbLog
%
%   nn(NomModele, [InputTensor], OutputVar, [Classes])
%
% fraud_model = FraudDetectorNet (neural_model.py)
% Entrée : vecteur 6 features de l'acteur X
% Sortie : distribution sur [standard, atypique, speculateur, fraude]
% ============================================================

nn(fraud_model, [X], Classe, [standard, atypique, speculateur, fraude]).

% neural_prediction(+Acteur, -Classe)
neural_prediction(X, Classe) :-
    acteur(X),
    features_acteur(X, FeatureVec),
    nn(fraud_model, [FeatureVec], Classe, [standard, atypique, speculateur, fraude]).

% ============================================================
% SECTION 2 : Extraction des features (Prolog -> tenseur)
% ============================================================

% features_acteur(+Acteur, -[f1,f2,f3,f4,f5,f6])
features_acteur(X, [NbP, FreqR, RatioPV, NbLiens, Tel, Age]) :-
    acteur(X),
    findall(P, possede(X,P), Ps),          length(Ps, NbP),
    findall(P, (possede(X,P), date_vente(X,P,_)), Rev),
    length(Rev, NbR),
    (NbP > 0 -> FreqR is NbR/NbP ; FreqR = 0.0),
    findall(R, (possede(X,P2), plus_value_ratio(X,P2,R)), Ratios),
    (Ratios \= [] -> max_list(Ratios, RatioPV) ; RatioPV = 0.0),
    findall(Y, lien_social(X,Y), Liens),   length(Liens, NbLiens),
    (partage_telephone(X,_,_) -> Tel = 1.0 ; Tel = 0.0),
    findall(YA, date_achat(X,_,YA-_), Ans),
    (Ans \= [] -> min_list(Ans, MinA), Age is 2026 - MinA ; Age = 5.0).

% ============================================================
% SECTION 3 : Règles hybrides neuro-symboliques
% Décision = signal neuronal ET contrainte symbolique
% ============================================================

% FRAUDE HYBRIDE
fraude_hybride(X, Explication) :-
    neural_prediction(X, fraude),
    (   accaparement_urbain(X,_)    -> Tag = accaparement_urbain
    ;   conflit_interet_direct(X,_) -> Tag = conflit_direct
    ;   reseau_telephone(X,_,_)     -> Tag = reseau_telephone
    ;   reseau_iban(X,_,_)          -> Tag = reseau_iban
    ;   reseau_circulaire(X,_,_)    -> Tag = blanchiment
    ;   Tag = signal_neural_seul
    ),
    format(atom(Explication), "FRAUDE [~w + neural] : ~w", [Tag, X]),
    log_inference('H-FRAUDE', fraude_hybride(X), X,
                  [neural,fraude,symbolique,Tag], critique).

% SPÉCULATEUR HYBRIDE
speculateur_hybride(X, Explication) :-
    neural_prediction(X, speculateur),
    (   findall(P,(possede(X,P),speculation_revente_rapide(X,P,_)),[_|_]) -> Tag=revente_rapide
    ;   findall(P,(possede(X,P),speculation_plus_value(X,P,_)),[_|_])     -> Tag=plus_value
    ;   Tag = signal_neural_seul
    ),
    format(atom(Explication), "SPÉCULATEUR [~w + neural] : ~w", [Tag, X]),
    log_inference('H-SPEC', speculateur_hybride(X), X,
                  [neural,speculateur,symbolique,Tag], haut).

% ACCAPAREUR HYBRIDE
accapareur_hybride(X, Explication) :-
    neural_prediction(X, Classe),
    member(Classe, [fraude, atypique]),
    accaparement_urbain(X, N),
    format(atom(Explication), "ACCAPAREMENT [neural=~w, ~w parcelles] : ~w", [Classe,N,X]),
    log_inference('H-ACCA', accapareur_hybride(X), X,
                  [neural,Classe,accaparement,N], haut).

% CONFLIT HYBRIDE
conflit_hybride(X, Explication) :-
    neural_prediction(X, Classe), Classe \= standard,
    conflit_interet_direct(X, D),
    format(atom(Explication), "CONFLIT [neural=~w, dossier ~w] : ~w", [Classe,D,X]),
    log_inference('H-CONF', conflit_hybride(X), X,
                  [neural,Classe,conflit_direct,D], critique).

% RÉSEAU HYBRIDE
reseau_hybride(X, Explication) :-
    neural_prediction(X, fraude),
    reseau_telephone(X, Y, Tel),
    format(atom(Explication), "RÉSEAU [neural=fraude, tel ~w, avec ~w] : ~w", [Tel,Y,X]),
    log_inference('H-RESEAU', reseau_hybride(X), X,
                  [neural,fraude,prete_nom,Y], critique).

% ============================================================
% SECTION 4 : Score et niveau hybride
% ============================================================

score_hybride(X, ScoreSym, ClasseNeurale) :-
    acteur(X),
    score_risque(X, ScoreSym),
    neural_prediction(X, ClasseNeurale).

niveau_hybride(X, critique) :-
    score_hybride(X, S, C), S >= 10, member(C, [fraude,speculateur]), !.
niveau_hybride(X, eleve) :-
    score_hybride(X, S, C), (S >= 5 ; member(C, [fraude,speculateur])), !.
niveau_hybride(X, moyen) :-
    score_hybride(X, S, C), (S >= 2 ; C = atypique), !.
niveau_hybride(_, faible).

% ============================================================
% SECTION 5 : Explicabilité hybride XAI
% ============================================================

expliquer_decision_hybride(X, ClasseNeurale, TraceTexte) :-
    acteur(X),
    neural_prediction(X, ClasseNeurale),
    features_acteur(X, [NbP, FreqR, RatioPV, NbLiens, Tel, Age]),
    evaluer_acteur(X, Alertes),
    length(Alertes, NbAlertes),
    score_risque(X, ScoreSym),
    niveau_hybride(X, Niveau),
    format(atom(TraceTexte),
        "=== DÉCISION HYBRIDE : ~w ===\n\
[NEURONAL] classe=~w | features: nb_p=~w freq=~w pv=~w liens=~w tel=~w age=~w\n\
[SYMBOLIQUE] alertes=~w score=~w\n\
[FUSION] niveau=~w",
        [X, ClasseNeurale, NbP, FreqR, RatioPV, NbLiens, Tel, Age,
         NbAlertes, ScoreSym, Niveau]),
    log_inference('XAI-HYB', expliquer_decision_hybride(X), X,
                  [classe,ClasseNeurale,score,ScoreSym,niveau,Niveau], Niveau).

% Rapport global
rapport_neuro_symbolique :-
    format("~n=== LANDGUARD RAPPORT NEURO-SYMBOLIQUE ===~n~n"),
    forall(acteur(X), (
        expliquer_decision_hybride(X, _, Trace),
        format("~w~n~n", [Trace]),
        (fraude_hybride(X, Expl) -> format("  >> ~w~n~n", [Expl]) ; true)
    )).

% ============================================================
% FIN deepproblog_model.pl
% ============================================================
