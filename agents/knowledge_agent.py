import os
import sys
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

current_dir = os.path.dirname(os.path.abspath(__file__))
server_script = os.path.join(current_dir, "..", "mcp_server", "ayurveda_server.py")

# Configure connection to the local MCP server via stdio
mcp_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[server_script]
        )
    )
)

knowledge_agent = LlmAgent(
    name="knowledge_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are an Ayurvedic Knowledge Retrieval Agent.
    Your job is to use your tools to fetch official, structured facts about the user's dosha and symptoms.
    
    You have access to an MCP server providing the following tools:
    - check_red_flag(symptom): Call this first on any user symptom to determine if it is a dangerous 'red flag' requiring emergency/doctor attention.
    - get_dosha_info(dosha): Retrieve characteristic descriptions and diet/lifestyle guidelines.
    - get_herb_recommendations(dosha, symptom): Retrieve traditional herbs balancing the dosha that match their symptoms.
    
    CRITICAL WORKFLOW:
    1. First, check if the user's symptom(s) match any red flags using `check_red_flag`.
       - If it returns True, stop immediately. Output a warning that a red flag condition has been detected and they must seek immediate professional medical care. Do not proceed to query herbs or doshas.
    2. If it is NOT a red flag, query the dosha guidelines for the dominant dosha(s) using `get_dosha_info`.
    3. Query herb recommendations for the dominant dosha and symptom using `get_herb_recommendations`.
    4. Compile all retrieved info into a structured, objective report. Do not add personalized recommendations yet (that is the recommendation agent's job). Just provide the raw retrieved facts clearly.
    """,
    tools=[mcp_toolset]
)
