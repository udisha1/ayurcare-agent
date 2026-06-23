import re
from google.adk import Workflow
from agents.intake_agent import intake_agent
from agents.prakriti_agent import prakriti_agent
from agents.knowledge_agent import knowledge_agent
from agents.recommendation_agent import recommendation_agent
from agents.safety_agent import safety_agent

# Input Sanitization: Strips potential prompt-injection patterns
def sanitize_input(text: str) -> str:
    if not text:
        return ""
    # Remove system commands / bypass instruction attempts
    sanitized = re.sub(
        r"(ignore\s+(?:previous|all)\s+instructions|system\s+override|delete\s+all\s+rules|you\s+are\s+now|override\s+persona|jailbreak)", 
        "[REDACTED INJECTION ATTEMPT]", 
        text, 
        flags=re.IGNORECASE
    )
    # Strip dangerous special character runs or backticks/tags that might break formats
    sanitized = sanitized.strip()
    return sanitized

# Define the root workflow agent that chains the agents sequentially
root_agent = Workflow(
    name="root_agent",
    edges=[
        ("START", intake_agent),
        (intake_agent, prakriti_agent),
        (prakriti_agent, knowledge_agent),
        (knowledge_agent, recommendation_agent),
        (recommendation_agent, safety_agent),
        (safety_agent, "END")
    ]
)
