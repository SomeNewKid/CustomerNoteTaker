# Customer Note Taker

Customer Note Taker is a small Python command-line sample for exploring
guardrails in the LangChain framework. It reads a pretend customer email from
`files`, asks a GPT-4o-backed LangChain agent to create a structured customer
note, and writes the note as JSON.

> [!WARNING]
> This is an experimental project and should not be considered production-ready.

The project was created to make LangChain guardrail wiring visible. The sample
guardrails are intentionally simple and keyword-based. They are useful for
learning where guardrails run in an agent workflow, not for real safety,
security, privacy, or compliance decisions.

## What It Does

The CLI accepts the name of a text file in the `files` directory:

```powershell
.\.venv\Scripts\python.exe -m customer_note_taker email-001.txt
```

The agent then:

- reads the RFC-style pretend email text
- checks the input before the agent run continues
- checks and modifies messages before model calls
- uses LangChain's built-in PII middleware to mask credit card numbers
- calls the `get_customer_account_number` tool
- checks tool input before the tool executes
- checks tool output after the tool executes
- asks the model for a structured `CustomerNote`
- checks the model and agent output before saving
- writes a JSON file next to the source email, such as `files/email-001.json`

The `CustomerNote` model contains:

```text
customer_email_address
has_profanity
has_domestic_violence
summary_of_email
customer_account_number
```

## Sample Emails

The `files` directory contains sample inputs for exercising the guardrails:

```text
email-001.txt  Valid customer email, expected to be processed
email-002.txt  Spam example, blocked before the agent runs
email-003.txt  PII example, processed with credit card details masked
email-004.txt  Profanity example, blocked after the agent runs
email-005.txt  Domestic violence signal, blocked after the model runs
email-006.txt  Prompt injection example, blocked before the model runs
email-007.txt  Password disclosure, processed with the password redacted
email-008.txt  Disposable email address, blocked before tool execution
email-009.txt  Flagged customer example, blocked after tool execution
```

## Requirements

- Python 3.11.
- PowerShell on Windows.
- An `OPENAI_API_KEY` environment variable for OpenAI model calls.

## Setup

Create the virtual environment and install the project with development
dependencies:

```powershell
.\scripts\setup-dev.ps1
```

The setup script expects Python 3.11 at the path configured in
`scripts\setup-dev.ps1`.

## Running

Run the agent from the repository root:

```powershell
.\.venv\Scripts\python.exe -m customer_note_taker email-001.txt
```

Successful runs create a JSON file in `files`:

```text
files/email-001.json
```

Guardrail failures print a short friendly message and do not save a customer
note.

## Development Checks

Run formatting, linting, type checking, and tests:

```powershell
.\scripts\check.ps1
```

This runs:

- `ruff format .`
- `ruff check .`
- `pyright`
- `pytest`

## Project Structure

```text
src/customer_note_taker/
  __main__.py     Package entry point for python -m customer_note_taker
  cli.py          Agent setup, file handling, and command-line entry point
  guardrails.py   LangChain middleware guardrail examples
  models.py       Pydantic CustomerNote model
  tools.py        Customer account lookup tool

files/
  email-001.txt
  email-002.txt
  email-003.txt
  email-004.txt
  email-005.txt
  email-006.txt
  email-007.txt
  email-008.txt
  email-009.txt

tests/
  test_smoke.py

scripts/
  setup-dev.ps1
  check.ps1
```

## Notes

This project is a guardrail learning exercise, not a real customer-support
automation system. The guardrails deliberately use simple checks such as keyword
matching, regular expressions, and fixed account numbers so their behavior is
easy to see.

Agent behavior and final summaries can vary between runs because the customer
note is model-driven. OpenAI API calls may incur usage costs.

## Third-Party Notices

This project has direct runtime dependencies on third-party Python packages,
including `langchain`, `langchain-openai`, `pydantic`, and `python-dotenv`. See
each package's PyPI license metadata for full license and notice terms.

## License

GNU General Public License v3.0. See the `LICENSE` file for details.
