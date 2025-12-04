from google.adk.agents import LlmAgent

def get_synthesizer_agent(model):
    return LlmAgent(
        name="Synthesizer",
        model=model,
        tools=[],
        instruction="Create a 400-word Executive Summary. Verdict(Pass/Reject with why?), Data, Risks, Roadmap."
    )
