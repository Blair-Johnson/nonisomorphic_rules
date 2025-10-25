all_unique([]).
all_unique([X|Xs]) :-
    maplist(dif(X), Xs),
    all_unique(Xs).
