# Contenedores y puertos del tercer parcial (PROPUESTA)

> Estado: **propuesta para acordar en la reunion de arranque**. Nadie crea un
> contenedor nuevo hasta que el equipo apruebe esta tabla, para que dos
> personas no tomen el mismo puerto ni el mismo nombre.

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
| 8008 | analisis-auditoria | 8 analisis-auditoria: se propone dejar aqui solo **auditoria** y mover el analisis a 8018 | existente |
| 8010 | clasificacion-motivos | 10 clasificacion de motivos | nuevo |
| 8011 | causa-raiz | 11 causa raiz + 12 acciones correctivas (CAPA) | nuevo |
| 8013 | proveedores | 13 proveedores | nuevo |
| 8014 | disposicion-inventario | 14 disposicion + 15 inventario inverso | nuevo |
| 8017 | notificaciones | 17 notificaciones | nuevo |
| 8018 | reportes-analitica | 18 reportes + 19 analitica predictiva + Pareto y alertas que hoy viven en 8008 | nuevo |
| 8020 | sincronizacion | 20 sincronizacion offline | nuevo |
| 8021 | integraciones-monitoreo | 21 integraciones + 22 monitoreo | nuevo |

Los puertos 8009, 8012, 8015, 8016, 8019 y 8022 quedan **libres a proposito**:
corresponden a dominios agrupados en otro contenedor. Conservar la numeracion de
la retroalimentacion hace evidente que dominio absorbio a cual.

El firewall de GCP (regla `permitir-microservicios-david`) abre 8001-8010. Si se
aprueba esta tabla, hay que ampliarlo a 8001-8021.

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
| Persona 3 | 030 - 039 |
| Persona 4 | 040 - 049 |

`scripts/migrate.py` aplica las que falten en orden de nombre, asi que los huecos
no importan. Ojo: si la 040 ya se aplico y despues alguien agrega la 015, la 015
corre despues de la 040. Si una migracion depende de la tabla de otro
integrante, avisen antes para no romper el orden.
