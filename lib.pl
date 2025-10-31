% define uniqueness constraint
all_unique([]).
all_unique([X|Xs]) :-
    maplist(dif(X), Xs),
    all_unique(Xs).

% declare edge predicates dynamic so that they can be asserted and retracted after facts
:- dynamic(di_edge_0/2).
:- dynamic(di_edge_1/2).
:- dynamic(di_edge_2/2).
:- dynamic(di_edge_3/2).
:- dynamic(di_edge_4/2).
:- dynamic(di_edge_5/2).
:- dynamic(di_edge_6/2).
:- dynamic(di_edge_7/2).
