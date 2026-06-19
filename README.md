# PDF 영역 블러 앱

PDF 또는 이미지 파일을 로컬 브라우저에서 열고, 필요한 영역만 선택해 블러 처리한 새 파일을 내려받는 Flask 기반 도구입니다. 기본 실행 주소는 `http://127.0.0.1:5000`입니다.

## 팀원용 빠른 실행

배포본은 `package.ps1` 실행 후 `dist/pdf-region-blur-app.zip`으로 생성됩니다. 압축을 풀면 운영체제별 폴더가 나뉩니다.

```text
pdf-region-blur-app
├─ Windows
│  ├─ start_windows.vbs
│  └─ launcher_windows.bat
├─ macOS
│  ├─ start_mac.command
│  ├─ launcher_mac.command
│  └─ build_mac_dmg.command
├─ README.txt
├─ USER_GUIDE_KO.txt
└─ docs
```

Windows 사용자는 `Windows/start_windows.vbs`를 더블클릭합니다. macOS 사용자는 `macOS/start_mac.command`를 더블클릭합니다. 실행하면 심볼 이미지가 포함된 작은 런처가 열리고, 런처에서 `서버 실행`, `서버 종료`, `접속하기`를 사용할 수 있습니다.

## macOS DMG 만들기

DMG 생성은 macOS의 `hdiutil`이 필요하므로 Mac에서 실행해야 합니다.

1. `package.ps1`로 만든 ZIP을 Mac에서 압축 해제합니다.
2. `macOS/build_mac_dmg.command`를 실행합니다.
3. `O-range-PDF-Blur-macOS.dmg`가 생성됩니다.

DMG 안에는 `.app` 형태의 런처가 들어가며, 앱을 실행하면 사용자 홈의 `~/Library/Application Support/OrangePdfBlur`에 실행 파일을 복사한 뒤 GUI 런처를 엽니다.

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

## 배포본 생성

Windows PowerShell에서 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1
```

생성 결과:

```text
dist/pdf-region-blur-app/
dist/pdf-region-blur-app.zip
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
