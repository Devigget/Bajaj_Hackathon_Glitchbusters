import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHROMA_PATH = os.getenv("CHROMA_PERSIST_PATH", "./data/chroma_db")  # Keep for FAISS storage
FAISS_DATA_PATH = os.getenv("FAISS_DATA_PATH", "./data/faiss_db")
