"""Guardrails for the Customer Note Taker agent."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command

from customer_note_taker.models import CustomerNote
from customer_note_taker.tools import get_customer_account_number


class GuardrailError(Exception):
    """Raised when a guardrail aborts processing."""


class BeforeAgentGuardrail(AgentMiddleware):
    """Blocks the agent when the user's input contains the word spam."""

    # The purpose of this project is to learn how to use LangChain guardrails,
    # not to implement real guardrails.  Hence the simplistic logic.

    def before_agent(self, state: AgentState, runtime: Runtime) -> None:
        messages = state.get("messages", [])

        if not messages:
            return

        for message in messages:
            content = getattr(message, "content", "")

            if isinstance(message, dict):
                content = message.get("content", "")

            if not isinstance(content, str):
                return

            words = content.lower().split()
            for word in words:
                if word.startswith("spam"):
                    raise GuardrailError(
                        "This email could not be processed "
                        "because it appears to be spam."
                    )


class AfterAgentGuardrail(AgentMiddleware):
    """Blocks the agent when the user's input contains profanity."""

    def after_agent(self, state: AgentState, runtime: Runtime) -> None:
        customer_note = state.get("structured_response")

        if isinstance(customer_note, dict):
            customer_note = CustomerNote.model_validate(customer_note)

        if not isinstance(customer_note, CustomerNote):
            return

        if customer_note.has_profanity:
            raise GuardrailError(
                "This email could not be processed because it contains profanity."
            )


class BeforeToolGuardrail(AgentMiddleware):
    """Blocks a call to a tool if the email address is disposable."""

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool_call.get("name", "")
        tool_args = request.tool_call.get("args", {})

        if tool_name == get_customer_account_number.__name__:
            email_address = tool_args.get("email_address", "")
            if "disposable" in email_address.lower():
                raise GuardrailError(
                    "This email could not be processed because "
                    "it uses a disposable email address."
                )

        # before-tool guardrail here

        result = handler(request)

        # after-tool guardrail here

        return result


class AfterToolGuardrail(AgentMiddleware):
    """Blocks a tool result if the customer is flagged."""

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool_call.get("name", "")

        # before-tool guardrail here

        result = handler(request)

        # after-tool guardrail here

        if tool_name == get_customer_account_number.__name__:
            tool_result = None
            if isinstance(result, ToolMessage):
                tool_result = result.content

            if tool_result is not None and isinstance(tool_result, str):
                if tool_result == "CUST-009":
                    raise GuardrailError(
                        "Emails from a flagged customer will not be processed. "
                    )

        return result


class BeforeModelGuardrail(AgentMiddleware):
    """Blocks a model call which may include prompt injection."""

    # The purpose of this project is to learn how to use LangChain guardrails,
    # not to implement real guardrails.  Hence the simplistic logic.

    def before_model(self, state: AgentState, runtime: Runtime) -> None:

        messages = state.get("messages", [])

        for message in messages:
            content = getattr(message, "content", "")

            if isinstance(message, dict):
                content = message.get("content", "")

            if not isinstance(content, str):
                continue

            content_lower = content.lower()

            if "ignore" in content_lower and "previous instructions" in content_lower:
                raise GuardrailError(
                    "This email could not be processed because "
                    "it appears to contain prompt injection."
                )


class AfterModelGuardrail(AgentMiddleware):
    """Blocks a model response that indicates domestic violence."""

    def after_model(self, state: AgentState, runtime: Runtime) -> None:
        customer_note = state.get("structured_response")

        if isinstance(customer_note, dict):
            customer_note = CustomerNote.model_validate(customer_note)

        if not isinstance(customer_note, CustomerNote):
            return

        if customer_note.has_domestic_violence:
            raise GuardrailError(
                "This email could not be processed because "
                "it appears to contain information about domestic violence."
            )


class ModifyStateGuardrail(AgentMiddleware):
    """Example of a guardrail that modifies the agent's state."""

    def before_model(
        self, state: AgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        messages = state.get("messages", [])
        updated_messages = []

        for message in messages:
            content = getattr(message, "content", "")

            if not isinstance(content, str):
                updated_messages.append(message)

            redacted_content = re.sub(
                pattern=r"\b(password\s+is\s+)(\S+)",
                repl=r"\1[REDACTED]",
                string=content,
                flags=re.IGNORECASE,
            )

            if isinstance(message, BaseMessage):
                updated_message = message.model_copy(
                    update={"content": redacted_content}
                )
                updated_messages.append(updated_message)
            elif isinstance(message, dict):
                updated_message = {**message, "content": redacted_content}
                updated_messages.append(updated_message)
            else:
                updated_messages.append(message)

        return {"messages": updated_messages}
