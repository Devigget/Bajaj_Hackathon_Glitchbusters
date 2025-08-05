from src.embedding.embedder import get_embeddings
from src.embedding.faiss_client import FAISSClient

# Don't specify dimension - let it auto-detect
faiss_client = FAISSClient()

def build_index(embeddings, chunks, metadata=None):
    """Build FAISS index from embeddings and chunks"""
    faiss_client.add_documents(embeddings, chunks, metadata)

def retrieve(query: str, k=5):
    """Retrieve relevant chunks for a query"""
    query_emb = get_embeddings([query])[0]
    results = faiss_client.search(query_emb, k=k)
    return results
