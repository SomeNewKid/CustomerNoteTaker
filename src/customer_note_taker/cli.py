"""Command-line interface for Customer Note Taker."""

from __future__ import annotations

import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

from customer_note_taker.guardrails import (
    AfterAgentGuardrail,
    AfterModelGuardrail,
    AfterToolGuardrail,
    BeforeAgentGuardrail,
    BeforeModelGuardrail,
    BeforeToolGuardrail,
    GuardrailError,
    ModifyStateGuardrail,
)
from customer_note_taker.models import CustomerNote
from customer_note_taker.tools import get_customer_account_number

# Expected results|
#   EMAIL         | GUARDRAIL    | RESULT
#   --------------|--------------|--------------------------------
#   email-001.txt |              | processed
#   email-002.txt | before agent | blocked for spam
#   email-003.txt |              | processed, with PII masked
#   email-004.txt | after agent  | blocked for profanity
#   email-005.txt | after model  | blocked for DV
#   email-006.txt | before model | blocked for prompt injection
#   email-007.txt |              | processed, with password masked
#   email-008.txt | before tool  | blocked for disposable email
#   email-009.txt | after tool   | blocked for flagged customer


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    file_name = _get_file_name(argv)
    if not file_name:
        raise SystemExit("Usage: python -m customer_note_taker email-001.txt")

    email_path = Path("files") / file_name

    output_path = email_path.with_suffix(".json")
    if output_path.exists():
        output_path.unlink()

    if not email_path.exists():
        raise SystemExit(f"File not found: {email_path}")
    if not email_path.is_file():
        raise SystemExit(f"File not found: {email_path}")
    if not email_path.suffix == ".txt":
        raise SystemExit("Only .txt files are supported.")

    email_content = email_path.read_text(encoding="utf-8")
    if not email_content.strip():
        raise ValueError("Email file was empty.")

    agent = create_agent(
        model="openai:gpt-4o",
        tools=[get_customer_account_number],
        response_format=CustomerNote,
        middleware=[
            BeforeAgentGuardrail(),
            BeforeModelGuardrail(),
            ModifyStateGuardrail(),
            AfterModelGuardrail(),
            BeforeToolGuardrail(),
            AfterToolGuardrail(),
            AfterAgentGuardrail(),
            PIIMiddleware("credit_card", strategy="mask"),
        ],
        system_prompt=(
            "You create structured a customer note from a customer's email. "
            "After determining the customer's email address, "
            "you must call the get_customer_account_number tool exactly one time "
            "using the customer's email ddress. "
            "If the tool returns None, set customer_account_number to an empty string. "
            "Set has_domestic_violence to True only when the email contains "
            "hints that the customer may be unsafe or controlled by another person. "
            "Set has_profanity to True when the email contains explicit profanity. "
            "Set summary_of_email to a concise (50 words or fewer) "
            "summary of the email. "
            "If the user provided personally identifiable information (PII), "
            "you must include that PII in the summary. "
            "if the word [REDACTED] appears, the summary must note that "
            "some details were redacted."
        ),
    )

    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Create a CustomerNote from this email:\n\n{email_content}"
                        ),
                    }
                ]
            }
        )
    except GuardrailError as error:
        print(error)
        return 1

    customer_note = _get_customer_note(result["structured_response"])
    if not customer_note:
        raise RuntimeError("Could not get CustomerNote from agent.")

    output_path.write_text(customer_note.model_dump_json(indent=2), encoding="utf-8")

    if output_path.exists():
        print(f"File created: {output_path.name}")
    else:
        print("No file created.")
    return 0


def _get_customer_note(value: object) -> CustomerNote | None:
    if not value:
        raise TypeError("Expected CustomerNote or dict, got None")

    if isinstance(value, CustomerNote):
        return value

    if isinstance(value, dict):
        return CustomerNote.model_validate(value)

    raise TypeError(f"Expected CustomerNote or dict, got {type(value).__name__}")


def _get_file_name(argv: list[str] | None = None) -> str:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        return ""

    return args[0]
