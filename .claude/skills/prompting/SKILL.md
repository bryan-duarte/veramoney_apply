---
name: prompting
description: Comprehensive prompt engineering guidance for creating effective prompts with Claude. Use this skill when crafting, improving, or debugging prompts for LLM interactions, including tasks like writing system prompts, structuring multi-turn conversations, using XML tags, implementing chain-of-thought prompting, creating few-shot examples, handling long context, or chaining complex prompts. Triggers include requests to "improve this prompt", "help me write a prompt", "why is my prompt not working", or any prompt engineering task.
---

# Prompt Engineering

Prompt engineering is writing effective instructions that consistently generate desired outputs from Claude.

## Core Principles

### Be Clear and Direct

Treat Claude as a brilliant new employee with no context. Provide explicit instructions.

**Key practices:**
- Give contextual information (task purpose, audience, workflow position)
- Be specific about desired output
- Use sequential numbered steps
- Apply the "colleague test": if a colleague would be confused, Claude will be too

**Example structure:**
```
Your task is to [specific action].

Instructions:
1. [First step]
2. [Second step]
3. [Third step]

Context: [Why this task matters, who will use the output]

Output format: [Specific format requirements]
```

See [references/be_clear.md](references/be_clear.md) for detailed examples.

### Use Examples (Few-shot Prompting)

Include 3-5 diverse, relevant examples to dramatically improve accuracy and consistency.

**Effective examples are:**
- **Relevant**: Mirror your actual use case
- **Diverse**: Cover edge cases and variations
- **Clear**: Wrapped in `<example>` tags

```xml
<examples>
<example>
Input: [sample input]
Output: [expected output]
</example>
</examples>
```

See [references/use_examples.md](references/use_examples.md) for detailed patterns.

### Let Claude Think (Chain of Thought)

For complex tasks, give Claude space to reason step-by-step.

**Techniques (increasing complexity):**
1. **Basic**: Add "Think step-by-step"
2. **Guided**: Outline specific reasoning steps
3. **Structured**: Use XML tags to separate thinking from answer

```xml
<thinking>
[Let Claude reason here]
</thinking>

<answer>
[Final output]
</answer>
```

Use CoT for: math, logic, multi-step analysis, complex decisions.

See [references/let_model_think.md](references/let_model_think.md) for examples.

### Structure with XML Tags

Use XML tags to separate prompt components and enable parsing.

**Benefits:**
- Clarity: Separate instructions, context, examples
- Accuracy: Reduce misinterpretation
- Flexibility: Easy to modify sections
- Parseability: Extract specific response parts

**Common tags:**
- `<instructions>` - Task directions
- `<context>` - Background information
- `<example>` / `<examples>` - Sample inputs/outputs
- `<output>` - Expected response format
- `<thinking>` / `<answer>` - CoT separation

```xml
<instructions>
Analyze the contract and identify risks.
</instructions>

<contract>
{{CONTRACT_TEXT}}
</contract>

<output_format>
List risks in bullet points.
</output_format>
```

See [references/use_xml_tags.md](references/use_xml_tags.md) for patterns.

### Give Claude a Role

Use the `system` parameter to set expertise and tone.

```python
response = client.messages.create(
    model="claude-opus-4-6",
    system="You are a senior financial analyst at a Fortune 500 company.",
    messages=[{"role": "user", "content": "..."}]
)
```

**Why role prompting works:**
- Enhanced accuracy in domain-specific tasks
- Tailored tone and communication style
- Improved focus on task requirements

See [references/give_system_prompt.md](references/give_system_prompt.md) for examples.

## Advanced Techniques

### Chain Complex Prompts

Break multi-step tasks into sequential subtasks for better accuracy.

**When to chain:**
- Multi-step analysis
- Content pipelines (research → outline → draft → edit)
- Data processing (extract → transform → analyze)
- Verification loops (generate → review → refine)

**Pattern:**
```
Prompt 1: Analyze → output in <analysis> tags
Prompt 2: Use <analysis> to create recommendation → output in <recommendation> tags
Prompt 3: Review <recommendation> for quality
```

See [references/complex_prompts.md](references/complex_prompts.md) for workflows.

### Long Context Optimization

For prompts with large documents or data:

1. **Put long data first**: Place documents above queries (up to 30% better performance)
2. **Structure with XML**: Use `<document>` tags with metadata
3. **Ground in quotes**: Ask Claude to quote relevant sections first

```xml
<documents>
  <document index="1">
    <source>report.pdf</source>
    <document_content>
    {{CONTENT}}
    </document_content>
  </document>
</documents>

Find quotes relevant to the question, then answer.
```

See [references/long_context_tips.md](references/long_context_tips.md) for patterns.

## Quick Reference

| Technique | When to Use | Key Action |
|-----------|-------------|------------|
| Clear instructions | All tasks | Number steps, specify output |
| Examples | Structured outputs | 3-5 diverse samples |
| Chain of thought | Complex reasoning | Add "think step-by-step" |
| XML tags | Multi-component prompts | Separate with tags |
| Role prompting | Domain expertise | Set role in system |
| Prompt chaining | Multi-step workflows | Break into subtasks |
| Quote grounding | Long documents | Request quotes first |

## Reference Files

For detailed examples and patterns, consult:
- [be_clear.md](references/be_clear.md) - Clarity and specificity
- [use_examples.md](references/use_examples.md) - Few-shot prompting
- [let_model_think.md](references/let_model_think.md) - Chain of thought
- [use_xml_tags.md](references/use_xml_tags.md) - XML structuring
- [give_system_prompt.md](references/give_system_prompt.md) - Role prompting
- [complex_prompts.md](references/complex_prompts.md) - Prompt chaining
- [long_context_tips.md](references/long_context_tips.md) - Long context handling
