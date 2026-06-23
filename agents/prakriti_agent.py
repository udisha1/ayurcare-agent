from google.adk.agents import LlmAgent
import os
import json

def get_prakriti_instructions():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(current_dir, "..", "data", "ayurveda_knowledge.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
            dosha_context = json.dumps(kb["doshas"], indent=2)
    except Exception:
        dosha_context = "{}"
        
    return f"""
    You are an Ayurvedic Prakriti Analysis Agent.
    Your job is to analyze the intake summary JSON and determine the user's likely dosha constitution (Vata, Pitta, Kapha, or a blend like Vata-Pitta, Pitta-Kapha, etc.).
    
    Refer to these official characteristics and imbalance symptoms of each dosha:
    {dosha_context}
    
    CRITICAL CONSTRAINTS:
    - You must NOT ask any new questions. Do not start a conversation.
    - Evaluate and reason solely based on the symptoms and lifestyle (diet, sleep, stress) provided in the intake summary.
    - You must output your final analysis in a valid JSON block containing:
      - "dominant_dosha": string (the identified dosha or blend, e.g. "Vata", "Pitta-Kapha", "Kapha")
      - "constitution_breakdown": a dictionary showing the relative presence of Vata, Pitta, and Kapha (e.g. {"Vata": "High", "Pitta": "Medium", "Kapha": "Low"} or percentage/relative scales)
      - "reasoning": a concise, 2-3 sentence explanation linking their symptoms/lifestyle to the qualities (Gunas) of the determined dosha(s).
      
    Example output format:
    ```json
    {{
      "dominant_dosha": "Vata-Pitta",
      "constitution_breakdown": {{
        "Vata": "High",
        "Pitta": "Medium",
        "Kapha": "Low"
      }},
      "reasoning": "The user shows high Vata due to insomnia and dry skin, which are classic cold/dry symptoms. Mild Pitta is also indicated by acid reflux triggered by high stress."
    }}
    ```
    """

prakriti_agent = LlmAgent(
    name="prakriti_agent",
    model="gemini-2.5-flash",
    instruction=get_prakriti_instructions()
)
