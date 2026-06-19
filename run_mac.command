#!/bin/zsh
cd "$(dirname "$0")"

echo "Starting Orange Factory Document Blur..."
echo

if [ -f "server.pid" ]; then
  server_pid="$(cat server.pid)"
  if kill -0 "$server_pid" >/dev/null 2>&1; then
    echo "Server is already running."
    open "http://127.0.0.1:5000"
    echo
    echo "Run stop_mac.command to stop the server."
    read "?Press Enter to close this window."
    exit 0
  fi
  rm -f server.pid
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found."
  echo "Install Python from https://www.python.org/downloads/ and run this again."
  read "?Press Enter to close this window."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv || {
    echo "Failed to create the virtual environment."
    read "?Press Enter to close this window."
    exit 1
  }
fi

echo "Checking required packages..."
".venv/bin/python" -m pip install -r requirements.txt || {
  echo "Package installation failed."
  echo "Check your internet connection and run this again."
  read "?Press Enter to close this window."
  exit 1
}

nohup ".venv/bin/python" app.py > server.out.log 2> server.err.log &
echo $! > server.pid
sleep 1

server_pid="$(cat server.pid)"
if ! kill -0 "$server_pid" >/dev/null 2>&1; then
  echo "The server stopped immediately."
  echo "Check server.err.log for details."
  rm -f server.pid
  read "?Press Enter to close this window."
  exit 1
fi

open "http://127.0.0.1:5000"
echo
echo "Server is running."
echo "http://127.0.0.1:5000"
echo
echo "Run stop_mac.command to stop the server."
read "?Press Enter to close this window."
