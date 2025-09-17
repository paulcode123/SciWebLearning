from typing import List, Dict, Tuple


def extract_knowledge_graph(messages: List[Dict[str, str]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Very simple heuristic extractor that turns a conversation into nodes and edges.
    This is a placeholder for a real NLP/LLM-based extraction pipeline.
    Returns (nodes, edges) where nodes are {label, type} and edges are {source, target, relation}.
    """
    # Collect candidate concepts by splitting on capitalized terms and known separators
    # Naive approach: take distinct words longer than 3 characters that appear frequently
    from collections import Counter
    import re

    full_text = ' '.join([m['content'] for m in messages])
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", full_text)
    counts = Counter([t.lower() for t in tokens])
    common = [w for w, c in counts.most_common(30) if c >= 2]

    nodes = [{"label": w.title(), "type": "concept"} for w in common[:15]]
    label_to_index = {n["label"]: idx for idx, n in enumerate(nodes)}

    # Create simple edges based on co-occurrence in the same sentence
    edges: List[Dict] = []
    sentences = re.split(r"[.!?]\s+", full_text)
    for s in sentences:
        present = [n for n in nodes if re.search(rf"\b{re.escape(n['label'])}\b", s, flags=re.IGNORECASE)]
        for i in range(len(present) - 1):
            src = present[i]["label"]
            tgt = present[i + 1]["label"]
            edges.append({"source": src, "target": tgt, "relation": "co_occurs_with"})

    # Deduplicate edges
    seen = set()
    unique_edges: List[Dict] = []
    for e in edges:
        key = (e["source"], e["target"], e["relation"]) 
        if key not in seen and e["source"] != e["target"]:
            seen.add(key)
            unique_edges.append(e)

    return nodes, unique_edges[:40]

