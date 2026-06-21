"""Tools for the Customer Note Taker agent."""

from __future__ import annotations


def get_customer_account_number(email_address: str) -> str | None:
    """
    Get the customer's account number from their email address.

    Args:
        email_address (str): The customer's email address.

    Returns:
        (str | None): The customer's account number if found, else None.
    """
    if not email_address:
        raise ValueError("Customer email address is required.")

    email_address = email_address.strip().lower()

    if email_address == "alex.rivera@example.com":
        return "CUST-001"

    if email_address == "morgan.chen@example.com":
        return "CUST-003"

    if email_address == "jamie.patel@example.com":
        return "CUST-004"

    if email_address == "priya.nair@example.com":
        return "CUST-005"

    if email_address == "casey.williams@example.com":
        return "CUST-007"

    return None
