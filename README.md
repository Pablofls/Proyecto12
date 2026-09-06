# Proyecto 12 — Plataforma de devoluciones y logistica inversa

Plataforma distribuida para la gestion y analisis de devoluciones de productos
refrigerados y no refrigerados, con seguimiento del expediente completo y
analisis de causas recurrentes.

**Integracion de Aplicaciones Computacionales — UDEM — Equipo 02**
Josue Berdeal · Roberto Sandoval · David Munoz · Pablo Flores

## Estado actual

**Primer parcial: monolito web funcional.** Sistema web sobre PostgreSQL y
Redis, ejecutado en contenedores dentro de la VM de GCP del equipo.

Cubre el proceso completo: registro de la solicitud a partir de una venta,
evidencias, autorizacion, recoleccion, recepcion, inspeccion con condiciones de
cadena de frio, decision de destino, inventario recuperado, reembolso, costos,
panel de causas y bitacora de auditoria.

Microservicios, aplicacion movil, aplicacion de escritorio, JWT, XML y Locust
corresponden a los parciales siguientes.

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

Los documentos del curso (analisis, requisitos y entregables) estan en
[Descripcion.md](Descripcion.md), [Requisitos.md](Requisitos.md) y
[Entregables.md](Entregables.md).

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
