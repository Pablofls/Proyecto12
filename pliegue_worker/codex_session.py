"""Manage the laboratory worker's CLI session without reading its credential store."""
import os
from pathlib import Path
import re
import subprocess
import threading

DEVICE_URL = "https://auth.openai.com/codex/device"
DEVICE_CODE = re.compile(rb"[A-Z0-9]{3,8}(?:-[A-Z0-9]{3,8}){1,2}")
ANSI = re.compile(rb"\x1b\[[0-9;]*m")


def cli_environment():
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": str(Path.home())}
    if os.environ.get("CODEX_HOME"):
        env["CODEX_HOME"] = os.environ["CODEX_HOME"]
    return env


class CodexSession:
    def __init__(self, executable, directory):
        self.executable = executable
        self.directory = directory
        self.lock = threading.Lock()
        self.owner = self.action = self.code = self.error = None

    def command(self, *args):
        return subprocess.run([self.executable, *args], cwd=self.directory, env=cli_environment(),
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=4, check=False)

    def status(self):
        if not self.executable:
            return "unavailable"
        try:
            result = self.command("login", "status")
        except (OSError, subprocess.TimeoutExpired):
            return "unavailable"
        if result.returncode == 0:
            return "chatgpt" if b"ChatGPT" in result.stdout else "authenticated"
        if any(marker in result.stdout.lower() for marker in (b"session expired", b"token expired", b"token_expired")):
            return "expired"
        return "signed_out" if b"Not logged in" in result.stdout else "unavailable"

    def state(self, owner):
        with self.lock:
            result = {"busy": self.action is not None}
            if self.owner == owner:
                result.update(action=self.action, code=self.code, error=self.error)
                if self.code:
                    result["url"] = DEVICE_URL
            return result

    def start(self, owner, action):
        with self.lock:
            if self.action is not None:
                return False
            self.owner, self.action = owner, action
            self.code = self.error = None
            threading.Thread(target=self.perform, args=(action,), daemon=True).start()
        return True

    def perform(self, action):
        error = None
        try:
            if action == "logout":
                if self.command("logout").returncode != 0:
                    error = "No se pudo cerrar la sesión de Codex."
            elif self.device_login() != 0:
                error = "No se pudo conectar Codex. Comprueba que ChatGPT permita el inicio con código de dispositivo."
        except (OSError, subprocess.TimeoutExpired):
            error = "Codex no pudo completar la operación."
        finally:
            with self.lock:
                self.action, self.code, self.error = None, None, error

    def device_login(self):
        with subprocess.Popen([self.executable, "login", "--device-auth"], cwd=self.directory,
                              env=cli_environment(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT) as process:
            timeout = threading.Timer(900, process.kill)
            timeout.start()
            try:
                official_url = False
                for raw in iter(lambda: process.stdout.readline(4096), b""):
                    line = ANSI.sub(b"", raw).strip()
                    if line == DEVICE_URL.encode():
                        official_url = True
                    elif official_url and DEVICE_CODE.fullmatch(line):
                        with self.lock:
                            self.code = line.decode("ascii")
                        official_url = False
                return process.wait()
            finally:
                timeout.cancel()
