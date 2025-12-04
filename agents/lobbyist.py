from google.adk.agents import LlmAgent

def get_lobbyist_agent(model, tools):
    return LlmAgent(
        name="Lobbyist",
        model=model,
        tools=tools,
        instruction="You are a Strategist. Propose 3 directives based on the analysis and critique. Format each directive strictly as: 1. Directive, 2. Rationale, 3. Actionable Steps. DO NOT include 'Search Queries' or any internal thought process in the final output."
    )
