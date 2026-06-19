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

## 3. ZIP 배포본 생성

```powershell
powershell -ExecutionPolicy Bypass -File .\package.ps1
```

확인할 결과:

```text
dist/pdf-region-blur-app.zip
dist/pdf-region-blur-app/Windows/start_windows.vbs
dist/pdf-region-blur-app/Windows/launcher_windows.bat
dist/pdf-region-blur-app/macOS/start_mac.command
dist/pdf-region-blur-app/macOS/launcher_mac.command
dist/pdf-region-blur-app/macOS/build_mac_dmg.command
```

## 4. macOS DMG 생성

Mac에서 ZIP 압축을 푼 뒤 실행합니다.

```bash
cd macOS
chmod +x build_mac_dmg.command launcher_mac.command start_mac.command
./build_mac_dmg.command
```

생성 결과:

```text
O-range-PDF-Blur-macOS.dmg
```

## 5. GitHub 업로드

```bash
git init
git add .
git commit -m "Initial PDF blur app"
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```
