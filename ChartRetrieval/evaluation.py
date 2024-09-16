# evaluation.py
import numpy as np

def dcg_at_k(r, k):
    """
    Calculate the DCG value at position k.
    """
    r = np.asarray(r)[:k]
    if r.size:
        return np.sum(r / np.log2(np.arange(2, r.size + 2)))
    return 0

def ndcg_at_k(r, k, all_r):
    """
    Calculate the NDCG value at position k.
    """
    # Calculate IDCG by sorting the relevance scores in descending order and computing the DCG for the top k
    sorted_r = sorted(all_r, reverse=True)
    print(f"Size of sorted relevance scores list: {len(sorted_r)}")
    idcg = dcg_at_k(sorted_r, k)
    if not idcg:
        return 0
    return dcg_at_k(r, k) / idcg
