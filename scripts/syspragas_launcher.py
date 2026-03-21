from __future__ import annotations

import os
import socket
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn


HOST = "127.0.0.1"
PORT = 8000
APP_URL = f"http://{HOST}:{PORT}/app"
HEALTH_URL = f"http://{HOST}:{PORT}/health"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def local_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(app_root())
    target = Path(base) / "SysPragas"
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_runtime_environment() -> None:
    data_dir = local_data_dir()
    db_path = data_dir / "syspragas.db"
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    os.environ.setdefault("PYTHONUTF8", "1")


def is_server_responding(timeout: float = 0.75) -> bool:
    try:
        with urlopen(HEALTH_URL, timeout=timeout) as response:
            return response.status == 200
    except URLError:
        return False


def is_port_busy() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.4)
        return connection.connect_ex((HOST, PORT)) == 0


class LauncherApp:
    def __init__(self) -> None:
        self.server_thread: threading.Thread | None = None
        self.server_instance: uvicorn.Server | None = None
        self.root = tk.Tk()
        self.root.title("SysPragas 3.1 - Teste")
        self.root.geometry("460x280")
        self.root.resizable(False, False)
        self.status_var = tk.StringVar(value="Preparando ambiente...")
        self.url_var = tk.StringVar(value=APP_URL)
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(150, self.bootstrap)

    def _build_ui(self) -> None:
        wrapper = tk.Frame(self.root, padx=24, pady=20)
        wrapper.pack(fill="both", expand=True)

        tk.Label(
            wrapper,
            text="SysPragas 3.1",
            font=("Segoe UI Semibold", 20),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            wrapper,
            text="Launcher de teste do sistema",
            font=("Segoe UI", 10),
            fg="#4b5b50",
            anchor="w",
        ).pack(fill="x", pady=(4, 18))

        status_card = tk.LabelFrame(wrapper, text="Status", padx=14, pady=12)
        status_card.pack(fill="x")

        tk.Label(
            status_card,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            justify="left",
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            status_card,
            textvariable=self.url_var,
            font=("Consolas", 10),
            fg="#1f4a38",
            anchor="w",
        ).pack(fill="x", pady=(8, 0))

        actions = tk.Frame(wrapper, pady=18)
        actions.pack(fill="x")

        self.open_button = tk.Button(actions, text="Abrir sistema", command=self.open_app, width=18)
        self.open_button.grid(row=0, column=0, padx=(0, 10), pady=6, sticky="ew")

        self.docs_button = tk.Button(actions, text="Abrir docs", command=self.open_docs, width=18)
        self.docs_button.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="ew")

        self.restart_button = tk.Button(actions, text="Reiniciar servidor", command=self.restart_server, width=18)
        self.restart_button.grid(row=1, column=0, padx=(0, 10), pady=6, sticky="ew")

        self.close_button = tk.Button(actions, text="Fechar launcher", command=self.on_close, width=18)
        self.close_button.grid(row=1, column=1, padx=(0, 10), pady=6, sticky="ew")

        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        tk.Label(
            wrapper,
            text="Banco local salvo em %LOCALAPPDATA%\\SysPragas\\syspragas.db",
            font=("Segoe UI", 9),
            fg="#66756a",
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

    def bootstrap(self) -> None:
        ensure_runtime_environment()
        self.start_server(open_browser=True)

    def start_server(self, open_browser: bool = False) -> None:
        if is_server_responding():
            self.status_var.set("Servidor ja estava ativo. Sistema pronto para uso.")
            if open_browser:
                self.open_app()
            return

        if is_port_busy():
            self.status_var.set("A porta 8000 esta em uso por outro processo. Libere a porta para continuar.")
            messagebox.showwarning("SysPragas", "A porta 8000 esta ocupada por outro processo.")
            return

        config = uvicorn.Config(
            "app.main:app",
            host=HOST,
            port=PORT,
            log_level="warning",
            reload=False,
        )
        self.server_instance = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.server_instance.run, daemon=True)
        self.server_thread.start()
        self.status_var.set("Subindo servidor local do SysPragas...")
        self._wait_until_ready(open_browser=open_browser)

    def _wait_until_ready(self, open_browser: bool) -> None:
        for _ in range(60):
            if is_server_responding():
                self.status_var.set("Servidor ativo. Clique em Abrir sistema para usar.")
                if open_browser:
                    self.open_app()
                return
            self.root.update()
            time.sleep(0.25)
        self.status_var.set("Nao foi possivel iniciar o servidor local.")
        messagebox.showerror("SysPragas", "Falha ao iniciar o servidor local.")

    def restart_server(self) -> None:
        self.stop_server()
        self.start_server(open_browser=False)

    def stop_server(self) -> None:
        if self.server_instance:
            self.status_var.set("Encerrando servidor local...")
            self.server_instance.should_exit = True
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)
        self.server_instance = None
        self.server_thread = None

    def open_app(self) -> None:
        webbrowser.open(APP_URL)

    def open_docs(self) -> None:
        webbrowser.open(f"http://{HOST}:{PORT}/docs")

    def on_close(self) -> None:
        self.stop_server()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    LauncherApp().run()
