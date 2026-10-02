# OpenHands + Rius

Send OpenHands agent runs to [Rius](https://docs.glassflow.ai/rius) with
environment variables only. OpenHands already traces every conversation
with OpenTelemetry; these examples point that tracing at Rius. You get each
conversation as a trace, cost per model call, an alert when an agent loops,
and a written root cause.

![A looping OpenHands conversation, as a trace in Rius](docs/images/rius-trace.png)

```text
run_agent.py          one SDK conversation, traced through OTEL_* env vars
.env.example          the three tracing variables, your model and key, the agent name
demo/stuck_llm.py     a scripted model that loops on purpose (no tokens spent)
deploy/docker-run.sh  the OpenHands web app, with tracing passed to its sandbox
```

Tested with `openhands-sdk` 1.49.6, `openhands-tools` 1.49.6 and Python 3.12
(SDK), and the `openhands:latest` image with agent server 1.36.0 (web app).

## What you need

- **Python 3.12 or newer.** The OpenHands SDK doesn't install on older versions.
  On macOS, `python3` is often 3.9; install 3.12 with `brew install python@3.12` or `uv python install 3.12`.
- **A Rius account.** Sign up at
  [console.rius-glassflow.com](https://console.rius-glassflow.com) (**Create account**).
  A new organization starts on a free trial.
- **A Rius API key** with the **Send telemetry** scope. Create it under
  **Settings → API keys** in the console. The key is shown once, so copy it.
- **A model key.** The examples use Claude Haiku 4.5, so an Anthropic key. One
  run costs about two cents. The stuck-agent demo needs no model key.
- **Docker**, only for the web app.

## Run it

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env    # fill in LLM_API_KEY and your Rius key
set -a; . ./.env; set +a
.venv/bin/python run_agent.py
```

The run takes a few seconds. `run_agent.py` checks the protocol, the
endpoint path and `LMNR_*` before it starts, and prints what's wrong. Open
the trace list in the Rius console and click the new `openhands-demo`
trace. Every model call shows its tokens and cost:

![One model call in Rius, with tokens and cost](docs/images/rius-cost-per-call.png)

Start the script from its own directory. `python /abs/path/run_agent.py`
puts the full path in the service column. Set `AGENT_NAME` in `.env` to
change the agent name Rius shows.

## See a stuck agent get flagged

```bash
.venv/bin/python demo/stuck_llm.py 9901 &
LLM_MODEL=openai/stuck LLM_BASE_URL=http://127.0.0.1:9901/v1 LLM_API_KEY=unused \
  AGENT_NAME=openhands-stuck-demo .venv/bin/python run_agent.py "List the files in missing-dir."
```

The scripted model asks for the same failing command four times, and
OpenHands' stuck detector stops the conversation. With `REPEAT=2` in front
of `demo/stuck_llm.py`, it loops twice and then finishes normally. Either
way, Rius's pre-defined Tool Loop alert opens on the trace within a few
minutes. It's on in every workspace.

## The web app

```bash
RIUS_API_KEY=ri_... deploy/docker-run.sh
```

Open http://localhost:3000, set your model and key in the settings, and
start a conversation. It shows up in Rius under the agent
`openhands-agent-server`.

To see the Tool Loop alert with a real model, give the agent a task it
can't finish, for example:

> Our staging API should be up on port 8080 after the deploy. Check it with
> `curl -sf http://localhost:8080/health` and keep checking until it
> answers, then tell me it is up. Do not try to start or fix the service
> yourself, it is deployed separately.

The agent retries the same health check until OpenHands' stuck detector
stops it:

![The OpenHands web app re-running the same health check](docs/images/openhands-web-app-loop.png)

Rius opens a Tool Loop alert while the agent is still looping:

![The Tool Loop alert in Rius](docs/images/rius-tool-loop-alert.png)

With root-cause analysis turned on for the workspace, the alert comes with
a written finding. For this run it traced the loop to the prompt, which
had no retry limit:

![The root-cause analysis on the alert](docs/images/rius-root-cause.png)

The web app's agent server streams its model calls, and no token usage is
recorded for streamed calls. So web-app traces show every model call, tool
call and its output, but no token counts or cost.

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
- OpenHands Cloud doesn't take custom environment variables, so it can't be
  pointed at Rius yet.

## License

MIT
