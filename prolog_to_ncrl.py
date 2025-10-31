# NOTE: This script was written using google gemini and modified manually
import re
import argparse
from collections import defaultdict

def parse_and_generate_files(prolog_file_path, output_dir):
    """
    Parses a Prolog file to extract graph information and writes it to
    several output files based on predicate types.

    Args:
        prolog_file_path (str): The path to the input Prolog file.
    """
    # Regex to capture: predicate_name(arg1, arg2).
    # It correctly handles whitespace after the comma.
    predicate_pattern = re.compile(r"(\w+)\((\w+),\s*(\w+)\)\.")

    entities = set()
    background_relations = set()
    label_relations = set()
    background_facts = []
    label_facts = []

    print(f"[*] Reading and parsing '{prolog_file_path}'...")

    try:
        with open(prolog_file_path, 'r') as f:
            for line in f:
                match = predicate_pattern.match(line.strip())
                if match:
                    relation, src, dst = match.groups()
                    
                    # Add entities to the set to ensure uniqueness
                    entities.add(src)
                    entities.add(dst)
                    
                    # Separate facts based on predicate prefix
                    if relation.startswith("di_edge"):
                        background_relations.add(relation)
                        background_facts.append((src, relation, dst))
                    elif relation.startswith("g"):
                        label_relations.add(relation)
                        label_facts.append((src, relation, dst))

    except FileNotFoundError:
        print(f"[!] Error: The file '{prolog_file_path}' was not found.")
        return
        
    print(f"[*] Found {len(entities)} entities, {len(background_facts)} background facts, and {len(label_facts)} label facts.")
    print("[*] Writing output files...")

    # 1. entities.txt
    with open(f'{output_dir}/entities.txt', 'w') as f:
        for entity in sorted(list(entities)): # Sorted for deterministic order
            f.write(f"{entity}\n")

    # 2. facts.txt
    with open(f'{output_dir}/facts.txt', 'w') as f:
        for src, rel, dst in background_facts:
            f.write(f"{src}\t{rel}\t{dst}\n")

    # 3. facts.txt.inv
    with open(f'{output_dir}/facts.txt.inv', 'w') as f:
        # First write the original facts
        for src, rel, dst in background_facts:
            f.write(f"{src}\t{rel}\t{dst}\n")
        # Then write the inverse facts
        for src, rel, dst in background_facts:
            inv_relation = f"inv_{rel}"
            f.write(f"{dst}\t{inv_relation}\t{src}\n")

    # 4. relations.txt
    with open(f'{output_dir}/relations.txt', 'w') as f:
        for relation in sorted(list(background_relations|label_relations)):
            f.write(f"{relation}\n")
    with open(f'{output_dir}/label_relations.txt', 'w') as f:
        for relation in sorted(list(label_relations)):
            f.write(f"{relation}\n")

    # 5, 6, 7. train.txt, test.txt, valid.txt
    for filename in ['train.txt', 'test.txt', 'valid.txt']:
        with open(output_dir+'/'+filename, 'w') as f:
            for src, rel, dst in label_facts:
                f.write(f"{src}\t{rel}\t{dst}\n")
                
    print("[*] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse a Prolog graph file and generate training/fact files."
    )
    parser.add_argument(
        "prolog_file", 
        type=str, 
        help="Path to the input Prolog file."
    )
    parser.add_argument(
        "output_path", 
        type=str, 
        help="Path to the output directory."
    )
    args = parser.parse_args()
    
    parse_and_generate_files(args.prolog_file, args.output_path)
