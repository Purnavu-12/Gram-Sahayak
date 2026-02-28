# Getting Started with Strands Agents SDK

## What You Have

Three example agent files to help you get started:

1. **agent.py** - ISS location agent with multiple tools
2. **agent_conversation.py** - Simple math agent showing conversation context
3. **agent_custom_tool.py** - Weather agent with custom tools

## Before You Run

You need to set up API credentials. Choose one option:

### Option 1: AWS Bedrock (Default)

```bash
# Set your Bedrock API key
$env:AWS_BEDROCK_API_KEY="your_bedrock_api_key"

# Run any example
python agent.py
```

Get your API key from: https://console.aws.amazon.com/bedrock

### Option 2: Use Anthropic Instead

```bash
# Install Anthropic support
pip install 'strands-agents[anthropic]'

# Set your API key
$env:ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Then modify the agent files to use Anthropic:

```python
from strands import Agent
from strands.models.anthropic import AnthropicModel
import os

model = AnthropicModel(
    client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
    model_id="claude-sonnet-4-20250514",
    max_tokens=1028,
    params={"temperature": 0.7}
)

agent = Agent(
    model=model,
    tools=[...],
    system_prompt="..."
)
```

## Running the Examples

Once credentials are set:

```bash
# Example 1: ISS location
python agent.py

# Example 2: Conversation with context
python agent_conversation.py

# Example 3: Custom tools
python agent_custom_tool.py
```

## Next Steps

- Explore the community tools: calculator, python_repl, http_request
- Create your own custom tools with the @tool decorator
- Try different model providers (OpenAI, Gemini, Llama)
- Adjust temperature for different use cases (0.1-0.3 for factual, 0.7-0.9 for creative)

## Need Help?

Use the Strands documentation tools:

```python
# Search documentation
kiroPowers("strands", "strands-agents", "search_docs", {
    "query": "how to create custom tools",
    "k": 3
})

# Fetch full documentation
kiroPowers("strands", "strands-agents", "fetch_doc", {
    "uri": "https://docs.strands.ai/user-guide/tools"
})
```
