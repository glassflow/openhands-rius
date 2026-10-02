# Contributing

Thanks for helping. Bug reports, fixes and docs improvements are all
welcome. For anything bigger than a small fix, open an issue first so we can
agree on the shape before you write it.

By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
Security problems go through [SECURITY.md](SECURITY.md), not public issues.

## Setting up

You need Python 3.12 or newer. The checks need no model key and no network:

```bash
git clone https://github.com/glassflow/openhands-rius.git
cd openhands-rius
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tests/smoke_test.py
```

`tests/smoke_test.py` runs `run_agent.py` against the scripted model in
`demo/` and a local OTLP receiver. It checks the decoded bearer header, the
agent name and one `TerminalAction` span per scripted repeat. CI runs it,
plus `shellcheck` on `deploy/` and a scan for key-shaped strings.

## Rules the example has to keep

- **No tracing code in `run_agent.py`.** The point of the repo is that the
  `OTEL_*` variables are enough. Settings checks are fine; exporters and
  SDK wiring are not.
- **No real keys.** Use placeholders like `ri_...` and `sk-ant-...` in docs
  and `.env.example`.
- **Pin what you test.** If you bump `requirements.txt` or the image tag,
  run the smoke test and update the tested versions in the README.

## Pull requests

- Keep a PR to one change, and say how you checked it.
- Update the README when anything a user sees changes.
- Commit subjects are a plain sentence, for example
  `Check the endpoint path before the run starts`.
