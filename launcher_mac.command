#!/bin/zsh
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display dialog "Python 3가 필요합니다. python.org에서 Python 3를 설치한 뒤 다시 실행하세요." buttons {"OK"} with icon caution'
  exit 1
fi

python3 launcher.py
