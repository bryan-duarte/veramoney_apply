# Message Placeholders in Chat Prompts

Message placeholders allow inserting dynamic lists of chat messages at specific positions within a chat prompt template.

## Overview

Placeholders are useful for:
- Injecting conversation history
- Adding few-shot examples dynamically
- Inserting context from RAG systems

## Creating Prompts with Placeholders

### Python SDK

```python
from langfuse import get_client

langfuse = get_client()

langfuse.create_prompt(
    name="chat-with-history",
    type="chat",
    prompt=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"type": "placeholder", "name": "chat_history"},
        {"role": "user", "content": "Based on our conversation, {{question}}"},
    ],
    labels=["production"],
)
```

### TypeScript SDK

```typescript
await langfuse.createPrompt({
  name: "chat-with-history",
  type: "chat",
  prompt: [
    { role: "system", content: "You are a helpful assistant." },
    { type: "placeholder", name: "chat_history" },
    { role: "user", content: "Based on our conversation, {{question}}" },
  ],
  labels: ["production"],
});
```

## Resolving Placeholders at Runtime

### Python

```python
prompt = langfuse.get_prompt("chat-with-history", type="chat")

compiled = prompt.compile(
    question="what should I do next?",
    chat_history=[
        {"role": "user", "content": "I'm learning Python"},
        {"role": "assistant", "content": "That's great! Python is versatile."},
        {"role": "user", "content": "I want to build web apps"},
    ]
)

# Result:
# [
#   {"role": "system", "content": "You are a helpful assistant."},
#   {"role": "user", "content": "I'm learning Python"},
#   {"role": "assistant", "content": "That's great! Python is versatile."},
#   {"role": "user", "content": "I want to build web apps"},
#   {"role": "user", "content": "Based on our conversation, what should I do next?"},
# ]
```

### TypeScript

```typescript
const prompt = await langfuse.getPrompt("chat-with-history", undefined, {
  type: "chat",
});

const compiled = prompt.compile(
  { question: "what should I do next?" },
  {
    chat_history: [
      { role: "user", content: "I'm learning Python" },
      { role: "assistant", content: "That's great! Python is versatile." },
    ],
  }
);
```

## Multiple Placeholders

```python
langfuse.create_prompt(
    name="multi-placeholder-chat",
    type="chat",
    prompt=[
        {"role": "system", "content": "You are a {{domain}} expert."},
        {"type": "placeholder", "name": "few_shot_examples"},
        {"type": "placeholder", "name": "chat_history"},
        {"role": "user", "content": "{{question}}"},
    ],
    labels=["production"],
)

# Compile with multiple placeholders
compiled = prompt.compile(
    domain="finance",
    question="What's the best investment strategy?",
    few_shot_examples=[
        {"role": "user", "content": "Example question 1"},
        {"role": "assistant", "content": "Example answer 1"},
    ],
    chat_history=[
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"},
    ],
)
```

## LangChain Integration

```python
from langchain_core.prompts import ChatPromptTemplate

langfuse_prompt = langfuse.get_prompt("chat-with-history", type="chat")

# Get LangChain template with MessagesPlaceholder objects
langchain_prompt = ChatPromptTemplate.from_messages(
    langfuse_prompt.get_langchain_prompt()
)

# Result includes MessagesPlaceholder for unresolved placeholders:
# [
#   SystemMessage(content="You are a helpful assistant."),
#   MessagesPlaceholder(name="chat_history"),
#   HumanMessage(content="Based on our conversation, {{question}}"),
# ]
```

## Use Cases

### 1. Conversation Memory

```python
def chat_with_memory(user_id: str, question: str):
    history = get_conversation_history(user_id)  # From DB/Redis

    prompt = langfuse.get_prompt("chat-with-history", type="chat")
    compiled = prompt.compile(question=question, chat_history=history)

    return llm.chat(compiled)
```

### 2. Few-Shot Learning

```python
def chat_with_examples(domain: str, question: str):
    examples = load_few_shot_examples(domain)  # From config

    prompt = langfuse.get_prompt("few-shot-chat", type="chat")
    compiled = prompt.compile(
        domain=domain,
        question=question,
        few_shot_examples=examples
    )

    return llm.chat(compiled)
```

### 3. RAG Context Injection

```python
def chat_with_rag(query: str):
    docs = retrieve_relevant_docs(query)
    context_messages = format_docs_as_messages(docs)

    prompt = langfuse.get_prompt("rag-chat", type="chat")
    compiled = prompt.compile(
        question=query,
        context=context_messages
    )

    return llm.chat(compiled)
```

## Requirements

- Python SDK: `langfuse >= 3.1.0`
- TypeScript SDK: `langfuse >= 3.38.0`
