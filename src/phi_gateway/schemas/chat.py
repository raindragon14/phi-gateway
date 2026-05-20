"""Pydantic schemas for chat completion requests and responses.

Mirrors the OpenAI chat completion API shape while adding
provider and cost metadata specific to PhiGateway.
"""

from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single message in a chat conversation.

    Supports all standard roles for both user-facing and tool
    interop messages.

    Attributes:
        role: ``"user"``, ``"assistant"``, ``"system"``, or ``"tool"``.
        content: Message body text.
        name: Optional sender name.
        tool_calls: Optional list of tool call dicts (assistant role).
    """

    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None


class ChatCompletionRequest(BaseModel):
    """Request body for a chat completion call.

    Attributes:
        model: Full model identifier string.
        messages: List of messages in the conversation.
        temperature: Sampling temperature (0-2, default 0.7).
        max_tokens: Optional cap on completion tokens.
        stream: Whether to stream the response via SSE.
        tools: Optional list of tool/function definitions.
    """

    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[list[dict]] = None


class ChatCompletionChoice(BaseModel):
    """A single completion choice within a response.

    Attributes:
        index: Zero-based index of this choice.
        message: The generated message.
        finish_reason: Reason the generation stopped (``"stop"``,
            ``"length"``, ``"tool_calls"``, etc.).
    """

    index: int
    message: ChatMessage
    finish_reason: str


class UsageInfo(BaseModel):
    """Token usage statistics for a completion.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens consumed.
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response body for a non-streaming chat completion.

    Attributes:
        id: Unique response identifier.
        object: Always ``"chat.completion"``.
        created: Unix timestamp of response generation.
        model: Model used for the completion.
        choices: List of completion choices.
        usage: Token usage statistics.
        provider: Provider slug used to route the request.
        cost_usd: Total cost in USD.
    """

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: UsageInfo
    provider: str
    cost_usd: float
