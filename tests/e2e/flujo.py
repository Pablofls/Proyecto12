"""Atajos para llevar una devolucion hasta un estado dado.

Los usan las pruebas de error (test_02) para armar escenarios sin repetir los
once pasos. El proceso completo y explicito vive en test_01_proceso_completo.py.

Trazabilidad: RNF-28, RF-07, RF-10, RF-12 a RF-15.
"""
from datetime import date, timedelta

from . import cliente as c

DESCRIPCION = "Prueba E2E: el empaque llego roto y danado."


def registrar(ctx, cantidad=1, token=None, correlation_id=None):
    resp = c.llamar("devoluciones", "POST", c.PREFIJO_API["devoluciones"],
                    {"venta_detalle_id": ctx.linea["id"], "motivo_id": ctx.motivo,
                     "descripcion_problema": DESCRIPCION,
                     "cantidad_devuelta": cantidad},
                    token=token or ctx.h(c.CLIENTE), correlation_id=correlation_id)
    if resp.status == 201:
        ctx.registrar_devolucion(resp.datos["id"])
    return resp


def autorizar(ctx, dev_id):
    return c.llamar("devoluciones", "PATCH",
                    f"{c.PREFIJO_API['devoluciones']}/{dev_id}/resolucion",
                    {"decision": "autorizar"}, token=ctx.h(c.ANALISTA))


def ruta_y_transportista():
    ruta = c.sql("SELECT id FROM rutas WHERE activo ORDER BY id LIMIT 1", uno=True)
    transp = c.sql("SELECT id FROM transportistas WHERE activo ORDER BY id LIMIT 1",
                   uno=True)
    assert ruta and transp, "Faltan rutas o transportistas activos (seed de catalogos)"
    return ruta["id"], transp["id"]


def recolectar_y_recibir(ctx, dev_id):
    """programada -> asignada -> en_transito -> completada -> recibida."""
    pref = c.PREFIJO_API["logistica"]
    coord = ctx.h(c.COORDINADOR)
    manana = (date.today() + timedelta(days=1)).isoformat()
    resp = c.llamar("logistica", "POST", f"{pref}/recolecciones",
                    {"devolucion_id": dev_id, "fecha_programada": manana,
                     "lugar": "Tienda de prueba E2E"}, token=coord)
    assert resp.status == 201, resp.texto
    rec_id = resp.datos["id"]
    ruta, transp = ruta_y_transportista()
    resp = c.llamar("logistica", "PATCH", f"{pref}/recolecciones/{rec_id}/asignacion",
                    {"ruta_id": ruta, "transportista_id": transp}, token=coord)
    assert resp.status == 200, resp.texto
    for estado in ("en_transito", "completada"):
        resp = c.llamar("logistica", "PATCH", f"{pref}/recolecciones/{rec_id}/estado",
                        {"estado": estado}, token=coord)
        assert resp.status == 200, resp.texto
    resp = c.llamar("logistica", "POST", f"{pref}/recepciones",
                    {"devolucion_id": dev_id, "coincide_expediente": True},
                    token=ctx.h(c.ENCARGADO_CENTRO))
    assert resp.status == 201, resp.texto
    return rec_id


def inspeccionar(ctx, dev_id, **condiciones):
    cuerpo = {"devolucion_id": dev_id, "estado_empaque": "Caja abierta",
              "temperatura_recepcion": 4.0, "minutos_fuera_refrigeracion": 10,
              "danos": False, "caducidad_vencida": False,
              "cadena_frio_rota": False, "observaciones": "Inspeccion E2E"}
    cuerpo.update(condiciones)
    return c.llamar("inspecciones", "POST", c.PREFIJO_API["inspecciones"], cuerpo,
                    token=ctx.h(c.INSPECTOR))


def hasta_recibida(ctx):
    """Devolucion nueva, autorizada, recolectada y recibida. Devuelve su id."""
    resp = registrar(ctx)
    assert resp.status == 201, resp.texto
    dev_id = resp.datos["id"]
    assert autorizar(ctx, dev_id).status == 200
    recolectar_y_recibir(ctx, dev_id)
    return dev_id
