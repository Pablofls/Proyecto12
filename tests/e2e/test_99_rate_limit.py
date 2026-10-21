"""Rate limiting de login (429), al final para no bloquear al resto de la suite.

El limite es por IP y minuto (LOGIN_MAX_POR_MINUTO, por defecto 10). La prueba
agota el contador con un correo inexistente (no bloquea cuentas reales) y, en
`finally`, borra las claves de limite para dejar el entorno como estaba.

Trazabilidad: RNF-28, RNF-13.
"""
import os
import uuid

from . import cliente as c


def test_login_responde_429_al_exceder_el_limite(ctx):
    maximo = int(os.environ.get("LOGIN_MAX_POR_MINUTO", "10"))
    # Un correo distinto por intento: repetir uno inexistente dispararia el
    # bloqueo por intentos fallidos (423) antes que el limite de peticiones.
    base = uuid.uuid4().hex[:8]
    correos = [f"limite{i}.{base}@demo.mx" for i in range(maximo + 2)]
    c.liberar_limite_login()
    try:
        estados = [c.llamar("auth", "POST", c.PREFIJO_API["auth"] + "/login",
                            {"email": correos[i], "password": "x"}).status
                   for i in range(maximo + 1)]
        assert estados[:maximo] == [401] * maximo
        assert estados[maximo] == 429
        ultimo = c.llamar("auth", "POST", c.PREFIJO_API["auth"] + "/login",
                          {"email": correos[-1], "password": "x"})
        assert int(ultimo.headers["Retry-After"]) >= 1
        assert c.error_tipo(ultimo) == "demasiadas_peticiones"
    finally:
        c.liberar_limite_login()
        r = c.redis_cli()
        for correo in correos:
            r.delete(f"devoluciones:intentos:{correo}", f"devoluciones:bloqueo:{correo}")
