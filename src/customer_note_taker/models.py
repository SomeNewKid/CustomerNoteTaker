"""Models for use in the Customer Note Taker application."""

from __future__ import annotations

from pydantic import BaseModel


class CustomerNote(BaseModel):
    """A note about a customer."""

    customer_email_address: str
    has_profanity: bool
    has_domestic_violence: bool
    summary_of_email: str
    customer_account_number: str
