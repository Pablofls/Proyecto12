"""Exportacion de reportes a CSV (RF-28, UC-24).

CSV con UTF-8 y BOM (Excel lo abre con acentos), en streaming: las filas se
leen con un cursor del lado del servidor y se escriben a medida que llegan,
asi que un reporte grande no se carga completo en memoria. El tope de filas
evita que una exportacion sin filtros sature la base compartida.

Trazabilidad: RF-28, UC-24, RNF-11, RNF-16
"""
import csv
import io
from datetime import date, datetime
from decimal import Decimal

from flask import Response, current_app, stream_with_context

from app.db import get_conn

LIMITE_FILAS = 50000
BLOQUE_FILAS = 500

# Una celda que empieza con estos caracteres puede ejecutarse como formula al
# abrir el archivo en Excel o Calc (inyeccion de formulas / CSV injection).
PREFIJOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def celda_segura(valor):
    """Convierte un valor a texto de celda neutralizando formulas.

    Los numeros reales (incluso negativos) se dejan tal cual: el riesgo esta en
    el texto que escribio un usuario, no en un monto.
    """
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "si" if valor else "no"
    if isinstance(valor, (int, float, Decimal)):
        return str(valor)
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(valor, date):
        return valor.isoformat()
    texto = str(valor)
    if texto.startswith(PREFIJOS_FORMULA):
        return "'" + texto
    return texto


def _filas(sql, parametros, limite):
    """Itera las filas con un cursor nombrado (streaming real en PostgreSQL)."""
    conexion = get_conn()
    with conexion.cursor(name="exportacion_csv") as cursor:
        cursor.itersize = BLOQUE_FILAS
        cursor.execute(f"{sql}\n LIMIT %s", (*parametros, limite))
        yield from cursor


def generar_csv(columnas, filas):
    """Genera el CSV en bloques de bytes. `columnas` es [(encabezado, clave)]."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer, lineterminator="\r\n")
    escritor.writerow([encabezado for encabezado, _ in columnas])
    yield ("﻿" + buffer.getvalue()).encode("utf-8")
    buffer.seek(0)
    buffer.truncate()

    pendientes = 0
    for fila in filas:
        escritor.writerow([celda_segura(fila[clave]) for _, clave in columnas])
        pendientes += 1
        if pendientes >= BLOQUE_FILAS:
            yield buffer.getvalue().encode("utf-8")
            buffer.seek(0)
            buffer.truncate()
            pendientes = 0
    if pendientes:
        yield buffer.getvalue().encode("utf-8")


def respuesta_csv(nombre, columnas, sql, parametros=(), limite=None):
    """Respuesta HTTP de descarga. El SQL no debe traer LIMIT: se agrega aqui.

    Quien llama debe haber registrado ya la bitacora y confirmado la
    transaccion (get_conn().commit()): el flujo en streaming termina despues
    de que la vista regresa.
    """
    limite = limite or current_app.config.get("EXPORT_MAX_FILAS", LIMITE_FILAS)
    archivo = f"{nombre}_{date.today().isoformat()}.csv"
    cuerpo = stream_with_context(generar_csv(columnas, _filas(sql, tuple(parametros), limite)))
    return Response(cuerpo, headers={
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="{archivo}"',
        "Cache-Control": "no-store",
    })
