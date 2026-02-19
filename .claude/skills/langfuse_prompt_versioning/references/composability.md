# Prompt Composability

Prompt composability allows referencing other text prompts within your prompts using a simple tag format, enabling modular and reusable prompt components.

## Overview

Benefits of prompt composability:
- Create reusable prompt components
- Maintain common instructions in a single place
- Update dependent prompts automatically when base prompts change
- Reduce duplication and improve consistency

## Reference Syntax

### By Version (Fixed)

```
@@@langfusePrompt:name=PromptName|version=1@@@
```

### By Label (Dynamic)

```
@@@langfusePrompt:name=PromptName|label=production@@@
```

## Creating Composable Prompts

### Step 1: Create Base Prompt

```python
langfuse.create_prompt(
    name="common/safety-guidelines",
    type="text",
    prompt="""
Always follow these safety guidelines:
1. Never provide medical advice
2. Never share personal information
3. Be respectful and professional
""",
    labels=["production"],
)
```

### Step 2: Create Dependent Prompt

```python
langfuse.create_prompt(
    name="customer-support",
    type="text",
    prompt="""You are a customer support agent.

@@@langfusePrompt:name=common/safety-guidelines|label=production@@@

When helping customers with {{issue}}, be empathetic and solution-oriented.
""",
    labels=["production"],
)
```

### Step 3: Use in Application

```python
prompt = langfuse.get_prompt("customer-support")
compiled = prompt.compile(issue="billing question")

# The reference tag is automatically replaced with the content
# of common/safety-guidelines prompt
```

## Use Cases

### 1. Shared System Instructions

```python
# Base prompt with system behavior
langfuse.create_prompt(
    name="shared/system-behavior",
    type="text",
    prompt="Respond in {{language}}. Be concise and accurate.",
    labels=["production"],
)

# Multiple prompts referencing it
langfuse.create_prompt(
    name="agents/researcher",
    type="text",
    prompt="""You are a research assistant.
@@@langfusePrompt:name=shared/system-behavior|label=production@@@
Help users find information on {{topic}}.""",
    labels=["production"],
)

langfuse.create_prompt(
    name="agents/writer",
    type="text",
    prompt="""You are a content writer.
@@@langfusePrompt:name=shared/system-behavior|label=production@@@
Write about {{topic}}.""",
    labels=["production"],
)
```

### 2. Few-Shot Examples Library

```python
# Example library
langfuse.create_prompt(
    name="examples/summarization",
    type="text",
    prompt="""
Example 1:
Input: "Long article about AI..."
Output: "AI is transforming industries."

Example 2:
Input: "Another long text..."
Output: "Brief summary here."
""",
    labels=["production"],
)

# Use in task prompt
langfuse.create_prompt(
    name="tasks/summarize",
    type="text",
    prompt="""Summarize the following text.

Examples:
@@@langfusePrompt:name=examples/summarization|label=production@@@

Text: {{input}}
Summary:""",
    labels=["production"],
)
```

### 3. Domain-Specific Knowledge

```python
# Domain knowledge base
langfuse.create_prompt(
    name="knowledge/finance-terms",
    type="text",
    prompt="""
Key financial terms:
- ROI: Return on Investment
- EBITDA: Earnings Before Interest, Taxes, Depreciation, and Amortization
- P/E Ratio: Price-to-Earnings Ratio
""",
    labels=["production"],
)

# Specialized agent
langfuse.create_prompt(
    name="agents/financial-analyst",
    type="text",
    prompt="""You are a financial analyst.

@@@langfusePrompt:name=knowledge/finance-terms|label=production@@@

Analyze the following: {{query}}""",
    labels=["production"],
)
```

### 4. Multi-Tenant Customization

```python
# Tenant-specific branding
langfuse.create_prompt(
    name="tenants/acme-corp/branding",
    type="text",
    prompt="Always mention Acme Corp's commitment to quality.",
    labels=["production"],
)

langfuse.create_prompt(
    name="tenants/acme-corp/support",
    type="text",
    prompt="""You are Acme Corp's support agent.
@@@langfusePrompt:name=tenants/acme-corp/branding|label=production@@@
Help with: {{issue}}""",
    labels=["production"],
)
```

## Nested References

Prompts can reference other prompts that also contain references (nested composition):

```python
# Level 1: Base
langfuse.create_prompt(
    name="base/formatting",
    type="text",
    prompt="Use markdown formatting. Be concise.",
    labels=["production"],
)

# Level 2: Intermediate (references Level 1)
langfuse.create_prompt(
    name="shared/assistant-base",
    type="text",
    prompt="""@@@langfusePrompt:name=base/formatting|label=production@@@
Always be helpful and polite.""",
    labels=["production"],
)

# Level 3: Final (references Level 2)
langfuse.create_prompt(
    name="agents/specialist",
    type="text",
    prompt="""@@@langfusePrompt:name=shared/assistant-base|label=production@@@
Specialize in {{domain}}.""",
    labels=["production"],
)
```

## UI Integration

In the Langfuse UI, use the "Add prompt reference" button to insert reference tags without typing the syntax manually.

## Best Practices

1. **Use labels over versions** - For dynamic resolution, use `label=production` instead of `version=1`
2. **Organize with folders** - Use `/` in names for hierarchy (e.g., `shared/`, `agents/`, `knowledge/`)
3. **Document dependencies** - Track which prompts reference others for maintenance
4. **Test resolution** - Verify nested references resolve correctly
5. **Version carefully** - Changes to base prompts affect all dependent prompts

## Limitations

- Only **text prompts** can be referenced (not chat prompts)
- Circular references are not supported
- Maximum nesting depth: 10 levels
