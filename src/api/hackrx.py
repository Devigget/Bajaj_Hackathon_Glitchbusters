from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.ingestion.fetcher import download
from src.ingestion.parser import parse_pdf, parse_docx, parse_email
from src.utils.text_splitter import split_text
from src.embedding.chroma_client import get_collection, persist
from src.embedding.embedder import get_embeddings
from src.retrieval.retriever import retrieve
from src.generation.generator import generate_answer
import time

router = APIRouter()

class Req(BaseModel):
    documents: list[str]
    questions: list[str]

class Ans(BaseModel):
    answers: list[str]

@router.post("/hackrx/run", response_model=Ans)
async def run(req: Req):
    start = time.time()
    all_chunks = []
    for idx, url in enumerate(req.documents):
        print(f"[{time.time()-start:.1f}s] Downloading document {idx+1}: {url}")
        path = download(url, f"temp_file_{idx}")
        print(f"[{time.time()-start:.1f}s] Downloaded to {path}")

        if path.endswith(".pdf"):
            text = parse_pdf(path)
        elif path.endswith(".docx"):
            text = parse_docx(path)
        else:
            text = parse_email(path)
        print(f"[{time.time()-start:.1f}s] Parsed document {idx+1}, length {len(text)} chars")

        chunks = split_text(text)
        print(f"[{time.time()-start:.1f}s] Split into {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"[{time.time()-start:.1f}s] Total chunks: {len(all_chunks)}")

    embeddings = get_embeddings(all_chunks)
    print(f"[{time.time()-start:.1f}s] Generated embeddings")

    col = get_collection()
    BATCH_SIZE = 5000  # Stay well under the 5461 limit
    ids = [f"c{i}" for i in range(len(all_chunks))]
    for i in range(0, len(all_chunks), BATCH_SIZE):
        chunk = all_chunks[i : i+BATCH_SIZE]
        emb = embeddings[i : i+BATCH_SIZE]
        id_subset = ids[i : i+BATCH_SIZE]
        col.add(documents=chunk, embeddings=emb, ids=id_subset)

    print(f"[{time.time()-start:.1f}s] Indexed chunks in ChromaDB")

    answers = []
    for q in req.questions:
        res = retrieve(q, k=5)
        contexts = [doc for doc in res["documents"][0]]
        print(f"[{time.time()-start:.1f}s] Retrieved top contexts for question: {q}")

        ans = generate_answer(q, contexts)
        print(f"[{time.time()-start:.1f}s] Generated answer")

        answers.append(ans)

    print(f"[{time.time()-start:.1f}s] Completed all questions")
    return Ans(answers=answers)
