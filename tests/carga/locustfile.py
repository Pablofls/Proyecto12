"""Pruebas de carga con Locust: cinco perfiles reales, no un solo endpoint (RNF-29).

Corre dentro de la red del compose en la VM (scripts/correr_carga.sh), asi se
mide la plataforma y no el internet entre la VM y quien la prueba.

Perfiles (el peso es cuantos usuarios de cada tipo hay en la mezcla):
- Cliente (5):     consulta sus devoluciones y ventas, catalogo de motivos, pide sugerencia.
- Analista (3):    bandeja de devoluciones, detalle, reportes, analitica, trazabilidad, causa raiz.
- Operacion (2):   Coordinador de Logistica e Inspector revisan recolecciones y devoluciones.
- Movil campo (2): el Recolector sincroniza su cola offline (reenvia siempre el mismo lote).
- Supervision (1): el Administrador revisa monitoreo, proveedores e investigaciones.

Login: el limite es de 10 logins por minuto por IP (H-07), asi que al arrancar se
inicia UNA sesion por rol y todos los usuarios de ese perfil comparten el token.

Limites por usuario (RNF-13): sugerencias de motivo y sincronizacion permiten 30
peticiones por minuto por usuario. Como el token se comparte, un 429 ahi es el
limite funcionando, no un error: se marca como correcto y se cuenta aparte.

Trazabilidad: RNF-29, RNF-13, RNF-28.
"""
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from locust import HttpUser, between, events, task

URL = {
    "auth": os.environ.get("AUTH_URL", "http://auth:8000"),
    "devoluciones": os.environ.get("DEVOLUCIONES_URL", "http://devoluciones:8000"),
    "ventas": os.environ.get("VENTAS_URL", "http://ventas-catalogos:8000"),
    "logistica": os.environ.get("LOGISTICA_URL", "http://logistica:8000"),
    "motivos": os.environ.get("MOTIVOS_URL", "http://clasificacion-motivos:8000"),
    "reportes": os.environ.get("REPORTES_URL", "http://reportes-analitica:8000"),
    "causa_raiz": os.environ.get("CAUSA_RAIZ_URL", "http://causa-raiz:8000"),
    "proveedores": os.environ.get("PROVEEDORES_URL", "http://proveedores:8000"),
    "sincronizacion": os.environ.get("SINCRONIZACION_URL", "http://sincronizacion:8000"),
    "monitoreo": os.environ.get("INTEGRACIONES_URL", "http://integraciones-monitoreo:8000"),
}

CUENTAS = {
    "cliente": "miguel.cliente@demo.mx",
    "analista": "josue.analista@demo.mx",
    "coordinador": "david.logistica@demo.mx",
    "inspector": "valentina.inspector@demo.mx",
    "recolector": "luis.recolector@demo.mx",
    "admin": "pablo.admin@demo.mx",
}

TOKENS = {}
LIMITE_ESPERADO = {"429": 0}

# El lote offline que reenvia el movil: un id fijo, asi cada envio despues del
# primero es un reintento (idempotencia) y la tabla no crece durante la prueba.
ID_OPERACION_MOVIL = str(uuid.UUID("00000000-0000-4000-8000-00000000ca29"))
DESCRIPCIONES = [
    "El empaque llego roto y el producto derramado.",
    "La leche llego caliente, sin cadena de frio.",
    "Me enviaron un producto diferente al que compre.",
    "El producto ya venia caducado.",
]


@events.test_start.add_listener
def iniciar_sesiones(environment, **_):
    """Una sesion por rol antes de la carga (no cuenta en las estadisticas)."""
    import requests  # viene con Locust

    clave = os.environ["PASSWORD_DEMO"]
    for rol, email in CUENTAS.items():
        r = requests.post(URL["auth"] + "/api/v1/auth/login",
                          json={"email": email, "password": clave}, timeout=10)
        r.raise_for_status()
        TOKENS[rol] = r.json()["access_token"]
    print(f"[carga] Sesiones iniciadas: {', '.join(TOKENS)}")


@events.test_stop.add_listener
def resumen(environment, **_):
    print(f"[carga] 429 del limite por usuario (esperados, contados como correctos): "
          f"{LIMITE_ESPERADO['429']}")


class Perfil(HttpUser):
    abstract = True
    host = URL["auth"]
    wait_time = between(1, 3)   # una persona no hace clic sin parar
    rol = None

    def _h(self):
        return {"Authorization": f"Bearer {TOKENS[self.rol]}", "Accept": "application/json"}

    def get(self, servicio, ruta, nombre=None):
        return self.client.get(URL[servicio] + ruta, headers=self._h(), name=nombre or ruta)

    def post_limitado(self, servicio, ruta, cuerpo, nombre=None):
        """POST con limite por usuario: 429 es el limite funcionando."""
        with self.client.post(URL[servicio] + ruta, json=cuerpo, headers=self._h(),
                              name=nombre or ruta, catch_response=True) as r:
            if r.status_code == 429:
                LIMITE_ESPERADO["429"] += 1
                r.success()
            elif r.status_code >= 400:
                r.failure(f"HTTP {r.status_code}")


class Cliente(Perfil):
    weight = 5
    rol = "cliente"

    @task(4)
    def mis_devoluciones(self):
        self.get("devoluciones", "/api/v1/devoluciones?por_pagina=10")

    @task(3)
    def mis_compras(self):
        self.get("ventas", "/api/v1/ventas?por_pagina=5")

    @task(2)
    def catalogo_de_motivos(self):
        self.get("motivos", "/api/v1/motivos/categorias")

    @task(1)
    def sugerencia_de_motivo(self):
        self.post_limitado("motivos", "/api/v1/motivos/sugerencias",
                           {"descripcion": random.choice(DESCRIPCIONES)})


class Analista(Perfil):
    weight = 3
    rol = "analista"

    @task(4)
    def bandeja_y_detalle(self):
        r = self.get("devoluciones", "/api/v1/devoluciones?por_pagina=20")
        if r.ok:
            datos = r.json().get("datos") or []
            if datos:
                dev = random.choice(datos)["id"]
                self.get("devoluciones", f"/api/v1/devoluciones/{dev}", "/api/v1/devoluciones/[id]")

    @task(2)
    def reportes(self):
        self.get("reportes", "/api/v1/reportes/pareto?dimension=motivo&medida=frecuencia",
                 "/api/v1/reportes/pareto")

    @task(1)
    def tendencias(self):
        self.get("reportes", "/api/v1/analitica/tendencias")

    @task(1)
    def alertas_de_fraude(self):
        self.get("reportes", "/api/v1/analitica/alertas-fraude")

    @task(1)
    def tasas_por_lote(self):
        self.get("ventas", "/api/v1/trazabilidad/tasas?por=lote", "/api/v1/trazabilidad/tasas")

    @task(1)
    def alertas_causa_raiz(self):
        self.get("causa_raiz", "/api/v1/causa-raiz/alertas")


class Operacion(Perfil):
    """Coordinador de Logistica o Inspector (se elige al arrancar cada usuario)."""
    weight = 2

    def on_start(self):
        self.rol = random.choice(("coordinador", "inspector"))

    @task(3)
    def recolecciones(self):
        if self.rol == "coordinador":
            self.get("logistica", "/api/v1/logistica/recolecciones?por_pagina=20",
                     "/api/v1/logistica/recolecciones")
        else:
            self.get("devoluciones", "/api/v1/devoluciones?por_pagina=20",
                     "/api/v1/devoluciones (inspector)")

    @task(1)
    def bandeja(self):
        self.get("devoluciones", "/api/v1/devoluciones?por_pagina=10")


class MovilCampo(Perfil):
    weight = 2
    rol = "recolector"
    wait_time = between(3, 6)   # la app sincroniza cada pocos segundos, no sin parar

    @task(1)
    def tipos_offline(self):
        self.get("sincronizacion", "/api/v1/sincronizacion/tipos")

    @task(1)
    def mis_operaciones(self):
        self.get("sincronizacion", "/api/v1/sincronizacion/operaciones?por_pagina=20",
                 "/api/v1/sincronizacion/operaciones [GET]")

    @task(2)
    def sincronizar_cola(self):
        # Una operacion que el servidor rechaza siempre (requiere conexion):
        # recorre validacion, permisos e idempotencia sin cambiar datos de negocio.
        capturada = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        lote = {"dispositivo_id": "carga-locust",
                "operaciones": [{"id_operacion": ID_OPERACION_MOVIL, "tipo": "aprobar_reembolso",
                                 "capturado_en": capturada, "datos": {"devolucion_id": 1}}]}
        self.post_limitado("sincronizacion", "/api/v1/sincronizacion/operaciones", lote,
                           "/api/v1/sincronizacion/operaciones [POST]")


class Supervision(Perfil):
    weight = 1
    rol = "admin"
    wait_time = between(5, 10)

    @task(3)
    def alertas_operativas(self):
        self.get("monitoreo", "/api/v1/monitoreo/alertas")

    @task(2)
    def disponibilidad(self):
        self.get("monitoreo", "/api/v1/monitoreo/disponibilidad")

    @task(1)
    def chequeo_en_vivo(self):
        # Revisa los 14 servicios y las 3 bases en ese momento: la peticion mas pesada.
        self.get("monitoreo", "/api/v1/monitoreo/estado")

    @task(2)
    def proveedores(self):
        self.get("proveedores", "/api/v1/proveedores")

    @task(2)
    def investigaciones(self):
        self.get("causa_raiz", "/api/v1/causa-raiz/investigaciones")
