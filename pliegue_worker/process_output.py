"""Bounded process I/O for the Unix worker."""
import os
import selectors
import signal
import subprocess
import time
from contextvars import ContextVar

EXECUTION = ContextVar("pliegue_execution", default=None)


class ExecutionCancelled(Exception):
    pass


def check_cancelled():
    execution = EXECUTION.get()
    if execution and execution.cancelled():
        raise ExecutionCancelled


def kill_session(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_render(command, *, input, timeout, **options):
    """Entregar el payload completo con EOF; conservar timeout y matar el grupo."""
    check_cancelled()
    with subprocess.Popen(command, stdin=subprocess.PIPE, start_new_session=True, **options) as process:
        try:
            process.communicate(input=input, timeout=timeout)
            check_cancelled()
            return process.returncode
        finally:
            kill_session(process)


CHUNK_BYTES = 64 * 1024
TAIL_BYTES = 12_000
SANDBOX_FILE_BYTES = 8 * 1024**2
CODEX_MAX_FILE_BYTES = 32 * 1024**2


def codex_file_limit():
    try:
        configured = int(os.environ.get("PLIEGUE_CODEX_FILE_BYTES", CODEX_MAX_FILE_BYTES))
    except ValueError:
        configured = CODEX_MAX_FILE_BYTES
    return max(SANDBOX_FILE_BYTES, min(configured, CODEX_MAX_FILE_BYTES))


def limit(name, default, maximum):
    try:
        return max(65536, min(int(os.environ.get(name, default)), maximum))
    except ValueError:
        return default


class ProcessOutput:
    def __init__(self, timeout, prompt):
        self.deadline = time.monotonic() + timeout
        self.pending = memoryview(prompt.encode(errors="replace") if prompt else b"")
        self.jsonl = prompt is not None
        self.tail = bytearray()
        self.stderr_diagnostic = ""
        self.expired = False
        self.error = ""
        self.oversized = False
        self.log_limit = limit("PLIEGUE_LOG_BYTES", 64 * 1024**2, 256 * 1024**2)
        self.line_limit = limit("PLIEGUE_JSONL_LINE_BYTES", 1024**2, 4 * 1024**2)

    def remaining(self):
        return max(0, self.deadline - time.monotonic())

    def records(self, process, diagnostic):
        lines = {process.stdout: bytearray(), process.stderr: bytearray()}
        dropping = set()
        total = 0
        with selectors.DefaultSelector() as selector:
            for stream in (process.stdout, process.stderr):
                selector.register(stream, selectors.EVENT_READ)
            if process.stdin:
                os.set_blocking(process.stdin.fileno(), False)
                selector.register(process.stdin, selectors.EVENT_WRITE)
            while selector.get_map():
                check_cancelled()
                remaining = self.remaining()
                if not remaining:
                    self.expired = True
                    return
                for key, _ in selector.select(min(remaining, 0.25) if EXECUTION.get() else remaining):
                    stream = key.fileobj
                    if stream is process.stdin:
                        try:
                            self.pending = self.pending[os.write(key.fd, self.pending[:CHUNK_BYTES]):]
                        except BlockingIOError:
                            continue
                        except BrokenPipeError:
                            self.pending = self.pending[:0]
                        if not self.pending:
                            selector.unregister(stream)
                            stream.close()
                        continue
                    chunk = os.read(key.fd, CHUNK_BYTES)
                    line = lines[stream]
                    if not chunk:
                        selector.unregister(stream)
                        if self.jsonl and stream is process.stderr:
                            self.stderr_diagnostic = self.stderr_diagnostic or diagnostic(
                                line.decode("utf-8", errors="replace"))
                        elif line:
                            yield bytes(line)
                        continue
                    total += len(chunk)
                    if total > self.log_limit:
                        self.error = f"La salida del proceso superó el límite de {self.log_limit} bytes."
                        return
                    if not self.jsonl:
                        self.tail.extend(chunk)
                        del self.tail[:-TAIL_BYTES]
                        continue
                    stderr = stream is process.stderr
                    if stderr and self.stderr_diagnostic:
                        continue
                    record_limit = TAIL_BYTES if stderr else self.line_limit
                    parts = chunk.split(b"\n")
                    for index, part in enumerate(parts):
                        if stream not in dropping:
                            if len(line) + len(part) <= record_limit:
                                line.extend(part)
                            else:
                                dropping.add(stream)
                                if stderr:
                                    line.extend(part[:record_limit - len(line)])
                                else:
                                    self.oversized = True
                                    line.clear()
                        if index < len(parts) - 1:
                            if stderr:
                                self.stderr_diagnostic = self.stderr_diagnostic or diagnostic(
                                    line.decode("utf-8", errors="replace"))
                            elif line.strip():
                                yield bytes(line)
                            line.clear()
                            dropping.discard(stream)

    def run(self, command, cwd, env, parse, diagnostic):
        check_cancelled()
        # Pipes keep streaming output outside the per-file limit enforced by prlimit.
        file_bytes = codex_file_limit() if self.jsonl else SANDBOX_FILE_BYTES
        with subprocess.Popen(
            ["/usr/bin/prlimit", f"--fsize={file_bytes}", "--", *command],
            cwd=cwd, env=env, stdin=subprocess.PIPE if self.pending else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        ) as process:
            try:
                with_records = self.records(process, diagnostic)
                try:
                    if self.jsonl:
                        result = parse(with_records)
                    else:
                        for _ in with_records:
                            pass
                        result = {"output": self.tail.decode("utf-8", errors="replace")}
                finally:
                    with_records.close()
                while not self.expired and not self.error:
                    check_cancelled()
                    try:
                        process.wait(timeout=min(self.remaining(), 0.25) if EXECUTION.get() else self.remaining())
                        break
                    except subprocess.TimeoutExpired:
                        self.expired = not self.remaining()
            finally:
                kill_session(process)
        code = process.returncode
        if self.expired:
            self.error = "Codex agotó su tiempo." if self.jsonl else "Las pruebas agotaron su tiempo."
        elif not self.error and code == -signal.SIGXFSZ:
            self.error = f"Se superó el límite de escritura por archivo de {file_bytes} bytes (SIGXFSZ)."
        elif not self.error and self.jsonl:
            prior = result["diagnostic"]
            if self.stderr_diagnostic and (code or not result["turn_completed"]):
                self.error = self.stderr_diagnostic
            elif code and (not prior or prior.startswith("Codex no confirmó")):
                self.error = (f"Codex terminó por la señal {-code}." if code < 0
                              else f"Codex terminó con código {code}.")
        if self.jsonl:
            if self.stderr_diagnostic and self.stderr_diagnostic not in result["warnings"]:
                result["warnings"].append(self.stderr_diagnostic)
            if self.oversized:
                warning = f"La salida de Codex incluyó un registro JSONL superior a {self.line_limit} bytes."
                result["warnings"].append(warning)
                if not result["diagnostic"]:
                    result["diagnostic"] = warning
            if self.error:
                result["diagnostic"] = self.error
        elif self.error:
            result["output"] = (result["output"] + "\n" + self.error).strip()
            code = code or 1
        return {"exit_code": None if self.expired else code, "timed_out": self.expired, **result}
