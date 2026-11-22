"""Seguridad del tercer parcial contra los servicios reales (HTTP).

Lo que agrego el tercer parcial y no cubre test_02:
- Los seis servicios nuevos rechazan peticiones sin token o con token revocado.
- Roles de campo (Recolector, Operador de Almacen, Supervisor): solo entran a lo
  que los nombra; Cliente y Supervisor no hacen lo que no les toca.
- Control por sucursal: un usuario con tienda no ve devoluciones de otra.
- Operaciones criticas: contrasena incorrecta, rol no permitido, falta de
  permiso, permiso para otro registro, permiso que no sirve como access token y
  permiso de un solo uso (se borra de Redis al usarse).
- Ataques de entrada: XXE, inyeccion SQL en el login y en la sincronizacion,
  rutas con caracteres peligrosos y /health sin datos sensibles.

Solo corre en la VM (INTEGRACION=1). Lo que crea se borra al terminar; la
bitacora se conserva (es de solo agregar, migracion 045).
Trazabilidad: RNF-28, RNF-08, RNF-09, RNF-11, RNF-16, RN-13, dominio 20 a 22.
"""
import base64
import json
import os
import uuid
from datetime import datetime, timezone

import pytest

from . import cliente as c

P = c.PREFIJO_API
RECOLECTOR = "luis.recolector@demo.mx"
ALMACEN = "marta.almacen@demo.mx"
SUPERVISOR = "Supervisor"

# Un endpoint protegido de cada servicio nuevo del tercer parcial.
NUEVOS = [
    ("motivos", "GET", P["motivos"] + "/categorias"),
    ("causa_raiz", "GET", P["causa_raiz"] + "/investigaciones"),
    ("proveedores", "GET", P["proveedores"]),
    ("reportes", "GET", P["reportes"]),
    ("sincronizacion", "GET", P["sincronizacion"] + "/tipos"),
    ("integraciones", "GET", P["monitoreo"] + "/alertas"),
]
IDS = [n[0] for n in NUEVOS]


@pytest.fixture(scope="module")
def campo(ctx):
    """Sesiones de los roles de campo; se cierran al terminar el modulo."""
    c.liberar_limite_login()
    for email in (RECOLECTOR, ALMACEN):
        if not c.sql("SELECT 1 FROM usuarios WHERE email = %s AND estado = 'activo'", (email,), uno=True):
            pytest.skip(f"Falta {email}: corre seed_demo.py")
    supervisor = c.email_de_rol(SUPERVISOR)
    if not supervisor:
        pytest.skip("No hay Supervisor: corre seed_demo.py")
    x = {"recolector": c.iniciar_sesion(RECOLECTOR), "almacen": c.iniciar_sesion(ALMACEN),
         "supervisor": c.iniciar_sesion(supervisor), "email_supervisor": supervisor,
         "devoluciones": [], "investigaciones": []}
    yield x
    if x["investigaciones"]:
        ids = tuple(x["investigaciones"])
        for paso in ("DELETE FROM seguimiento_investigacion WHERE investigacion_id IN %s",
                     "DELETE FROM investigaciones WHERE id IN %s"):
            try:
                c.sql(paso, (ids,))
            except Exception as exc:  # noqa: BLE001 - limpieza de mejor esfuerzo
                print("Limpieza de investigaciones:", exc)
    c.borrar_devoluciones(x["devoluciones"])
    for rol in ("recolector", "almacen", "supervisor"):
        c.cerrar_sesion(x[rol])


def _payload(token):
    """Claims de un JWT sin verificar la firma (solo para leer el jti)."""
    cuerpo = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))


# --------------------------------------------------------------------------- #
# 1. Servicios nuevos: sin token y con token revocado
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("servicio,metodo,ruta", NUEVOS, ids=IDS)
def test_servicio_nuevo_sin_token_responde_401(ctx, servicio, metodo, ruta):
    assert c.llamar(servicio, metodo, ruta).status == 401


@pytest.mark.parametrize("servicio,metodo,ruta", NUEVOS, ids=IDS)
def test_servicio_nuevo_rechaza_token_revocado(ctx, servicio, metodo, ruta):
    c.liberar_limite_login()  # cada caso inicia sesion; el limite es de 10 por minuto
    token = c.iniciar_sesion(ctx.emails[c.ADMINISTRADOR])
    c.cerrar_sesion(token)
    resp = c.llamar(servicio, metodo, ruta, token=token)
    assert resp.status == 401
    assert c.error_tipo(resp) in ("token_revocado", "sesion_inactiva")


# --------------------------------------------------------------------------- #
# 2. Roles de campo y roles que no deben hacer ciertas cosas
# --------------------------------------------------------------------------- #
def test_recolector_no_consulta_devoluciones(campo):
    assert c.llamar("devoluciones", "GET", P["devoluciones"], token=campo["recolector"]).status == 403


def test_recolector_no_ve_el_monitoreo(campo):
    assert c.llamar("integraciones", "GET", P["monitoreo"] + "/alertas",
                    token=campo["recolector"]).status == 403


def test_operador_de_almacen_no_resuelve_devoluciones(ctx, campo):
    resp = c.llamar("devoluciones", "PATCH", P["devoluciones"] + "/1/resolucion",
                    {"decision": "autorizar"}, token=campo["almacen"])
    assert resp.status == 403


def test_supervisor_no_importa_ventas_del_pos(campo):
    resp = c.llamar("integraciones", "POST", P["integraciones"] + "/ventas",
                    {"id_externo": "TK-SEG"}, token=campo["supervisor"])
    assert resp.status == 403


def test_cliente_no_sincroniza_ni_ve_el_monitoreo(ctx):
    cliente = ctx.h(c.CLIENTE)
    assert c.llamar("sincronizacion", "POST", P["sincronizacion"] + "/operaciones",
                    {"dispositivo_id": "x", "operaciones": []}, token=cliente).status == 403
    assert c.llamar("integraciones", "GET", P["monitoreo"] + "/estado", token=cliente).status == 403


# --------------------------------------------------------------------------- #
# 3. Control por sucursal
# --------------------------------------------------------------------------- #
def test_operador_no_ve_devoluciones_de_otra_sucursal(ctx, campo):
    tienda = c.sql("SELECT tienda_id FROM usuarios WHERE email = %s", (ALMACEN,), uno=True)["tienda_id"]
    if tienda is None:
        pytest.skip("marta.almacen no tiene sucursal: corre seed_demo.py")
    linea = c.sql("""SELECT vd.id FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id
                      WHERE v.tienda_id <> %s AND v.eliminado_en IS NULL ORDER BY vd.id LIMIT 1""",
                  (tienda,), uno=True)
    if not linea:
        pytest.skip("No hay ventas de otra sucursal")
    dev = c.sql("""INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema, cantidad_devuelta)
                   VALUES (%s, %s, 'Prueba de seguridad: otra sucursal.', 1) RETURNING id""",
                (linea["id"], ctx.motivo), uno=True)["id"]
    campo["devoluciones"].append(dev)
    resp = c.llamar("devoluciones", "GET", f"{P['devoluciones']}/{dev}", token=campo["almacen"])
    assert resp.status == 403
    assert c.error_tipo(resp) == "fuera_de_sucursal"
    # Y en el listado solo aparecen devoluciones de su tienda.
    lista = c.llamar("devoluciones", "GET", P["devoluciones"] + "?por_pagina=100", token=campo["almacen"])
    assert lista.status == 200
    ids = [d["id"] for d in lista.datos["datos"]]
    assert dev not in ids
    if ids:
        tiendas = c.sql("""SELECT DISTINCT v.tienda_id FROM devoluciones d
                             JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
                             JOIN ventas v ON v.id = vd.venta_id WHERE d.id = ANY(%s)""", (ids,))
        assert {t["tienda_id"] for t in tiendas} == {tienda}


# --------------------------------------------------------------------------- #
# 4. Operaciones criticas (reconfirmar contrasena, permiso de un solo uso)
# --------------------------------------------------------------------------- #
def _autorizar(token, operacion, recurso, password=None):
    return c.llamar("auth", "POST", P["auth"] + "/autorizar-operacion",
                    {"operacion": operacion, "recurso_id": str(recurso),
                     "password": password or os.environ["PASSWORD_DEMO"]}, token=token)


def _investigacion_lista_para_cerrar(campo):
    """Investigacion concluida como inconclusa (se puede cerrar sin acciones),
    llevada por un analista distinto del supervisor."""
    analista = c.sql("""SELECT u.id FROM usuarios u JOIN roles r ON r.id = u.rol_id
                         WHERE r.nombre = %s AND u.estado = 'activo' ORDER BY u.id LIMIT 1""",
                     (c.ANALISTA,), uno=True)["id"]
    iid = c.sql("""
        INSERT INTO investigaciones (dimension, referencia_id, etiqueta, titulo, descripcion, estado,
                                     analista_id, linea_base, conclusion, justificacion, fecha_conclusion)
        VALUES ('producto', 1, 'Prueba de seguridad', 'Prueba de seguridad',
                'Investigacion sembrada por la suite de seguridad.', 'concluida', %s, '{}'::jsonb,
                'inconclusa', 'Sin datos suficientes (prueba).', CURRENT_TIMESTAMP)
        RETURNING id""", (analista,), uno=True)["id"]
    campo["investigaciones"].append(iid)
    return iid


def test_contrasena_incorrecta_no_da_permiso(campo):
    resp = _autorizar(campo["supervisor"], "cerrar_investigacion", 1, password="incorrecta-" + uuid.uuid4().hex)
    assert resp.status == 401
    assert c.error_tipo(resp) == "credenciales_invalidas"


def test_rol_sin_esa_operacion_no_recibe_permiso(campo):
    resp = _autorizar(campo["recolector"], "cerrar_investigacion", 1)
    assert resp.status == 403


def test_permiso_de_operacion_no_sirve_como_token_de_acceso(campo):
    permiso = _autorizar(campo["supervisor"], "cerrar_investigacion", 999999)
    assert permiso.status == 201
    resp = c.llamar("devoluciones", "GET", P["devoluciones"], token=permiso.datos["token_operacion"])
    assert resp.status == 401


def test_cierre_exige_permiso_para_ese_registro_y_es_de_un_solo_uso(campo):
    iid = _investigacion_lista_para_cerrar(campo)
    ruta = f"{P['causa_raiz']}/investigaciones/{iid}/cierre"
    cuerpo = {"comentario": "Cierre de la prueba de seguridad."}
    # Sin permiso
    resp = c.llamar("causa_raiz", "POST", ruta, cuerpo, token=campo["supervisor"])
    assert (resp.status, c.error_tipo(resp)) == (403, "autorizacion_operacion_requerida")
    # Permiso pedido para OTRO registro
    otro = _autorizar(campo["supervisor"], "cerrar_investigacion", iid + 100000).datos["token_operacion"]
    resp = c.llamar("causa_raiz", "POST", ruta, cuerpo, token=campo["supervisor"],
                    cabeceras={"X-Autorizacion-Operacion": otro})
    assert (resp.status, c.error_tipo(resp)) == (403, "autorizacion_operacion_invalida")
    # Permiso correcto: se cierra y el permiso desaparece de Redis
    permiso = _autorizar(campo["supervisor"], "cerrar_investigacion", iid)
    assert permiso.status == 201
    clave = "devoluciones:operacion_autorizada:" + _payload(permiso.datos["token_operacion"])["jti"]
    assert c.redis_cli().exists(clave) == 1
    resp = c.llamar("causa_raiz", "POST", ruta, cuerpo, token=campo["supervisor"],
                    cabeceras={"X-Autorizacion-Operacion": permiso.datos["token_operacion"]})
    assert resp.status == 200, resp.texto
    assert c.redis_cli().exists(clave) == 0
    estado = c.sql("SELECT estado FROM investigaciones WHERE id = %s", (iid,), uno=True)["estado"]
    assert estado == "cerrada"


# --------------------------------------------------------------------------- #
# 5. Ataques de entrada
# --------------------------------------------------------------------------- #
def test_xml_con_entidad_externa_no_lee_archivos(ctx):
    xxe = ('<?xml version="1.0"?><!DOCTYPE login [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
           '<login><email>&x;</email><password>x</password></login>')
    resp = c.llamar("auth", "POST", P["auth"] + "/login", xml=xxe)
    assert resp.status in (400, 401)
    assert "root:" not in (resp.texto or "")


def test_inyeccion_sql_en_el_login_no_entra(ctx):
    resp = c.llamar("auth", "POST", P["auth"] + "/login",
                    {"email": "' OR '1'='1' --@x.mx", "password": "' OR '1'='1"})
    assert resp.status in (400, 401)


def test_inyeccion_en_la_sincronizacion_se_rechaza(campo):
    resp = c.llamar("sincronizacion", "POST", P["sincronizacion"] + "/operaciones",
                    {"dispositivo_id": "tel'; DROP TABLE devoluciones; --",
                     "operaciones": [{"id_operacion": str(uuid.uuid4()), "tipo": "evidencia",
                                      "capturado_en": datetime.now(timezone.utc).isoformat(), "datos": {}}]},
                    token=campo["recolector"])
    assert resp.status == 400
    assert c.sql("SELECT to_regclass('devoluciones') IS NOT NULL AS existe", uno=True)["existe"]


def test_traza_con_caracteres_peligrosos_se_rechaza(ctx):
    resp = c.llamar("integraciones", "GET", P["monitoreo"] + "/traza/a'%20OR%201=1",
                    token=ctx.h(c.ADMINISTRADOR))
    assert resp.status == 400


@pytest.mark.parametrize("servicio", ["sincronizacion", "integraciones", "auth", "devoluciones"])
def test_health_publico_sin_datos_sensibles(ctx, servicio):
    resp = c.llamar(servicio, "GET", "/health")
    assert resp.status == 200
    texto = (resp.texto or "").lower()
    for palabra in ("password", "secret", "postgres:5432", "devoluciones_app", "traceback"):
        assert palabra not in texto
