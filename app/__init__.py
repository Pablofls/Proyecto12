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

    app.teardown_appcontext(db.cerrar_conn)

    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.catalogos import bp as catalogos_bp
    from app.blueprints.devoluciones import bp as devoluciones_bp
    from app.blueprints.inspecciones import bp as inspecciones_bp
    from app.blueprints.logistica import bp as logistica_bp
    from app.blueprints.panel import bp as panel_bp
    from app.blueprints.reembolsos import bp as reembolsos_bp
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
    app.register_blueprint(reembolsos_bp)

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
        }

    return app
