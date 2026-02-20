"""
LangFuse @observe Decorator - Agent Response Generator Example

This file demonstrates using the @observe decorator with LangGraph agents
that use tools.
Source: clickbait project - app/services/ai/agent/agent_response_generator.py

Key patterns:
- @observe decorator with agent execution
- Callbacks propagation to agent.invoke()
- Token extraction from messages
- Model fallback middleware
- Error handling with fallback tracking
"""

import logging
from typing import Any

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import BaseMessage, HumanMessage
from langfuse import observe
from pydantic import BaseModel


class FallbackFailure(BaseModel):
    """Record of a failed fallback attempt."""
    provider_name: str
    model_name: str
    error: str


class AgentResponse(BaseModel):
    """Response from agent execution."""
    content: BaseModel | None
    messages: list[BaseMessage] = []
    provider_enum: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    failures: list[FallbackFailure] = []

    @staticmethod
    def error_response(
        provider_enum: str | None,
        provider_name: str | None,
        model_name: str | None,
        error_message: str,
        failures: list[FallbackFailure],
    ) -> "AgentResponse":
        return AgentResponse(
            content=None,
            provider_enum=provider_enum,
            provider_name=provider_name,
            model_name=model_name,
            failures=failures,
        )


class GenerateAgentResponseConfig(BaseModel):
    """Configuration for agent response generation."""
    name: str = "default_agent"
    system_prompt: str | None = None
    user_prompt: str | None = None
    tools: list[Any] | None = None
    response_schema: type[BaseModel] | None = None
    temperature: float = 0.7
    max_iterations: int = 10
    force_execution: bool = False


class AgentResponseGenerator:
    """Generates agent-based AI responses with tools.

    Handles creation and execution of agents with tool calling,
    model fallback, and structured output validation.

    Usage:
        generator = AgentResponseGenerator()
        response = generator.generate(
            generation_config=config,
            callbacks=[langfuse_handler],
        )
    """

    def __init__(self):
        self.providers = [{"name": "OpenAI", "enum": "OPENAI"}]
        self.current_provider = None
        self.current_provider_enum = None

    @observe(name="agent_response_generator")
    def generate(
        self,
        generation_config: GenerateAgentResponseConfig,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> AgentResponse:
        """Generate agent response with LangFuse tracing.

        The @observe decorator creates a span that captures:
        - Input: generation_config
        - Output: AgentResponse
        - Timing: Automatic
        - Errors: Automatic

        Args:
            generation_config: Configuration for the agent
            callbacks: LangChain callbacks for tracing

        Returns:
            AgentResponse with structured content and metadata
        """
        logging.info(
            f"Starting agent response: {generation_config.name} | "
            f"schema: {generation_config.response_schema.__name__ if generation_config.response_schema else 'None'}"
        )

        failures: list[FallbackFailure] = []
        initial_provider_name = None
        initial_model_name = None

        for provider_info in self.providers:
            provider_name = provider_info["name"]
            provider_enum = provider_info["enum"]
            model_name = "gpt-4"

            if initial_provider_name is None:
                initial_provider_name = provider_name
                initial_model_name = model_name

            self.current_provider = provider_name
            self.current_provider_enum = provider_enum

            try:
                # In a real implementation, you would:
                # 1. Get provider client with callbacks
                # 2. Create agent with tools and system prompt
                # 3. Invoke agent with callbacks

                # Example agent invocation pattern:
                # agent = create_agent(
                #     model=model_client,
                #     tools=generation_config.tools,
                #     system_prompt=generation_config.system_prompt,
                #     response_format=generation_config.response_schema,
                # )
                #
                # invocation_config = {
                #     "recursion_limit": generation_config.max_iterations,
                # }
                # if callbacks:
                #     invocation_config["callbacks"] = callbacks
                #
                # agent_response = agent.invoke(
                #     {"messages": [HumanMessage(content=generation_config.user_prompt)]},
                #     config=invocation_config,
                # )

                # Simulated response for example
                agent_messages = [
                    HumanMessage(content=generation_config.user_prompt or "Hello"),
                ]

                token_summary = self._extract_tokens_from_messages(agent_messages)

                logging.info(
                    f"Agent response generated with provider {provider_name} - {model_name}"
                )

                return AgentResponse(
                    content=None,
                    messages=agent_messages,
                    provider_enum=provider_enum,
                    provider_name=provider_name,
                    model_name=model_name,
                    input_tokens=token_summary.get("input_tokens"),
                    output_tokens=token_summary.get("output_tokens"),
                    total_tokens=token_summary.get("total_tokens"),
                    failures=failures,
                )

            except Exception as error:
                error_message = f"Agent execution failed: {type(error).__name__}: {str(error)[:200]}"
                logging.error(error_message)

                failures.append(
                    FallbackFailure(
                        provider_name=provider_name,
                        model_name=model_name,
                        error=str(error),
                    )
                )
                continue

        final_error_message = f"All providers failed for agent {generation_config.name}."

        return AgentResponse.error_response(
            provider_enum=self.current_provider_enum,
            provider_name=initial_provider_name or self.current_provider,
            model_name=initial_model_name or "N/A",
            error_message=final_error_message,
            failures=failures,
        )

    def _extract_tokens_from_messages(
        self,
        messages: list[BaseMessage],
    ) -> dict[str, int]:
        """Extract token usage from LangChain message metadata.

        LangChain messages include usage_metadata when returned
        from LLM calls. This extracts the aggregate token counts.

        Args:
            messages: List of LangChain messages

        Returns:
            Dict with input_tokens, output_tokens, total_tokens
        """
        if not messages:
            return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0

        for message in messages:
            usage_metadata = getattr(message, "usage_metadata", None)
            if not usage_metadata:
                continue

            total_input_tokens += usage_metadata.get("input_tokens", 0)
            total_output_tokens += usage_metadata.get("output_tokens", 0)
            total_tokens += usage_metadata.get("total_tokens", 0)

        return {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
        }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os
    from langfuse import get_client
    from langfuse.langchain import CallbackHandler

    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test"

    langfuse = get_client()
    langfuse.update_current_trace(
        name="agent-generation-example",
        tags=["example", "agent", "demo"],
    )

    langfuse_handler = CallbackHandler()

    class SampleOutputSchema(BaseModel):
        answer: str
        confidence: float

    generator = AgentResponseGenerator()
    config = GenerateAgentResponseConfig(
        name="example_agent",
        user_prompt="What is the weather in San Francisco?",
        system_prompt="You are a helpful weather assistant.",
        response_schema=SampleOutputSchema,
        max_iterations=5,
    )

    response = generator.generate(
        generation_config=config,
        callbacks=[langfuse_handler],
    )

    print(f"Provider: {response.provider_name}")
    print(f"Model: {response.model_name}")
    print(f"Tokens: {response.total_tokens}")
    print(f"Failures: {len(response.failures)}")

    get_client().flush()
