from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import tempfile
import os

from src.ingestion.fetcher import download
from src.ingestion.parser import parse_pdf, parse_docx, parse_email
from src.utils.text_splitter import split_text
from src.embedding.embedder import get_embeddings
from src.retrieval.retriever import build_index, retrieve
from src.generation.generator import generate_answer

router = APIRouter()

class Req(BaseModel):
    documents: List[str]  # List of document URLs
    questions: List[str]

class Ans(BaseModel):
    answers: List[str]

@router.post("/hackrx/run", response_model=Ans)
async def run(req: Req):
    all_chunks = []
    chunk_metadata = []

    # Process each document URL
    for idx, url in enumerate(req.documents):
        print(f"Processing document {idx+1}: {url}")

        # Download document to a temporary file
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                temp_path = download(url, tmp_file.name)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to download document {url}: {e}")

        try:
            # Parse document text based on extension
            if temp_path.endswith(".pdf"):
                text = parse_pdf(temp_path)
            elif temp_path.endswith(".docx"):
                text = parse_docx(temp_path)
            else:
                # Treat as email or fallback parser
                text = parse_email(temp_path)

            print(f"Extracted {len(text)} characters from document {idx+1}")

            # Chunk the extracted text
            chunks = split_text(text, chunk_size=800, chunk_overlap=100)
            print(f"Created {len(chunks)} chunks from document {idx+1}")

            # Add each chunk and its metadata
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "doc_url": url,
                    "doc_index": idx,
                    "chunk_index": chunk_idx,
                    "chunk_id": f"doc{idx}_chunk{chunk_idx}"
                })
        finally:
            # Clean up temporary file safely
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Warning: Failed to delete temp file {temp_path}: {e}")

    print(f"Total chunks collected: {len(all_chunks)}")

    # Generate embeddings for all chunks
    print("Generating embeddings...")
    embeddings = get_embeddings(all_chunks)
    print(f"Generated {len(embeddings)} embeddings")

    # Build or update FAISS index with embeddings, chunks, and metadata
    print("Building FAISS index...")
    build_index(embeddings, all_chunks, chunk_metadata)

    # Process questions: retrieve relevant chunks and generate answers
    answers = []
    for i, question in enumerate(req.questions):
        print(f"\nProcessing question {i+1}: {question}")

        # Retrieve top-k similar chunks (pass metadata too)
        contexts = retrieve(question, k=7)
        
        # Log the retrieved contexts for debug
        print("Retrieved contexts:")
        for j, ctx in enumerate(contexts):
            snippet = ctx['text'][:100].replace("\n", " ")  # One-line preview
            print(f"  {j+1}. Score: {ctx['score']:.3f} - {snippet}...")

        # Generate answer from Gemini API
        try:
            answer = generate_answer(question, contexts)
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"
            print(answer)

        answers.append(answer)
        print(f"Generated answer: {answer}")

    return Ans(answers=answers)

@router.get("/")
def read_root():
    return {"message": "GlitchBusters HackRX API!"}