from strands import Agent
from strands_tools import calculator, python_repl, http_request

# Create an agent with community tools (uses Bedrock Claude 4 Sonnet by default)
agent = Agent(
    tools=[calculator, python_repl, http_request],
    system_prompt="You are an expert in the international space station and geography."
)

# Test the agent
response = agent("Which city is the closest to the international space station right now?")
print(response)
