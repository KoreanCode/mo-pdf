#!/bin/zsh
cd "$(dirname "$0")"

export SYSTEM_VERSION_COMPAT=0
export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Library/Frameworks/Python.framework/Versions/3.12/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

find_python() {
  local candidate
  for candidate in \
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3"
  do
    if [[ -x "$candidate" ]] && check_python "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done

  candidate="$(command -v python3 || true)"
  if [[ -n "$candidate" && "$candidate" != "/usr/bin/python3" ]] && check_python "$candidate"; then
    echo "$candidate"
    return 0
  fi

  return 1
}

is_arm64_mac() {
  [[ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" == "1" ]]
}

check_python() {
  if is_arm64_mac; then
    /usr/bin/arch -arm64 "$1" -c 'import tkinter' >/dev/null 2>&1
  else
    "$1" -c 'import tkinter' >/dev/null 2>&1
  fi
}

run_python() {
  if is_arm64_mac; then
    exec /usr/bin/arch -arm64 "$@"
  fi
  exec "$@"
}

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  osascript -e 'display dialog "Python 3가 필요합니다. python.org 또는 Homebrew로 Python 3를 설치한 뒤 다시 실행하세요." buttons {"OK"} with icon caution'
  exit 1
fi

run_python "$PYTHON_BIN" launcher.py
