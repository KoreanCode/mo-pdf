# 릴리스 체크리스트

## 1. 소스 확인

- `README.md`가 최신 실행 방법을 설명합니다.
- `USER_GUIDE_KO.md`가 런처 버튼과 OS별 실행 방법을 설명합니다.
- `docs/team-handoff.md`가 팀 전달 경로를 설명합니다.
- `.gitignore`가 배포물, 가상환경, 로그, 런타임 파일을 제외합니다.

## 2. 로컬 검증

```powershell
python -m compileall app.py pdf_blur.py launcher.py
node --check static/app.js
```

## 3. Windows ZIP 배포본 생성

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1
```

확인할 결과:

```text
dist/O-range-PDF-Blur-Windows.zip
dist/pdf-region-blur-app-windows/Windows/OrangePdfBlur.exe
dist/pdf-region-blur-app-windows/Windows/_internal
```

## 4. macOS DMG 생성

Mac에서 실행합니다.

```bash
chmod +x build_mac_dmg.command
zsh build_mac_dmg.command
```

생성 결과:

```text
dist/O-range-PDF-Blur-macOS.dmg
```

서명과 notarization까지 함께 진행할 때는 `APPLE_SIGNING_IDENTITY`, `APPLE_API_KEY`, `APPLE_API_ISSUER`, `APPLE_API_KEY_PATH`를 설정한 뒤 실행합니다.

## 5. GitHub 업로드

```bash
git init
git add .
git commit -m "Initial PDF blur app"
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```
