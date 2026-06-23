from google.adk.agents import LlmAgent
import os
import json

def get_safety_instructions():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(current_dir, "..", "data", "ayurveda_knowledge.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
            red_flags = kb["red_flags"]
    except Exception:
        red_flags = []
        
    return f"""
    You are the final Safety Gatekeeping Agent.
    Your role is to perform a rigorous safety review on the entire output of the pipeline before it is returned to the user.
    
    Here is the list of medical red-flag symptoms:
    {json.dumps(red_flags, indent=2)}
    
    CRITICAL WORKFLOW:
    1. Red Flag Override:
       Check if the user's original symptoms match or imply any of the red-flag entries.
       - If any red flags are found (e.g. chest pain, breathing difficulty, sudden numbness, high fever, etc.), you MUST override all previous suggestions and output a clear, prominent warning advising the user to seek immediate professional medical attention or emergency care. Use the prefix "SAFETY WARNING:" on its own line followed by the warning.
       
    2. Quality Assurance review:
       If no red flags are found, review the recommendation_agent's response. Ensure that:
       - There are NO specific dosage numbers (e.g., '500mg', '2 tablets', 'twice daily').
       - There are NO claims to cure, diagnose, or treat any disease.
       - The mandatory wellness disclaimer is present: "Disclaimer: This is traditional Ayurvedic wellness guidance, not a medical diagnosis or treatment plan."
       - If any violations are found (e.g., a specific dosage is mentioned, or a cure claim is made), rewrite the recommendations to remove the violation while preserving the general diet/lifestyle/herb suggestions in a compliant tone. Add the disclaimer if it was missing.
       - If everything is already correct and safe, output the recommendation exactly as-is.
    """

safety_agent = LlmAgent(
    name="safety_agent",
    model="gemini-2.5-flash",
    instruction=get_safety_instructions()
)
