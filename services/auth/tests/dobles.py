"""Dobles de prueba: Redis y PostgreSQL en memoria.

Permiten probar la logica del servicio sin levantar contenedores. Las pruebas
contra las bases reales son las de integracion (docs/PRUEBAS.md).
"""
import time

from werkzeug.security import generate_password_hash

PASSWORD = "Prueba-123"


class RedisFalso:
    def __init__(self):
        self.datos, self.expira, self.caido = {}, {}, False

    def _vivo(self, k):
        if self.caido:
            raise ConnectionError("redis caido")
        if k in self.expira and self.expira[k] <= time.time():
            self.datos.pop(k, None)
            self.expira.pop(k, None)
        return k in self.datos

    def ping(self):
        self._vivo("_")
        return True

    def incr(self, k):
        self._vivo(k)
        self.datos[k] = int(self.datos.get(k, 0)) + 1
        return self.datos[k]

    def expire(self, k, seg):
        if self._vivo(k):
            self.expira[k] = time.time() + seg

    def ttl(self, k):
        if not self._vivo(k):
            return -2
        return int(self.expira[k] - time.time()) if k in self.expira else -1

    def setex(self, k, seg, v):
        self._vivo(k)
        self.datos[k] = v
        self.expira[k] = time.time() + seg

    def exists(self, *ks):
        return sum(1 for k in ks if self._vivo(k))

    def delete(self, *ks):
        n = 0
        for k in ks:
            if self._vivo(k):
                n += 1
            self.datos.pop(k, None)
            self.expira.pop(k, None)
        return n

    def hset(self, k, mapping):
        self._vivo(k)
        self.datos.setdefault(k, {}).update(mapping)

    def sadd(self, k, v):
        self._vivo(k)
        self.datos.setdefault(k, set()).add(v)

    def srem(self, k, v):
        if self._vivo(k):
            self.datos[k].discard(v)

    def smembers(self, k):
        return set(self.datos[k]) if self._vivo(k) else set()


class BaseFalsa:
    def __init__(self):
        self.usuarios = {
            "analista@demo.com": {"id": 3, "nombre": "Ana Analista",
                                  "email": "analista@demo.com",
                                  "rol": "Analista de Devoluciones"},
            "admin@demo.com": {"id": 1, "nombre": "Admin",
                               "email": "admin@demo.com",
                               "rol": "Administrador"},
        }
        for u in self.usuarios.values():
            u.update(password_hash=generate_password_hash(PASSWORD),
                     estado="activo", bloqueado_hasta=None)
        self.sentencias = []

    def consultar(self, sql, params=None, uno=False):
        if "FROM usuarios u" in sql:
            return self.usuarios.get(params[0])
        if "FROM usuarios WHERE id" in sql:
            existe = any(u["id"] == params[0] for u in self.usuarios.values())
            return {"id": params[0]} if existe else None
        raise AssertionError(f"Consulta no prevista: {sql}")

    def ejecutar(self, sql, params=None, devolver=False):
        self.sentencias.append(" ".join(sql.split()))
