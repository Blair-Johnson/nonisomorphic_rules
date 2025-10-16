import networkx as nx
from pyswip import Prolog
from digraph6 import load_digraph6_file

def create_prolog_rule(G:nx.DiGraph, name:str='query') -> str:
    atoms = [f"di_edge(Z{i},Z{j})" for i,j in G.edges()]
    atoms.append(f"all_distinct([{', '.join([f'Z{i}' for i in G.nodes()])}])")
    head = name + f"(Z0, Z{len(G.nodes())-1})"
    return head + " :- " + ", ".join(atoms)

def find_SAT_pairs(query_graph:nx.DiGraph, facts_graph:nx.DiGraph) -> list:
    prolog = Prolog()
    prolog.assertz("all_distinct(L) :- sort(L,S), length(L,N), length(S,N)")
    # ingest background facts
    for i,j in facts_graph.edges():
        prolog.assertz(f"di_edge(v{i}, v{j})")
    rule = create_prolog_rule(query_graph)
    prolog.assertz(rule)
    solns = list(set([(soln['X'],soln['Y']) for soln in prolog.query("query(X,Y)")]))
    return solns

if __name__ == '__main__':
    graphs = {f'g{n}':load_digraph6_file(f'./digraphs/g{n}cd.g6')[f'g{n}'] for n in range(2,6)}
    solns = find_SAT_pairs(graphs['g3'][0], graphs['g5'][0])
