# Proyecto 12 — Plataforma de devoluciones y logistica inversa

Plataforma distribuida para la gestion y analisis de devoluciones de productos
refrigerados y no refrigerados, con seguimiento del expediente completo y
analisis de causas recurrentes.

**Integracion de Aplicaciones Computacionales — UDEM — Equipo 02**
Josue Berdeal · Roberto Sandoval · David Munoz · Pablo Flores

## Estado actual

**Segundo parcial: monolito web ampliado y ocho microservicios** (JWT, JSON y
XML con XSD, PostgreSQL, MongoDB, Redis, Swagger y Docker Compose), ejecutados
en contenedores dentro de la VM de GCP del equipo. Sobre el monolito web del
primer parcial, descrito abajo.

Cubre el proceso completo: registro de la solicitud a partir de una venta,
evidencias, autorizacion, recoleccion, recepcion, inspeccion con condiciones de
cadena de frio, decision de destino, inventario recuperado, reembolso, costos,
panel de causas y bitacora de auditoria.

Las aplicaciones movil y de escritorio quedan fuera del alcance de esta entrega
(sus contratos JSON y XML si estan implementados), y las pruebas de carga con
Locust corresponden al tercer parcial.

## Antes de tocar el codigo

Lee **[CLAUDE.md](CLAUDE.md)**. Contiene las reglas del proyecto, en particular
las dos que mas importan:

1. **Las bases de datos viven unicamente en la VM de GCP.** No instales
   PostgreSQL ni Redis en tu laptop.
2. **Todo se sincroniza por GitHub.** Ramas por integrante y Pull Request hacia
   `main`.

## Documentacion

| Documento | Contenido |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Reglas del proyecto y convenciones |
| [docs/SETUP.md](docs/SETUP.md) | Como levantar todo en la VM y el guion de la demostracion |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Estructura, capas y decisiones de diseno |
| [docs/TRAZABILIDAD.md](docs/TRAZABILIDAD.md) | Que RF, RNF y RN cubre cada archivo |
| [docs/BITACORA.md](docs/BITACORA.md) | Decisiones tecnicas y su justificacion |
| [docs/DOCUMENTO_TECNICO.md](docs/DOCUMENTO_TECNICO.md) | Documento tecnico integral del segundo parcial |
| [docs/diagramas/](docs/diagramas/) | Diagramas Mermaid: componentes, despliegue, secuencias, PostgreSQL, MongoDB y Redis |

Los documentos del curso (analisis, requisitos y entregables) estan en
[Descripcion.md](docs/enunciado/Descripcion.md), [Requisitos.md](docs/enunciado/Requisitos.md) y
[Entregables.md](docs/enunciado/Entregables.md).

## Arranque rapido (en la VM)

```bash
git pull origin main
cp .env.example .env     # completar y guardar
docker compose up -d --build
docker compose exec app python scripts/migrate.py
docker compose exec -T postgres psql -U devoluciones_app -d devoluciones < db/seeds/001_catalogos.sql
docker compose exec app python scripts/seed_demo.py
curl -s localhost:8000/health
```

El detalle completo, incluidas las cuentas de demostracion, esta en
[docs/SETUP.md](docs/SETUP.md).

## Tecnologias

Python 3.11 · Flask · Jinja2 · PostgreSQL 16 · Redis 7 · Highcharts · Docker
Compose · Google Compute Engine
