from sentence_transformers import SentenceTransformer
import threading
import torch
import os

class OptimizedEmbedding:
    _instance = None
    _model = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    print("Loading optimized embedding model...")
                    
                    # Use the smallest efficient model
                    self._model = SentenceTransformer(
                        "paraphrase-MiniLM-L3-v2",  # Only 61MB
                        device='cpu'  # Use CPU to save GPU memory for LLM
                    )
                    
                    # Optional: Quantize to reduce memory further
                    if hasattr(torch, 'quantization'):
                        try:
                            self._model[0].auto_model = torch.quantization.quantize_dynamic(
                                self._model[0].auto_model,
                                {torch.nn.Linear},
                                dtype=torch.qint8
                            )
                            print("Model quantized successfully")
                        except Exception as e:
                            print(f"Quantization failed: {e}")
                    
                    print("Embedding model loaded and optimized")
        return self._model

# Global instance
_embedding_instance = OptimizedEmbedding()

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings using optimized singleton model"""
    model = _embedding_instance.get_model()
    return model.encode(
        texts, 
        show_progress_bar=False, 
        convert_to_tensor=False,
        batch_size=32  # Process in smaller batches
    ).tolist()
