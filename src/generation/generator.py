import google.generativeai as genai
from src.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def generate_answer(query: str, contexts: list[str]) -> str:
    prompt = "Use the following passages to answer and cite clause IDs:\n\n"
    for i, ctx in enumerate(contexts):
        prompt += f"[{i}] {ctx}\n"
    prompt += f"\nQuestion: {query}\nAnswer with JSON: {{'answer':'', 'clauses':[]}}"
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    resp = model.generate_content(prompt)
    return resp.text
