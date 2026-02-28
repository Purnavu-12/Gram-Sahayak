from strands import Agent, tool

# Define a custom tool
@tool
def get_weather(location: str) -> str:
    """Get weather for a location.
    
    Args:
        location: City name
    """
    # In a real app, this would call a weather API
    return f"Weather in {location}: Sunny, 72°F"

@tool
def convert_temperature(temp: float, from_unit: str, to_unit: str) -> str:
    """Convert temperature between Celsius and Fahrenheit.
    
    Args:
        temp: Temperature value
        from_unit: Source unit (C or F)
        to_unit: Target unit (C or F)
    """
    if from_unit == "C" and to_unit == "F":
        result = (temp * 9/5) + 32
        return f"{temp}°C = {result}°F"
    elif from_unit == "F" and to_unit == "C":
        result = (temp - 32) * 5/9
        return f"{temp}°F = {result}°C"
    else:
        return "Invalid conversion"

# Create agent with custom tools
agent = Agent(
    tools=[get_weather, convert_temperature],
    system_prompt="You are a helpful weather assistant."
)

# Test the agent
print("Example 1: Get weather")
response = agent("What's the weather in Seattle?")
print(f"Response: {response}\n")

print("Example 2: Convert temperature")
response = agent("Convert 72 Fahrenheit to Celsius")
print(f"Response: {response}")
