# Contributing

Read AGENTS.md first. Keep one logical change per commit and describe the actual failure or behavior it changes. Run the checks for the affected path and the full release checks before tagging. Add a failing fixture before changing an accounting invariant. Do not change a registration or promoted source to improve a score. Write source fetches as explicit versioned requests and report unavailable sources.

Use Python 3.12 with uv and the frontend lock with npm ci. Use a separate migration credential for Alembic. Never commit live connection strings, access tokens, private model prompts or employer identifiers.
