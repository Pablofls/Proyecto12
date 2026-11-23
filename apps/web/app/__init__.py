"""Plataforma de devoluciones y logistica inversa -- monolito modular.

Primer parcial: sistema web funcional sobre PostgreSQL y Redis, ejecutado en
contenedores dentro de la VM de GCP. La organizacion sigue el patron MVC
descrito en la seccion 5.2 del documento: cada blueprint es un modulo del
negocio y las plantillas Jinja2 son la capa de presentacion.
"""
import os

from flask import Flask, jsonify, render_template
from flask_session import Session

from app import cache, db
from app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SESSION_REDIS"] = Config.session_redis()
    Session(app)

    # Integración segura: apagada por defecto, sin tocar la app del equipo.
    app.config["ORVIA_PLIEGUE20"] = os.environ.get("ORVIA_PLIEGUE20") == "1"
    app.config["PLIEGUE_LAB"] = False
    app.config["PLIEGUE_VISUAL"] = (app.config["ORVIA_PLIEGUE20"] and
                                    os.environ.get("PLIEGUE_GLOBAL_CODE") == "1")
    app.config["PLIEGUE_FASE6"] = (app.config["ORVIA_PLIEGUE20"] and
                                   os.environ.get("PLIEGUE_FASE6") == "1")
    app.config["PLIEGUE_WORKER_SOCKET"] = os.environ.get("PLIEGUE_WORKER_SOCKET", "")

    app.teardown_appcontext(db.cerrar_conn)

    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.catalogos import bp as catalogos_bp
    from app.blueprints.devoluciones import bp as devoluciones_bp
    from app.blueprints.inspecciones import bp as inspecciones_bp
    from app.blueprints.integracion import bp as integracion_bp
    from app.blueprints.logistica import bp as logistica_bp
    from app.blueprints.notificaciones import bp as notificaciones_bp
    from app.blueprints.panel import bp as panel_bp
    from app.blueprints.reembolsos import bp as reembolsos_bp
    from app.blueprints.reportes import bp as reportes_bp
    from app.blueprints.usuarios import bp as usuarios_bp
    from app.blueprints.ventas import bp as ventas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(panel_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(catalogos_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(devoluciones_bp)
    app.register_blueprint(logistica_bp)
    app.register_blueprint(inspecciones_bp)
    app.register_blueprint(integracion_bp)
    app.register_blueprint(reembolsos_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(reportes_bp)

    if app.config["ORVIA_PLIEGUE20"]:
        from app.blueprints.pliegue import bp as pliegue_bp, orvia as pliegue_orvia_bp
        app.register_blueprint(pliegue_bp)
        app.register_blueprint(pliegue_orvia_bp)
        from app.pliegue_asistente_roles import bp as pliegue_roles_bp
        app.register_blueprint(pliegue_roles_bp)

    @app.get("/health")
    def health():
        """Health check del monolito y sus dependencias (RNF-22, RF-32)."""
        pg_ok, pg_error = db.salud()
        redis_ok, redis_error = cache.salud()
        estado = "ok" if pg_ok and redis_ok else "degradado"
        cuerpo = {
            "servicio": "web-devoluciones",
            "estado": estado,
            "dependencias": {
                "postgresql": {"ok": pg_ok, "error": pg_error},
                "redis": {"ok": redis_ok, "error": redis_error},
            },
        }
        return jsonify(cuerpo), (200 if estado == "ok" else 503)

    @app.errorhandler(403)
    def sin_permiso(_):
        return render_template("error.html", codigo=403,
                               mensaje="No tienes permiso para acceder a esta seccion."), 403

    @app.errorhandler(404)
    def no_encontrado(_):
        return render_template("error.html", codigo=404,
                               mensaje="La pagina solicitada no existe."), 404

    @app.context_processor
    def inyectar_contexto():
        from app.security import TODOS_LOS_ROLES, rol_actual, usuario_actual
        return {
            "usuario_actual": usuario_actual(),
            "rol_actual": rol_actual(),
            "TODOS": list(TODOS_LOS_ROLES),
            "modo_distribuido": app.config["USE_MICROSERVICES"],
        }

    @app.context_processor
    def inyectar_pliegue20():
        # No filtrar secretos ni registros privados en el contexto compartido.
        if not app.config["ORVIA_PLIEGUE20"]:
            return {"pliegue_activo": False}
        from app.blueprints.pliegue import code_csrf, orvia_pages, public_context
        from app.security import rol_actual
        info = public_context()
        admin = rol_actual() == "Administrador"
        info["is_admin"] = admin
        return {
            "pliegue_activo": True,
            "pliegue_boot": info,
            "orvia_pages": orvia_pages() if admin else {},
            "csrf": code_csrf() if admin else "",
        }


    # PLIEGUE20: REGISTRO OPT-IN VERIFICADO
    # Inactivo por defecto. No habilita Codex en instalaciones que no lo soliciten.
    if os.environ.get("PLIEGUE_LAB", "").strip().lower() in ("1", "true", "yes", "si"):
        for _flag in ("PLIEGUE_LAB", "PLIEGUE_VISUAL", "PLIEGUE_FASE6", "PLIEGUE_REVISIONS"):
            app.config[_flag] = os.environ.get(_flag, "1").strip().lower() in ("1", "true", "yes", "si")

        from app.blueprints.pliegue import bp as _pliegue_bp, orvia as _pliegue_orvia_bp
        from app.pliegue_asistente_roles import bp as _pliegue_roles_bp

        # No se duplican blueprints si una configuración anterior ya los registró.
        for _pliegue_blueprint in (_pliegue_bp, _pliegue_orvia_bp, _pliegue_roles_bp):
            if _pliegue_blueprint.name not in app.blueprints:
                app.register_blueprint(_pliegue_blueprint)
    # FIN PLIEGUE20: REGISTRO OPT-IN VERIFICADO

    return app
