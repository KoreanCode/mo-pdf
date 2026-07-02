from __future__ import annotations

import os
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import messagebox
import tkinter as tk


APP_NAME = "O'range PDF Blur"
APP_HOST = "127.0.0.1"
APP_HEALTH_RESPONSE = "orange-pdf-blur"
DEFAULT_PORT = int(os.environ.get("PORT", "5000"))
FROZEN = bool(getattr(sys, "frozen", False))


def _resource_dir() -> Path:
    if FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


BASE_DIR = _resource_dir()


def _state_dir() -> Path:
    if not FROZEN:
        return BASE_DIR
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "OrangePdfBlur"
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "OrangePdfBlur"
        return Path.home() / "AppData" / "Local" / "OrangePdfBlur"
    return Path.home() / ".orange-pdf-blur"


STATE_DIR = _state_dir()
VENV_DIR = BASE_DIR / ".venv"
RUNTIME_DIR = STATE_DIR / "runtime"
LOG_DIR = STATE_DIR / "logs"
PID_FILE = RUNTIME_DIR / "server.pid"
PORT_FILE = RUNTIME_DIR / "server.port"
LEGACY_PID_FILE = STATE_DIR / "server.pid"
OUT_LOG = LOG_DIR / "server.out.log"
ERR_LOG = LOG_DIR / "server.err.log"
FONT_FAMILY = "Apple SD Gothic Neo" if sys.platform == "darwin" else "Segoe UI"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _app_url(port: int) -> str:
    return f"http://{APP_HOST}:{port}"


def _read_port() -> int:
    try:
        raw_port = PORT_FILE.read_text(encoding="ascii").strip()
        port = int(raw_port)
    except (OSError, ValueError):
        return DEFAULT_PORT
    if 1 <= port <= 65535:
        return port
    return DEFAULT_PORT


def _write_port(port: int) -> None:
    RUNTIME_DIR.mkdir(exist_ok=True)
    PORT_FILE.write_text(str(port), encoding="ascii")


def _read_pid() -> int | None:
    for pid_path in (PID_FILE, LEGACY_PID_FILE):
        try:
            raw_pid = pid_path.read_text(encoding="ascii").strip()
        except OSError:
            continue
        if raw_pid.isdigit():
            return int(raw_pid)
    return None


def _write_pid(pid: int) -> None:
    RUNTIME_DIR.mkdir(exist_ok=True)
    PID_FILE.write_text(str(pid), encoding="ascii")
    LEGACY_PID_FILE.write_text(str(pid), encoding="ascii")


def _clear_pid() -> None:
    for pid_path in (PID_FILE, LEGACY_PID_FILE, PORT_FILE):
        try:
            pid_path.unlink()
        except FileNotFoundError:
            pass


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _server_is_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"{_app_url(port)}/healthz", timeout=0.75) as response:
            if response.status != 200:
                return False
            return response.read().decode("utf-8").strip() == APP_HEALTH_RESPONSE
    except (OSError, urllib.error.URLError):
        return False


def _find_available_port(start_port: int) -> int:
    for port in range(start_port, min(start_port + 100, 65536)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((APP_HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError("사용 가능한 로컬 포트를 찾지 못했습니다.")


def _environment_is_usable(python_path: Path) -> bool:
    if not python_path.exists():
        return False
    result = subprocess.run(
        [
            str(python_path),
            "-c",
            "import flask, fitz; from PIL import Image",
        ],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _terminate_pid(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return

    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return

    for _ in range(20):
        if not _pid_is_alive(pid):
            return
        time.sleep(0.1)

    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


class LauncherApp:
    def __init__(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("500x620")
        self.root.minsize(500, 620)
        self.root.configure(bg="#fff7f0")
        self.root.resizable(False, False)
        self.process: subprocess.Popen[bytes] | None = None
        self.logo_image: tk.PhotoImage | None = None
        self.port = _read_port()

        self.status_text = tk.StringVar(value="대기 중")
        self.detail_text = tk.StringVar(value="서버 실행을 누르면 로컬 서버를 준비합니다.")
        self.url_text = tk.StringVar(value=_app_url(self.port))

        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg="#fff7f0", padx=34, pady=28)
        container.pack(fill="both", expand=True)

        logo_path = BASE_DIR / "static" / "simbol_2.png"
        if logo_path.exists():
            image = tk.PhotoImage(file=str(logo_path))
            scale = max(1, max(image.width() // 74, image.height() // 74))
            self.logo_image = image.subsample(scale, scale)
            tk.Label(
                container,
                image=self.logo_image,
                bg="#fff7f0",
                borderwidth=0,
                highlightthickness=0,
            ).pack(pady=(0, 18))

        tk.Frame(container, bg="#ff7e12", height=4, width=42).pack(pady=(0, 16))

        tk.Label(
            container,
            text=APP_NAME,
            bg="#fff7f0",
            fg="#282625",
            font=(FONT_FAMILY, 24, "bold"),
            borderwidth=0,
            highlightthickness=0,
        ).pack()

        tk.Label(
            container,
            text="PDF 영역 블러 로컬 도구",
            bg="#fff7f0",
            fg="#6b6461",
            font=(FONT_FAMILY, 12),
            borderwidth=0,
            highlightthickness=0,
        ).pack(pady=(6, 28))

        status_panel = tk.Frame(container, bg="#fff7f0", padx=0, pady=0, highlightthickness=0, borderwidth=0)
        status_panel.pack(fill="x")

        tk.Label(
            status_panel,
            textvariable=self.status_text,
            bg="#fff7f0",
            fg="#282625",
            font=(FONT_FAMILY, 18, "bold"),
            borderwidth=0,
            highlightthickness=0,
        ).pack(anchor="w")
        tk.Label(
            status_panel,
            textvariable=self.detail_text,
            bg="#fff7f0",
            fg="#6b6461",
            justify="left",
            wraplength=420,
            font=(FONT_FAMILY, 11),
            borderwidth=0,
            highlightthickness=0,
        ).pack(anchor="w", pady=(8, 0))

        tk.Frame(container, bg="#ffdfc4", height=1).pack(fill="x", pady=(22, 16))

        url_panel = tk.Frame(container, bg="#fff7f0", padx=0, pady=0, highlightthickness=0, borderwidth=0)
        url_panel.pack(fill="x")

        tk.Label(
            url_panel,
            text="접속 주소",
            bg="#fff7f0",
            fg="#893f00",
            font=(FONT_FAMILY, 10, "bold"),
            borderwidth=0,
            highlightthickness=0,
        ).pack(anchor="w")
        tk.Label(
            url_panel,
            textvariable=self.url_text,
            bg="#fff7f0",
            fg="#282625",
            font=("Menlo", 12, "bold"),
            borderwidth=0,
            highlightthickness=0,
        ).pack(anchor="w", pady=(4, 0))

        button_frame = tk.Frame(container, bg="#fff7f0")
        button_frame.pack(fill="x", pady=26)

        self.start_button = self._make_action_button(
            button_frame,
            text="서버 실행",
            command=self.start_server,
            bg="#ff7e12",
            activebg="#ff9843",
        )
        self.start_button.pack(fill="x", pady=(0, 12))

        self.open_button = self._make_action_button(
            button_frame,
            text="접속하기",
            command=self.open_app,
            bg="#ffecdc",
            activebg="#ffdfc4",
        )
        self.open_button.pack(fill="x", pady=(0, 12))

        self.stop_button = self._make_action_button(
            button_frame,
            text="서버 종료",
            command=self.stop_server,
            bg="#ffffff",
            activebg="#f5f4f4",
        )
        self.stop_button.pack(fill="x")

        tk.Label(
            container,
            text="실행 로그는 logs 폴더에 저장됩니다.",
            bg="#fff7f0",
            fg="#918a87",
            font=(FONT_FAMILY, 9),
            borderwidth=0,
            highlightthickness=0,
        ).pack(side="bottom", pady=(20, 0))

    def _make_action_button(self, parent: tk.Frame, *, text: str, command, bg: str, activebg: str) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            height=2,
            bg=bg,
            fg="#282625",
            activebackground=activebg,
            activeforeground="#282625",
            disabledforeground="#918a87",
            font=(FONT_FAMILY, 14, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.start_button.configure(state=state)
        self.stop_button.configure(state=state)
        self.open_button.configure(state=state)

    def _set_status(self, status: str, detail: str) -> None:
        self.status_text.set(status)
        self.detail_text.set(detail)

    def _set_port(self, port: int) -> None:
        self.port = port
        self.url_text.set(_app_url(port))

    def _refresh_status(self) -> None:
        pid = _read_pid()
        saved_port = _read_port()
        if saved_port != self.port and _server_is_ready(saved_port):
            self._set_port(saved_port)

        if _server_is_ready(self.port):
            self._set_status("서버 실행 중", "브라우저에서 접속할 수 있습니다.")
        elif pid and not _pid_is_alive(pid):
            _clear_pid()
            self._set_status("대기 중", "서버 실행을 누르면 로컬 서버를 준비합니다.")
        else:
            self._set_status("대기 중", "서버 실행을 누르면 로컬 서버를 준비합니다.")

    def _run_in_thread(self, target) -> None:
        self._set_busy(True)
        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _ensure_environment(self) -> Path:
        if FROZEN:
            return Path(sys.executable)

        python_path = _venv_python()
        if python_path.exists() and not _environment_is_usable(python_path):
            self.root.after(0, self._set_status, "처음 실행 준비 중", "기존 Python 가상환경을 다시 만들고 있습니다.")
            shutil.rmtree(VENV_DIR, ignore_errors=True)
            python_path = _venv_python()

        if not python_path.exists():
            self.root.after(0, self._set_status, "처음 실행 준비 중", "Python 가상환경을 만들고 있습니다.")
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], cwd=BASE_DIR, check=True)

        self.root.after(0, self._set_status, "처음 실행 준비 중", "필요한 패키지를 확인하고 있습니다.")
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if not _environment_is_usable(python_path):
            raise RuntimeError("Python 패키지 설치 후에도 실행 환경을 확인하지 못했습니다.")
        return python_path

    def _server_command(self) -> list[str]:
        if FROZEN:
            return [sys.executable, "--server"]

        python_path = self._ensure_environment()
        return [str(python_path), str(BASE_DIR / "app.py")]

    def start_server(self) -> None:
        self._run_in_thread(self._start_server_worker)

    def _start_server_worker(self) -> None:
        try:
            if _server_is_ready(self.port):
                self.root.after(0, self._set_status, "서버 실행 중", "이미 실행 중입니다. 접속하기를 누르세요.")
                return

            server_command = self._server_command()
            LOG_DIR.mkdir(exist_ok=True)
            port = _find_available_port(DEFAULT_PORT)
            self.root.after(0, self._set_port, port)
            env = os.environ.copy()
            env["PORT"] = str(port)

            self.root.after(0, self._set_status, "서버 시작 중", "로컬 서버를 실행하고 있습니다.")
            with OUT_LOG.open("a", encoding="utf-8") as out_log, ERR_LOG.open("a", encoding="utf-8") as err_log:
                kwargs: dict[str, object] = {
                    "cwd": STATE_DIR if FROZEN else BASE_DIR,
                    "stdout": out_log,
                    "stderr": err_log,
                    "env": env,
                }
                if os.name == "nt":
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
                        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
                    )
                    kwargs["creationflags"] = creationflags
                else:
                    kwargs["start_new_session"] = True

                self.process = subprocess.Popen(server_command, **kwargs)
            _write_pid(self.process.pid)
            _write_port(port)

            for _ in range(40):
                if self.process.poll() is not None:
                    raise RuntimeError("서버가 바로 종료되었습니다. logs/server.err.log를 확인하세요.")
                if _server_is_ready(port):
                    self.root.after(0, self._set_status, "서버 실행 중", "브라우저에서 접속할 수 있습니다.")
                    return
                time.sleep(0.25)

            raise TimeoutError("서버 응답을 확인하지 못했습니다. logs/server.err.log를 확인하세요.")
        except Exception as exc:
            _clear_pid()
            self.root.after(0, self._set_status, "실행 실패", str(exc))
            self.root.after(0, messagebox.showerror, APP_NAME, str(exc))
        finally:
            self.root.after(0, self._set_busy, False)

    def stop_server(self) -> None:
        self._run_in_thread(self._stop_server_worker)

    def _stop_server_worker(self) -> None:
        try:
            pid = _read_pid()
            if self.process and self.process.poll() is None:
                pid = self.process.pid

            if not pid:
                self.root.after(0, self._set_status, "종료할 서버 없음", "실행 중인 서버 정보를 찾지 못했습니다.")
                return

            self.root.after(0, self._set_status, "서버 종료 중", "서버 프로세스를 정리하고 있습니다.")
            _terminate_pid(pid)
            _clear_pid()
            self.process = None
            self.root.after(0, self._set_status, "서버 종료됨", "필요하면 다시 서버 실행을 누르세요.")
        except Exception as exc:
            self.root.after(0, self._set_status, "종료 실패", str(exc))
            self.root.after(0, messagebox.showerror, APP_NAME, str(exc))
        finally:
            self.root.after(0, self._set_busy, False)

    def open_app(self) -> None:
        if not _server_is_ready(self.port):
            self._set_status("접속 대기", "서버가 아직 실행 중이 아닙니다. 먼저 서버 실행을 누르세요.")
            return
        webbrowser.open(_app_url(self.port))

    def run(self) -> None:
        self.root.mainloop()


def run_server() -> None:
    import socket as socket_module

    from app import APP_HOST as SERVER_HOST
    from app import APP_PORT as SERVER_PORT
    from app import WORK_ROOT, _cleanup_old_uploads, app

    original_getfqdn = socket_module.getfqdn

    def local_getfqdn(name: str = "") -> str:
        if name in ("", SERVER_HOST, "127.0.0.1", "localhost"):
            return "localhost"
        return original_getfqdn(name)

    socket_module.getfqdn = local_getfqdn
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    _cleanup_old_uploads()
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)


def main() -> None:
    if "--server" in sys.argv:
        run_server()
        return
    LauncherApp().run()


if __name__ == "__main__":
    main()
