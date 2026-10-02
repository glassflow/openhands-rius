"""End-to-end check with no network and no model key.

Runs run_agent.py against demo/stuck_llm.py and a local OTLP receiver, then
checks what a Rius ingest endpoint would get: the decoded bearer header, the
agent name, and one TerminalAction span per scripted repeat.

    python tests/smoke_test.py
"""

import gzip
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

ROOT = Path(__file__).resolve().parent.parent
REPEAT = 3
received = {"auth": set(), "spans": [], "attrs": {}}


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Sink(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        received["auth"].add(self.headers.get("Authorization"))
        request = ExportTraceServiceRequest.FromString(body)
        for resource_spans in request.resource_spans:
            for scope_spans in resource_spans.scope_spans:
                for span in scope_spans.spans:
                    received["spans"].append(span.name)
                    for kv in span.attributes:
                        received["attrs"].setdefault(kv.key, set()).add(kv.value.string_value)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def main():
    model_port, sink_port = free_port(), free_port()
    sink = HTTPServer(("127.0.0.1", sink_port), Sink)
    threading.Thread(target=sink.serve_forever, daemon=True).start()
    model = subprocess.Popen([sys.executable, "demo/stuck_llm.py", str(model_port)], cwd=ROOT,
                             env={**os.environ, "REPEAT": str(REPEAT)})
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("LMNR_")},
        "OPENHANDS_SUPPRESS_BANNER": "1",
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": f"http://127.0.0.1:{sink_port}/v1/traces",
        "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL": "http/protobuf",
        "OTEL_EXPORTER_OTLP_TRACES_HEADERS": "Authorization=Bearer%20ri_test",
        "LLM_MODEL": "openai/stuck",
        "LLM_BASE_URL": f"http://127.0.0.1:{model_port}/v1",
        "LLM_API_KEY": "unused",
        "AGENT_NAME": "openhands-smoke-test",
    }
    try:
        subprocess.run([sys.executable, "run_agent.py", "List the files in missing-dir."],
                       cwd=ROOT, env=env, check=True, timeout=300)
    finally:
        model.terminate()
        sink.shutdown()

    terminal_calls = received["spans"].count("TerminalAction")
    checks = {
        "bearer header arrives decoded": received["auth"] == {"Bearer ri_test"},
        "agent name is set": any("openhands-smoke-test" in values for key, values in received["attrs"].items()
                                 if key.endswith("metadata.agent.name")),
        f"{REPEAT} TerminalAction spans": terminal_calls == REPEAT,
        "conversation finishes": "FinishAction" in received["spans"],
    }
    for name, ok in checks.items():
        print("ok  " if ok else "FAIL", name)
    print(f"{len(received['spans'])} spans received, {terminal_calls} TerminalAction")
    if not all(checks.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
