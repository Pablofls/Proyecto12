"""Cliente PySide6 del centro de devoluciones; comunica exclusivamente XML."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from cliente_xml import ClienteXml, ErrorServicio, raiz_recursos
from tema import ESTILO

RAIZ = raiz_recursos()
INSPECTOR = "Inspector"
CENTRO = "Encargado del Centro de Devoluciones"
ANALISTA = "Analista de Devoluciones"
REEMBOLSOS = "Encargado de Reembolsos"
ADMIN = "Administrador"
SUPERVISOR = "Supervisor"


def texto_error(exc: Exception) -> str:
    if isinstance(exc, ErrorServicio):
        cid = f"\nCódigo de seguimiento: {exc.correlation_id}" if exc.correlation_id else ""
        return f"{exc} ({exc.tipo}, HTTP {exc.codigo}){cid}"
    return str(exc)


def filas_respuesta(respuesta) -> list[dict]:
    """Normaliza las variantes XML lista/vacío/un elemento para la tabla."""
    if not isinstance(respuesta, dict):
        return []
    filas = respuesta.get("datos", respuesta)
    if isinstance(filas, dict) and set(filas) == {"item"}:
        filas = filas["item"]
    if isinstance(filas, dict):
        filas = [filas]
    if not isinstance(filas, list):
        return []
    return [fila for fila in filas if isinstance(fila, dict)]


def valor_tabla(valor) -> str:
    if isinstance(valor, dict):
        return " · ".join(f"{k}: {valor_tabla(v)}" for k, v in valor.items())
    if isinstance(valor, list):
        return ", ".join(valor_tabla(v) for v in valor)
    if valor in (None, ""):
        return "—"
    if str(valor).lower() in ("true", "false"):
        return "Sí" if str(valor).lower() == "true" else "No"
    return str(valor)


def valor_celda(columna: str, valor) -> str:
    """Presentación humana sin alterar el dato recibido del microservicio."""
    if columna == "horas_pendiente":
        try: return f"{float(valor):.1f} h"
        except (TypeError, ValueError): pass
    if "fecha" in columna and isinstance(valor, str):
        return valor.replace("T", " ").replace("+00:00", " UTC")[:23]
    if columna in {"estado", "prioridad", "clasificacion_temperatura", "estado_dictamen", "destino"}:
        return valor_tabla(valor).replace("_", " ").capitalize()
    return valor_tabla(valor)


class Trabajo(QThread):
    terminado = Signal(object)
    fallo = Signal(object)

    def __init__(self, funcion, parent=None):
        super().__init__(parent)
        self.funcion = funcion

    def run(self):
        try:
            self.terminado.emit(self.funcion())
        except Exception as exc:
            self.fallo.emit(exc)


class Tarjeta(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")


class Pagina(QWidget):
    def __init__(self, titulo: str, subtitulo: str):
        super().__init__()
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(22, 20, 22, 22)
        exterior.setSpacing(14)
        h1 = QLabel(titulo); h1.setObjectName("titulo")
        sub = QLabel(subtitulo); sub.setObjectName("subtitulo"); sub.setWordWrap(True)
        exterior.addWidget(h1); exterior.addWidget(sub)
        self.contenido = QVBoxLayout(); self.contenido.setSpacing(14)
        exterior.addLayout(self.contenido); exterior.addStretch()


class TablaServicio(Pagina):
    def __init__(self, titulo, subtitulo, cargador, columnas_preferidas=()):
        super().__init__(titulo, subtitulo)
        self.cargador = cargador
        self.columnas_preferidas = list(columnas_preferidas)
        self.cargado = False
        tarjeta = Tarjeta(); caja = QVBoxLayout(tarjeta); caja.setContentsMargins(16, 16, 16, 16)
        barra = QHBoxLayout()
        self.estado = QLabel("Pulsa Actualizar para consultar los microservicios.")
        self.estado.setObjectName("ayuda")
        self.actualizar_btn = QPushButton("Actualizar")
        self.actualizar_btn.setObjectName("secundario")
        self.actualizar_btn.clicked.connect(self.actualizar)
        barra.addWidget(self.estado); barra.addStretch(); barra.addWidget(self.actualizar_btn)
        self.tabla = QTableWidget(); self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        caja.addLayout(barra); caja.addWidget(self.tabla)
        self.contenido.addWidget(tarjeta)

    def showEvent(self, evento):
        super().showEvent(evento)
        if not self.cargado:
            self.actualizar()

    def actualizar(self):
        self.actualizar_btn.setEnabled(False); self.actualizar_btn.setText("Consultando…")
        self.estado.setText("Solicitando información XML al microservicio…")
        self.trabajo = Trabajo(self.cargador, self)
        self.trabajo.terminado.connect(self.mostrar)
        self.trabajo.fallo.connect(self.error)
        self.trabajo.finished.connect(self._finalizar)
        self.trabajo.start()

    def _finalizar(self):
        self.actualizar_btn.setEnabled(True); self.actualizar_btn.setText("Actualizar")

    def error(self, exc):
        self.estado.setText("No fue posible actualizar.")
        self.estado.setObjectName("estadoError"); self.estado.style().unpolish(self.estado); self.estado.style().polish(self.estado)
        QMessageBox.critical(self, "Consulta rechazada", texto_error(exc))

    def mostrar(self, respuesta):
        filas = filas_respuesta(respuesta)
        todas = {clave for fila in filas for clave in fila}
        columnas = [c for c in self.columnas_preferidas if c in todas]
        columnas += sorted(todas - set(columnas))
        self.tabla.clear(); self.tabla.setColumnCount(len(columnas)); self.tabla.setRowCount(len(filas))
        self.tabla.setHorizontalHeaderLabels([c.replace("_", " ").upper() for c in columnas])
        for i, fila in enumerate(filas):
            for j, columna in enumerate(columnas):
                self.tabla.setItem(i, j, QTableWidgetItem(valor_celda(columna, fila.get(columna))))
        self.tabla.resizeColumnsToContents()
        if columnas:
            self.tabla.horizontalHeader().setStretchLastSection(True)
        self.estado.setText(f"{len(filas)} registro(s) recibidos mediante XML validado.")
        self.estado.setObjectName("estadoOk"); self.estado.style().unpolish(self.estado); self.estado.style().polish(self.estado)
        self.cargado = True


class FormularioOperacion(Pagina):
    def __init__(self, titulo, subtitulo):
        super().__init__(titulo, subtitulo)
        self.tarjeta = Tarjeta(); self.form = QFormLayout(self.tarjeta)
        self.form.setContentsMargins(20, 18, 20, 18); self.form.setSpacing(12)
        self.contenido.addWidget(self.tarjeta)
        self.resultado = QLabel("Completa los campos obligatorios.")
        self.resultado.setObjectName("ayuda"); self.resultado.setWordWrap(True)
        self.contenido.addWidget(self.resultado)

    def ejecutar(self, funcion, boton, mensaje):
        boton.setEnabled(False); boton.setText("Procesando…")
        self.trabajo = Trabajo(funcion, self)
        self.trabajo.terminado.connect(lambda r: self.exito(r, mensaje))
        self.trabajo.fallo.connect(self.error)
        self.trabajo.finished.connect(lambda: (boton.setEnabled(True), boton.setText(boton.property("texto"))))
        self.trabajo.start()

    def exito(self, respuesta, mensaje):
        identificador = respuesta.get("id") if isinstance(respuesta, dict) else None
        sufijo = f" Identificador: {identificador}." if identificador else ""
        self.resultado.setText(mensaje + sufijo)
        self.resultado.setObjectName("estadoOk"); self.resultado.style().unpolish(self.resultado); self.resultado.style().polish(self.resultado)

    def error(self, exc):
        self.resultado.setText("La operación fue rechazada; no se guardaron cambios.")
        self.resultado.setObjectName("estadoError"); self.resultado.style().unpolish(self.resultado); self.resultado.style().polish(self.resultado)
        QMessageBox.critical(self, "Operación rechazada", texto_error(exc))

    @staticmethod
    def boton(texto):
        boton = QPushButton(texto); boton.setProperty("texto", texto)
        return boton


class Inspeccion(FormularioOperacion):
    def __init__(self, cliente):
        super().__init__("Inspección técnica", "Registra condiciones físicas y de transporte. El microservicio genera el dictamen; esta pantalla no decide el destino comercial.")
        self.cliente = cliente
        self.devolucion = QSpinBox(); self.devolucion.setRange(1, 999999)
        self.empaque = QLineEdit("Empaque sin alteraciones")
        self.temperatura = QLineEdit(); self.temperatura.setPlaceholderText("Obligatoria para refrigerados, p. ej. 4.2")
        self.minutos = QLineEdit(); self.minutos.setPlaceholderText("Obligatorios para refrigerados")
        self.transporte = QComboBox(); self.transporte.addItems(["adecuada", "inadecuada", "desconocida"])
        self.observaciones = QTextEdit(); self.observaciones.setMaximumHeight(75)
        self.danos = QCheckBox("Daños visibles"); self.alterado = QCheckBox("Empaque alterado")
        self.faltantes = QCheckBox("Faltantes"); self.caducidad = QCheckBox("Caducidad vencida")
        self.cadena = QCheckBox("Cadena de frío rota"); self.evidencia = QCheckBox("Evidencia suficiente"); self.evidencia.setChecked(True)
        indicadores = QWidget(); rejilla = QHBoxLayout(indicadores); rejilla.setContentsMargins(0, 0, 0, 0)
        for control in (self.danos, self.alterado, self.faltantes, self.caducidad, self.cadena, self.evidencia): rejilla.addWidget(control)
        rejilla.addStretch()
        self.form.addRow("Devolución ID *", self.devolucion); self.form.addRow("Estado del empaque *", self.empaque)
        self.form.addRow("Temperatura de recepción (°C)", self.temperatura); self.form.addRow("Minutos fuera de refrigeración", self.minutos)
        self.form.addRow("Condición de transporte", self.transporte); self.form.addRow("Hallazgos", indicadores)
        self.form.addRow("Observaciones", self.observaciones)
        self.enviar = self.boton("Registrar inspección"); self.enviar.clicked.connect(self.registrar); self.form.addRow("", self.enviar)

    def registrar(self):
        empaque = self.empaque.text().strip()
        if len(empaque) < 3: return self.error(ValueError("Describe el estado del empaque."))
        temperatura, minutos = self.temperatura.text().strip(), self.minutos.text().strip()
        if temperatura:
            try: float(temperatura)
            except ValueError: return self.error(ValueError("La temperatura debe ser numérica."))
        if minutos:
            try:
                if int(minutos) < 0: raise ValueError
            except ValueError: return self.error(ValueError("Los minutos deben ser un entero no negativo."))
        datos = {"devolucion_id": self.devolucion.value(), "estado_empaque": empaque,
            "danos": self.danos.isChecked(), "empaque_alterado": self.alterado.isChecked(),
            "faltantes": self.faltantes.isChecked(), "caducidad_vencida": self.caducidad.isChecked(),
            "cadena_frio_rota": self.cadena.isChecked(), "condicion_transporte": self.transporte.currentText(),
            "evidencia_suficiente": self.evidencia.isChecked(), "observaciones": self.observaciones.toPlainText().strip()}
        if temperatura: datos["temperatura_recepcion"] = temperatura
        if minutos: datos["minutos_fuera_refrigeracion"] = minutos
        xsd = RAIZ / "services/inspecciones/contratos/inspeccion.xsd"
        self.ejecutar(lambda: self.cliente.solicitar("inspecciones", "POST", "/api/v1/inspecciones", raiz="inspeccion", xsd=xsd, datos=datos), self.enviar, "Inspección registrada y dictamen técnico generado.")


class Disposicion(FormularioOperacion):
    def __init__(self, cliente):
        super().__init__("Disposición autorizada", "Elige el destino únicamente después del dictamen técnico. Reintegrar nunca procede si el producto no es recuperable.")
        self.cliente = cliente
        self.devolucion = QSpinBox(); self.devolucion.setRange(1, 999999)
        self.destino = QComboBox(); self.destino.addItems(["reintegrar", "reparacion", "reacondicionamiento", "devolucion_proveedor", "reciclaje", "donacion", "desecho"])
        self.justificacion = QTextEdit("Producto recuperable conforme al dictamen técnico"); self.justificacion.setMaximumHeight(85)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password); self.password.setPlaceholderText("Reconfirmación obligatoria")
        self.form.addRow("Devolución ID *", self.devolucion); self.form.addRow("Destino *", self.destino)
        self.form.addRow("Justificación *", self.justificacion); self.form.addRow("Confirma tu contraseña *", self.password)
        self.enviar = self.boton("Autorizar disposición"); self.enviar.clicked.connect(self.registrar); self.form.addRow("", self.enviar)

    def registrar(self):
        dev, justificacion, password = self.devolucion.value(), self.justificacion.toPlainText().strip(), self.password.text()
        if len(justificacion) < 10: return self.error(ValueError("La justificación debe tener al menos 10 caracteres."))
        if not password: return self.error(ValueError("Confirma tu contraseña para autorizar esta operación crítica."))
        destino = self.destino.currentText(); xsd = RAIZ / "services/disposicion_inventario/contratos/disposicion.xsd"
        def accion():
            permiso = self.cliente.autorizar("aprobar_disposicion", str(dev), password)
            return self.cliente.solicitar("disposicion", "POST", "/api/v1/disposicion-inventario/disposiciones", raiz="disposicion", xsd=xsd, datos={"devolucion_id": dev, "destino": destino, "justificacion": justificacion}, token_operacion=permiso)
        self.ejecutar(accion, self.enviar, "Disposición autorizada con permiso de un solo uso.")


class Reembolso(FormularioOperacion):
    def __init__(self, cliente):
        super().__init__("Resolución del reembolso", "Aprueba una sola devolución económica. Redis y PostgreSQL impiden pagos duplicados, incluso con solicitudes concurrentes.")
        self.cliente = cliente
        self.devolucion = QSpinBox(); self.devolucion.setRange(1, 999999)
        self.decision = QComboBox(); self.decision.addItems(["aprobado", "rechazado"])
        self.monto = QDoubleSpinBox(); self.monto.setRange(0, 99999999); self.monto.setDecimals(2); self.monto.setPrefix("$ ")
        self.metodo = QComboBox(); self.metodo.addItems(["tarjeta", "transferencia", "efectivo", "vale"])
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password); self.password.setPlaceholderText("Solo se exige al aprobar")
        self.decision.currentTextChanged.connect(lambda d: (self.monto.setEnabled(d == "aprobado"), self.metodo.setEnabled(d == "aprobado"), self.password.setEnabled(d == "aprobado")))
        self.form.addRow("Devolución ID *", self.devolucion); self.form.addRow("Decisión *", self.decision)
        self.form.addRow("Monto", self.monto); self.form.addRow("Método", self.metodo); self.form.addRow("Confirma tu contraseña", self.password)
        self.enviar = self.boton("Resolver reembolso"); self.enviar.clicked.connect(self.registrar); self.form.addRow("", self.enviar)

    def registrar(self):
        dev, decision = self.devolucion.value(), self.decision.currentText(); password = self.password.text()
        monto = f"{self.monto.value():.2f}" if decision == "aprobado" else "0.00"
        if decision == "aprobado" and not password: return self.error(ValueError("Confirma tu contraseña para aprobar el reembolso."))
        datos = {"devolucion_id": dev, "monto": monto, "metodo": self.metodo.currentText(), "estado": decision}
        xsd = RAIZ / "services/reembolsos_costos/contratos/reembolso.xsd"
        def accion():
            permiso = self.cliente.autorizar("aprobar_reembolso", str(dev), password) if decision == "aprobado" else None
            return self.cliente.solicitar("reembolsos", "POST", "/api/v1/reembolsos-costos/reembolsos", raiz="reembolso", xsd=xsd, datos=datos, token_operacion=permiso)
        self.ejecutar(accion, self.enviar, f"Reembolso {decision} correctamente.")


class Inventario(FormularioOperacion):
    def __init__(self, cliente):
        super().__init__("Control de inventario recuperable", "El ingreso siempre inicia en cuarentena. La reincorporación requiere una segunda autorización y nunca es automática.")
        self.cliente = cliente
        self.disposicion = QSpinBox(); self.disposicion.setRange(1, 999999); self.ubicacion = QLineEdit("CUARENTENA-A1")
        self.ingresar = self.boton("Ingresar a cuarentena"); self.ingresar.clicked.connect(self.cuarentena)
        self.inventario = QSpinBox(); self.inventario.setRange(1, 999999); self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password)
        self.reincorporar_btn = self.boton("Autorizar reincorporación"); self.reincorporar_btn.clicked.connect(self.reincorporar)
        self.form.addRow("Disposición ID *", self.disposicion); self.form.addRow("Ubicación de cuarentena *", self.ubicacion); self.form.addRow("", self.ingresar)
        separador = QLabel("REINCORPORACIÓN CONTROLADA"); separador.setObjectName("ayuda"); self.form.addRow(separador)
        self.form.addRow("Inventario ID *", self.inventario); self.form.addRow("Confirma tu contraseña *", self.password); self.form.addRow("", self.reincorporar_btn)

    def cuarentena(self):
        ubicacion, disposicion = self.ubicacion.text().strip(), self.disposicion.value()
        if len(ubicacion) < 2: return self.error(ValueError("Indica la ubicación física de cuarentena."))
        xsd = RAIZ / "services/disposicion_inventario/contratos/cuarentena.xsd"
        self.ejecutar(lambda: self.cliente.solicitar("disposicion", "POST", f"/api/v1/disposicion-inventario/inventario/{disposicion}/cuarentena", raiz="cuarentena", xsd=xsd, datos={"ubicacion": ubicacion}), self.ingresar, "Artículo recibido en cuarentena.")

    def reincorporar(self):
        inventario, password = self.inventario.value(), self.password.text()
        if not password: return self.error(ValueError("Confirma tu contraseña para reincorporar inventario."))
        def accion():
            permiso = self.cliente.autorizar("reincorporar_inventario", str(inventario), password)
            return self.cliente.solicitar("disposicion", "POST", f"/api/v1/disposicion-inventario/inventario/{inventario}/reincorporar", datos=None, token_operacion=permiso)
        self.ejecutar(accion, self.reincorporar_btn, "Artículo reincorporado al inventario disponible.")


class Encabezado(QWidget):
    cerrar = Signal()
    def __init__(self, usuario):
        super().__init__(); self.setObjectName("encabezado")
        # En Windows, los QWidget transparentes no siempre pintan el fondo
        # definido por selector; esta regla local asegura paridad con la web.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #1f6f4a;")
        paleta = self.palette(); paleta.setColor(QPalette.Window, QColor("#1f6f4a"))
        self.setPalette(paleta); self.setAutoFillBackground(True)
        caja = QHBoxLayout(self); caja.setContentsMargins(20, 12, 20, 12)
        marca = QLabel("DEVOLUCIONES · LOGÍSTICA INVERSA"); marca.setObjectName("marca")
        api = QLabel("XML · API distribuida"); api.setObjectName("insignia")
        sesion = QLabel(f"{usuario.get('nombre', 'Usuario')} — {usuario.get('rol', '')}"); sesion.setObjectName("sesion")
        salir = QPushButton("Cerrar sesión"); salir.setObjectName("salir"); salir.clicked.connect(self.cerrar)
        caja.addWidget(marca); caja.addWidget(api); caja.addStretch(); caja.addWidget(sesion); caja.addWidget(salir)


class Ventana(QMainWindow):
    sesion_cerrada = Signal()
    def __init__(self, cliente):
        super().__init__(); self.cliente = cliente; usuario = cliente.usuario or {}; rol = usuario.get("rol", "")
        self.setWindowTitle("Centro de devoluciones — Plataforma distribuida"); self.resize(1240, 780); self.setMinimumSize(960, 640)
        raiz = QWidget(); raiz.setObjectName("raiz"); layout = QVBoxLayout(raiz); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        encabezado = Encabezado(usuario); encabezado.cerrar.connect(self.cerrar_sesion); layout.addWidget(encabezado)
        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True); layout.addWidget(self.tabs); self.setCentralWidget(raiz)
        self._agregar_modulos(rol); self.statusBar().showMessage("Conectado · Sesión y tokens únicamente en memoria · Comunicación XML/XSD")

    def agregar(self, widget, etiqueta):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(widget); self.tabs.addTab(scroll, etiqueta)

    def _agregar_modulos(self, rol):
        if rol in (INSPECTOR, CENTRO):
            self.agregar(TablaServicio("Trabajo pendiente", "Productos recibidos que todavía requieren inspección técnica.", lambda: self.cliente.solicitar("inspecciones", "GET", "/api/v1/inspecciones/pendientes"), ("prioridad", "id", "folio_devolucion", "producto", "clasificacion_temperatura", "numero_lote")), "Panel")
        elif rol in (ANALISTA, SUPERVISOR):
            self.agregar(TablaServicio("Decisiones pendientes", "Dictámenes técnicos que esperan una decisión humana de disposición.", lambda: self.cliente.solicitar("disposicion", "GET", "/api/v1/disposicion-inventario/pendientes"), ("id", "folio_devolucion", "producto", "estado_dictamen", "apto_para_inventario", "recomendacion")), "Panel")
        elif rol == REEMBOLSOS:
            self.agregar(TablaServicio("Reembolsos registrados", "Historial económico consultado directamente al microservicio.", lambda: self.cliente.solicitar("reembolsos", "GET", "/api/v1/reembolsos-costos/reembolsos"), ("id", "folio_devolucion", "monto", "metodo", "estado", "fecha_resolucion")), "Panel")
        if rol == INSPECTOR: self.agregar(Inspeccion(self.cliente), "Inspección")
        if rol in (ANALISTA, SUPERVISOR): self.agregar(Disposicion(self.cliente), "Disposición")
        if rol == REEMBOLSOS: self.agregar(Reembolso(self.cliente), "Reembolso")
        if rol in (CENTRO, SUPERVISOR): self.agregar(Inventario(self.cliente), "Inventario")
        if rol in (CENTRO, ANALISTA, SUPERVISOR):
            self.agregar(TablaServicio("Inventario recuperado", "Trazabilidad de artículos en cuarentena, bloqueados o disponibles.", lambda: self.cliente.solicitar("disposicion", "GET", "/api/v1/disposicion-inventario/inventario"), ("id", "etiqueta_codigo", "producto", "estado", "ubicacion", "folio_devolucion")), "Existencias")
        if rol in (CENTRO, INSPECTOR, ANALISTA, SUPERVISOR):
            self.agregar(TablaServicio("Evidencias del expediente", "Metadatos de evidencias del cliente, recolección, recepción e inspección.", lambda: self.cliente.solicitar("evidencias", "GET", "/api/v1/evidencias"), ("id", "devolucion_id", "tipo", "etapa", "fecha")), "Evidencias")
        if rol in (ANALISTA, REEMBOLSOS):
            self.agregar(TablaServicio("Reembolsos", "Consulta de resoluciones económicas; la base conserva unicidad por devolución.", lambda: self.cliente.solicitar("reembolsos", "GET", "/api/v1/reembolsos-costos/reembolsos"), ("id", "folio_devolucion", "monto", "metodo", "estado", "encargado")), "Historial")
        if rol in (ADMIN, ANALISTA):
            self.agregar(TablaServicio("Auditoría de operaciones", "Registro de solo lectura. La aplicación no puede alterar la bitácora.", lambda: self.cliente.solicitar("analisis", "GET", "/api/v1/auditoria"), ("fecha", "usuario", "accion", "entidad", "entidad_id")), "Auditoría")
            self.agregar(TablaServicio("Investigación de causas", "Eventos y señales para analizar patrones sistémicos sin modificar la auditoría.", lambda: self.cliente.solicitar("analisis", "GET", "/api/v1/analisis/eventos"), ("fecha", "servicio", "tipo", "devolucion_id")), "Investigaciones")
        if self.tabs.count() == 0:
            self.agregar(Pagina("Sin operaciones de escritorio", "Tu rol no tiene procesos asignados en el centro de devoluciones."), "Inicio")

    def cerrar_sesion(self):
        self.cliente.cerrar_sesion_local(); self.sesion_cerrada.emit(); self.close()


class Login(QWidget):
    autenticado = Signal(object)
    def __init__(self, cliente):
        super().__init__(); self.cliente = cliente; self.setWindowTitle("Acceso XML — Centro de devoluciones"); self.setFixedSize(460, 440)
        exterior = QVBoxLayout(self); exterior.setContentsMargins(38, 30, 38, 34); exterior.setSpacing(12)
        marca = QLabel("DEVOLUCIONES · LOGÍSTICA INVERSA"); marca.setObjectName("marca"); marca.setStyleSheet("color: #1f6f4a;")
        titulo = QLabel("Centro de devoluciones"); titulo.setObjectName("titulo")
        sub = QLabel("Aplicación de escritorio conectada a microservicios mediante XML validado con XSD."); sub.setObjectName("subtitulo"); sub.setWordWrap(True)
        tarjeta = Tarjeta(); form = QFormLayout(tarjeta); form.setContentsMargins(22, 20, 22, 20); form.setSpacing(12)
        self.email = QLineEdit(); self.email.setPlaceholderText("nombre@demo.mx")
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password); self.password.setPlaceholderText("Contraseña")
        self.boton = QPushButton("Iniciar sesión"); self.boton.clicked.connect(self.entrar); self.password.returnPressed.connect(self.entrar)
        form.addRow("Correo", self.email); form.addRow("Contraseña", self.password); form.addRow("", self.boton)
        seguridad = QLabel("Los tokens se conservan solo en memoria y se eliminan al cerrar sesión."); seguridad.setObjectName("ayuda"); seguridad.setWordWrap(True)
        exterior.addWidget(marca); exterior.addWidget(titulo); exterior.addWidget(sub); exterior.addSpacing(6); exterior.addWidget(tarjeta); exterior.addWidget(seguridad); exterior.addStretch()

    def entrar(self):
        email, password = self.email.text().strip(), self.password.text()
        if not email or not password: return QMessageBox.warning(self, "Datos incompletos", "Captura correo y contraseña.")
        self.boton.setEnabled(False); self.boton.setText("Verificando…")
        self.trabajo = Trabajo(lambda: self.cliente.login(email, password), self)
        self.trabajo.terminado.connect(self._abrir)
        self.trabajo.fallo.connect(lambda e: QMessageBox.critical(self, "Acceso rechazado", texto_error(e)))
        self.trabajo.finished.connect(lambda: (self.boton.setEnabled(True), self.boton.setText("Iniciar sesión")))
        self.trabajo.start()

    def _abrir(self, _respuesta):
        self.autenticado.emit(self.cliente); self.hide()


class Controlador:
    def __init__(self):
        self.cliente = ClienteXml(); self.login = None; self.ventana = None; self.mostrar_login()

    def mostrar_login(self):
        self.login = Login(self.cliente); self.login.autenticado.connect(self.mostrar_principal); self.login.show()

    def mostrar_principal(self, cliente):
        self.ventana = Ventana(cliente); self.ventana.sesion_cerrada.connect(self.mostrar_login); self.ventana.show(); self.login.close()


def crear_aplicacion(argv=None):
    app = QApplication.instance() or QApplication(argv or sys.argv)
    app.setWindowIcon(QIcon(str(RAIZ / "apps/escritorio/assets/orvia-hoja.png")))
    app.setApplicationName("Centro de devoluciones"); app.setStyle("Fusion"); app.setStyleSheet(ESTILO)
    return app


def main():
    app = crear_aplicacion(); controlador = Controlador(); app.controlador = controlador
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
