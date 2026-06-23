from mcp.server.fastmcp import FastMCP
import datetime

# Create a FastMCP instance named "Seasonal Server"
mcp = FastMCP("Seasonal Server")

@mcp.tool()
def get_current_ritu() -> str:
    """
    Get the current Ayurvedic season (Ritu) based on the system month and its effect on the doshas.
    
    Returns:
        str: Description of the current season and general guidance.
    """
    month = datetime.datetime.now().month
    
    # Map months to Ayurvedic Ritus
    if month in [1, 2]:
        ritu = "Shishir"
        english_name = "Winter"
        effect = "Kapha is accumulating, Vata is high. Advise warm, nourishing, easily digestible foods and herbs."
    elif month in [3, 4]:
        ritu = "Vasant"
        english_name = "Spring"
        effect = "Kapha is liquefying/aggravated. Advise warm, light, dry, and spicy foods to reduce Kapha."
    elif month in [5, 6]:
        ritu = "Grishma"
        english_name = "Summer"
        effect = "It is currently Grishma (Summer). Pitta is accumulating, Vata is increasing. Advise cooling foods."
    elif month in [7, 8]:
        ritu = "Varsha"
        english_name = "Monsoon"
        effect = "Vata is aggravated, Pitta is accumulating. Advise warm, light, freshly cooked meals with healthy fats."
    elif month in [9, 10]:
        ritu = "Sharad"
        english_name = "Autumn"
        effect = "Pitta is aggravated. Advise sweet, bitter, astringent, and cooling foods to calm Pitta."
    else:  # month in [11, 12]
        ritu = "Hemant"
        english_name = "Pre-winter"
        effect = "Vata is pacified, digestive fire (Agni) is strong. Advise sweet, sour, salty, warm, and nourishing foods."
        
    return f"It is currently {ritu} ({english_name}). {effect}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
