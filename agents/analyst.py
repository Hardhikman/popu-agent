from google.adk.agents import LlmAgent

def get_analyst_agent(model, tools):
    return LlmAgent(
        name="Analyst",
        model=model,
        tools=tools,
        instruction="Analyze impact on: Rural, Urban, Working Class, Farmers, Women, Youth, Mfg/Services. "
            "Cite 1 data point per sector."
    )
