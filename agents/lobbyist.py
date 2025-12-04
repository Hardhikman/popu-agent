from google.adk.agents import LlmAgent

def get_lobbyist_agent(model, tools):
    return LlmAgent(
        name="Lobbyist",
        model=model,
        tools=tools,
        instruction="You are a Strategist. Propose 3 directives based on the analysis and critique. Use Google Search for news."
    )
