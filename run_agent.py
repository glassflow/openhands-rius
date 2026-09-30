"""Run one OpenHands conversation and send its trace to Rius.

Tracing is configured only through the OTEL_* variables in .env; this file
has no Rius or tracing code in it. OpenHands' built-in tracing picks them up.

    python run_agent.py "create hello.py that prints hi, run it, then finish"
"""

import os
import sys
import tempfile

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool


def tracing_problems(env):
    """The three settings that silently drop every span when wrong."""
    problems = []
    endpoint = env.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "")
    if not endpoint.endswith("/v1/traces"):
        problems.append("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT must end in /v1/traces")
    if env.get("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL") != "http/protobuf":
        problems.append("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL must be http/protobuf (the default is gRPC)")
    problems += [f"unset {key}: a Laminar key overrides the OTEL settings"
                 for key in env if key.startswith("LMNR_")]
    return problems


def main():
    for problem in tracing_problems(os.environ):
        print("tracing:", problem, file=sys.stderr)

    llm = LLM(
        usage_id="agent",
        model=os.getenv("LLM_MODEL", "anthropic/claude-haiku-4-5-20251001"),
        base_url=os.getenv("LLM_BASE_URL") or None,
        api_key=os.environ["LLM_API_KEY"],
    )
    agent = Agent(llm=llm, tools=[Tool(name=TerminalTool.name), Tool(name=FileEditorTool.name)])

    # Without this, Rius names the agent after the script ("run_agent").
    metadata = {"agent.name": os.getenv("AGENT_NAME", "openhands-demo")}
    workspace = tempfile.mkdtemp(prefix="openhands-rius-")
    conversation = Conversation(agent=agent, workspace=workspace, observability_metadata=metadata)

    task = sys.argv[1] if len(sys.argv) > 1 else "Write fib.py that prints the 10th Fibonacci number, run it, then finish."
    conversation.send_message(task)
    conversation.run()
    print("conversation", conversation.id, "finished in", workspace)


if __name__ == "__main__":
    main()
