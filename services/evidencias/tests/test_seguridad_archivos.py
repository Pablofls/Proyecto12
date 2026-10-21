"""Pruebas locales: MIME por magic bytes y caducidad del enlace firmado."""
import io
import os
import time
import pytest
from shared.respuestas import ErrorApi
import app


def test_detecta_mime_por_contenido():
    assert app._tipo_real(b"%PDF-1.7\n...")=="application/pdf"
    assert app._tipo_real(b"\x89PNG\r\n\x1a\nresto")=="image/png"
    assert app._tipo_real(b"\xff\xd8\xffimage")=="image/jpeg"
    assert app._tipo_real(b".exe")==None


def test_enlace_temporal_firmado(monkeypatch):
    monkeypatch.setenv("JWT_SECRET","f"*40)
    exp=int(time.time())+300
    firma=app._firma(53,exp)
    assert app.firma_valida(53,str(exp),firma)
    assert not app.firma_valida(54,str(exp),firma)
    assert not app.firma_valida(53,str(exp),"0"*64)
    assert not app.firma_valida(53,str(int(time.time())-10),firma)


class Archivo:
    filename="evidencia.pdf"
    def __init__(self,cuerpo):self.stream=io.BytesIO(cuerpo)


def test_archivo_crea_id_privado_y_rechaza_exe(monkeypatch,tmp_path):
    monkeypatch.setattr(app,"DIR",tmp_path)
    registrado=app.guardar_archivo(Archivo(b"%PDF-1.7\ncontenido"))
    assert app.OBJETO_SEGURO.fullmatch(registrado["objeto"])
    assert registrado["ruta"].is_file()
    assert registrado["mime_type"]=="application/pdf"
    with pytest.raises(ErrorApi) as err:
        app.guardar_archivo(Archivo(b"MZ exe ejecutable"))
    assert err.value.codigo==415

