import networkx as nx

def parse_d6_string(d6_string: str) -> nx.DiGraph:
    # handle any headers
    if d6_string.startswith('&'):
        data = d6_string[1:]
    elif d6_string.startswith('>>digraph6<<'):
        data = d6_string[12:]
    else:
        data = d6_string
        
    N = ord(data[0]) - 63
    assert N <= 62, f"Graphs with more than 62 vertices are not supported by this parser."
    
    # create bitstream char by char
    adj_data = data[1:]
    bit_stream = ""
    for char in adj_data:
        val = ord(char) - 63
        bit_stream += format(val, '06b')
        
    # cut any padding
    required_bits = N**2
    adj_bits = bit_stream[:required_bits]
    
    G = nx.DiGraph()
    G.add_nodes_from(range(N))
    for i in range(required_bits):
        if adj_bits[i] == '1':
            source_node = i//N
            target_node = i%N
            G.add_edge(source_node, target_node)
    return G

def load_digraph6_file(filename: str):
    all_graphs = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                g = parse_d6_string(line)
                all_graphs.append(g)

    graphs = {}
    for i, G in enumerate(all_graphs):
        key = f'g{G.number_of_nodes()}'
        if key not in graphs.keys():
            graphs[key] = [G]
        else:
            graphs[key].append(G)
    print(f"Loaded {len(all_graphs)} directed graphs.")
    return graphs
