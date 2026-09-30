#!/bin/bash
# The OpenHands web app (local GUI) with tracing sent to Rius.
#
# The app runs each agent in its own sandbox container and forwards only
# LLM_* and LMNR_* variables into it. Setting OTEL_* on the app container
# does nothing. OH_AGENT_SERVER_ENV takes a JSON object of extra variables
# for the sandbox, and that is how tracing gets in.
#
# Tested with openhands:latest (agent server 1.36.0). The agent server streams
# model calls, so its traces have no token counts; tools and content arrive.
set -euo pipefail
: "${RIUS_API_KEY:?set RIUS_API_KEY to an ingest key}"

OH_AGENT_SERVER_ENV=$(cat <<EOF
{"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT":"https://ingest.eu.console.rius-glassflow.com/v1/traces",
 "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL":"http/protobuf",
 "OTEL_EXPORTER_OTLP_TRACES_HEADERS":"Authorization=Bearer%20${RIUS_API_KEY}"}
EOF
)

docker run -it --rm --pull=always \
  -e OH_AGENT_SERVER_ENV="$OH_AGENT_SERVER_ENV" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.openhands:/.openhands \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name openhands-app \
  docker.openhands.dev/openhands/openhands:latest
