# OpenHands + Rius

Send OpenHands agent runs to [Rius](https://docs.glassflow.ai/rius) with
environment variables only. OpenHands already traces itself with
OpenTelemetry; these examples point that tracing at Rius.

```text
run_agent.py          one SDK conversation, traced through OTEL_* env vars
.env.example          the four tracing variables, plus your model key
demo/stuck_llm.py     a scripted model that loops on purpose (no tokens spent)
deploy/docker-run.sh  the OpenHands web app, with tracing passed to its sandbox
```

Tested with `openhands-sdk` 1.49.6, `openhands-tools` 1.49.6 and Python 3.12.

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env    # fill in LLM_API_KEY and your Rius key
set -a; . ./.env; set +a
.venv/bin/python run_agent.py
```

The run takes a few seconds. Open the trace list in the Rius console, or ask
the Rius MCP server for your latest `openhands-demo` trace.

## See a stuck agent get flagged

```bash
.venv/bin/python demo/stuck_llm.py 9901 &
LLM_MODEL=openai/stuck LLM_BASE_URL=http://127.0.0.1:9901/v1 LLM_API_KEY=unused \
  AGENT_NAME=openhands-stuck-demo .venv/bin/python run_agent.py "List the files in missing-dir."
```

The scripted model asks for the same failing command again and again.
Rius's Tool Loop alert fires on the trace within a few minutes.

## The traps

- `OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf`. The default is gRPC,
  which Rius doesn't accept.
- The endpoint must end in `/v1/traces`.
- `Bearer%20ri_...`. The header value is URL-encoded, so the space is `%20`.
- No `LMNR_*` variables. A Laminar key takes over and the OTEL settings are
  ignored.
- The web app only forwards `LLM_*` and `LMNR_*` into the agent's sandbox.
  Pass tracing through `OH_AGENT_SERVER_ENV` instead (see
  `deploy/docker-run.sh`).

## The web app

```bash
RIUS_API_KEY=ri_... deploy/docker-run.sh
```

Then open http://localhost:3000. Conversations show under the agent
`openhands-agent-server`. The app's agent server streams model calls, and
`lmnr` records no token usage for streamed calls, so those traces have no
token counts or cost. Tool calls and content arrive in full.

## License

MIT
