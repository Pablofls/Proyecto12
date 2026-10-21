# Se construye desde la raiz del repositorio (ver docker-compose.yml) para
# poder copiar la carpeta shared/, comun a todos los microservicios.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv

WORKDIR /srv
COPY services/auth/requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

COPY shared/ /srv/shared/
COPY services/auth/ /srv/servicio/
WORKDIR /srv/servicio

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:create_app()"]
