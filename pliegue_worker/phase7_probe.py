"""Trusted probe. Runs exclusively in Bubblewrap with synthetic HTTP contracts."""
import ctypes
import errno
import io
import json
import sys
import urllib.error
import urllib.parse

sys.path[:0] = ["/deps", "/workspace/apps/web", "/workspace"]

from flask import Flask
from app import api_client

BASE = "/estadisticas/devoluciones/"
FIXTURE_JWT = "jwt-ficticio-prueba-contrato"


def restrict():
    sec = ctypes.CDLL("libseccomp.so.2")
    sec.seccomp_init.argtypes, sec.seccomp_init.restype = [ctypes.c_uint32], ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    sec.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    sec.seccomp_load.argtypes = [ctypes.c_void_p]
    sec.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = sec.seccomp_init(0x7FFF0000)
    if not ctx:
        raise RuntimeError("seccomp")
    try:
        for name in b"socket socketpair clone clone3 fork vfork execve execveat unshare setns ptrace".split():
            number = sec.seccomp_syscall_resolve_name(name)
            if number >= 0 and sec.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0):
                raise RuntimeError("seccomp")
        if sec.seccomp_load(ctx):
            raise RuntimeError("seccomp")
    finally:
        sec.seccomp_release(ctx)


def probe(data):
    from app.blueprints.returns_dashboard import bp

    app = Flask(__name__, template_folder="/workspace/apps/web/app/templates")
    app.config.update(SECRET_KEY="local-fixture", USE_MICROSERVICES=True, MICROSERVICE_TIMEOUT=1,
                      SERVICE_URLS={"devoluciones": "http://fixture.invalid"}, ORVIA_DASHBOARD_FRAGMENT=True)
    app.register_blueprint(bp)
    calls = []

    def upstream(request, timeout, strict):
        url = urllib.parse.urlsplit(request.full_url)
        args = urllib.parse.parse_qs(url.query)
        calls.append([request.get_method(), url.path, request.get_header("Authorization"), args, timeout, strict])
        mode = data.get("mode")
        if mode == "timeout":
            raise TimeoutError
        if mode == "forbidden":
            raise urllib.error.HTTPError(request.full_url, 403, "forbidden", {}, io.BytesIO(b"{}"))
        page = int(args["pagina"][0])
        rows = [row for row in data["rows"] if not args.get("estado") or row["estado"] == args["estado"][0]]
        total = len(rows) if mode != "excess" else 501
        if mode == "changed" and page == 2:
            total += 1
        response = {"datos": rows[(page - 1) * 100:page * 100],
                    "paginacion": {"pagina": page, "por_pagina": 100, "total": total, "paginas": (total + 99)//100}}
        if mode == "malformed":
            response = {"datos": 1}
        return io.BytesIO(json.dumps(response).encode())

    # The actual app.api_client calls this transport: no service or token is real.
    api_client._open_response = upstream
    with app.test_client() as client:
        if data.get("role"):
            with client.session_transaction() as session:
                session["usuario"] = {"rol": data["role"], "id": 1}
                if not data.get("no_token"):
                    session["access_token"] = FIXTURE_JWT
        results = []
        for path in data["paths"]:
            calls.clear()
            response = client.get(BASE + path)
            results.append({"status": response.status_code, "json": response.get_json(silent=True),
                            "html": response.get_data(as_text=True) if path == "" else "", "calls": list(calls)})
        return results


if __name__ == "__main__":
    requests = json.load(sys.stdin)
    restrict()
    print(json.dumps([probe(case) for case in requests]))
