import google.generativeai as genai
import json
from src.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

def generate_answer(query: str, contexts: list[dict]) -> str:
    """Generate answer using retrieved contexts"""
    
    # Build context from retrieved chunks
    context_text = ""
    clause_refs = []
    
    for i, ctx in enumerate(contexts):
        context_text += f"[CLAUSE_{i+1}] {ctx['text']}\n\n"
        clause_refs.append(f"CLAUSE_{i+1}")
    
    prompt = f"""You are an expert insurance policy analyst. Based on the provided policy clauses, answer the user's question accurately and cite specific clauses.

POLICY CLAUSES:
{context_text}

QUESTION: {query}

INSTRUCTIONS:
1. Read all the provided clauses carefully
2. If the answer is found in the clauses, provide a clear, specific answer
3. Cite the specific clause numbers that support your answer
4. If no relevant information is found, state that clearly
5. Do not make up information not present in the clauses

Respond in this exact JSON format:
{{"answer": "Your detailed answer here", "clauses": ["CLAUSE_1", "CLAUSE_2"]}}

JSON Response:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return json.dumps({"answer": f"Error generating response: {str(e)}", "clauses": []})
