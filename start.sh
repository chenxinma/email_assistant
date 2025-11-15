#!/bin/bash

cd ~/work/python/email_assistant

export CC=/usr/local/gcc-15.2/bin/gcc
export LD_LIBRARY_PATH=/usr/local/gcc-15.2/lib64:$LD_LIBRARY_PATH
export BAILIAN_API_KEY="$OPENAI_API_KEY"
# start otel viewer
$(~/app/go/bin/go env GOPATH)/bin/otel-desktop-viewer --browser-port 8999 > /dev/null 2>&1 & echo $! > otel.pid

# start server
~/app/uv0.9.7/bin/uv run email-assistant --api > ./logs/email-assistant.log 2>&1 & echo $! > email-assistant.pid

sleep 5

~/app/private-assistant-linux-arm64/private-assistant

sleep 2

kill `cat email-assistant.pid`
kill `cat otel.pid`

