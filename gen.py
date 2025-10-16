import time
import networkx as nx
from tqdm import tqdm
from pyswip import Prolog
from digraph6 import load_digraph6_file

def create_prolog_rule(G:nx.DiGraph, name:str='query') -> str:
    atoms = [f"di_edge(Z{i},Z{j})" for i,j in G.edges()]
    atoms.append(f"all_distinct([{', '.join([f'Z{i}' for i in G.nodes()])}])")
    head = name + f"(Z0, Z{len(G.nodes())-1})"
    return head + " :- " + ", ".join(atoms)

def find_SAT_pairs(prolog:Prolog, query_graph:nx.DiGraph, facts_graph:nx.DiGraph) -> list:
    # ingest background facts
    prolog.assertz("all_distinct(L) :- sort(L,S), length(L,N), length(S,N)")
    for i,j in facts_graph.edges():
        prolog.assertz(f"di_edge(v{i}, v{j})")
    rule = create_prolog_rule(query_graph)
    prolog.assertz(rule)
    solns = list(set([(soln['X'],soln['Y']) for soln in prolog.query("query(X,Y)")]))
    prolog.retractall("di_edge(_,_)")
    prolog.retractall("query(_,_)")
    prolog.retractall("all_distinct(_)")
    return solns

def filter_search_space(query_graphs:list[nx.DiGraph], fact_graphs:list[nx.DiGraph]) -> list[list[int]]:
    valid_search_pairs = [[] for _ in range(len(query_graphs))]
    for i,query in enumerate(query_graphs):
        edge_count = query.number_of_edges()
        for j,facts in enumerate(fact_graphs):
            if edge_count > facts.number_of_edges():
                continue
            elif query is facts:
                continue
            else:
                valid_search_pairs[i].append(j)
    return valid_search_pairs

def find_all_facts(prolog:Prolog(), graphs:dict[str,nx.DiGraph]) -> list[str]:
    gn_ordered = sorted(list(graphs.keys()))
    all_tasks = []
    for i in range(len(gn_ordered)):
        for gn in gn_ordered[i:]:
            query_graphs = graphs[gn_ordered[i]]
            fact_graphs = graphs[gn]
            valid_search_pairs = filter_search_space(query_graphs, fact_graphs)
            all_tasks.append((query_graphs,fact_graphs,valid_search_pairs))
    comps = [(task[0][q],task[1][t]) for task in all_tasks for q,nums in enumerate(task[2]) for t in nums]
    print(f'Performing {len(comps)} graph comparisons to check for subgraphs.')
    extra_facts = []
    for q_graph, f_graph in tqdm(comps):
        solns = find_SAT_pairs(prolog, q_graph, f_graph)
        extra_facts.append(solns)
    return extra_facts

if __name__ == '__main__':
    graphs = {f'g{n}':load_digraph6_file(f'./digraphs/g{n}cd.g6')[f'g{n}'] for n in range(2,6)}
    prolog = Prolog()
    solns = find_SAT_pairs(prolog, graphs['g3'][0], graphs['g5'][0])
    find_all_facts(prolog, graphs)
