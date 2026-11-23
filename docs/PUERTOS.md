# Contenedores y puertos internos del tercer parcial

> Los números 8000–8021 identifican los servicios en desarrollo y en la
> documentación histórica. En Docker todos escuchan en `8000` dentro de la red
> privada y los clientes acceden exclusivamente mediante Nginx por 80/443.

La retroalimentacion del segundo parcial pide cubrir 22 dominios funcionales,
pero aclara que **no es obligatorio desplegar 22 contenedores**: se pueden
agrupar si se justifican sus limites y existe consistencia transaccional. Esta
propuesta usa 16 contenedores: los 8 actuales (con sus puertos sin cambios) y 8
nuevos.

## Contenedores

| Puerto | Contenedor | Dominios que cubre (numero de la retroalimentacion) | Estado |
|---|---|---|---|
| 8000 | app (web) | Sistema web | existente |
| 8001 | auth | 1 auth (+ sucursal y operaciones criticas) | existente |
| 8002 | devoluciones | 2 devoluciones (+ plazos, elegibilidad, duplicados) | existente |
| 8003 | logistica | 3 logistica + 16 transporte-seguimiento | existente |
| 8004 | inspecciones | 4 inspecciones (+ reglas por categoria) | existente |
| 8005 | reembolsos-costos | 5 reembolsos-costos (+ gestion economica completa) | existente |
| 8006 | ventas-catalogos | 6 ventas-catalogos + 9 lotes-trazabilidad | existente |
| 8007 | evidencias | 7 evidencias (+ videos, firmas, integridad) | existente |
| 8008 | analisis-auditoria | 8 analisis-auditoria: queda solo **auditoria**; el analisis esta aislado y obsoleto (sucesores: 8010 y 8018) y se retira por etapas, ver `docs/MIGRACION_ANALISIS_8008.md` | **separado** (analisis pendiente de retiro) |
| 8010 | clasificacion-motivos | 10 clasificacion de motivos | **implementado** |
| 8011 | causa-raiz | 11 causa raiz + 12 acciones correctivas (CAPA) | **implementado** |
| 8013 | proveedores | 13 proveedores | **implementado** |
| 8014 | disposicion-inventario | 14 disposicion + 15 inventario inverso | nuevo |
| 8017 | notificaciones | 17 notificaciones | nuevo |
| 8018 | reportes-analitica | 18 reportes + 19 analitica predictiva + Pareto y alertas que hoy viven en 8008 | **implementado** (8008 aun conserva lo suyo; se retira al separar la auditoria) |
| 8020 | sincronizacion | 20 sincronizacion offline | **implementado** |
| 8021 | integraciones-monitoreo | 21 integraciones + 22 monitoreo | **implementado** |

Los puertos 8009, 8012, 8015, 8016, 8019 y 8022 quedan **libres a proposito**:
corresponden a dominios agrupados en otro contenedor. Conservar la numeracion de
la retroalimentacion hace evidente que dominio absorbio a cual.

## Publicación y firewall de GCP

La configuración objetivo publica únicamente el reverse proxy:

| Entrada | Puerto público | Destino | Origen recomendado |
|---|---:|---|---|
| HTTP | tcp:80 | Nginx; redirección a HTTPS cuando TLS está activo | Internet |
| HTTPS | tcp:443 | Nginx; rutas web y API | Internet |
| SSH | tcp:22 | administración de la VM | IPs administrativas |

PostgreSQL, Redis y MongoDB se enlazan solamente a `127.0.0.1` para tareas de
administración. Web y microservicios no publican puertos del host: usan
`expose: 8000` en la red Docker interna `orvia_backend`.

Las reglas históricas que permiten 8000–8021 deben deshabilitarse **después** de
desplegar Nginx y comprobar los recorridos por 80/443. No se eliminan a ciegas:
primero se ejecuta `scripts/probar_proxy.py`, se valida la app web y los clientes,
y luego se comprueba desde una red externa que esos puertos ya no respondan.

**Estado real de la VM (22-11-2026).** El proxy publica el **80**. Antes lo ocupaba
un Apache (`httpd`, sitios `libreria` y `waylo`, sin uso) que se detuvo con
`systemctl stop httpd` sin deshabilitarlo; sigue sin arrancar al reiniciar solo si
se hace `systemctl disable httpd`. El 443 queda libre (TLS de Orvia aun sin
activar). Rollback: `systemctl start httpd` y `PROXY_HTTP_PORT=8000` en `.env`.
Ojo: la regla de firewall `libreria-permitir-http` abre el 80 a `0.0.0.0/0`; si
Orvia no debe ser publica, restringirla a las IPs del equipo.

Al agregar un servicio nuevo se crea su ruta en `infra/nginx/conf.d/`; no se abre
otro puerto público. La matriz ejecutable está en `docs/REVERSE_PROXY.md`.

## Por que se agrupan

| Agrupacion | Justificacion |
|---|---|
| logistica + transporte-seguimiento | El seguimiento GPS y la prueba de entrega son pasos de la misma recoleccion; separarlos obligaria a coordinar dos escrituras por cada evento de traslado |
| ventas-catalogos + lotes-trazabilidad | El lote, la serie y la venta ya viven en las mismas tablas (`venta_detalle`, `lotes`); la trazabilidad es una consulta sobre ellas |
| causa-raiz + acciones correctivas | Una accion correctiva nace de una investigacion y su eficacia reabre la investigacion; comparten ciclo de vida y responsables |
| disposicion + inventario inverso | La disposicion "reintegrar" es la entrada al inventario; deben confirmarse en la misma transaccion para no tener producto disponible sin autorizacion |
| reportes + analitica | Ambos leen los mismos datos agregados y no escriben en el expediente |
| integraciones + monitoreo | Ninguno tiene datos de negocio propios; los dos observan o traducen a los demas servicios |

## Migraciones de base de datos

Para que dos integrantes no creen la misma migracion al mismo tiempo, cada quien
usa su rango de numeros:

| Integrante | Rango |
|---|---|
| David | 014 - 019 |
| Persona 2 | 020 - 029 |
| Roberto | 030 - 039 |
| Persona 4 | 040 - 049 |

`scripts/migrate.py` aplica las que falten en orden de nombre, asi que los huecos
no importan. Ojo: si la 040 ya se aplico y despues alguien agrega la 015, la 015
corre despues de la 040. Si una migracion depende de la tabla de otro
integrante, avisen antes para no romper el orden.
