import time
import networkx as nx
import random
from tqdm import tqdm
from pyswip import Prolog
from digraph6 import load_digraph6_file

# only enable if you want ground truth labels to obey glidr's more limited semantics
GLIDR_SEMANTICS = False

def create_prolog_rule(G:nx.DiGraph, name:str='query') -> str:
    atoms = [f"di_edge_{dat['pred']}(Z{i},Z{j})" for i,j,dat in G.edges(data=True)]
    if GLIDR_SEMANTICS:
        # NOTE: Adds equivalent constraints to GLIDR's "restrict_existential_grounding" mode
        for j in list(G.nodes())[1:-1]:
            atoms.append(f"all_unique([Z0, Z{j}])")
            atoms.append(f"all_unique([Z{len(G.nodes())-1}, Z{j}])")
    else:
        # This is the standard interpretation of each graph as a rule
        # Each variable in the rule must be grounded by a different entity
        atoms.append(f"all_unique([{', '.join([f'Z{i}' for i in G.nodes()])}])")
    head = name + f"(Z0, Z{len(G.nodes())-1})"
    return head + " :- " + ", ".join(atoms)

def find_SAT_pairs(prolog:Prolog, query_graph:nx.DiGraph, facts_graph:nx.DiGraph) -> list:
    # ingest background facts
    seen = set()
    for i,j,dat in facts_graph.edges(data=True):
        prolog.assertz(f"di_edge_{dat['pred']}(v{i}, v{j})")
        seen.add(dat['pred'])
    rule = create_prolog_rule(query_graph)
    prolog.assertz(rule)
    solns = list(set([(soln['X'],soln['Y']) for soln in prolog.query("query(X,Y)")]))
    for p in seen:
        prolog.retractall(f"di_edge_{p}(_,_)")
    prolog.retractall("query(_,_)")
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

def invert_graph_index(graphs:dict[str,list[nx.DiGraph]]) -> dict[nx.DiGraph,str]:
    # graph names g{n_nodes}_{global_index}
    rev_index = {}
    global_idx = 0
    for k,v in graphs.items():
        for g in v:
            rev_index[g] = k + f"_{global_idx}"
            global_idx += 1
    return rev_index

def construct_fact_strings(facts:list, graphs:dict[str,list[nx.DiGraph]], rev_index:dict[nx.DiGraph,str]) -> list[str]:
    output_facts = []
    for def_graph, bk_graph, vertices in facts:
        rule_head = rev_index[def_graph]
        vertex_suffix = rev_index[bk_graph]
        new_facts = [f"{rule_head}({x}_{vertex_suffix},{y}_{vertex_suffix})" for x,y in vertices]
        output_facts += new_facts
    return output_facts

def create_graph_facts(rev_index:dict[nx.DiGraph,str]) -> list[str]:
    output_facts = []
    for graph,name in rev_index.items():
        n_nodes = len(graph.nodes())
        output_facts.append(f"{name}(v0_{name},v{n_nodes-1}_{name})")
        for i,j,dat in graph.edges(data=True):
            output_facts.append(f"di_edge_{dat['pred']}(v{i}_{name},v{j}_{name})")
    return output_facts

def find_all_facts(prolog:Prolog(), graphs:dict[str,list[nx.DiGraph]]) -> list[str]:
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
        if len(solns) > 0:
            extra_facts.append((q_graph,f_graph,solns))
    rev_index = invert_graph_index(graphs)
    extra_facts = construct_fact_strings(extra_facts, graphs, rev_index)
    base_facts = create_graph_facts(rev_index)
    all_facts = base_facts + extra_facts
    return all_facts

def add_edge_types(graph:nx.DiGraph, n_preds:int) -> nx.DiGraph:
    edge_attributes = {(u,v): random.randint(0, n_preds-1) for u,v in graph.edges()}
    nx.set_edge_attributes(graph, edge_attributes, name="pred")
    return graph

if __name__ == '__main__':
    for n_preds in [1,2,4]:
        graphs = {f'g{n}':list(map(lambda x: add_edge_types(x, n_preds), load_digraph6_file(f'./digraphs/g{n}cd.g6')[f'g{n}'])) for n in range(3,6)}
        prolog = Prolog()
        prolog.consult("lib.pl")
        all_facts = find_all_facts(prolog, graphs)
        all_facts = [f"% N_PREDS={n_preds}", f"% GLIDR_SEMANTICS={GLIDR_SEMANTICS}"] + all_facts
        with open(f"prolog_graphs/bk_{n_preds}_random_preds.pl", "w") as f:
            f.write('.\n'.join(all_facts))
            f.write('.')
