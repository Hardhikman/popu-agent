from google.adk.agents import LlmAgent

def get_critic_agent(model, tools):
    return LlmAgent(
        name="Critic",
        model=model,
        tools=tools,
        instruction="You are a Policy Critic. Provide a critical perspective on the topic. Find flaws, costs, and missing demographics and cite 2 failed examples seperately."
    )
