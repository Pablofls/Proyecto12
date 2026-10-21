"""Catalogos del sistema: proveedores, productos, lotes, tiendas, rutas,
transportistas y motivos de devolucion.

Los nombres de tabla y de columna NUNCA provienen de la peticion: se toman de
la definicion CATALOGOS de este modulo, que actua como lista blanca. Los valores
siempre viajan como parametros ligados (RNF-11).

Trazabilidad: RF-05, HU-05, UC-05
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.db import consultar, ejecutar
from app.security import ADMINISTRADOR, ANALISTA, registrar_bitacora, roles_required

bp = Blueprint("catalogos", __name__, url_prefix="/catalogos")


def campo(nombre, etiqueta, tipo="texto", requerido=False, opciones=None):
    return {"nombre": nombre, "etiqueta": etiqueta, "tipo": tipo,
            "requerido": requerido, "opciones": opciones}


CATALOGOS = {
    "proveedores": {
        "titulo": "Proveedores",
        "tabla": "proveedores",
        "campos": [
            campo("nombre", "Nombre", requerido=True),
            campo("contacto", "Contacto"),
        ],
    },
    "productos": {
        "titulo": "Productos",
        "tabla": "productos",
        "campos": [
            campo("sku", "SKU", requerido=True),
            campo("nombre", "Nombre", requerido=True),
            campo("clasificacion_temperatura", "Clasificacion", tipo="seleccion",
                  requerido=True, opciones=[("refrigerado", "Refrigerado"),
                                            ("no_refrigerado", "No refrigerado")]),
            campo("proveedor_id", "Proveedor", tipo="referencia", requerido=True,
                  opciones="proveedores"),
        ],
    },
    "lotes": {
        "titulo": "Lotes",
        "tabla": "lotes",
        "campos": [
            campo("producto_id", "Producto", tipo="referencia", requerido=True,
                  opciones="productos"),
            campo("proveedor_id", "Proveedor", tipo="referencia", requerido=True,
                  opciones="proveedores"),
            campo("numero_lote", "Numero de lote", requerido=True),
            campo("fecha_fabricacion", "Fecha de fabricacion", tipo="fecha"),
            campo("fecha_caducidad", "Fecha de caducidad", tipo="fecha"),
        ],
    },
    "tiendas": {
        "titulo": "Tiendas",
        "tabla": "tiendas",
        "campos": [
            campo("nombre", "Nombre", requerido=True),
            campo("direccion", "Direccion"),
        ],
    },
    "rutas": {
        "titulo": "Rutas",
        "tabla": "rutas",
        "campos": [
            campo("origen", "Origen", requerido=True),
            campo("destino", "Destino", requerido=True),
        ],
    },
    "transportistas": {
        "titulo": "Transportistas",
        "tabla": "transportistas",
        "campos": [
            campo("nombre", "Nombre", requerido=True),
            campo("empresa", "Empresa"),
        ],
    },
    "motivos": {
        "titulo": "Motivos de devolucion",
        "tabla": "motivos",
        "campos": [
            campo("nombre", "Nombre", requerido=True),
            campo("descripcion", "Descripcion"),
        ],
    },
}


def _definicion(catalogo):
    if catalogo not in CATALOGOS:
        abort(404)
    return CATALOGOS[catalogo]


def _etiqueta_referencia(tabla):
    """Como se muestra un registro de un catalogo referenciado."""
    return {
        "proveedores": "nombre",
        "productos": "nombre",
    }.get(tabla, "nombre")


def _opciones_referencia(definicion):
    """Carga los registros activos de los catalogos referenciados."""
    referencias = {}
    for c in definicion["campos"]:
        if c["tipo"] == "referencia":
            tabla = c["opciones"]
            etiqueta = _etiqueta_referencia(tabla)
            referencias[c["nombre"]] = consultar(
                f"SELECT id, {etiqueta} AS etiqueta FROM {tabla} WHERE activo = TRUE ORDER BY {etiqueta}"
            )
    return referencias


def _valores_del_formulario(definicion):
    valores, faltantes = {}, []
    for c in definicion["campos"]:
        bruto = (request.form.get(c["nombre"]) or "").strip()
        if not bruto:
            if c["requerido"]:
                faltantes.append(c["etiqueta"])
            valores[c["nombre"]] = None
        else:
            valores[c["nombre"]] = bruto
    return valores, faltantes


@bp.get("/")
@roles_required(ADMINISTRADOR, ANALISTA)
def indice():
    return render_template("catalogos/indice.html", catalogos=CATALOGOS)


@bp.get("/<catalogo>")
@roles_required(ADMINISTRADOR, ANALISTA)
def listar(catalogo):
    definicion = _definicion(catalogo)
    columnas = ", ".join(c["nombre"] for c in definicion["campos"])
    registros = consultar(
        f"SELECT id, {columnas}, activo FROM {definicion['tabla']} ORDER BY id DESC"
    )
    referencias = _opciones_referencia(definicion)
    etiquetas = {
        campo_nombre: {fila["id"]: fila["etiqueta"] for fila in filas}
        for campo_nombre, filas in referencias.items()
    }
    return render_template("catalogos/listar.html", catalogo=catalogo,
                           definicion=definicion, registros=registros, etiquetas=etiquetas)


@bp.route("/<catalogo>/nuevo", methods=["GET", "POST"])
@roles_required(ADMINISTRADOR)
def nuevo(catalogo):
    definicion = _definicion(catalogo)
    referencias = _opciones_referencia(definicion)

    if request.method == "POST":
        valores, faltantes = _valores_del_formulario(definicion)
        if faltantes:
            flash("Faltan campos obligatorios: " + ", ".join(faltantes), "error")
            return render_template("catalogos/formulario.html", catalogo=catalogo,
                                   definicion=definicion, referencias=referencias,
                                   registro=valores), 400

        columnas = list(valores.keys())
        marcadores = ", ".join(["%s"] * len(columnas))
        fila = ejecutar(
            f"INSERT INTO {definicion['tabla']} ({', '.join(columnas)}) "
            f"VALUES ({marcadores}) RETURNING id",
            tuple(valores[c] for c in columnas),
            devolver=True,
        )
        registrar_bitacora("alta_catalogo", definicion["tabla"], fila["id"],
                           f"Alta en el catalogo {definicion['titulo']}")
        flash(f"Registro agregado a {definicion['titulo']}.", "ok")
        return redirect(url_for("catalogos.listar", catalogo=catalogo))

    return render_template("catalogos/formulario.html", catalogo=catalogo,
                           definicion=definicion, referencias=referencias, registro=None)


@bp.route("/<catalogo>/<int:registro_id>/editar", methods=["GET", "POST"])
@roles_required(ADMINISTRADOR)
def editar(catalogo, registro_id):
    definicion = _definicion(catalogo)
    referencias = _opciones_referencia(definicion)
    columnas = ", ".join(c["nombre"] for c in definicion["campos"])
    registro = consultar(
        f"SELECT id, {columnas}, activo FROM {definicion['tabla']} WHERE id = %s",
        (registro_id,), uno=True,
    )
    if registro is None:
        abort(404)

    if request.method == "POST":
        valores, faltantes = _valores_del_formulario(definicion)
        if faltantes:
            flash("Faltan campos obligatorios: " + ", ".join(faltantes), "error")
            return render_template("catalogos/formulario.html", catalogo=catalogo,
                                   definicion=definicion, referencias=referencias,
                                   registro=registro), 400

        asignaciones = ", ".join(f"{c} = %s" for c in valores.keys())
        ejecutar(
            f"UPDATE {definicion['tabla']} SET {asignaciones} WHERE id = %s",
            tuple(valores.values()) + (registro_id,),
        )
        registrar_bitacora("edicion_catalogo", definicion["tabla"], registro_id,
                           f"Edicion en el catalogo {definicion['titulo']}")
        flash("Registro actualizado.", "ok")
        return redirect(url_for("catalogos.listar", catalogo=catalogo))

    return render_template("catalogos/formulario.html", catalogo=catalogo,
                           definicion=definicion, referencias=referencias, registro=registro)


@bp.post("/<catalogo>/<int:registro_id>/alternar")
@roles_required(ADMINISTRADOR)
def alternar(catalogo, registro_id):
    """Activa o desactiva el registro. Nunca se borra: hay devoluciones que lo
    referencian y el historial debe conservarse (UC-05, RNF-30)."""
    definicion = _definicion(catalogo)
    fila = ejecutar(
        f"UPDATE {definicion['tabla']} SET activo = NOT activo WHERE id = %s RETURNING activo",
        (registro_id,), devolver=True,
    )
    if fila is None:
        abort(404)
    estado = "activado" if fila["activo"] else "desactivado"
    registrar_bitacora(f"catalogo_{estado}", definicion["tabla"], registro_id,
                       f"Registro {estado} en {definicion['titulo']}")
    flash(f"Registro {estado}.", "ok")
    return redirect(url_for("catalogos.listar", catalogo=catalogo))
