from src.embedding.embedder import get_embeddings
from src.embedding.faiss_client import search_faiss

def retrieve(query: str, k=5):
    q_emb = get_embeddings([query])[0]  # Get single embedding as list
    results = search_faiss(q_emb, k)
    return results
