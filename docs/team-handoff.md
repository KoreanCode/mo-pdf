# 팀 전달 문서

## 목적

이 프로젝트는 PDF 또는 이미지에서 사용자가 지정한 영역만 블러 처리하는 로컬 Flask 앱입니다. 팀원에게는 GitHub 저장소와 `dist/pdf-region-blur-app.zip` 배포본을 함께 전달합니다.

## 전달할 파일

- GitHub 저장소: 소스 코드, 문서, 패키징 스크립트
- `dist/pdf-region-blur-app.zip`: 비개발자 실행용 배포본
- `dist/pdf-region-blur-app/macOS/build_mac_dmg.command`: Mac에서 DMG 생성용 스크립트

## 팀원 실행 경로

Windows:

```text
Windows/start_windows.vbs
```

macOS:

```text
macOS/start_mac.command
```

두 파일 모두 심볼 이미지가 포함된 `O'range PDF Blur` 런처를 엽니다. 런처 버튼은 `서버 실행`, `서버 종료`, `접속하기` 세 가지입니다.

## 개발자가 확인할 명령

```powershell
python -m compileall app.py pdf_blur.py launcher.py
powershell -ExecutionPolicy Bypass -File .\package.ps1
```

JavaScript 변경이 있을 때는 아래도 확인합니다.

```powershell
node --check static/app.js
```

## GitHub 업로드 전 확인

- `.venv`, `node_modules`, `dist`, `logs`, `runtime`, `server.pid`는 커밋하지 않습니다.
- `static` 안의 PNG 이미지는 앱 UI에 필요하므로 커밋합니다.
- macOS DMG는 Mac에서 생성합니다. Windows에서 `package.ps1`을 실행하면 DMG 빌더 스크립트까지만 포함됩니다.
- 배포본을 새로 만들 때 기존 `dist`는 삭제되고 다시 생성됩니다.
