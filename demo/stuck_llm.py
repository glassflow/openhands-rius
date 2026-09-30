"""A scripted, OpenAI-compatible model that gets stuck on purpose.

It asks for the same terminal command REPEAT times, then finishes. That is
the shape of a real stuck agent (the same call, over and over, making no
progress) without spending tokens. Run it, point run_agent.py at it, and
Rius's Tool Loop alert fires on the trace.

    python demo/stuck_llm.py 9901 &
    LLM_MODEL=openai/stuck LLM_BASE_URL=http://127.0.0.1:9901/v1 LLM_API_KEY=unused \
      python run_agent.py

Env: REPEAT (default 4).
"""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9901
REPEAT = int(os.getenv("REPEAT", "4"))
COMMAND = "ls missing-dir"


def offered(tools, name):
    names = [t["function"]["name"] for t in tools]
    if name not in names:
        raise SystemExit(f"{name!r} not in offered tools {names}")
    return name


def tool_call(name, arguments, n):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": f"call_{n}",
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)},
        }],
    }


def reply(request):
    tools = request.get("tools") or []
    done = sum(1 for m in request["messages"] if m.get("role") == "tool")
    if done < REPEAT:
        message = tool_call(offered(tools, "terminal"),
                            {"command": COMMAND, "summary": "Look again", "security_risk": "LOW"}, done)
    else:
        message = tool_call(offered(tools, "finish"),
                            {"message": "Gave up.", "summary": "Finish", "security_risk": "LOW"}, done)
    return {
        "id": f"chatcmpl-stuck-{done}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.get("model", "stuck"),
        "choices": [{"index": 0, "message": message, "finish_reason": "tool_calls"}],
        "usage": {"prompt_tokens": 1200 + 150 * done, "completion_tokens": 30,
                  "total_tokens": 1230 + 150 * done},
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        out = json.dumps(reply(body)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, fmt, *args):
        pass


HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
