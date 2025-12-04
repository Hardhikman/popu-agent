import gradio as gr
import config
import tools
import os
import logging
import uuid  # CRITICAL: For unique session IDs per run
import asyncio
from typing import List, Any, Dict, Tuple, Optional

# ADK Imports
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# Agent Imports
from agents.analyst import get_analyst_agent
from agents.critic import get_critic_agent
from agents.lobbyist import get_lobbyist_agent
from agents.synthesizer import get_synthesizer_agent

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global Session Service (Instantiated once to mimic a real DB connection)
# We will use unique IDs to keep runs separate.
session_service = InMemorySessionService()

# --- HELPER: Robust Agent Runner ---
async def run_agent_step(
    agent_name: str,
    agent: LlmAgent,
    prompt: str,
    run_id: str
) -> Tuple[str, str]:
    """
    Executes a single agent step within a specific run context.
    """
    logger.info(f"Starting Agent: {agent_name} [RunID: {run_id}]")
    
    # 1. Fix App Name Mismatch: ADK defaults to "agents" for dynamic agents
    APP_NAME = "agents"
    
    # 2. Unique Session ID: Prevents history from previous button clicks from leaking in
    session_id = f"sess_{agent_name.lower()}_{run_id}"
    
    # 3. Initialize Runner
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    
    # 4. Ensure Session Exists
    try:
        # We create a fresh session for this specific agent step to ensure clean context window
        await session_service.create_session(app_name=APP_NAME, user_id="user", session_id=session_id)
    except Exception:
        # If session exists (rare with UUID), we just continue
        pass
    
    msg = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_text = ""
    
    try:
        async for event in runner.run_async(user_id="user", session_id=session_id, new_message=msg):
            if hasattr(event, 'function_call') and event.function_call:
                logger.info(f"[{agent_name}] Tool Call: {event.function_call.name}")

            if event.is_final_response() and event.content and event.content.parts:
                text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                final_text = '\n'.join(text_parts)
                break 
                
    except Exception as e:
        error_msg = f"Execution Error in {agent_name}: {str(e)}"
        logger.error(error_msg)
        return "", error_msg

    if not final_text.strip():
        return "", f"⚠️ {agent_name} returned empty response."
        
    return final_text, f"✅ {agent_name} Completed."

# --- CORE LOGIC ---
async def run_policy_analysis(topic, google_key, tavily_key):
    # 1. Generate Run ID (Fixes Workflow Problem)
    run_id = str(uuid.uuid4())[:8]
    logger.info(f"--- Starting Analysis Run: {run_id} ---")

    # 2. Authentication
    active_google_key = google_key or getattr(config, 'GOOGLE_API_KEY', '')
    active_tavily_key = tavily_key or getattr(config, 'TAVILY_API_KEY', '')

    if not active_google_key or not active_tavily_key:
        err = "❌ Authentication Error: Missing API Keys."
        yield err, err, err, err
        return

    os.environ["GOOGLE_API_KEY"] = active_google_key
    
    # 3. Model & Tool Init
    try:
        # ADK Recommended: specific safety settings for robustness
        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH
            )
        ]

        model = Gemini(
            model="gemini-2.5-flash-lite", 
            safety_settings=safety_settings
        )
        
        tavily_tool = tools.get_tavily_search_tool(api_key=active_tavily_key)
        google_tool = google_search 
        
    except Exception as e:
        yield f"Setup Failed: {e}", "", "", ""
        return

    # 4. Pipeline Execution (Parallel Workflow)
    state = {"analysis": "", "critique": "", "lobbyist": "", "summary": ""}
    def get_ui(): return state["analysis"], state["critique"], state["lobbyist"], state["summary"]

    # --- ANALYST & CRITIC (PARALLEL) ---
    yield "🔎 Analyst & ⚖️ Critic: Researching & Reviewing...", "", "", ""
    
    analyst_agent = get_analyst_agent(model, [tavily_tool])
    critic_agent = get_critic_agent(model, [tavily_tool])

    # Run in parallel
    results = await asyncio.gather(
        run_agent_step("Analyst", analyst_agent, f"Analyze topic: {topic}", run_id),
        run_agent_step("Critic", critic_agent, f"Critique topic: {topic}", run_id)
    )
    
    (analyst_res, analyst_log), (critic_res, critic_log) = results

    if "Error" in analyst_log: state["analysis"] = analyst_log
    else: state["analysis"] = analyst_res

    if "Error" in critic_log: state["critique"] = critic_log
    else: state["critique"] = critic_res
    
    yield get_ui()
    if "Error" in analyst_log or "Error" in critic_log: return

    # --- LOBBYIST ---
    state["lobbyist"] = "🤝 Lobbyist: Strategizing..."
    yield get_ui()
    
    lobbyist_agent = get_lobbyist_agent(model, [google_tool])
    prompt = f"Analysis: {state['analysis']}\nCritique: {state['critique']}\nTask: Propose 3 directives."
    res, log = await run_agent_step("Lobbyist", lobbyist_agent, prompt, run_id)
    if "Error" in log: state["lobbyist"] = log; yield get_ui(); return
    state["lobbyist"] = res; yield get_ui()

    # --- SYNTHESIZER ---
    state["summary"] = "📝 Synthesizer: Writing Report..."
    yield get_ui()
    
    summary_agent = get_synthesizer_agent(model)
    prompt = f"Context:\n{state['analysis']}\n{state['critique']}\n{state['lobbyist']}\nSummarize."
    res, log = await run_agent_step("Synthesizer", summary_agent, prompt, run_id)
    state["summary"] = res; yield get_ui()


def generate_markdown_report(topic, analysis, critique, lobbyist, summary):
    import datetime, tempfile
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"# Policy Report: {topic}\n**Date**: {timestamp}\n\n## 📊 Analysis\n{analysis}\n\n## ⚖️ Critique\n{critique}\n\n## 📢 Directives\n{lobbyist}\n\n## 📝 Summary\n{summary}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
        tmp.write(md_content)
        return tmp.name

# --- UI ---
with gr.Blocks(title="ADK Policy Analyzer", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏛️ Data-Driven Policy Analyzer (ADK-Powered)")
    with gr.Row():
        with gr.Column(scale=1):
            topic_input = gr.Textbox(label="Topic", value="Universal Basic Income in India")
            with gr.Accordion("API Keys", open=False):
                google_key_input = gr.Textbox(label="Google API Key", type="password")
                tavily_key_input = gr.Textbox(label="Tavily API Key", type="password")
            analyze_btn = gr.Button("Run", variant="primary")
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📊 Analysis"): analysis_out = gr.Markdown()
                with gr.TabItem("⚖️ Critique"): critique_out = gr.Markdown()
                with gr.TabItem("📢 Lobbyist"): lobbyist_out = gr.Markdown()
                with gr.TabItem("📝 Summary"): summary_out = gr.Markdown()
    
    dl_btn = gr.DownloadButton("📥 Download Report", interactive=False)

    analyze_btn.click(
        fn=run_policy_analysis,
        inputs=[topic_input, google_key_input, tavily_key_input],
        outputs=[analysis_out, critique_out, lobbyist_out, summary_out]
    ).then(
        fn=generate_markdown_report,
        inputs=[topic_input, analysis_out, critique_out, lobbyist_out, summary_out],
        outputs=[dl_btn]
    ).then(lambda: gr.DownloadButton(interactive=True), outputs=[dl_btn])

if __name__ == "__main__":
    demo.launch()