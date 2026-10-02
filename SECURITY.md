# Security

This example handles a Rius API key and a model key, and its traces carry
prompts, model replies and tool output. We take reports about any of it
seriously.

## Reporting a vulnerability

Please don't open a public issue. Report it privately instead:

- **GitHub:** [open a private security advisory](https://github.com/glassflow/openhands-rius/security/advisories/new)
  on this repository, or
- **Email:** [help@glassflow.ai](mailto:help@glassflow.ai) with "Security"
  in the subject.

Include what you found, how to reproduce it, and the OpenHands and Python
versions you used. If a report needs a trace or a log, remove API keys and
anything your runs captured before sending it.

We'll confirm we have the report, keep you posted while we work on it, and
credit you if you'd like.

## What's in scope

- Code in this repository: `run_agent.py`, `demo/`, `deploy/` and the tests.
- Anything here that sends data somewhere other than the endpoint in your
  `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`, or writes a key to a log or a file.

Issues in the Rius service itself (the console, ingest or the MCP server)
are welcome through the same channels. Issues in OpenHands belong with the
[OpenHands project](https://github.com/OpenHands/OpenHands/security).
