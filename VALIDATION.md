# Validation record

September 10, 2026, local Python 3.12:

- 29 unit tests passed, including existing offline/Gemini tests and seven OpenAI workflow tests.
- OpenAI Agents SDK 0.22.2 installed and the structured agent initialized successfully.
- A live synthetic-passage request reached the provider but returned `RateLimitError`; a diagnostic retry had the same result. No successful live classification or review report is claimed.
- The live failure may require resolving API rate limits or account quota. No real research corpus was sent.
- No Gemini live request was made.
- Unit tests use mocked model outputs. They validate software behavior, not stance accuracy.

Run `python -m unittest discover -s tests -v` after installing requirements. Use Python 3.12 or newer for the AI workflow.

Before reporting research accuracy, evaluate on a separately labeled human-coded dataset, inspect errors by category, and document the coding protocol. The two AI passes can share mistakes; exact quotation validation establishes source fidelity only.
