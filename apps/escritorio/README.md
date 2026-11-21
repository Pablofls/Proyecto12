# Aplicacion de escritorio del centro de devoluciones

Cliente PySide6 de Roberto. No accede directamente a PostgreSQL, MongoDB ni
Redis y no repite reglas del negocio: consume los microservicios desplegados.
Todas sus peticiones y respuestas usan `application/xml`; los cuerpos se
validan localmente con XSD antes de enviarse y nuevamente en el servicio.

1. Copiar `config.example.json` como `config.json` y ajustar las URL.
2. Instalar: `python -m pip install -r apps/escritorio/requirements.txt`.
3. Ejecutar desde la raiz: `python apps/escritorio/main.py`.

Los tokens viven solo en memoria durante la sesion. Las decisiones críticas
requieren un token de operación de un solo uso emitido por `auth`.
