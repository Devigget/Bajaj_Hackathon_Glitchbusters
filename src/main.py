from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.embedding.embedder import _embedding_instance
from src.api.hackrx import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Preloading embedding model...")
    _embedding_instance.get_model()  # Load on startup
    yield

app = FastAPI(
    title="Bajaj Hackathon - Document RAG API",
    description="RAG API for document processing and question answering",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(router, tags=["RAG"])

@app.get("/")
async def root():
    return {"message": "Bajaj Hackathon RAG API is running!", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "document-rag-api"}
