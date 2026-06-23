import os
import asyncio
from dotenv import load_dotenv

# Load env variables (GOOGLE_API_KEY)
load_dotenv()

async def main():
    # Verify API key
    if not os.environ.get("GOOGLE_API_KEY"):
        print("[Warning] GOOGLE_API_KEY environment variable is not set. The Gemini model calls may fail.")
        print("Please set your GOOGLE_API_KEY in a .env file in the root directory.")
        
    print("=" * 60)
    print("Welcome to Ayurcare Agent - Ayurveda Health Guidance System")
    print("This runner will launch the sequential multi-agent workflow.")
    print("Agents: Intake -> Prakriti -> Knowledge (MCP server) -> Recommendation -> Safety")
    print("=" * 60)
    print("Initializing ADK Workflow...")
    
    # Import locally to keep startup clear
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    from agents.orchestrator import root_agent
    
    runner = InMemoryRunner(agent=root_agent)
    session_id = "local_interactive_test"
    user_id = "test_user"
    
    print("\nSystem: Intake Agent is ready. Type 'exit' to end.")
    print("Ayurcare Agent: Hello! I'm here to help guide you on your wellness journey. What main symptom(s) are you experiencing today?")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            # Construct message
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)]
            )
            
            response_text = ""
            print("System: Thinking...", end="\r")
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            
            # Print agent response
            print(f"\nAyurcare Agent:\n{response_text.strip()}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nSystem Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
