import faiss
import numpy as np
import pickle
import os

class FAISSClient:
    def __init__(self, dimension=None):
        self.dimension = dimension
        self.index = None  # Initialize later when we know the dimension
        self.chunk_texts = []
        self.chunk_metadata = []
    
    def _init_index(self, dimension):
        """Initialize index with the correct dimension"""
        if self.index is None:
            self.dimension = dimension
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            print(f"Initialized FAISS index with dimension: {dimension}")
    
    def add_documents(self, embeddings, texts, metadata=None):
        """Add documents to FAISS index"""
        embeddings = np.array(embeddings).astype('float32')
        
        # Auto-detect dimension from first embedding
        if self.index is None:
            self._init_index(embeddings.shape[1])
        
        # Verify dimension matches
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} doesn't match index dimension {self.dimension}")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        self.index.add(embeddings)
        self.chunk_texts.extend(texts)
        if metadata:
            self.chunk_metadata.extend(metadata)
        
        print(f"Added {len(embeddings)} embeddings to FAISS index")
    
    def search(self, query_embedding, k=5):
        """Search for similar documents"""
        if self.index is None:
            return []
            
        query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunk_texts):  # Valid index
                results.append({
                    "text": self.chunk_texts[idx],
                    "score": float(scores[0][i]),
                    "metadata": self.chunk_metadata[idx] if self.chunk_metadata else None
                })
        
        return results
    
    def save(self, filepath):
        """Save index and metadata"""
        if self.index is not None:
            faiss.write_index(self.index, f"{filepath}.faiss")
            with open(f"{filepath}.pkl", "wb") as f:
                pickle.dump({
                    "dimension": self.dimension,
                    "chunk_texts": self.chunk_texts,
                    "chunk_metadata": self.chunk_metadata
                }, f)
    
    def load(self, filepath):
        """Load index and metadata"""
        if os.path.exists(f"{filepath}.faiss"):
            self.index = faiss.read_index(f"{filepath}.faiss")
            with open(f"{filepath}.pkl", "rb") as f:
                data = pickle.load(f)
                self.dimension = data.get("dimension")
                self.chunk_texts = data["chunk_texts"]
                self.chunk_metadata = data["chunk_metadata"]
