import os
import sys
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

current_dir = os.path.dirname(os.path.abspath(__file__))
server_script = os.path.join(current_dir, "..", "mcp_server", "ayurveda_server.py")
season_script = os.path.join(current_dir, "..", "mcp_server", "season_server.py")

# Configure connection to the local MCP server via stdio
mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[server_script]
        )
    )
)

# Configure connection to the local Seasonal MCP server via stdio
season_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[season_script]
        )
    )
)

knowledge_agent = LlmAgent(
    name="knowledge_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are an Ayurvedic Knowledge Retrieval Agent.
    Your job is to use your tools to fetch official, structured facts about the user's dosha and symptoms.
    
    You MUST consider the current Ayurvedic season. Request the current season using your tools. Do not recommend heating therapies if it is Grishma (Summer), and do not recommend excessively cold items if it is Shishir (Winter).
    
    You have access to MCP servers providing the following tools:
    - check_red_flag(symptom): Call this first on any user symptom to determine if it is a dangerous 'red flag' requiring emergency/doctor attention.
    - get_dosha_info(dosha): Retrieve characteristic descriptions and diet/lifestyle guidelines.
    - get_herb_recommendations(dosha, symptom): Retrieve traditional herbs balancing the dosha that match their symptoms.
    - get_current_ritu(): Get the current Ayurvedic season and its impact on the doshas.
    
    CRITICAL WORKFLOW:
    1. First, check if the user's symptom(s) match any red flags using `check_red_flag`.
       - If it returns True, stop immediately. Output a warning that a red flag condition has been detected and they must seek immediate professional medical care. Do not proceed to query herbs or doshas.
    2. If it is NOT a red flag, query the current season using `get_current_ritu`.
    3. Query the dosha guidelines for the dominant dosha(s) using `get_dosha_info`.
    4. Query herb recommendations for the dominant dosha and symptom using `get_herb_recommendations`.
    5. Compile all retrieved info (including seasonal details and safety checks) into a structured, objective report. Do not add personalized recommendations yet (that is the recommendation agent's job). Just provide the raw retrieved facts clearly.
    """,
    tools=[mcp_toolset, season_toolset]
)
