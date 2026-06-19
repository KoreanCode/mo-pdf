#!/bin/zsh
cd "$(dirname "$0")"

pid_file=""
if [ -f "server.pid" ]; then
  pid_file="server.pid"
elif [ -f "runtime/server.pid" ]; then
  pid_file="runtime/server.pid"
fi

if [ -z "$pid_file" ]; then
  echo "No server.pid found."
  echo "The server may already be stopped."
  read "?Press Enter to close this window."
  exit 0
fi

server_pid="$(cat "$pid_file")"
if kill -0 "$server_pid" >/dev/null 2>&1; then
  kill "$server_pid" >/dev/null 2>&1 || kill -9 "$server_pid" >/dev/null 2>&1
  echo "Server stopped."
else
  echo "Server process was not found."
fi

rm -f server.pid runtime/server.pid
read "?Press Enter to close this window."
