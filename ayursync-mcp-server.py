from mcp.server.fastmcp import FastMCP
import os
import json

# Initialize FastMCP Server
# FastMCP automatically configures the server to support stdio transport,
# which is the default when mcp.run() is called.
mcp = FastMCP("AyurSyncServer")

def load_db():
    # Load knowledge base from ayurveda_db.json in the same directory (project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "ayurveda_db.json")
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def get_dosha_routine(dosha_type: str) -> str:
    """
    Retrieve specific daily routines (Dinacharya) for a given dosha type.
    
    Args:
        dosha_type (str): The type of dosha ('vata', 'pitta', or 'kapha').
    
    Returns:
        str: JSON-formatted list of daily routines for the requested dosha.
    """
    try:
        db = load_db()
        d_type = dosha_type.strip().capitalize()
        
        if d_type in db["doshas"]:
            routines = db["doshas"][d_type]["balancing_routines"]
            return json.dumps(routines, indent=2)
        else:
            return json.dumps({
                "error": f"Dosha type '{dosha_type}' not found. Please specify 'vata', 'pitta', or 'kapha'."
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve routines: {str(e)}"})

# KAGGLER MCP SERVER REQUIREMENT COMPLIANCE:
# 1. Runs over stdio: The mcp.run() call executes the FastMCP server, which defaults to standard input/output
#    (stdio) communication using JSON-RPC 2.0. This allows any standard MCP host (like the Google ADK runner,
#    Claude Desktop, or a Python subprocess parent) to spawn the server process and query tools without
#    network configuration (e.g. HTTP/WebSockets).
# 2. Schema Discovery: Tools registered via @mcp.tool() expose standard JSON Schema definitions for parameters
#    and outputs, enabling client agents to dynamically discover and correctly call the tool.
if __name__ == "__main__":
    mcp.run()
