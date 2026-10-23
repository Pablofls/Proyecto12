"""Panel web de integracion y salud de microservicios (RNF-22, RF-32)."""
from flask import Blueprint, render_template

from app.microservicios import estado_arquitectura
from app.security import ADMINISTRADOR, roles_required

bp = Blueprint("integracion", __name__, url_prefix="/integracion")


@bp.get("/servicios")
@roles_required(ADMINISTRADOR)
def servicios():
    estados = estado_arquitectura()
    return render_template(
        "integracion/servicios.html",
        estados=estados,
        disponibles=sum(1 for estado in estados if estado["disponible"]),
    )
