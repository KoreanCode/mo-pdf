# PDF 영역 블러 앱

PDF 또는 이미지 파일을 로컬 브라우저에서 열고, 필요한 영역만 선택해 블러 처리한 새 파일을 내려받는 Flask 기반 도구입니다. 기본 실행 주소는 `http://127.0.0.1:5000`입니다.

## 사용자용 빠른 실행

배포본은 운영체제별로 따로 생성합니다. 사용자는 Python을 따로 설치하지 않아도 됩니다.

```text
Windows: dist/O-range-PDF-Blur-Windows.zip
macOS:   dist/O-range-PDF-Blur-macOS.dmg
```

Windows 사용자는 ZIP 압축을 푼 뒤 `Windows/OrangePdfBlur.exe`를 실행합니다. macOS 사용자는 DMG 안의 `O'range PDF Blur.app`을 실행합니다. 런처에서 `서버 실행`, `접속하기`, `서버 종료`를 사용합니다.

서버는 `127.0.0.1`에서만 실행되며 내 컴퓨터 밖으로 공개되지 않습니다.

## macOS DMG 만들기

DMG 생성은 Mac에서 실행해야 합니다. 빌드용 Mac에는 Python 3.10 이상과 tkinter가 필요하지만, 생성된 DMG를 받는 사용자는 Python이 필요 없습니다.

1. `build_mac_dmg.command`를 실행합니다.
2. PyInstaller가 Python 런타임과 필요한 패키지를 포함한 `.app`을 만듭니다.
3. `O-range-PDF-Blur-macOS.dmg`가 생성됩니다.

서명과 notarization까지 같이 진행하려면 아래 환경변수를 설정한 뒤 실행합니다.

```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: junsoo park (46K42B83U8)"
export APPLE_API_KEY="WPPQWF32X9"
export APPLE_API_ISSUER="43354aeb-0669-4093-9d9d-dc9a1ee72730"
export APPLE_API_KEY_PATH="/Users/planex/Desktop/apple/AuthKey_WPPQWF32X9.p8"
zsh build_mac_dmg.command
```

## 개발 환경 실행

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

macOS 또는 Linux에서는 아래처럼 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

## Windows 배포본 생성

Windows PowerShell에서 실행합니다. 빌드용 Windows PC에는 Python 3.10 이상과 tkinter가 필요하지만, 생성된 ZIP을 받는 사용자는 Python이 필요 없습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1
```

생성 결과:

```text
dist/pdf-region-blur-app-windows/
dist/O-range-PDF-Blur-Windows.zip
```

## GitHub 업로드

현재 저장소에는 배포물, 가상환경, 로그, 런타임 PID 파일, 로컬 도구 흔적이 커밋되지 않도록 `.gitignore`와 `.gitattributes`를 포함했습니다.

새 GitHub 저장소에 처음 올릴 때는 아래 순서로 진행합니다.

```bash
git init
git add .
git commit -m "Initial PDF blur app"
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```

팀 전달 체크리스트는 `docs/team-handoff.md`, 릴리스 절차는 `docs/release-checklist.md`를 확인하세요.
