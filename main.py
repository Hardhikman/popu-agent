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
from google.adk.tools import google_search
from google.genai import types

# --- CORE LOGIC ---

async def run_policy_analysis(topic, google_key, tavily_key):
    # 1. Auth check
    active_google_key = google_key if google_key else config.GOOGLE_API_KEY
    active_tavily_key = tavily_key if tavily_key else config.TAVILY_API_KEY
    
    if not active_google_key or not active_tavily_key:
        err = "Error: Missing API Keys. Please provide both Google API Key and Tavily API Key."
        print(f"❌ Authentication Error: {err}")
        yield err, err, err, err
        return

    yield f"Starting analysis for: {topic}...\nCheck terminal for live logs.", "", "", "" 

    # 2. Setup
    try:
        os.environ["GOOGLE_API_KEY"] = active_google_key
        
        # Define retry configuration
        retry_config = types.HttpRetryOptions(
            attempts=5,  # Maximum retry attempts
            exp_base=7,  # Delay multiplier
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
        )
        
        model = Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config)
        tavily_search_tool = tools.get_tavily_search_tool(api_key=active_tavily_key)
        
        # Use Google Search tool directly as shown in the example
        google_search_tool = google_search
        
        # Tools for different agents - following project memory guidelines
        analyst_critic_tools: List[Any] = [tavily_search_tool]  # Analyst and Critic use Tavily
        lobbyist_summary_tools: List[Any] = [google_search_tool]  # Lobbyist and Summary use Google Search
    except Exception as e:
        err = f"Setup Error: {str(e)}"
        print(f"❌ Setup Error: {err}")
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
        
        Analyze the topic and structure your response strictly under:
        1.Rural Society 2.Urban Society 3.Working Class 4.Backward class
        5.Farmers 6.Manufacturing 7.Services 8.Women 9.Youth 10.Tribals.
        
        For each section, cite 1 specific data point found with persusasive argument via the tool.
        """,
        tools=analyst_critic_tools
    )

    critic_agent = LlmAgent(
        name="Critic",
        model=model,
        instruction="""
        You are a Critical Policy Reviewer. 
        MANDATE: Be direct and ruthless. No polite padding.
        CRITICAL RULE: Use the 'fetch_policy_data' tool to find counter-evidence.
        
        Critique the analysis focusing by highlighting:
        - Economic feasibility (cite costs).
        - Failed examples from other countries.
        - Direct negative impact on specific groups in single paragraph.
        """,
        tools=analyst_critic_tools
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
        tools=lobbyist_summary_tools
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
        5. **Final Recommendation**: Pass, Reject, or Amend with why(in single sentence)?
        """,
        tools=lobbyist_summary_tools
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
        
        # Run without custom retry wrapper
        async for event in runner_analyst.run_async(user_id="user", session_id="sess_analyst", new_message=msg):
            # DEBUG: Print if the agent decides to call a tool
            if hasattr(event, 'function_call') and event.function_call:
                print(f"   🛠️  [Analyst] Calling Tool: {event.function_call.name}")
            
            if event.is_final_response() and event.content and event.content.parts:
                # Process all parts of the response, handling different part types explicitly
                text_parts = []
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                    # Explicitly handle other part types to avoid warnings
                    elif hasattr(part, 'function_call'):
                        # Function calls are handled separately by the framework
                        pass
                    elif hasattr(part, 'thought_signature'):
                        # Thought signatures are metadata, not content
                        pass
                analysis_text = '\n'.join(text_parts) if text_parts else ""
        
        print(f"✅ [Analyst] Execution Complete")
        if not analysis_text.strip():
            print("⚠️  [Analyst] Warning: No analysis content generated")
    except Exception as e:
        error_msg = f"Analyst Failed: {str(e)}"
        print(f"❌ {error_msg}")
        yield error_msg, "", "", ""
        return

    status_log = ">>> Analyst finished. Starting Critic...\n"
    yield analysis_text, status_log, "", "" 

    # --- CRITIC ---
    critique_text = ""
    try:
        await session_service.create_session(app_name=app_name, user_id="user", session_id="sess_critic")
        runner_critic = Runner(agent=critic_agent, app_name=app_name, session_service=session_service)
        msg = types.Content(role="user", parts=[types.Part(text=f"Critique this analysis ruthlessly: \n{analysis_text}")])

        # Run without custom retry wrapper
        async for event in runner_critic.run_async(user_id="user", session_id="sess_critic", new_message=msg):
            # DEBUG: Print if the agent decides to call a tool
            if hasattr(event, 'function_call') and event.function_call:
                print(f"   🛠️  [Critic] Calling Tool: {event.function_call.name}")
            
            if event.is_final_response() and event.content and event.content.parts:
                # Process all parts of the response, handling different part types explicitly
                text_parts = []
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                    # Explicitly handle other part types to avoid warnings
                    elif hasattr(part, 'function_call'):
                        # Function calls are handled separately by the framework
                        pass
                    elif hasattr(part, 'thought_signature'):
                        # Thought signatures are metadata, not content
                        pass
                critique_text = '\n'.join(text_parts) if text_parts else ""
        
        print(f"✅ [Critic] Execution Complete")
        if not critique_text.strip():
            print("⚠️  [Critic] Warning: No critique content generated")
    except Exception as e:
        error_msg = f"Critic Failed: {str(e)}"
        print(f"❌ {error_msg}")
        yield analysis_text, error_msg, "", ""
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
        
        # Run without custom retry wrapper
        async for event in runner_lobbyist.run_async(user_id="user", session_id="sess_lobbyist", new_message=msg):
            # DEBUG: Print if the agent decides to call a tool
            if hasattr(event, 'function_call') and event.function_call:
                print(f"   🛠️  [Lobbyist] Calling Tool: {event.function_call.name}")
            
            if event.is_final_response() and event.content and event.content.parts:
                # Process all parts of the response, handling different part types explicitly
                text_parts = []
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                    # Explicitly handle other part types to avoid warnings
                    elif hasattr(part, 'function_call'):
                        # Function calls are handled separately by the framework
                        pass
                    elif hasattr(part, 'thought_signature'):
                        # Thought signatures are metadata, not content
                        pass
                lobbyist_text = '\n'.join(text_parts) if text_parts else ""
        
        print(f"✅ [Lobbyist] Execution Complete")
        if not lobbyist_text.strip():
            print("⚠️  [Lobbyist] Warning: No lobbyist content generated")
    except Exception as e:
        error_msg = f"Lobbyist Failed: {str(e)}"
        print(f"❌ {error_msg}")
        yield analysis_text, critique_text, error_msg, ""
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
        
        # Run without custom retry wrapper
        async for event in runner_summary.run_async(user_id="user", session_id="sess_summary", new_message=msg):
            # DEBUG: Print if the agent decides to call a tool
            if hasattr(event, 'function_call') and event.function_call:
                print(f"   🛠️  [Synthesizer] Calling Tool: {event.function_call.name}")
            
            if event.is_final_response() and event.content and event.content.parts:
                # Process all parts of the response, handling different part types explicitly
                text_parts = []
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                    # Explicitly handle other part types to avoid warnings
                    elif hasattr(part, 'function_call'):
                        # Function calls are handled separately by the framework
                        pass
                    elif hasattr(part, 'thought_signature'):
                        # Thought signatures are metadata, not content
                        pass
                summary_text = '\n'.join(text_parts) if text_parts else ""
        
        print(f"✅ [Synthesizer] Execution Complete")
        if not summary_text.strip():
            print("⚠️  [Synthesizer] Warning: No summary content generated")
    except Exception as e:
        error_msg = f"Summary Failed: {str(e)}"
        print(f"❌ {error_msg}")
        yield analysis_text, critique_text, lobbyist_text, error_msg
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
    gr.Markdown("Powered by **Google ADK**, **Gemini 2.5 Flash**, **Tavily** and **Google Search**")
    
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