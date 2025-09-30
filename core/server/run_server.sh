#!/bin/bash

# Handle Ctrl+C signal
trap 'echo -e "\nShutting down both servers..."; kill $PID_ALPHA $PID_BETA 2>/dev/null; exit 0' SIGINT

echo "Starting Alpha server (port 9011)..."
fastmcp run alpha.py --transport http --port 9011 &
PID_ALPHA=$!

echo "Starting Beta server (port 9012)..."
fastmcp run beta.py --transport http --port 9012 &
PID_BETA=$!

echo "Both servers are running. Press Ctrl+C to terminate."
echo "Alpha PID: $PID_ALPHA"
echo "Beta PID: $PID_BETA"

# Wait until processes terminate
wait