import faiss
import numpy as np
import pickle
import os
from src.config import CHROMA_PATH

# Global FAISS index and storage
_faiss_index = None
_chunk_texts = []
_chunk_metadata = []

# Path for persisting FAISS index and data
FAISS_INDEX_PATH = os.path.join(CHROMA_PATH, "faiss.idx")
FAISS_DATA_PATH = os.path.join(CHROMA_PATH, "faiss_data.pkl")

def initialize_faiss_index(embed_dim=384):
    """Initialize a new FAISS index"""
    global _faiss_index
    _faiss_index = faiss.IndexFlatL2(embed_dim)
    return _faiss_index

def get_faiss_index():
    """Get the current FAISS index"""
    global _faiss_index
    if _faiss_index is None:
        # Try to load existing index
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_DATA_PATH):
            load_faiss_index()
        else:
            # Initialize new index with default embedding dimension
            initialize_faiss_index()
    return _faiss_index

def add_to_faiss(embeddings, chunks, metadata=None):
    """Add embeddings and chunks to FAISS index"""
    global _faiss_index, _chunk_texts, _chunk_metadata
    
    if _faiss_index is None:
        embed_dim = len(embeddings[0])
        initialize_faiss_index(embed_dim)
    
    # Convert embeddings to numpy array
    emb_matrix = np.array(embeddings).astype('float32')
    
    # Add to FAISS index
    _faiss_index.add(emb_matrix)
    
    # Store chunk texts
    _chunk_texts.extend(chunks)
    
    # Store metadata if provided
    if metadata:
        _chunk_metadata.extend(metadata)
    else:
        # Create default metadata
        _chunk_metadata.extend([{"chunk_id": len(_chunk_texts) - len(chunks) + i} for i in range(len(chunks))])

def search_faiss(query_embedding, k=5):
    """Search FAISS index for similar vectors"""
    global _faiss_index, _chunk_texts
    
    if _faiss_index is None or len(_chunk_texts) == 0:
        return {"documents": [[]], "ids": [[]]}
    
    # Convert query embedding to numpy array
    query_emb = np.array([query_embedding]).astype('float32')
    
    # Search FAISS index
    distances, indices = _faiss_index.search(query_emb, min(k, len(_chunk_texts)))
    
    # Get corresponding texts
    retrieved_chunks = [_chunk_texts[i] for i in indices[0] if i < len(_chunk_texts)]
    retrieved_ids = [f"c{i}" for i in indices[0] if i < len(_chunk_texts)]
    
    # Return in ChromaDB-compatible format
    return {
        "documents": [retrieved_chunks],
        "ids": [retrieved_ids]
    }

def save_faiss_index():
    """Save FAISS index and associated data to disk"""
    global _faiss_index, _chunk_texts, _chunk_metadata
    
    if _faiss_index is not None:
        # Create directory if it doesn't exist
        os.makedirs(CHROMA_PATH, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(_faiss_index, FAISS_INDEX_PATH)
        
        # Save chunk texts and metadata
        with open(FAISS_DATA_PATH, 'wb') as f:
            pickle.dump({
                'chunk_texts': _chunk_texts,
                'chunk_metadata': _chunk_metadata
            }, f)

def load_faiss_index():
    """Load FAISS index and associated data from disk"""
    global _faiss_index, _chunk_texts, _chunk_metadata
    
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FAISS_DATA_PATH):
        # Load FAISS index
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        
        # Load chunk texts and metadata
        with open(FAISS_DATA_PATH, 'rb') as f:
            data = pickle.load(f)
            _chunk_texts = data['chunk_texts']
            _chunk_metadata = data['chunk_metadata']

def clear_faiss_index():
    """Clear the current FAISS index and data"""
    global _faiss_index, _chunk_texts, _chunk_metadata
    
    _faiss_index = None
    _chunk_texts = []
    _chunk_metadata = []
    
    # Remove saved files
    if os.path.exists(FAISS_INDEX_PATH):
        os.remove(FAISS_INDEX_PATH)
    if os.path.exists(FAISS_DATA_PATH):
        os.remove(FAISS_DATA_PATH)

def get_index_stats():
    """Get statistics about the current index"""
    global _faiss_index, _chunk_texts
    
    if _faiss_index is None:
        return {"total_vectors": 0, "total_chunks": 0}
    
    return {
        "total_vectors": _faiss_index.ntotal,
        "total_chunks": len(_chunk_texts)
    }
