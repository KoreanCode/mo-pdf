from __future__ import annotations

import os
import signal
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
APP_URL = "http://127.0.0.1:5000"
BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / ".venv"
RUNTIME_DIR = BASE_DIR / "runtime"
LOG_DIR = BASE_DIR / "logs"
PID_FILE = RUNTIME_DIR / "server.pid"
LEGACY_PID_FILE = BASE_DIR / "server.pid"
OUT_LOG = LOG_DIR / "server.out.log"
ERR_LOG = LOG_DIR / "server.err.log"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


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
    for pid_path in (PID_FILE, LEGACY_PID_FILE):
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


def _server_is_ready() -> bool:
    try:
        with urllib.request.urlopen(APP_URL, timeout=0.75) as response:
            return 200 <= response.status < 500
    except (OSError, urllib.error.URLError):
        return False


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
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("430x520")
        self.root.minsize(430, 520)
        self.root.configure(bg="#fff7ed")
        self.root.resizable(False, False)
        self.process: subprocess.Popen[bytes] | None = None
        self.logo_image: tk.PhotoImage | None = None

        self.status_text = tk.StringVar(value="대기 중")
        self.detail_text = tk.StringVar(value="서버 실행을 누르면 로컬 서버를 준비합니다.")

        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg="#fff7ed", padx=24, pady=22)
        container.pack(fill="both", expand=True)

        logo_path = BASE_DIR / "static" / "simbol.png"
        if logo_path.exists():
            image = tk.PhotoImage(file=str(logo_path))
            scale = max(1, max(image.width() // 112, image.height() // 112))
            self.logo_image = image.subsample(scale, scale)
            tk.Label(container, image=self.logo_image, bg="#fff7ed").pack(pady=(2, 14))

        tk.Label(
            container,
            text=APP_NAME,
            bg="#fff7ed",
            fg="#2b2118",
            font=("Segoe UI", 18, "bold"),
        ).pack()

        tk.Label(
            container,
            text="PDF 영역 블러 로컬 서버 런처",
            bg="#fff7ed",
            fg="#6b5a47",
            font=("Segoe UI", 10),
        ).pack(pady=(4, 20))

        status_panel = tk.Frame(container, bg="#ffffff", padx=18, pady=16, highlightthickness=1, highlightbackground="#f0d8be")
        status_panel.pack(fill="x")

        tk.Label(
            status_panel,
            textvariable=self.status_text,
            bg="#ffffff",
            fg="#1f1a17",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            status_panel,
            textvariable=self.detail_text,
            bg="#ffffff",
            fg="#6b5a47",
            justify="left",
            wraplength=340,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(7, 0))

        button_frame = tk.Frame(container, bg="#fff7ed")
        button_frame.pack(fill="x", pady=22)

        self.start_button = tk.Button(
            button_frame,
            text="서버 실행",
            command=self.start_server,
            width=14,
            height=2,
            bg="#f97316",
            fg="#ffffff",
            activebackground="#ea580c",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
        )
        self.start_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.stop_button = tk.Button(
            button_frame,
            text="서버 종료",
            command=self.stop_server,
            width=14,
            height=2,
            bg="#2f2a24",
            fg="#ffffff",
            activebackground="#1f1a17",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
        )
        self.stop_button.grid(row=0, column=1, padx=4, sticky="ew")

        self.open_button = tk.Button(
            button_frame,
            text="접속하기",
            command=self.open_app,
            width=14,
            height=2,
            bg="#138a43",
            fg="#ffffff",
            activebackground="#0f7037",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
        )
        self.open_button.grid(row=0, column=2, padx=(8, 0), sticky="ew")

        for column in range(3):
            button_frame.columnconfigure(column, weight=1)

        tk.Label(
            container,
            text=APP_URL,
            bg="#fff7ed",
            fg="#8a4b12",
            font=("Consolas", 10),
        ).pack(pady=(2, 0))

        tk.Label(
            container,
            text="실행 로그는 logs 폴더에 저장됩니다.",
            bg="#fff7ed",
            fg="#826f5e",
            font=("Segoe UI", 9),
        ).pack(side="bottom", pady=(20, 0))

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.start_button.configure(state=state)
        self.stop_button.configure(state=state)
        self.open_button.configure(state=state)

    def _set_status(self, status: str, detail: str) -> None:
        self.status_text.set(status)
        self.detail_text.set(detail)

    def _refresh_status(self) -> None:
        pid = _read_pid()
        if _server_is_ready():
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
        return python_path

    def start_server(self) -> None:
        self._run_in_thread(self._start_server_worker)

    def _start_server_worker(self) -> None:
        try:
            if _server_is_ready():
                self.root.after(0, self._set_status, "서버 실행 중", "이미 실행 중입니다. 접속하기를 누르세요.")
                return

            python_path = self._ensure_environment()
            LOG_DIR.mkdir(exist_ok=True)
            env = os.environ.copy()
            env.setdefault("PORT", "5000")

            self.root.after(0, self._set_status, "서버 시작 중", "로컬 서버를 실행하고 있습니다.")
            with OUT_LOG.open("a", encoding="utf-8") as out_log, ERR_LOG.open("a", encoding="utf-8") as err_log:
                kwargs: dict[str, object] = {
                    "cwd": BASE_DIR,
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

                self.process = subprocess.Popen([str(python_path), str(BASE_DIR / "app.py")], **kwargs)
            _write_pid(self.process.pid)

            for _ in range(40):
                if self.process.poll() is not None:
                    raise RuntimeError("서버가 바로 종료되었습니다. logs/server.err.log를 확인하세요.")
                if _server_is_ready():
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
        if not _server_is_ready():
            self._set_status("접속 대기", "서버가 아직 실행 중이 아닙니다. 먼저 서버 실행을 누르세요.")
            return
        webbrowser.open(APP_URL)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    LauncherApp().run()
