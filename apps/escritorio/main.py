"""Aplicacion PySide6 para el centro de devoluciones; toda operacion usa XML."""
import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QApplication, QFormLayout, QHBoxLayout, QLabel,
                               QCheckBox, QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QTabWidget, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from cliente_xml import ClienteXml, ErrorServicio


class Trabajo(QThread):
    terminado = Signal(object)
    fallo = Signal(str)

    def __init__(self, funcion):
        super().__init__(); self.funcion = funcion

    def run(self):
        try: self.terminado.emit(self.funcion())
        except Exception as exc: self.fallo.emit(str(exc))


class TablaServicio(QWidget):
    def __init__(self, titulo, cargador):
        super().__init__(); self.cargador = cargador; self.titulo = titulo
        layout = QVBoxLayout(self); layout.addWidget(QLabel(titulo))
        self.tabla = QTableWidget(); layout.addWidget(self.tabla)
        boton = QPushButton("Actualizar desde microservicios"); boton.clicked.connect(self.actualizar)
        layout.addWidget(boton)

    def actualizar(self):
        self.trabajo = Trabajo(self.cargador); self.trabajo.terminado.connect(self.mostrar)
        self.trabajo.fallo.connect(lambda m: QMessageBox.critical(self, "Error", m))
        self.trabajo.start()

    def mostrar(self, respuesta):
        filas = respuesta.get("datos", []) if isinstance(respuesta, dict) else []
        if isinstance(filas, dict): filas = [filas]
        columnas = sorted({k for fila in filas for k in fila}) if filas else []
        self.tabla.setColumnCount(len(columnas)); self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            for j, col in enumerate(columnas): self.tabla.setItem(i, j, QTableWidgetItem(str(fila.get(col, ""))))
        self.tabla.resizeColumnsToContents()


class Operaciones(QWidget):
    """Captura operaciones reales; la UI solo arma XML y la API decide."""
    def __init__(self, cliente):
        super().__init__(); self.cliente = cliente; layout = QVBoxLayout(self)
        form = QFormLayout(); self.devolucion = QLineEdit(); self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.empaque = QLineEdit("Empaque sin alteraciones"); self.destino = QLineEdit("reintegrar")
        self.temperatura = QLineEdit(); self.minutos_frio = QLineEdit()
        self.danos = QCheckBox(); self.empaque_alterado = QCheckBox()
        self.faltantes = QCheckBox(); self.cadena_rota = QCheckBox()
        self.evidencia_suficiente = QCheckBox(); self.evidencia_suficiente.setChecked(True)
        self.justificacion = QLineEdit("Producto recuperable conforme al dictamen tecnico")
        self.monto = QLineEdit("0.00"); self.metodo = QLineEdit("tarjeta")
        form.addRow("Devolucion ID", self.devolucion); form.addRow("Estado del empaque", self.empaque)
        form.addRow("Temperatura °C (solo refrigerado)", self.temperatura)
        form.addRow("Minutos fuera (solo refrigerado)", self.minutos_frio)
        form.addRow("Daños visibles", self.danos); form.addRow("Empaque alterado", self.empaque_alterado)
        form.addRow("Faltantes", self.faltantes); form.addRow("Cadena de frío rota", self.cadena_rota)
        form.addRow("Evidencia suficiente", self.evidencia_suficiente)
        form.addRow("Destino", self.destino); form.addRow("Justificacion", self.justificacion)
        form.addRow("Monto", self.monto); form.addRow("Metodo", self.metodo)
        form.addRow("Confirmar contrasena", self.password); layout.addLayout(form)
        acciones = QHBoxLayout()
        for texto, funcion in (("Registrar inspeccion", self.inspeccionar),
                               ("Autorizar disposicion", self.disponer),
                               ("Aprobar reembolso", self.reembolsar)):
            boton = QPushButton(texto); boton.clicked.connect(funcion); acciones.addWidget(boton)
        layout.addLayout(acciones); self.resultado = QLabel("Listo")
        self.resultado.setWordWrap(True); layout.addWidget(self.resultado)

    def _id(self):
        valor = int(self.devolucion.text())
        if valor < 1: raise ValueError("La devolucion debe ser positiva.")
        return valor

    def _ejecutar(self, funcion):
        self.trabajo = Trabajo(funcion)
        self.trabajo.terminado.connect(lambda r: self.resultado.setText(str(r)))
        self.trabajo.fallo.connect(lambda m: QMessageBox.critical(self, "Operacion rechazada", m))
        self.trabajo.start()

    def inspeccionar(self):
        devolucion, empaque = self._id(), self.empaque.text()
        temperatura, minutos = self.temperatura.text().strip(), self.minutos_frio.text().strip()
        danos, alterado = self.danos.isChecked(), self.empaque_alterado.isChecked()
        faltantes, cadena = self.faltantes.isChecked(), self.cadena_rota.isChecked()
        evidencia = self.evidencia_suficiente.isChecked()
        def accion():
            xsd = Path(__file__).parents[2] / "services" / "inspecciones" / "contratos" / "inspeccion.xsd"
            datos={"devolucion_id": devolucion, "estado_empaque": empaque,
                "danos": danos, "empaque_alterado": alterado, "faltantes": faltantes,
                "caducidad_vencida": False, "cadena_frio_rota": cadena}
            if minutos: datos["minutos_fuera_refrigeracion"] = minutos
            if temperatura: datos["temperatura_recepcion"] = temperatura
            datos.update({"condicion_transporte": "adecuada", "evidencia_suficiente": evidencia})
            return self.cliente.solicitar("inspecciones", "POST", "/api/v1/inspecciones",
                raiz="inspeccion", xsd=xsd, datos=datos)
        self._ejecutar(accion)

    def disponer(self):
        devolucion, password = self._id(), self.password.text()
        destino, justificacion = self.destino.text(), self.justificacion.text()
        def accion():
            permiso = self.cliente.autorizar(
                "aprobar_disposicion", str(devolucion), password)
            xsd = Path(__file__).parents[2] / "services" / "disposicion_inventario" / "contratos" / "disposicion.xsd"
            return self.cliente.solicitar("disposicion", "POST",
                "/api/v1/disposicion-inventario/disposiciones", raiz="disposicion", xsd=xsd,
                datos={"devolucion_id": devolucion, "destino": destino,
                       "justificacion": justificacion}, token_operacion=permiso)
        self._ejecutar(accion)

    def reembolsar(self):
        devolucion, password = self._id(), self.password.text()
        monto, metodo = self.monto.text(), self.metodo.text()
        def accion():
            permiso = self.cliente.autorizar(
                "aprobar_reembolso", str(devolucion), password)
            xsd = Path(__file__).parents[2] / "services" / "reembolsos_costos" / "contratos" / "reembolso.xsd"
            return self.cliente.solicitar("reembolsos", "POST",
                "/api/v1/reembolsos-costos/reembolsos", raiz="reembolso", xsd=xsd,
                datos={"devolucion_id": devolucion, "monto": monto,
                       "estado": "aprobado", "metodo": metodo},
                token_operacion=permiso)
        self._ejecutar(accion)


class Ventana(QMainWindow):
    def __init__(self, cliente):
        super().__init__(); self.cliente = cliente
        self.setWindowTitle("Centro de devoluciones — Roberto"); self.resize(1180, 720)
        tabs = QTabWidget(); self.setCentralWidget(tabs)
        tabs.addTab(Operaciones(cliente), "Operaciones")
        tabs.addTab(TablaServicio("Panel: dictamenes pendientes", lambda:
            cliente.solicitar("disposicion", "GET", "/api/v1/disposicion-inventario/pendientes")), "Panel")
        tabs.addTab(TablaServicio("Inspecciones tecnicas", lambda:
            cliente.solicitar("inspecciones", "GET", "/api/v1/inspecciones/pendientes")), "Inspeccion")
        tabs.addTab(TablaServicio("Evidencias del expediente", lambda:
            cliente.solicitar("evidencias", "GET", "/api/v1/evidencias")), "Evidencias")
        tabs.addTab(TablaServicio("Disposiciones", lambda:
            cliente.solicitar("disposicion", "GET", "/api/v1/disposicion-inventario/pendientes")), "Disposicion")
        tabs.addTab(TablaServicio("Reembolsos", lambda:
            cliente.solicitar("reembolsos", "GET", "/api/v1/reembolsos-costos/reembolsos")), "Reembolsos")
        tabs.addTab(TablaServicio("Inventario recuperado", lambda:
            cliente.solicitar("disposicion", "GET", "/api/v1/disposicion-inventario/inventario")), "Inventario")
        tabs.addTab(TablaServicio("Auditoria (solo lectura)", lambda:
            cliente.solicitar("analisis", "GET", "/api/v1/auditoria")), "Auditoria")
        tabs.addTab(TablaServicio("Investigaciones (solo lectura)", lambda:
            cliente.solicitar("analisis", "GET", "/api/v1/analisis/eventos")), "Investigaciones")


class Login(QWidget):
    def __init__(self, cliente):
        super().__init__(); self.cliente = cliente; self.setWindowTitle("Acceso XML")
        form = QFormLayout(self); self.email = QLineEdit(); self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("Correo", self.email); form.addRow("Contrasena", self.password)
        boton = QPushButton("Iniciar sesion"); boton.clicked.connect(self.entrar); form.addRow(boton)

    def entrar(self):
        try:
            self.cliente.login(self.email.text(), self.password.text())
            self.ventana = Ventana(self.cliente); self.ventana.show(); self.close()
        except ErrorServicio as exc:
            QMessageBox.critical(self, "Acceso rechazado", f"{exc}\nCID: {exc.correlation_id or '-'}")


def main():
    app = QApplication(sys.argv); login = Login(ClienteXml()); login.show(); sys.exit(app.exec())


if __name__ == "__main__": main()
