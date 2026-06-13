% ============================================================
%  LandGuard — inference_engine.pl (sans module)
% ============================================================

evaluer_acteur(X, Alertes) :-
    acteur(X),
    findall(v(Cat,R,N), violation(X,Cat,R,N), Vs),
    sort(Vs, Alertes).

acteurs_suspects(Suspects) :-
    findall(X-Niveau, (
        acteur(X),
        findall(v(C,R,N), violation(X,C,R,N), Vs),
        Vs \= [],
        sort(Vs, VsU),
        findall(W, (member(v(_,_,Niv),VsU), poids_niveau(Niv,W)), Poids),
        sumlist(Poids, Score),
        niveau_risque(Score, Niveau)
    ), Suspects).

evaluer_tous(Resultats) :-
    findall(r(X,Score,Niveau,Alertes), (
        acteur(X),
        evaluer_acteur(X, Alertes),
        findall(W,(member(v(_,_,N),Alertes),poids_niveau(N,W)),Ps),
        sumlist(Ps, Score),
        niveau_risque(Score, Niveau)
    ), Resultats).

% ============================================================
% FIN inference_engine.pl
% ============================================================
