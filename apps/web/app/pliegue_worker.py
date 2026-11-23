"""Cliente privado de Pliegue. La identidad se verifica con SO_PEERCRED de Linux."""
import http.client
import json
import os
import socket
import struct

from flask import current_app


class WorkerConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("pliegue-worker", timeout=10)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)
        peer = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        _, uid, _ = struct.unpack("3i", peer)
        if uid != os.getuid():
            raise PermissionError("UID inesperado en el socket de Pliegue")


def worker_request(method, path, owner, payload=None):
    sock_path = current_app.config.get("PLIEGUE_WORKER_SOCKET") or os.environ.get("PLIEGUE_WORKER_SOCKET")
    if not sock_path:
        return {"error": "Configura el socket del worker local de Pliegue."}, 503
    connection = WorkerConnection(sock_path)
    try:
        connection.request(method, path, None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                           {"X-Pliegue-Owner": owner, "Content-Type": "application/json"})
        response = connection.getresponse()
        body = response.read(2_000_001)
        if len(body) > 2_000_000 or response.status not in (200, 202, 400, 403, 404, 409, 415, 429, 503):
            raise ValueError("Respuesta inesperada")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("Respuesta inesperada")
        return data, response.status
    except (OSError, http.client.HTTPException, ValueError):
        return {"error": "El worker local de Pliegue no está disponible."}, 503
    finally:
        connection.close()
