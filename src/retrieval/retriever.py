from src.embedding.embedder import get_embeddings
from src.embedding.chroma_client import get_collection

def retrieve(query: str, k=5):
    col = get_collection()
    q_emb = get_embeddings([query])
    results = col.query(query_embeddings=q_emb, n_results=k, include=["documents","ids"])
    return results
