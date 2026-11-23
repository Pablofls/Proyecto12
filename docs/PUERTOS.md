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

## Firewall de GCP

Proyecto `integracion-505116`, red `default`. Solo se abren los puertos que tienen un
servicio, y los microservicios solo para las IPs del equipo, no para todo internet:

| Regla | Puertos | Origen |
|---|---|---|
| `permitir-8000-devoluciones` | tcp:8000 (monolito web) | cualquier IP |
| `permitir-servicios-8001-8008` | tcp:8001-8008 (microservicios originales) | dos IPs del equipo |
| `permitir-servicios-8010-8021` | tcp:8010, 8011, 8013, 8018, 8020 y 8021 (tercer parcial) | las mismas dos IPs |

Verificado el 2026-11-22 desde una de esas IPs: el `/health` de los seis puertos nuevos
responde 200 y 8009, 8012, 8014 y 8019 siguen cerrados. Desde otra IP no se ve nada: hay
que sumarla a la regla (el comando reemplaza la lista completa, asi que se repiten las
IPs actuales; se ven con `gcloud compute firewall-rules describe permitir-servicios-8010-8021`).
Las IPs no se escriben en el repositorio.

```bash
gcloud compute firewall-rules update permitir-servicios-8010-8021 \
  --source-ranges=IP_1/32,IP_2/32,IP_NUEVA/32
```

Al agregar un servicio con puerto nuevo, se agrega ese puerto a la regla correspondiente
y se actualiza esta tabla. Antes decia que una regla `permitir-microservicios-david` abria
8001-8021; esa regla no existe en el proyecto (se comprobo el 2026-11-22).

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
