# Reverse proxy de Orvia

## Objetivo

Nginx es el único punto de entrada público. La web y las API permanecen en la
red interna `orvia_backend`; sus puertos `8000–8021` ya no se publican en el
host. Esto cubre control de puertos, propagación de IP y correlation ID,
límites de petición y terminación TLS.

## Acceso

| Recurso | URL pública |
|---|---|
| Sistema web | `http(s)://HOST/` |
| API | `http(s)://HOST/api/v1/...` |
| Salud del proxy | `http(s)://HOST/proxy-health` |
| Swagger de auth | `http(s)://HOST/servicios/auth/docs` |
| Salud de auth | `http(s)://HOST/servicios/auth/health` |
| Contrato de un servicio | `http(s)://HOST/servicios/SERVICIO/contratos/NOMBRE.xsd` |

Los prefijos disponibles bajo `/servicios/` son `auth`, `devoluciones`,
`logistica`, `inspecciones`, `reembolsos-costos`, `ventas-catalogos`,
`evidencias`, `auditoria`, `reportes-analitica`, `causa-raiz`,
`sincronizacion`, `proveedores`, `integraciones-monitoreo` y
`clasificacion-motivos`.

## Desarrollo o demostración HTTP

En `.env`, defina `PROXY_HTTP_PORT=80` y levante normalmente:

```bash
docker compose up -d --build
curl -i http://localhost/proxy-health
curl -i http://localhost/servicios/auth/health
```

Sólo Nginx aparece publicado en `0.0.0.0`. PostgreSQL, Redis y MongoDB conservan
sus enlaces administrativos exclusivamente en `127.0.0.1`.

## Producción con HTTPS

Obtenga un certificado válido para el dominio y defina rutas absolutas en
`.env`:

```dotenv
TLS_CERT_PATH=/etc/letsencrypt/live/orvia.example/fullchain.pem
TLS_KEY_PATH=/etc/letsencrypt/live/orvia.example/privkey.pem
PROXY_HTTP_PORT=80
PROXY_HTTPS_PORT=443
```

Después:

```bash
docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d --build
curl -i https://orvia.example/proxy-health
```

La variante TLS redirige HTTP a HTTPS, admite únicamente TLS 1.2/1.3 y agrega
HSTS. No se almacenan certificados ni llaves en Git.

## Seguridad y trazabilidad

- Nginx reemplaza el correlation ID vacío por `$request_id` y lo propaga.
- `X-Forwarded-For` conserva la IP observada por el último proxy. Los servicios
  sólo confían en él cuando `TRUST_PROXY_HEADERS=true`.
- El login tiene un límite adicional de 10 solicitudes por minuto; Redis sigue
  aplicando la política de autenticación de negocio.
- Las cargas admiten hasta 30 MB; las respuestas extensas de reportes tienen
  timeout de 120 segundos.
- No se agregan cabeceras CORS: web, Android y escritorio usan el mismo origen o
  son clientes nativos.

## Reversión y diagnóstico

```bash
docker compose config
docker compose exec proxy nginx -t
docker compose logs proxy
docker compose ps
```

Para depurar un servicio no se vuelve a abrir su puerto. Use, por ejemplo,
`docker compose exec auth wget -qO- http://localhost:8000/health` o su URL bajo
`/servicios/`. El archivo `scripts/probar_proxy.py` verifica todos los health
checks a través de Nginx.
