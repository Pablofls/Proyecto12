"""Ventas y catalogos: API adicional; no toca los blueprints del monolito.

Fuente de verdad: PostgreSQL; venta_detalle_id conserva la relacion precisa
entre devolucion y compra. Las tablas y campos son listas blancas fijas.
"""
import os
from datetime import date

from flask import Blueprint, Flask, g, request

from shared import docs, respuestas
from shared.infra import (cerrar_conexion, consultar, ejecutar,
                          registrar_bitacora, salud_postgres, salud_redis)
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import ADMINISTRADOR, ANALISTA, CLIENTE, requiere_jwt

NOMBRE = "ventas-catalogos"
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")
api_ventas = Blueprint("ventas", __name__, url_prefix="/api/v1/ventas")
api_catalogos = Blueprint("catalogos", __name__, url_prefix="/api/v1/catalogos")

# Refleja exactamente los siete catalogos en app/blueprints/catalogos.py.
# (tipo, obligatorio, longitud maxima o nombre de la tabla referenciada)
CATALOGOS = {
    "proveedores": {"nombre": ("texto", True, 150), "contacto": ("texto", False, 150)},
    "productos": {"sku": ("texto", True, 50), "nombre": ("texto", True, 150),
                  "clasificacion_temperatura": ("temperatura", True, None),
                  "proveedor_id": ("referencia", True, "proveedores")},
    "lotes": {"producto_id": ("referencia", True, "productos"),
              "proveedor_id": ("referencia", True, "proveedores"),
              "numero_lote": ("texto", True, 50),
              "fecha_fabricacion": ("fecha", False, None),
              "fecha_caducidad": ("fecha", False, None)},
    "tiendas": {"nombre": ("texto", True, 150), "direccion": ("texto", False, 255)},
    "rutas": {"origen": ("texto", True, 150), "destino": ("texto", True, 150)},
    "transportistas": {"nombre": ("texto", True, 150), "empresa": ("texto", False, 150)},
    "motivos": {"nombre": ("texto", True, 100), "descripcion": ("texto", False, 255)},
}


def validar_catalogo(nombre):
    if nombre not in CATALOGOS:
        raise ErrorApi(404, "no_encontrado", "No existe ese catalogo.")
    return CATALOGOS[nombre]


def validar_datos(nombre, datos):
    """Reglas de entrada, sin SQL, id/activo nunca se escriben por PUT/POST."""
    campos = validar_catalogo(nombre)
    if not isinstance(datos, dict):
        raise ErrorApi(400, "validacion", "Se requiere un objeto.")
    desconocidos = set(datos) - set(campos)
    errores, limpios = [], {}
    if desconocidos:
        errores.append({"campo": ",".join(sorted(desconocidos)), "problema": "campo no permitido"})
    for campo, (tipo, requerido, extra) in campos.items():
        val = datos.get(campo)
        if val is None or val == "":
            if requerido:
                errores.append({"campo": campo, "problema": "obligatorio"})
            limpios[campo] = None
            continue
        if tipo in ("texto", "temperatura", "fecha"):
            if not isinstance(val, str):
                errores.append({"campo": campo, "problema": "debe ser texto"})
                continue
            val = val.strip()
        if tipo == "texto" and (not val or len(val) > extra):
            errores.append({"campo": campo, "problema": f"entre 1 y {extra} caracteres"})
        if tipo == "temperatura" and val not in ("refrigerado", "no_refrigerado"):
            errores.append({"campo": campo, "problema": "clasificacion no permitida"})
        if tipo == "fecha":
            try:
                date.fromisoformat(val)
            except ValueError:
                errores.append({"campo": campo, "problema": "fecha AAAA-MM-DD invalida"})
        if tipo == "referencia":
            try:
                # bool es int en Python, pero no es un identificador valido.
                if isinstance(val, bool):
                    raise ValueError
                val = int(val)
                if val <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                errores.append({"campo": campo, "problema": "entero positivo requerido"})
                continue
        limpios[campo] = val
    if errores:
        raise ErrorApi(400, "validacion", "Campos invalidos.", errores)
    return limpios


def exigir_referencias(nombre, datos):
    """No permite asignar un producto/lote a un catalogo inactivo."""
    for campo, (tipo, _, tabla) in CATALOGOS[nombre].items():
        if tipo == "referencia" and datos.get(campo) is not None:
            # 'tabla' proviene EXCLUSIVAMENTE de la lista blanca CATALOGOS.
            if not consultar(f"SELECT id FROM {tabla} WHERE id=%s AND activo=TRUE",
                            (datos[campo],), uno=True):
                raise ErrorApi(409, "referencia_inactiva",
                               f"El campo {campo} no referencia un registro activo.")


def permiso_lectura(nombre):
    """Clientes solo leen motivos para solicitar devoluciones; internos leen todos."""
    if g.usuario["rol"] == CLIENTE and nombre != "motivos":
        raise ErrorApi(403, "sin_permiso", "No puedes consultar este catalogo.")


@api_ventas.get("")
@requiere_jwt()
def ventas():
    pag = leer_paginacion()
    condiciones, parametros = ["v.eliminado_en IS NULL"], []
    if g.usuario["rol"] == CLIENTE:
        condiciones.append("v.cliente_id=%s")
        parametros.append(g.usuario["id"])
    q = (request.args.get("q") or "").strip()
    if len(q) > 100:
        raise ErrorApi(400, "validacion", "La busqueda no puede superar 100 caracteres.")
    if q:
        condiciones.append("v.folio_venta ILIKE %s")
        parametros.append("%" + q + "%")
    where = " AND ".join(condiciones)
    total = consultar(f"SELECT COUNT(*) AS n FROM ventas v WHERE {where}",
                     tuple(parametros), uno=True)["n"]
    filas = consultar(f"""
        SELECT v.id, v.folio_venta, v.cliente_id, v.fecha_venta,
               u.nombre AS cliente, t.nombre AS tienda,
               COUNT(vd.id) AS lineas,
               COALESCE(SUM(vd.cantidad*vd.precio_unitario),0) AS total
          FROM ventas v JOIN usuarios u ON u.id=v.cliente_id
          JOIN tiendas t ON t.id=v.tienda_id
          LEFT JOIN venta_detalle vd ON vd.venta_id=v.id
         WHERE {where}
         GROUP BY v.id,u.nombre,t.nombre
         ORDER BY v.fecha_venta DESC,v.id DESC LIMIT %s OFFSET %s
    """, tuple(parametros) + (pag.limite, pag.desplazamiento))
    return responder(paginar(filas, total, pag), raiz="ventas")


@api_ventas.get("/<int:venta_id>")
@requiere_jwt()
def detalle_venta(venta_id):
    venta = consultar("""
        SELECT v.id,v.folio_venta,v.fecha_venta,v.cliente_id,
               u.nombre AS cliente,t.nombre AS tienda
          FROM ventas v JOIN usuarios u ON u.id=v.cliente_id
          JOIN tiendas t ON t.id=v.tienda_id
         WHERE v.id=%s AND v.eliminado_en IS NULL
    """, (venta_id,), uno=True)
    if not venta:
        raise ErrorApi(404, "no_encontrado", "Venta inexistente.")
    if g.usuario["rol"] == CLIENTE and venta["cliente_id"] != g.usuario["id"]:
        raise ErrorApi(403, "sin_permiso", "La venta no te pertenece.")
    venta["lineas"] = consultar("""
        SELECT vd.id,vd.lote_id,vd.cantidad,vd.precio_unitario,
               l.numero_lote,l.fecha_caducidad,p.id AS producto_id,
               p.nombre AS producto,p.sku,p.clasificacion_temperatura,
               pr.nombre AS proveedor,
               (SELECT COALESCE(SUM(d.cantidad_devuelta),0)
                  FROM devoluciones d
                 WHERE d.venta_detalle_id=vd.id AND d.eliminado_en IS NULL
                   AND d.estado <> 'rechazada') AS ya_devuelto
          FROM venta_detalle vd JOIN lotes l ON l.id=vd.lote_id
          JOIN productos p ON p.id=l.producto_id
          JOIN proveedores pr ON pr.id=l.proveedor_id
         WHERE vd.venta_id=%s ORDER BY vd.id
    """, (venta_id,))
    for linea in venta["lineas"]:
        linea["disponible"] = linea["cantidad"] - linea["ya_devuelto"]
    return responder(venta, raiz="venta")


@api_catalogos.get("")
@requiere_jwt(ADMINISTRADOR, ANALISTA)
def lista_catalogos():
    return responder({"catalogos": sorted(CATALOGOS)}, raiz="catalogos")


@api_catalogos.get("/<nombre>")
@requiere_jwt()
def listado_catalogo(nombre):
    campos = validar_catalogo(nombre)
    permiso_lectura(nombre)
    pag = leer_paginacion()
    solo_activos = (request.args.get("solo_activos", "true").lower() == "true")
    if g.usuario["rol"] == CLIENTE:
        solo_activos = True
    where = " WHERE activo=TRUE" if solo_activos else ""
    columnas = ",".join(campos)
    total = consultar(f"SELECT COUNT(*) AS n FROM {nombre}{where}", uno=True)["n"]
    filas = consultar(f"SELECT id,{columnas},activo FROM {nombre}{where} "
                     "ORDER BY id DESC LIMIT %s OFFSET %s",
                     (pag.limite,pag.desplazamiento))
    return responder(paginar(filas, total, pag), raiz="catalogo")


@api_catalogos.get("/<nombre>/<int:registro_id>")
@requiere_jwt()
def detalle_catalogo(nombre, registro_id):
    campos = validar_catalogo(nombre)
    permiso_lectura(nombre)
    solo_activos = " AND activo=TRUE" if g.usuario["rol"] == CLIENTE else ""
    registro = consultar(f"SELECT id,{','.join(campos)},activo FROM {nombre} "
                        f"WHERE id=%s{solo_activos}", (registro_id,), uno=True)
    if not registro:
        raise ErrorApi(404, "no_encontrado", "Registro inexistente.")
    return responder(registro, raiz="registro")


@api_catalogos.post("/<nombre>")
@requiere_jwt(ADMINISTRADOR)
def crear_catalogo(nombre):
    campos = validar_catalogo(nombre)
    datos = validar_datos(nombre, leer_cuerpo(xsd=os.path.join(CONTRATOS, "catalogo.xsd")))
    exigir_referencias(nombre, datos)
    columnas = list(campos)
    fila = ejecutar(f"INSERT INTO {nombre} ({','.join(columnas)}) VALUES "
                   f"({','.join(['%s']*len(columnas))}) RETURNING id",
                   tuple(datos[c] for c in columnas), devolver=True)
    registrar_bitacora("alta_catalogo", nombre, fila["id"], "Alta de catalogo por API")
    return responder({"id": fila["id"], "catalogo": nombre},201,"registro",
                    {"Location": f"/api/v1/catalogos/{nombre}/{fila['id']}"})


@api_catalogos.put("/<nombre>/<int:registro_id>")
@requiere_jwt(ADMINISTRADOR)
def editar_catalogo(nombre, registro_id):
    campos = validar_catalogo(nombre)
    datos = validar_datos(nombre, leer_cuerpo(xsd=os.path.join(CONTRATOS, "catalogo.xsd")))
    exigir_referencias(nombre, datos)
    if not consultar(f"SELECT id FROM {nombre} WHERE id=%s",(registro_id,),uno=True):
        raise ErrorApi(404,"no_encontrado","Registro inexistente.")
    columnas = list(campos)
    ejecutar(f"UPDATE {nombre} SET {','.join(c+'=%s' for c in columnas)} WHERE id=%s",
            tuple(datos[c] for c in columnas)+(registro_id,))
    registrar_bitacora("edicion_catalogo",nombre,registro_id,"Edicion de catalogo por API")
    return responder({"id":registro_id,"catalogo":nombre,"actualizado":True},raiz="registro")


@api_catalogos.patch("/<nombre>/<int:registro_id>/estado")
@requiere_jwt(ADMINISTRADOR)
def estado_catalogo(nombre, registro_id):
    validar_catalogo(nombre)
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS,"estado.xsd"))
    activo=datos.get("activo")
    if isinstance(activo,str) and activo.lower() in ("true","false"):
        activo = activo.lower()=="true"
    if not isinstance(activo,bool):
        raise ErrorApi(400,"validacion","activo debe ser booleano.")
    fila=ejecutar(f"UPDATE {nombre} SET activo=%s WHERE id=%s RETURNING id",
                 (activo,registro_id),devolver=True)
    if not fila:
        raise ErrorApi(404,"no_encontrado","Registro inexistente.")
    registrar_bitacora("catalogo_activado" if activo else "catalogo_desactivado",
                       nombre,registro_id,"Cambio de estado por API")
    return responder({"id":registro_id,"activo":activo},raiz="registro")


@api_catalogos.delete("/<nombre>/<int:registro_id>")
@requiere_jwt(ADMINISTRADOR)
def desactivar_catalogo(nombre, registro_id):
    validar_catalogo(nombre)
    fila=ejecutar(f"UPDATE {nombre} SET activo=FALSE WHERE id=%s RETURNING id",
                 (registro_id,),devolver=True)
    if not fila:
        raise ErrorApi(404,"no_encontrado","Registro inexistente.")
    registrar_bitacora("catalogo_desactivado",nombre,registro_id,"Desactivacion por API")
    return responder({"id":registro_id,"activo":False},raiz="registro")


def create_app():
    app=Flask(__name__)
    app.json.sort_keys=False
    respuestas.registrar(app,NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api_ventas)
    app.register_blueprint(api_catalogos)
    docs.registrar(app,os.path.join(os.path.dirname(__file__),"openapi.yaml"))

    @app.get("/health")
    def health():
        deps={"postgresql":salud_postgres(),"redis":salud_redis()}
        ok=all(x["ok"] for x in deps.values())
        return responder({"servicio":NOMBRE,"version":"v1","estado":"ok" if ok else "degradado",
                         "dependencias":deps},200 if ok else 503)
    return app

