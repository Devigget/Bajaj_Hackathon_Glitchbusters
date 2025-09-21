from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from fastapi import Body
from typing import List, Dict, Any, Optional
import tempfile
import os
import json
import uuid
from datetime import datetime
from urllib.parse import urlparse

from src.ingestion.fetcher import download
from src.ingestion.parser import parse_pdf, parse_docx, parse_email
from src.utils.text_splitter import split_text
from src.embedding.embedder import get_embeddings
from src.retrieval.retriever import build_index, retrieve
from src.generation.generator import generate_case_investigation_steps

router = APIRouter()

class CaseDetails(BaseModel):
    """Case details model for investigation context"""
    title: str
    FIRNo: str
    FI_book_no: str
    date_time: str
    place: str
    offence: str
    action_time_frame: str
    visited_places: str
    record: str
    modusOperandi: str
    weapon: str
    officer_id: str
    status: bool
    createdAt: str
    updatedAt: str

class Req(BaseModel):
    """Request model for /hackrx/run

    documents: List of document URLs (PDF/DOCX)
    case: Case details object containing investigation context
    
    Example JSON body:
    {
      "documents": ["https://.../file.pdf", "https://.../document.docx"],
      "case": {
        "title": "Sexual Assault Case",
        "FIRNo": "FIR008",
        "FI_book_no": "FI-2025-009",
        "date_time": "2025-09-20T10:30:00Z",
        "place": "Mapusa Market, Goa",
        "offence": "Sexual Assault",
        "action_time_frame": "48",
        "visited_places": "Crime scene, Victim House",
        "record": "Initial investigation started, evidence being collected",
        "modusOperandi": "The person is left handed",
        "weapon": "knife",
        "officer_id": "68cd838fc8a4557439f42c88",
        "status": true,
        "createdAt": "2025-09-21T03:30:30.209+00:00",
        "updatedAt": "2025-09-21T06:26:38.291+00:00"
      }
    }
    """

    documents: List[str]  # List of document URLs
    case: CaseDetails  # Case details object

    @field_validator("documents", mode="before")
    def ensure_documents_list(cls, v):
        # Allow passing a single string; coerce to list
        if isinstance(v, str):
            # Support newline or comma separated values
            if "\n" in v:
                parts = [x.strip() for x in v.splitlines() if x.strip()]
                return parts
            if "," in v:
                parts = [x.strip() for x in v.split(",") if x.strip()]
                return parts if parts else [v]
            return [v]
        return v

    @field_validator("documents")
    def non_empty_documents_list(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError("documents must be a non-empty list")
        return v

class ChecklistItem(BaseModel):
    id: str
    title: str
    type: str
    status: bool
    _id: str

class Ans(BaseModel):
    check_list: List[ChecklistItem]

def generate_case_specific_questions(case: CaseDetails) -> List[str]:
    """Generate focused investigation question based on case details"""
    
    # Single comprehensive question that will generate a complete investigation workflow
    comprehensive_question = f"""Create a complete chronological investigation workflow for {case.offence} case {case.FIRNo} with the following details:
- Location: {case.place}
- Time constraint: {case.action_time_frame} hours for urgent actions
- Weapon involved: {case.weapon}
- Suspect pattern: {case.modusOperandi}
- Current status: {case.record}
- Investigation areas: {case.visited_places}

Generate 12-15 distinct, sequential investigation steps covering immediate response, evidence collection, interviews, forensic analysis, suspect apprehension, and case completion. Each step must be unique and actionable."""
    
    return [comprehensive_question]

@router.post("/hackrx/run", response_model=Ans)
async def run(req: Req):

    # Generate case-specific investigation questions
    case_questions = generate_case_specific_questions(req.case)
    print(f"Generated {len(case_questions)} case-specific questions based on case details")
    
    all_chunks = []
    chunk_metadata = []

    # Process each document URL
    for idx, url in enumerate(req.documents):
        print(f"Processing document {idx+1}: {url}")

        # Detect file type from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Determine file extension
        if filename.lower().endswith('.docx'):
            suffix = '.docx'
        elif filename.lower().endswith('.pdf'):
            suffix = '.pdf'
        else:
            # Default to PDF for unknown extensions
            suffix = '.pdf'
            
        print(f"Detected file type: {suffix}")

        # Download document to a temporary file
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
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
    check_list = []
    all_investigation_steps = []  # Collect all steps first
    seen_steps = set()  # Track duplicate steps
    
    for i, question in enumerate(case_questions):
        print(f"\nProcessing question {i+1}: {question}")

        # Retrieve top-k similar chunks (pass metadata too)
        contexts = retrieve(question, k=7)
        
        # Log the retrieved contexts for debug
        print("Retrieved contexts:")
        for j, ctx in enumerate(contexts):
            snippet = ctx['text'][:100].replace("\n", " ")  # One-line preview
            print(f"  {j+1}. Score: {ctx['score']:.3f} - {snippet}...")

        # Generate answer from Gemini API with case context
        try:
            # Convert case details to dict for generator
            case_dict = req.case.dict() if req.case else None
            answer = generate_case_investigation_steps(question, contexts, case_dict)
            
            # Parse the JSON response from the generator
            try:
                parsed_response = json.loads(answer)
                investigation_steps = parsed_response.get("steps", [])
                
                # Add unique steps to the master list
                for step in investigation_steps:
                    if step and step.strip():  # Only add non-empty steps
                        clean_step = step.strip()
                        
                        # Skip steps that are too short or generic
                        if len(clean_step) < 15:
                            print(f"Skipped too short step: {clean_step}")
                            continue
                            
                        # Skip obviously generic steps
                        generic_phrases = [
                            "follow procedures", "take action", "complete investigation",
                            "do necessary steps", "handle case", "process evidence"
                        ]
                        if any(phrase in clean_step.lower() for phrase in generic_phrases):
                            print(f"Skipped generic step: {clean_step[:50]}...")
                            continue
                        
                        # Create a normalized version for duplicate checking
                        normalized_step = ' '.join(clean_step.lower().split())
                        
                        # Check for similarity with existing steps (not just exact duplicates)
                        is_similar = False
                        for existing_step in seen_steps:
                            # Check if steps are too similar (share too many words)
                            existing_words = set(existing_step.split())
                            current_words = set(normalized_step.split())
                            
                            if len(existing_words) > 3 and len(current_words) > 3:
                                overlap = len(existing_words.intersection(current_words))
                                similarity_ratio = overlap / min(len(existing_words), len(current_words))
                                
                                if similarity_ratio > 0.6:  # 60% word overlap = too similar
                                    is_similar = True
                                    print(f"Skipped similar step: {clean_step[:50]}...")
                                    break
                        
                        # Only add if not duplicate or similar
                        if not is_similar and normalized_step not in seen_steps:
                            seen_steps.add(normalized_step)
                            all_investigation_steps.append({
                                "step": clean_step,
                                "question_context": question
                            })
                            print(f"Added unique step {len(all_investigation_steps)}: {clean_step[:50]}...")
                        elif normalized_step in seen_steps:
                            print(f"Skipped exact duplicate step: {clean_step[:50]}...")
                        
            except json.JSONDecodeError:
                # Fallback: treat the raw answer as a single step
                if answer and answer.strip():
                    clean_step = answer.strip()
                    normalized_step = ' '.join(clean_step.lower().split())
                    
                    if normalized_step not in seen_steps:
                        seen_steps.add(normalized_step)
                        all_investigation_steps.append({
                            "step": clean_step,
                            "question_context": question
                        })
                
        except Exception as e:
            error_message = f"Error generating answer: {str(e)}"
            print(error_message)
            
            # Add error as a step (if not duplicate)
            normalized_error = ' '.join(error_message.lower().split())
            if normalized_error not in seen_steps:
                seen_steps.add(normalized_error)
                all_investigation_steps.append({
                    "step": error_message,
                    "question_context": question
                })

    # Now create properly numbered checklist items from all collected UNIQUE steps
    print(f"\nCreating checklist from {len(all_investigation_steps)} unique investigation steps")
    
    for step_index, step_data in enumerate(all_investigation_steps):
        step_text = step_data["step"]
        
        # Generate sequential ID starting from 1 (step_index + 1)
        item_id = str(step_index + 1)
        
        # Clean up step text and determine type based on content
        clean_step = step_text.strip()
        step_type = "Field Work"  # Default type
        
        # Determine type based on step content
        if any(keyword in clean_step.lower() for keyword in ["document", "report", "file", "record", "form", "register"]):
            step_type = "Documentation"
        elif any(keyword in clean_step.lower() for keyword in ["interview", "statement", "witness", "victim", "complainant", "question"]):
            step_type = "Interview"
        elif any(keyword in clean_step.lower() for keyword in ["evidence", "collect", "preserve", "forensic", "sample", "photograph", "seize"]):
            step_type = "Evidence Collection"
        elif any(keyword in clean_step.lower() for keyword in ["coordinate", "contact", "notify", "inform", "communicate", "report to"]):
            step_type = "Coordination"
        elif any(keyword in clean_step.lower() for keyword in ["secure", "scene", "visit", "inspect", "examine", "search"]):
            step_type = "Field Work"
        
        checklist_item = ChecklistItem(
            id=item_id,
            title=clean_step,
            type=step_type,
            status=False,  # Default to uncompleted
            _id=str(uuid.uuid4())  # Generate unique ObjectId-like string
        )
        check_list.append(checklist_item)
        print(f"Created checklist item {item_id}: {clean_step[:50]}...")

    print(f"Generated {len(check_list)} sequential, unique checklist items")
    return Ans(check_list=check_list)

@router.post("/hackrx/debug")
async def debug(req: Req):
    """Return the parsed request for debugging 422 errors."""
    return {
        "documents_count": len(req.documents) if req.documents else 0,
        "documents": req.documents,
        "case_details": req.case.dict() if req.case else None,
        "generated_questions": generate_case_specific_questions(req.case) if req.case else []
    }

@router.get("/")
def read_root():
    return {"message": "GlitchBusters HackRX API!"}