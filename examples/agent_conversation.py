from strands import Agent
from strands_tools import calculator

# Create a simple agent with calculator tool
agent = Agent(
    tools=[calculator],
    system_prompt="You are a helpful math assistant."
)

# Example 1: Simple calculation
print("Example 1: Simple calculation")
response = agent("What is 25 * 47?")
print(f"Response: {response}\n")

# Example 2: Conversation with context
print("Example 2: Conversation with context")
agent("My name is Alice")
response = agent("What's my name?")
print(f"Response: {response}\n")

# Example 3: Multi-step calculation
print("Example 3: Multi-step calculation")
response = agent("Calculate the area of a circle with radius 5, then multiply by 3")
print(f"Response: {response}")
