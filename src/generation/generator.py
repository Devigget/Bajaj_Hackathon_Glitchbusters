import google.generativeai as genai
import json
import re
from typing import List, Dict, Any
import os

# --- Configuration ---
# It's recommended to load the API key from an environment variable or a secure config file.
# For this example, we'll assume it's stored in a config.py file.
# Create a file named 'config.py' in the same directory with the line:
# GEMINI_API_KEY = "YOUR_API_KEY_HERE"

# Configure the Gemini client
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")


def generate_case_investigation_steps(query: str, contexts: List[Dict[str, Any]], case_details: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Generates a case-specific sexual offence investigation checklist using an LLM.

    This function constructs a detailed prompt with legal contexts and case details,
    sends it to the Gemini model, and robustly parses the JSON response to return a
    structured checklist.

    Args:
        query (str): The primary user query for the investigation plan.
        contexts (List[Dict[str, Any]]): A list of document chunks for legal context.
                                         Each dictionary should have a 'text' key.
        case_details (Dict[str, Any], optional): A dictionary containing specific
                                                 details of the case. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of checklist items, where each item is a
                              dictionary with 'id', 'item', and 'status' keys.
                              Returns a list with a single error item on failure.
    """
    # 1. Build context from retrieved document chunks
    context_text = ""
    for i, ctx in enumerate(contexts):
        context_text += f"[CLAUSE_{i+1}] {ctx.get('text', 'N/A')}\n\n"

    # 2. Build case context if provided
    case_context = ""
    if case_details:
        case_context = f"""
CASE DETAILS:
- FIR Number: {case_details.get('FIRNo', 'N/A')}
- Location: {case_details.get('place', 'N/A')}
- Offense Type: {case_details.get('offence', 'N/A')}
- Action Time Frame: {case_details.get('action_time_frame', 'N/A')} hours
- Modus Operandi: {case_details.get('modusOperandi', 'N/A')}
- Weapon Involved: {case_details.get('weapon', 'N/A')}
- Investigating Officer ID: {case_details.get('officer_id', 'N/A')}
"""

    # 3. Construct the final, detailed prompt
    # The prompt is specifically engineered to request the exact JSON format needed.
    prompt = f"""
You are an expert criminal investigation officer specializing in sexual offense cases. Your task is to create a comprehensive, step-by-step investigation checklist.

{case_context}

AVAILABLE LEGAL DOCUMENTS AND RESOURCES:
{context_text}

INVESTIGATION QUERY: {query}

YOUR TASK: Create a detailed investigation action plan with 12-15 DISTINCT, SEQUENTIAL steps covering the complete investigation process from initial response to case completion.

INVESTIGATION PHASES TO COVER:
1. IMMEDIATE RESPONSE (First 2-4 hours)
2. SCENE MANAGEMENT & EVIDENCE COLLECTION (Day 1-2)
3. VICTIM & WITNESS INTERVIEWS (Day 1-3)
4. SUSPECT IDENTIFICATION & APPREHENSION (Day 2-7)
5. FORENSIC ANALYSIS & DOCUMENTATION (Week 1-2)
6. CASE BUILDING & LEGAL PROCEEDINGS (Week 2-4)

REQUIREMENTS:
- Each step must be a SPECIFIC, ACTIONABLE task.
- Steps must follow a logical chronological order and be completely distinct.
- Incorporate details from the case file where relevant.

CRITICAL: You must respond with ONLY a valid JSON array of objects. Do not include any explanatory text, markdown, or other characters before or after the JSON array. Each object in the array must contain three keys:
1. "id": A sequential integer starting from 1.
2. "item": A string containing the concise description of the investigation task.
3. "status": A boolean value, which must be set to `false`.

EXAMPLE OF THE REQUIRED EXACT JSON OUTPUT FORMAT:
[
  {{"id": 1, "item": "Secure crime scene perimeter and establish a single entry/exit control log within 30 minutes.", "status": false}},
  {{"id": 2, "item": "Coordinate with the medical unit to ensure the victim receives a forensic medical examination by a qualified professional.", "status": false}},
  {{"id": 3, "item": "Conduct the primary victim interview using trauma-informed techniques with a female officer or support person present.", "status": false}}
]

JSON Response:
"""

    try:
        # 4. Call the LLM and get the response
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # 5. Robustly extract the JSON array from the response text
        # This handles cases where the LLM might still wrap the JSON in ```json ... ```
        json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)

        if not json_match:
            # Error case: No JSON array found in the response
            error_message = f"Error: Failed to find a valid JSON array in the LLM response. Raw response: '{raw_text[:200]}...'"
            return [{"id": 1, "item": error_message, "status": False}]

        clean_json_str = json_match.group(0)

        # 6. Parse the cleaned JSON string
        try:
            parsed_response = json.loads(clean_json_str)
            # Basic validation to ensure the response is in the expected format
            if isinstance(parsed_response, list) and all(
                isinstance(item, dict) and 'id' in item and 'item' in item and 'status' in item
                for item in parsed_response
            ):
                return parsed_response
            else:
                error_message = "Error: Parsed JSON does not match the required format (list of dicts with 'id', 'item', 'status')."
                return [{"id": 1, "item": error_message, "status": False}]

        except json.JSONDecodeError:
            # Error case: The extracted string is not valid JSON
            error_message = f"Error: Failed to parse JSON from the LLM response. Extracted text: '{clean_json_str[:200]}...'"
            return [{"id": 1, "item": error_message, "status": False}]

    except Exception as e:
        # Error case: General failure (e.g., API call failed)
        return [{"id": 1, "item": f"An unexpected error occurred: {str(e)}", "status": False}]


# --- Example Usage ---
if __name__ == "__main__":
    # 1. Define sample inputs for the function
    sample_query = "Generate a full investigation plan for the sexual assault case reported."

    sample_contexts = [
        {"text": "Section 164A of the CrPC mandates that the victim of a sexual offense shall be sent for medical examination by a registered medical practitioner within twenty-four hours from the time of receiving the information relating to the commission of such offense."},
        {"text": "The Indian Evidence Act, Section 53A, allows for the evidence of the character of the victim or of such person's previous sexual experience with any person to be considered not relevant in such prosecutions."}
    ]

    sample_case_details = {
        'FIRNo': 'CR-123-2025',
        'place': 'Greenwood Park, City Center',
        'offence': 'Sexual Assault (Section 376 IPC)',
        'action_time_frame': '24',
        'modusOperandi': 'Attacker approached victim from behind in a poorly lit area.',
        'weapon': 'None reported',
        'officer_id': 'INSP-GUPTA-45'
    }

    # 2. Call the function to generate the investigation steps
    print("Generating investigation checklist...")
    investigation_checklist = generate_case_investigation_steps(
        query=sample_query,
        contexts=sample_contexts,
        case_details=sample_case_details
    )

    # 3. Print the result in a readable format
    print("\n--- Generated Investigation Checklist ---\n")
    # Using json.dumps for pretty printing the output list of dictionaries
    print(json.dumps(investigation_checklist, indent=2))
    print("\n---------------------------------------\n")