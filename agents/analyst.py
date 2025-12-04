from google.adk.agents import LlmAgent

def get_analyst_agent(model, tools):
    return LlmAgent(
        name="Analyst",
        model=model,
        tools=tools,
        instruction="Conduct a comprehensive 360-degree analysis covering: 1. PESTLE Factors (Political, Economic, Social, Technological, Legal, Environmental), 2. Demographic Impact (Rural/Urban, Women, Youth, Farmers), and 3. Economic Indicators (Fiscal, GDP, Jobs). Cite at least 1 specific data point for each major category. Optimize for search efficiency: derive maximum insight from available sources."
    )
