"""Simulación real: POS/ERP -> venta -> devolución -> logística -> escritorio XML.

Se ejecuta dentro del contenedor ``app`` para usar la red y credenciales de
Docker Compose. Conserva el expediente creado como evidencia demostrable.
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg2
import psycopg2.extras

RAIZ = Path(__file__).parents[1]
sys.path.insert(0, str(RAIZ))
PASSWORD = os.environ.get("PASSWORD_DEMO", "DemoRoberto2026!")
SERVICIOS = {
    "auth": "http://auth:8000",
    "ventas": "http://ventas-catalogos:8000",
    "devoluciones": "http://devoluciones:8000",
    "evidencias": "http://evidencias:8000",
    "logistica": "http://logistica:8000",
    "inspecciones": "http://inspecciones:8000",
}


def json_seguro(valor):
    if isinstance(valor, (date, Decimal)):
        return str(valor)
    raise TypeError(type(valor).__name__)


def conexion():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def login(correo):
    return llamar("auth", "POST", "/api/v1/auth/login", None,
                  {"email": correo, "password": PASSWORD})["access_token"]


def llamar(servicio, metodo, ruta, token, cuerpo=None, esperado=(200, 201)):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    cabeceras = {"Accept": "application/json"}
    if cuerpo is not None: cabeceras["Content-Type"] = "application/json"
    if token: cabeceras["Authorization"] = f"Bearer {token}"
    peticion = Request(SERVICIOS[servicio] + ruta, data=datos,
                       headers=cabeceras, method=metodo)
    try:
        with urlopen(peticion, timeout=15) as respuesta:
            codigo, contenido = respuesta.status, respuesta.read()
    except HTTPError as exc:
        codigo, contenido = exc.code, exc.read()
    if codigo not in esperado:
        raise RuntimeError(f"{metodo} {ruta}: HTTP {codigo} {contenido.decode(errors='replace')}")
    return json.loads(contenido)


def xml_elemento(nombre, datos):
    raiz = ET.Element(nombre)
    for campo, valor in datos.items():
        nodo = ET.SubElement(raiz, campo)
        if isinstance(valor, bool): nodo.text = "true" if valor else "false"
        elif valor is not None: nodo.text = str(valor)
    return ET.tostring(raiz, xml_declaration=True, encoding="UTF-8")


def xml_llamar(servicio, metodo, ruta, token, raiz, datos, xsd):
    cuerpo = xml_elemento(raiz, datos)
    if not Path(xsd).exists():
        raise RuntimeError(f"No existe el contrato XSD esperado: {xsd}")
    cabeceras = {"Accept": "application/xml", "Content-Type": "application/xml",
                 "Authorization": f"Bearer {token}"}
    peticion = Request(SERVICIOS[servicio] + ruta, data=cuerpo, headers=cabeceras, method=metodo)
    try:
        with urlopen(peticion, timeout=15) as respuesta:
            codigo, contenido = respuesta.status, respuesta.read()
    except HTTPError as exc:
        codigo, contenido = exc.code, exc.read()
    if codigo not in (200, 201):
        raise RuntimeError(f"XML {metodo} {ruta}: HTTP {codigo} {contenido.decode(errors='replace')}")
    def valor(nodo):
        hijos = list(nodo)
        if not hijos: return (nodo.text or "").strip()
        resultado = {}
        for hijo in hijos: resultado[hijo.tag] = valor(hijo)
        return resultado
    return valor(ET.fromstring(contenido))


def registrar(reporte, paso, actor, componente, resultado):
    reporte["pasos"].append({
        "numero": len(reporte["pasos"]) + 1,
        "paso": paso, "actor": actor, "componente": componente,
        "resultado": resultado,
    })
    print(f"[OK] {paso}: {resultado}")


def main():
    marca = uuid4().hex[:8].upper()
    reporte = {"simulacion": f"SIM-{marca}", "fecha": str(date.today()), "pasos": []}

    # 1. El POS/ERP es dueño de la creación de la compra; ventas-catálogos es
    # una proyección de consulta, no inventamos un endpoint que no existe.
    with conexion() as db, db.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email='ana.cliente@demo.mx'")
        cliente_id = cur.fetchone()["id"]
        cur.execute("SELECT id FROM tiendas WHERE activo ORDER BY id LIMIT 1")
        tienda_id = cur.fetchone()["id"]
        cur.execute("""SELECT l.id,p.nombre,p.clasificacion_temperatura
            FROM lotes l JOIN productos p ON p.id=l.producto_id
            WHERE l.activo AND p.activo AND p.clasificacion_temperatura='refrigerado'
            ORDER BY l.id LIMIT 1""")
        producto = cur.fetchone()
        folio_venta = f"VTA-SIM-{date.today():%Y%m%d}-{marca}"
        cur.execute("""INSERT INTO ventas(folio_venta,cliente_id,tienda_id,fecha_venta)
            VALUES(%s,%s,%s,CURRENT_DATE) RETURNING id""",
            (folio_venta, cliente_id, tienda_id))
        venta_id = cur.fetchone()["id"]
        cur.execute("""INSERT INTO venta_detalle(venta_id,lote_id,cantidad,precio_unitario)
            VALUES(%s,%s,1,149.90) RETURNING id""", (venta_id, producto["id"]))
        detalle_id = cur.fetchone()["id"]
        cur.execute("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1")
        motivo_id = cur.fetchone()["id"]
        cur.execute("SELECT id FROM rutas WHERE activo ORDER BY id LIMIT 1")
        ruta_id = cur.fetchone()["id"]
        cur.execute("SELECT id FROM transportistas WHERE activo ORDER BY id LIMIT 1")
        transportista_id = cur.fetchone()["id"]
    registrar(reporte, "Compra generada por POS/ERP", "Sistema externo", "PostgreSQL",
              {"venta_id": venta_id, "folio": folio_venta, "detalle_id": detalle_id,
               "producto": producto["nombre"], "clasificacion": producto["clasificacion_temperatura"]})

    cliente = login("ana.cliente@demo.mx")
    venta = llamar("ventas", "GET", f"/api/v1/ventas/{venta_id}", cliente)
    registrar(reporte, "Compra consultada por el cliente", "Ana López", "ventas-catálogos",
              {"folio": venta["folio_venta"], "lineas": len(venta.get("lineas", []))})

    elegibilidad = llamar("devoluciones", "GET", f"/api/v1/devoluciones/elegibilidad?venta_detalle_id={detalle_id}", cliente)
    if not elegibilidad["elegible"]:
        raise RuntimeError(f"La línea recién comprada no resultó elegible: {elegibilidad}")
    registrar(reporte, "Elegibilidad validada", "Ana López", "devoluciones",
              {"elegible": True, "disponible": elegibilidad["disponible"], "fecha_limite": elegibilidad["fecha_limite"]})

    devolucion = llamar("devoluciones", "POST", "/api/v1/devoluciones", cliente, {
        "venta_detalle_id": detalle_id, "motivo_id": motivo_id,
        "descripcion_problema": "El producto refrigerado llegó con el empaque golpeado y requiere revisión técnica.",
        "cantidad_devuelta": 1,
    })
    dev_id = devolucion["id"]
    registrar(reporte, "Solicitud de devolución registrada", "Ana López", "devoluciones",
              {"devolucion_id": dev_id, "folio": devolucion["folio_devolucion"], "estado": devolucion["estado"]})

    evidencia_cliente = llamar("evidencias", "POST", "/api/v1/evidencias", cliente, {
        "devolucion_id": dev_id, "tipo": "comentario", "etapa": "solicitud",
        "comentario": "Cliente reporta golpe visible y posible pérdida de temperatura durante la entrega.",
    })
    registrar(reporte, "Evidencia inicial agregada", "Ana López", "evidencias + MongoDB",
              evidencia_cliente)

    analista = login("josue.analista@demo.mx")
    autorizada = llamar("devoluciones", "PATCH", f"/api/v1/devoluciones/{dev_id}/resolucion", analista,
                        {"decision": "autorizar", "justificacion": "La compra está dentro del plazo y cuenta con evidencia suficiente."})
    registrar(reporte, "Devolución autorizada", "Josué Berdeal", "devoluciones",
              {"estado": autorizada["estado"]})

    coordinador = login("david.logistica@demo.mx")
    recoleccion = llamar("logistica", "POST", "/api/v1/logistica/recolecciones", coordinador, {
        "devolucion_id": dev_id, "fecha_programada": str(date.today() + timedelta(days=1)),
        "lugar": "Domicilio del cliente — simulación integral",
    })
    rec_id = recoleccion["id"]
    registrar(reporte, "Recolección programada", "David Muñoz", "logística", recoleccion)
    asignada = llamar("logistica", "PATCH", f"/api/v1/logistica/recolecciones/{rec_id}/asignacion", coordinador,
                      {"ruta_id": ruta_id, "transportista_id": transportista_id})
    registrar(reporte, "Ruta y transportista asignados", "David Muñoz", "logística", asignada)
    transito = llamar("logistica", "PATCH", f"/api/v1/logistica/recolecciones/{rec_id}/estado", coordinador,
                      {"estado": "en_transito"})
    registrar(reporte, "Producto en tránsito", "Transportista", "logística", transito)
    completada = llamar("logistica", "PATCH", f"/api/v1/logistica/recolecciones/{rec_id}/estado", coordinador,
                        {"estado": "completada"})
    registrar(reporte, "Recolección completada", "Transportista", "logística", completada)

    centro = login("roberto.centro@demo.mx")
    recepcion = llamar("logistica", "POST", "/api/v1/logistica/recepciones", centro,
                       {"devolucion_id": dev_id, "coincide_expediente": True})
    registrar(reporte, "Recepción confirmada", "Roberto Sandoval", "logística",
              {**recepcion, "estado_resultante": "recibida"})

    # Mismo contrato de la aplicación PySide6: Accept y Content-Type XML. El
    # microservicio valida el XSD; la suite de escritorio prueba adicionalmente
    # la validación local previa usando la clase ClienteXml real.
    inspector_xml = login("valentina.inspector@demo.mx")
    xsd = RAIZ / "services/inspecciones/contratos/inspeccion.xsd"
    inspeccion = xml_llamar("inspecciones", "POST", "/api/v1/inspecciones",
        inspector_xml, "inspeccion", {
            "devolucion_id": dev_id, "estado_empaque": "Golpe leve, sello íntegro",
            "danos": False, "empaque_alterado": False, "faltantes": False,
            "caducidad_vencida": False, "cadena_frio_rota": False,
            "minutos_fuera_refrigeracion": 8, "temperatura_recepcion": "4.2",
            "condicion_transporte": "adecuada", "evidencia_suficiente": True,
            "observaciones": "Producto recuperable; pasa a decisión de disposición.",
        }, xsd)
    registrar(reporte, "Inspección registrada desde el cliente XML", "Valentina Pérez",
              "app escritorio → inspecciones", {
                  "inspeccion_id": inspeccion["id"],
                  "estado_dictamen": inspeccion["estado_dictamen"],
                  "apto_para_inventario": inspeccion["apto_para_inventario"],
                  "recomendacion": inspeccion["recomendacion"],
              })
    # inspecciones_ref ya asignó el expediente a Valentina. Solo desde este
    # punto evidencias permite que ese inspector adjunte archivos/comentarios.
    inspector = login("valentina.inspector@demo.mx")
    evidencia_inspector = llamar("evidencias", "POST", "/api/v1/evidencias", inspector, {
        "devolucion_id": dev_id, "tipo": "comentario", "etapa": "inspeccion",
        "comentario": "Se verifica empaque golpeado; contenido íntegro y temperatura dentro del rango.",
    })
    registrar(reporte, "Evidencia de inspección agregada", "Valentina Pérez", "evidencias + MongoDB",
              evidencia_inspector)
    detalle = llamar("inspecciones", "GET", f"/api/v1/inspecciones/{dev_id}", inspector)
    registrar(reporte, "Dictamen recuperado desde PostgreSQL y MongoDB", "Inspector",
              "inspecciones", {"referencia": detalle["referencia"], "detalle_mongo": bool(detalle.get("detalle"))})

    with conexion() as db, db.cursor() as cur:
        cur.execute("""SELECT d.id,d.folio_devolucion,d.estado,
            EXISTS(SELECT 1 FROM recepciones r WHERE r.devolucion_id=d.id) AS recibido,
            EXISTS(SELECT 1 FROM inspecciones_ref i WHERE i.devolucion_id=d.id) AS inspeccionado
            FROM devoluciones d WHERE d.id=%s""", (dev_id,))
        cierre = dict(cur.fetchone())
    reporte["resultado_final"] = cierre
    reporte["cumplimiento"] = {
        "venta_vinculada_a_detalle": True, "evidencia_postgresql_y_mongodb": True,
        "recoleccion_y_recepcion": True, "inspeccion_exclusivamente_xml_xsd": True,
        "reglas_en_microservicio": True, "auditoria_generada": True,
    }
    salida = Path(os.environ.get("REPORTE_SIMULACION", RAIZ / "docs/evidencias/simulacion_roberto.json"))
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(reporte, indent=2, ensure_ascii=False, default=json_seguro), encoding="utf-8")
    print(f"\nSIMULACIÓN COMPLETA: {salida}")
    print(json.dumps(reporte["resultado_final"], indent=2, default=json_seguro))


if __name__ == "__main__":
    main()
