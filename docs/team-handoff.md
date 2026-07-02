# 팀 전달 문서

## 목적

이 프로젝트는 PDF 또는 이미지에서 사용자가 지정한 영역만 블러 처리하는 로컬 Flask 앱입니다. 팀원에게는 GitHub 저장소와 운영체제별 standalone 배포본을 함께 전달합니다.

## 전달할 파일

- GitHub 저장소: 소스 코드, 문서, 패키징 스크립트
- `dist/O-range-PDF-Blur-Windows.zip`: Windows 비개발자 실행용 배포본
- `dist/O-range-PDF-Blur-macOS.dmg`: macOS 비개발자 실행용 배포본

## 팀원 실행 경로

Windows:

```text
Windows/OrangePdfBlur.exe
```

macOS:

```text
O'range PDF Blur.app
```

두 파일 모두 심볼 이미지가 포함된 `O'range PDF Blur` 런처를 엽니다. 런처 버튼은 `서버 실행`, `서버 종료`, `접속하기` 세 가지입니다. 사용자는 Python을 따로 설치하지 않아도 됩니다.

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
- Windows ZIP은 Windows에서, macOS DMG는 Mac에서 생성합니다.
- 배포본을 새로 만들 때 기존 `dist`는 삭제되고 다시 생성됩니다.
