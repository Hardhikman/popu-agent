import gradio as gr
import config
import tools
import os
import asyncio
import time
from typing import List, Any

# ADK Imports
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- CORE LOGIC ---

async def run_with_retry(runner, user_id, session_id, message, agent_name="Agent", max_retries=3):
    """
    Runs agent with 503 retry logic and DETAILED LOGGING.
    """
    print(f"\n▶️  [{agent_name}] Starting execution...")
    start_time = time.time()
    final_text = ""
    
    for attempt in range(max_retries):
        try:
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
                
                # DEBUG: Print if the agent decides to call a tool
                if hasattr(event, 'function_call') and event.function_call:
                    print(f"   🛠️  [{agent_name}] Calling Tool: {event.function_call.name}")
                
                if event.is_final_response() and event.content and event.content.parts:
                    # Process all parts of the response, not just the first one
                    text_parts = [part.text for part in event.content.parts if hasattr(part, 'text') and part.text]
                    final_text = '\n'.join(text_parts) if text_parts else ""
            
            # Execution successful
            duration = time.time() - start_time
            print(f"✅ [{agent_name}] Execution Complete ({duration:.2f}s)")
            return final_text
        
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt 
                    print(f"   ⚠️  [{agent_name}] API Overload (503). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
            print(f"   ❌ [{agent_name}] Crashed: {str(e)}")
            raise e
    return final_text

async def run_policy_analysis(topic, google_key, tavily_key):
    # 1. Auth check
    active_google_key = google_key if google_key else config.GOOGLE_API_KEY
    active_tavily_key = tavily_key if tavily_key else config.TAVILY_API_KEY
    
    if not active_google_key or not active_tavily_key:
        err = "Error: Missing API Keys."
        yield err, err, err, err
        return

    yield f"Starting analysis for: {topic}...\nCheck terminal for live logs.", "", "", "" 

    # 2. Setup
    try:
        os.environ["GOOGLE_API_KEY"] = active_google_key
        model = Gemini(model="gemini-2.5-flash")
        search_tool = tools.get_tavily_search_tool(api_key=active_tavily_key)
        tool_list: List[Any] = [search_tool]
    except Exception as e:
        err = f"Setup Error: {str(e)}"
        yield err, err, err, err
        return

    # 3. Define Agents
    
    analyst_agent = LlmAgent(
        name="Analyst",
        model=model,
        instruction="""
        You are a Senior Data-Driven Policy Analyst.
        MANDATE: Be extremely concise. Use bullet points.
        CRITICAL RULE: You MUST use the 'fetch_policy_data' tool to get real-world statistics.
        
        Structure your response strictly under:
        1. Rural Society 2. Urban Society 3. Working Class 
        4. Farmers 5. Manufacturing 6. Services 7. Women 8. Youth 9. Tribals.
        
        For each section, cite 1 specific data point found via the tool.
        """,
        tools=tool_list
    )

    critic_agent = LlmAgent(
        name="Critic",
        model=model,
        instruction="""
        You are a Critical Policy Reviewer. 
        MANDATE: Be direct and ruthless. No polite padding.
        CRITICAL RULE: Use the 'fetch_policy_data' tool to find counter-evidence.
        
        Critique the analysis focusing on:
        - Economic feasibility (cite costs).
        - Failed examples from other countries.
        - Direct negative impact on specific groups.
        """,
        tools=tool_list
    )

    lobbyist_agent = LlmAgent(
        name="Lobbyist",
        model=model,
        instruction="""
        You are a Future Policy Strategist & Lobbyist.
        
        Your Goal: Based on the Analysis and Critique, propose 3 concrete Future Policy Directives.
        For each directive, you must LOBBY for a specific section of society (e.g., "Lobbying for Farmers").
        
        Structure:
        1. **Directive Name**
        2. **Target Beneficiary** (e.g., Rural Women, Gig Workers)
        3. **The Pitch**: A persuasive argument using DATA from the tool to justify why this directive is urgent.
        
        MANDATE: Use the tool to find fresh data to support your lobbying pitch. Be persuasive but factual.
        """,
        tools=tool_list
    )

    summary_agent = LlmAgent(
        name="Synthesizer",
        model=model,
        instruction="""
        You are a Policy Synthesizer.
        
        MANDATE: Create a "TL;DR" Executive Summary based on the Analysis, Critique, and Lobbyist proposals.
        - Maximum 400 words.
        
        Format:
        1. **The Verdict**: One sentence summary.
        2. **Key Data Points** (Top 3 facts from the agents).
        3. **Major Risks** (from Critique).
        4. **Future Roadmap** (Top 2 directives from Lobbyist).
        5. **Final Recommendation**: Pass, Reject, or Amend.
        """,
        tools=tool_list 
    )

    # 4. Execution
    session_service = InMemorySessionService()
    app_name = "agents" 

    # --- ANALYST ---
    yield ">>> Analyst: Searching for data...\n", "", "", ""
    analysis_text = ""
    try:
        await session_service.create_session(app_name=app_name, user_id="user", session_id="sess_analyst")
        runner_analyst = Runner(agent=analyst_agent, app_name=app_name, session_service=session_service)
        msg = types.Content(role="user", parts=[types.Part(text=f"Analyze with data (be concise): '{topic}'")])
        
        # LOGGING: Added agent_name parameter
        analysis_text = await run_with_retry(runner_analyst, "user", "sess_analyst", msg, agent_name="Analyst")
    except Exception as e:
        yield f"Analyst Failed: {str(e)}", "", "", ""
        return

    status_log = ">>> Analyst finished. Starting Critic...\n"
    yield analysis_text, status_log, "", "" 

    # --- CRITIC ---
    critique_text = ""
    try:
        await session_service.create_session(app_name=app_name, user_id="user", session_id="sess_critic")
        runner_critic = Runner(agent=critic_agent, app_name=app_name, session_service=session_service)
        msg = types.Content(role="user", parts=[types.Part(text=f"Critique this analysis ruthlessly: \n{analysis_text}")])

        critique_text = await run_with_retry(runner_critic, "user", "sess_critic", msg, agent_name="Critic")
    except Exception as e:
        yield analysis_text, f"Critic Failed: {str(e)}", "", ""
        return

    status_log = ">>> Critic finished. Starting Lobbyist...\n"
    yield analysis_text, critique_text, status_log, ""

    # --- LOBBYIST ---
    lobbyist_text = ""
    try:
        await session_service.create_session(app_name=app_name, user_id="user", session_id="sess_lobbyist")
        runner_lobbyist = Runner(agent=lobbyist_agent, app_name=app_name, session_service=session_service)
        lobbyist_input = f"""
        Context Analysis: {analysis_text}
        Context Critique: {critique_text}
        
        Task: Propose 3 Future Directives and lobby for specific groups using new data.
        """
        msg = types.Content(role="user", parts=[types.Part(text=lobbyist_input)])
        
        lobbyist_text = await run_with_retry(runner_lobbyist, "user", "sess_lobbyist", msg, agent_name="Lobbyist")
    except Exception as e:
        yield analysis_text, critique_text, f"Lobbyist Failed: {str(e)}", ""
        return

    status_log = ">>> Lobbyist finished. Synthesizing Final Report...\n"
    yield analysis_text, critique_text, lobbyist_text, status_log

    # --- SUMMARY ---
    summary_text = ""
    try:
        await session_service.create_session(app_name=app_name, user_id="user", session_id="sess_summary")
        runner_summary = Runner(agent=summary_agent, app_name=app_name, session_service=session_service)
        
        combined_input = f"""
        Summarize these into a TL;DR Executive Report:
        
        [ANALYSIS]
        {analysis_text}
        
        [CRITIQUE]
        {critique_text}
        
        [LOBBYIST PROPOSALS]
        {lobbyist_text}
        """
        msg = types.Content(role="user", parts=[types.Part(text=combined_input)])
        
        summary_text = await run_with_retry(runner_summary, "user", "sess_summary", msg, agent_name="Synthesizer")

    except Exception as e:
        yield analysis_text, critique_text, lobbyist_text, f"Summary Failed: {str(e)}"
        return

    # Final Yield
    print(f"\n✅ [System] Workflow Completed Successfully.")
    yield analysis_text, critique_text, lobbyist_text, summary_text

def generate_markdown_report(topic, analysis, critique, lobbyist, summary):
    """
    Generate a markdown report from the analysis results
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md_content = f"""# Policy Analysis Report

**Topic**: {topic}
**Generated**: {timestamp}

---

## 📊 Analysis

{analysis}

---

## ⚖️ Critique

{critique}

---

## 📢 Future Directives (Lobbyist)

{lobbyist}

---

## 📝 Final Summary

{summary}

---
*Report generated by Popu Agent*
"""
    
    # Save to a temporary file
    import tempfile
    import os
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    temp_file.write(md_content)
    temp_file.close()
    
    return temp_file.name

# --- UI ---
with gr.Blocks(title="ADK Policy Analyzer") as demo:
    gr.Markdown("# 🏛️ Data-Driven Policy Analyzer")
    gr.Markdown("Powered by **Google ADK**, **Gemini 2.5 Flash**, and **Tavily**")
    
    # Store the latest results
    analysis_state = gr.State()
    critique_state = gr.State()
    lobbyist_state = gr.State()
    summary_state = gr.State()
    topic_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=1):
            topic_input = gr.Textbox(
                label="Enter Policy Topic", 
                value=config.DEFAULT_POLICY_TOPIC,
                lines=2
            )
            with gr.Accordion("API Settings", open=False):
                google_key_input = gr.Textbox(label="Google API Key", type="password")
                tavily_key_input = gr.Textbox(label="Tavily API Key", type="password")
            
            analyze_btn = gr.Button("🚀 Run 4-Agent Workflow", variant="primary")
            
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📊 Analysis"):
                    analysis_output = gr.Markdown()
                with gr.TabItem("⚖️ Critique"):
                    critique_output = gr.Markdown()
                with gr.TabItem("📢 Future Directives (Lobbyist)"):
                    lobbyist_output = gr.Markdown()
                with gr.TabItem("📝 Final Summary"):
                    summary_output = gr.Markdown()
    
    with gr.Row():
        download_btn = gr.DownloadButton("📥 Download Full Report as MD", variant="secondary", interactive=False)
        download_btn_visible = gr.State(value=False)

    # Update states when analysis is complete
    analyze_btn.click(
        fn=run_policy_analysis,
        inputs=[topic_input, google_key_input, tavily_key_input],
        outputs=[analysis_output, critique_output, lobbyist_output, summary_output]
    ).then(
        fn=lambda topic, analysis, critique, lobbyist, summary: (topic, analysis, critique, lobbyist, summary, gr.DownloadButton(interactive=True)),
        inputs=[topic_input, analysis_output, critique_output, lobbyist_output, summary_output],
        outputs=[topic_state, analysis_state, critique_state, lobbyist_state, summary_state, download_btn]
    )

    # Generate and download the markdown report
    download_btn.click(
        fn=generate_markdown_report,
        inputs=[topic_state, analysis_state, critique_state, lobbyist_state, summary_state],
        outputs=[download_btn]
    )

if __name__ == "__main__":
    demo.launch(share=True)
