import chromadb
from src.config import CHROMA_PATH

# Initialize ChromaDB client with the new API
_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Create or get collection
def get_collection(name="documents"):
    return _client.get_or_create_collection(name)

def persist():
    # Note: PersistentClient automatically persists data
    # This function is kept for backward compatibility
    pass
