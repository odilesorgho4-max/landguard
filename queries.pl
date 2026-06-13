% ============================================================
%  LandGuard — queries.pl
%  Requetes ProbLog d'inference probabiliste
% ============================================================

% Fraude globale
query(fraude_probable(abdou)).
query(fraude_probable(mariama)).
query(fraude_probable(oumar)).
query(fraude_probable(aminata)).
query(fraude_probable(konate)).
query(fraude_probable(moussa)).
query(fraude_probable(fatou)).

% Prete-nom
query(prete_nom(mariama, oumar)).
query(prete_nom(oumar, aminata)).
query(prete_nom_confirme(mariama, oumar)).
query(prete_nom_financier(oumar, delta_group)).

% Speculation
query(speculateur(mariama)).
query(speculateur_confirme(mariama)).

% Accaparement
query(accapareur(abdou)).
query(accapareur_reseau(abdou)).
query(accapareur_reseau(moussa)).

% Conflit
query(conflit_certain(konate)).

% ============================================================
% FIN queries.pl
% ============================================================
