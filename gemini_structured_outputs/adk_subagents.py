# adk_subagents.py
import os
import asyncio
from typing import Optional

# ADK core
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService

# Gemini SDK types for Content/Part and configs
from google import genai
from google.genai import types  # Content/Part for messages

# Optional multi-model support (OpenAI via LiteLLM); fallback to Gemini if not present
try:
    from google.adk.models.lite_llm import LiteLlm  # pip install litellm
    HAS_LITELLM = True
except Exception:
    LiteLlm = None  # type: ignore
    HAS_LITELLM = False

# ---------- Models ----------
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"
MODEL_GEMINI_2_5_FLASH = os.getenv("GEMINI_RAG_MODEL", "gemini-2.5-flash")  # for RAG agent reasoning + answers
MODEL_OPENAI_DEFAULT = "gpt-5-mini"

def pick_model():
    if HAS_LITELLM:
        print(f"🔁 Using OpenAI via LiteLlm with model '{MODEL_OPENAI_DEFAULT}'.")
        return LiteLlm(model=MODEL_OPENAI_DEFAULT)
    else:
        print(f"🔁 Using Gemini model '{MODEL_GEMINI_2_0_FLASH}'.")
        return MODEL_GEMINI_2_0_FLASH

# ---------- Tools ----------
def get_weather(city: str) -> dict:
    """Mock weather tool."""
    print(f"--- Tool: get_weather called for city: {city} ---")
    city_key = city.lower().replace(" ", "")
    mock = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }
    return mock.get(city_key, {"status": "error", "error_message": f"Sorry, no weather info for '{city}'."})

def say_hello(name: Optional[str] = None) -> str:
    if name:
        print(f"--- Tool: say_hello called with name: {name} ---")
        return f"Hello, {name}!"
    print(f"--- Tool: say_hello called without a specific name (name_arg_value: {name}) ---")
    return "Hello there!"

def say_goodbye() -> str:
    print(f"--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."

print("Greeting and Farewell tools defined.")

# ---------- Gemini RAG tool (Gemini SDK File Search) ----------
# Requires: export GOOGLE_API_KEY=...  (or GEMINI_API_KEY)
# Also set:  export GEMINI_FILE_SEARCH_STORE="fileSearchStores/your-store-id"
GEMINI_FILE_SEARCH_STORE = os.getenv("GEMINI_FILE_SEARCH_STORE")

def gemini_rag_answer(query: str, file_search_store: Optional[str] = None) -> str:
    """
    Uses Gemini API File Search (managed RAG) to answer questions grounded in your File Search store.
    Args:
        query: user question
        file_search_store: optional override; if not provided, uses GEMINI_FILE_SEARCH_STORE env var
    Returns:
        str: grounded answer text, or an error banner if misconfigured
    """
    store = (file_search_store or GEMINI_FILE_SEARCH_STORE or "").strip()
    if not store:
        return ("[RAG not configured] Set GEMINI_FILE_SEARCH_STORE env var to your File Search store name "
                "(e.g., 'fileSearchStores/my-file-store').")

    client = genai.Client()  # picks up GOOGLE_API_KEY / GEMINI_API_KEY automatically
    try:
        # Use dict configs (SDK accepts dicts OR typed models)
        resp = client.models.generate_content(
            model=MODEL_GEMINI_2_5_FLASH,
            contents=query,
            config={
                "tools": [
                    {"fileSearch": {"fileSearchStoreNames": [store]}}
                ]
            },
        )
        return resp.text or "(empty response)"
    except Exception as e:
        return f"[RAG error] {e!s}"

print("Gemini RAG tool defined.")

# ---------- Sub-agents ----------
MODEL_FOR_AGENTS = pick_model()

diagram_agent = Agent(
    model=MODEL_FOR_AGENTS,
    name="diagram_agent",
    instruction=("You are the Diagram Agent. ONLY provide Mermaid diagrams when a diagram is requested. "
                 "Output valid Mermaid code blocks with no prose."),
    description="Handles diagram requests.",
    tools=[say_hello],  # keeping original example tool; agent still outputs Mermaid per instruction
)
print(f"✅ Agent '{diagram_agent.name}' created.")

farewell_agent = Agent(
    model=MODEL_FOR_AGENTS,
    name="farewell_agent",
    instruction=("You are the Farewell Agent. ONLY provide a polite goodbye using the 'say_goodbye' tool "
                 "when the user ends the conversation. Do not do anything else."),
    description="Handles simple farewells via 'say_goodbye'.",
    tools=[say_goodbye],
)
print(f"✅ Agent '{farewell_agent.name}' created.")

# New: Gemini RAG agent (uses Gemini for reasoning + tool for File Search answers)
gemini_rag_agent = Agent(
    model=MODEL_GEMINI_2_5_FLASH,  # ensure Gemini is used for this agent even if LiteLLM is enabled elsewhere
    name="gemini_rag_agent",
    instruction=(
        "You are the Gemini RAG Agent. Use the 'gemini_rag_answer' tool to answer knowledge questions grounded in the "
        "configured File Search store. Never fabricate; if the store isn't configured or retrieval fails, state that."
    ),
    description="Answers knowledge/KB/doc questions using Gemini API File Search (managed RAG).",
    tools=[gemini_rag_answer],
)
print(f"✅ Agent '{gemini_rag_agent.name}' created.")

# ---------- Root agent ----------
root_agent = Agent(
    name="orchestrator_agent",
    model=MODEL_FOR_AGENTS,
    description="Main coordinator: handles weather; delegates diagrams/farewells/RAG.",
    instruction=(
        "You are the main Orchestrator Agent coordinating a team. Route requests to the correct sub-agent.\n"
        "- Use the 'get_weather' tool ONLY for specific weather requests.\n"
        "- Sub-agents:\n"
        "  1) 'diagram_agent': Outputs Mermaid diagrams.\n"
        "  2) 'farewell_agent': Handles simple farewells like 'Bye', 'See you'.\n"
        "  3) 'gemini_rag_agent': For questions that require knowledge from a document store, KB, PDF, or 'our docs'.\n"
        "If the user asks for grounded answers from documents/KB/policies/specs—or mentions 'docs', 'kb', 'handbook', "
        "'pdf', or 'file'—delegate to 'gemini_rag_agent'. Otherwise respond yourself or say you cannot handle it."
    ),
    tools=[get_weather],
    sub_agents=[diagram_agent, farewell_agent, gemini_rag_agent],
)

# ---------- Test run using ADK sessions + runner ----------
async def main():
    print("\n--- Testing orchestrator with a diagram request ---")
    app_name = "root_app"
    user_id = "local_user"
    session_id = "test_session_1"

    runner = InMemoryRunner(app_name=app_name, agent=root_agent)
    session_service: InMemorySessionService = runner.session_service  # type: ignore
    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    # 1) Diagram test
    user_content = types.Content(role="user", parts=[types.Part(text="draw a mermaid diagram of Agent to Agent communication using websockets")])
    final_text: Optional[str] = None
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text
    print(f"Root Agent Response (diagram): {final_text}")

    # 2) RAG test (will return a config warning unless GEMINI_FILE_SEARCH_STORE is set and populated)
    print("\n--- Testing orchestrator with a RAG question ---")
    rag_query = "Summarize the onboarding policy in our KB and cite key steps."
    user_content = types.Content(role="user", parts=[types.Part(text=rag_query)])
    final_text = None
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text
    print(f"Root Agent Response (RAG): {final_text}")

if __name__ == "__main__":
    asyncio.run(main())
