from mcp.server.fastmcp import FastMCP
import os
import json

mcp = FastMCP("AyurvedaKnowledgeServer")

def load_kb():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(current_dir, "..", "data", "ayurveda_knowledge.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool
def get_dosha_info(dosha: str) -> str:
    """Retrieve characteristics, imbalance symptoms, and general lifestyle/diet guidance for a specific dosha (Vata, Pitta, Kapha)."""
    kb = load_kb()
    d = dosha.strip().capitalize()
    if d in kb["doshas"]:
        return json.dumps(kb["doshas"][d], indent=2)
    return f"Dosha '{dosha}' not found. Available doshas: Vata, Pitta, Kapha."

@mcp.tool
def get_herb_recommendations(dosha: str, symptom: str) -> str:
    """Get recommendations of traditional Ayurvedic herbs/foods that balance the given dosha and match the general symptom description."""
    kb = load_kb()
    d = dosha.strip().capitalize()
    s_lower = symptom.strip().lower()
    matching_herbs = []
    
    for herb in kb["herbs"]:
        if d in herb["balances"]:
            if s_lower:
                if s_lower in herb["use_note"].lower() or s_lower in herb["name"].lower():
                    matching_herbs.append(herb)
            else:
                matching_herbs.append(herb)
                
    if not matching_herbs:
        # Fallback to returning all herbs balancing the given dosha
        matching_herbs = [h for h in kb["herbs"] if d in h["balances"]]
        
    return json.dumps(matching_herbs, indent=2)

@mcp.tool
def check_red_flag(symptom: str) -> bool:
    """Check if a symptom matches any 'red flag' conditions requiring medical escalation. Returns True if a match is found."""
    kb = load_kb()
    s_lower = symptom.strip().lower()
    for flag in kb["red_flags"]:
        if flag in s_lower or s_lower in flag:
            return True
    return False

if __name__ == "__main__":
    mcp.run()
