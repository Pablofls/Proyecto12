"""Notificaciones internas por rol (RF-29, UC-25, RN-13)."""
import unittest

from app.notificaciones import EVENTOS, CLIENTE_DEL_CASO, notificar_evento
from app.security import (
    ANALISTA, CLIENTE, COORDINADOR, ENCARGADO_CENTRO, ENCARGADO_REEMBOLSOS, INSPECTOR,
    TODOS_LOS_ROLES,
)
from app.tests.dobles import PruebaWeb

EXPEDIENTE = {"id": 40, "folio_devolucion": "DEV-0040", "cliente_id": 9}


class PruebaBandeja(PruebaWeb):
    def test_sin_sesion_redirige_al_login(self):
        resp = self.app.test_client().get("/notificaciones/resumen")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_resumen_solo_consulta_las_del_usuario_en_sesion(self):
        self.bd.cuando("COUNT(*) AS n", {"n": 3})
        self.bd.cuando("SELECT id, mensaje, leido", [])
        resp = self.cliente_como(CLIENTE, usuario_id=9).get("/notificaciones/resumen")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"no_leidas": 3, "ultimas": []})
        self.assertEqual(resp.headers["Cache-Control"], "no-store")
        for _, params in self.bd.consultas:
            self.assertEqual(params[0], 9)

    def test_leer_una_ajena_responde_404_y_no_actualiza(self):
        # La consulta incluye usuario_id: una fila de otro usuario no aparece.
        self.bd.cuando("FROM notificaciones WHERE id", None)
        resp = self.cliente_como(CLIENTE, usuario_id=9).post("/notificaciones/5/leer")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.bd.actualizadas("notificaciones"), [])
        self.assertEqual(self.bd.consultas[0][1], (5, 9))

    def test_leer_propia_marca_leida_y_redirige_al_destino(self):
        self.bd.cuando("FROM notificaciones WHERE id",
                       {"id": 5, "url": "/devoluciones/40", "devolucion_id": 40})
        resp = self.cliente_como(ANALISTA, usuario_id=3).post("/notificaciones/5/leer")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], "/devoluciones/40")
        (sql, params), = self.bd.actualizadas("notificaciones")
        self.assertEqual(params, (5, 3))
        acciones = [p[1] for p in self.bd.insertadas("bitacora")]
        self.assertIn("leer_notificacion", acciones)

    def test_destino_externo_se_ignora(self):
        for url in ("//evil.example/x", "https://evil.example/x", "/\\evil"):
            self.bd.reglas.clear()
            self.bd.cuando("FROM notificaciones WHERE id",
                           {"id": 5, "url": url, "devolucion_id": 40})
            resp = self.cliente_como(ANALISTA, usuario_id=3).post("/notificaciones/5/leer")
            self.assertEqual(resp.headers["Location"], "/devoluciones/40", url)

    def test_leer_todas_filtra_por_usuario(self):
        self.bd.cuando("WITH marcadas", {"n": 4})
        resp = self.cliente_como(CLIENTE, usuario_id=9).post("/notificaciones/leer-todas")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.bd.consultas[0][1], (9,))
        self.assertIn("4 notificacion", self.bd.insertadas("bitacora")[0][4])

    def test_filtro_no_leidas_usa_parametros_ligados(self):
        self.bd.cuando("COUNT(*) AS cuenta", {"cuenta": 0})
        resp = self.cliente_como(CLIENTE, usuario_id=9).get(
            "/notificaciones/?filtro=no_leidas&pagina=1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("No tienes notificaciones sin leer", resp.get_data(as_text=True))
        sql_total, params_total = self.bd.consultas[0]
        self.assertIn("NOT n.leido", sql_total)
        self.assertEqual(params_total, (9,))


class PruebaDestinatarios(PruebaWeb):
    def _usuarios_por_rol(self, mapa):
        self.bd.cuando("FROM usuarios u JOIN roles r",
                       lambda sql, params: [{"id": i} for i in mapa.get(params[0], [])])

    def _avisos(self):
        # (usuario_id, tipo, mensaje, url)
        return [(p[0], p[2], p[3], p[4]) for p in self.bd.insertadas("notificaciones")]

    def notificar(self, evento, rol=ANALISTA, usuario_id=3, **kw):
        cliente = self.cliente_como(rol, usuario_id)
        with self.app.test_request_context():
            from flask import session
            session["usuario"] = {"id": usuario_id, "nombre": "x", "email": "x", "rol": rol}
            return notificar_evento(evento, EXPEDIENTE, **kw)

    def test_autorizacion_avisa_al_cliente_y_al_coordinador_con_su_enlace(self):
        self._usuarios_por_rol({COORDINADOR: [20, 21]})
        self.assertEqual(self.notificar("autorizacion"), 3)
        avisos = self._avisos()
        self.assertEqual(avisos[0][:1], (9,))
        self.assertEqual(avisos[0][3], "/devoluciones/40")
        self.assertEqual({a[0] for a in avisos[1:]}, {20, 21})
        self.assertTrue(all(a[3] == "/logistica/recolecciones/40/programar" for a in avisos[1:]))
        self.assertTrue(all("DEV-0040" in a[2] for a in avisos))

    def test_omitir_cliente_salta_al_cliente_del_caso(self):
        self._usuarios_por_rol({ANALISTA: [3, 4]})
        self.notificar("reembolso_aprobado", rol=ENCARGADO_REEMBOLSOS, usuario_id=8,
                       omitir_cliente=True, monto="150.00")
        avisos = self._avisos()
        self.assertEqual({a[0] for a in avisos}, {3, 4})
        self.assertIn("$150.00", avisos[0][2])

    def test_quien_ejecuta_no_se_notifica_a_si_mismo(self):
        self._usuarios_por_rol({ANALISTA: [3]})
        self.notificar("solicitud_nueva", rol=ANALISTA, usuario_id=3)
        self.assertEqual(self._avisos(), [])

    def test_rol_sin_usuarios_se_omite_y_queda_en_bitacora(self):
        self._usuarios_por_rol({})
        self.assertEqual(self.notificar("recepcion_confirmada", rol=ENCARGADO_CENTRO,
                                        usuario_id=5), 1)
        self.assertEqual([a[0] for a in self._avisos()], [9])
        omitidas = [p for p in self.bd.insertadas("bitacora") if p[1] == "notificacion_omitida"]
        self.assertEqual(len(omitidas), 1)

    def test_recepcion_va_al_inspector_con_enlace_de_inspeccion(self):
        self._usuarios_por_rol({INSPECTOR: [30]})
        self.notificar("recepcion_confirmada", rol=ENCARGADO_CENTRO, usuario_id=5)
        inspector = [a for a in self._avisos() if a[0] == 30][0]
        self.assertEqual(inspector[3], "/inspecciones/40/registrar")

    def test_disposicion_a_inventario_avisa_al_centro_a_la_bandeja_de_inventario(self):
        self._usuarios_por_rol({ENCARGADO_CENTRO: [6]})
        self.notificar("disposicion_inventario")
        self.assertEqual(self._avisos()[0][3], "/inspecciones/inventario")

    def test_mensaje_largo_se_recorta_a_500(self):
        self._usuarios_por_rol({})
        self.notificar("rechazo", nota="x" * 900)
        self.assertEqual(len(self._avisos()[0][2]), 500)

    def test_matriz_cubre_el_flujo_y_solo_usa_roles_conocidos(self):
        destinatarios = set()
        for avisos in EVENTOS.values():
            for destinatario, tipo, mensaje, endpoint in avisos:
                destinatarios.add(destinatario)
                self.assertLessEqual(len(tipo), 50)
        validos = set(TODOS_LOS_ROLES) | {CLIENTE_DEL_CASO}
        self.assertTrue(destinatarios <= validos)
        # El Administrador no recibe avisos de flujo.
        self.assertNotIn("Administrador", destinatarios)
        # Los siete roles de negocio que actuan en el flujo reciben algo.
        self.assertTrue({ANALISTA, COORDINADOR, ENCARGADO_CENTRO, INSPECTOR,
                         ENCARGADO_REEMBOLSOS, CLIENTE_DEL_CASO} <= destinatarios)


if __name__ == "__main__":
    unittest.main()
