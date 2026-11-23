# Guia de reportes y analitica

Servicio `reportes-analitica`, puerto **8018**. Swagger: `http://<IP-VM>:8018/docs`.
Es de **solo lectura**: no escribe en el expediente. Cada descarga queda en la
bitacora con el reporte, el formato y el numero de filas (nunca con los datos).

## Quien puede que

| Operacion | Roles |
|---|---|
| Reportes, graficas, tendencias, pronosticos y anomalias | Administrador, Analista, Supervisor, Encargado de Reembolsos |
| Alertas de posible fraude | **Solo Administrador y Analista**: nombran clientes (RN-15) |

## Reportes (RF-28)

`GET /api/v1/reportes` lista los reportes y sus filtros. `GET /api/v1/reportes/{nombre}`:

| Reporte | Filtros | Que trae |
|---|---|---|
| `devoluciones` | desde, hasta, estado, proveedor_id, tienda_id | Una fila por devolucion, con motivo, producto, lote, proveedor, tienda y costo |
| `costos` | desde, hasta | Costo por etapa de cada devolucion y total |
| `tasas` | por (proveedor, tienda, producto, lote), desde, hasta | Unidades vendidas, devueltas y tasa |
| `pareto` | dimension, medida, desde, hasta | Categorias con % y % acumulado, de mayor a menor |
| `tendencia` | medida, meses, dimension, referencia_id | La serie mensual |

`formato` elige la salida:

| formato | Salida | Limite |
|---|---|---|
| `json` (por omision) o `xml` con `Accept` | Paginado (`pagina`, `por_pagina`) con `columnas` y `datos`; XSD: `/contratos/reporte.xsd` | por pagina |
| `csv` | UTF-8 con BOM (Excel lo abre con acentos) | 50 000 filas |
| `xlsx` | Libro con la hoja *Datos* (encabezado en negrita y congelado, numeros como numeros) y la hoja *Informacion* (fecha, filtros, filas) | 50 000 filas |
| `pdf` | Tabla A4 horizontal con encabezado repetido y numeracion | 3 000 filas |

Pasarse del limite responde **422** `demasiadas_filas`: se acota con `desde` y `hasta`.
Las descargas se limitan a **20 por minuto por usuario** (429) y no se cachean.

### Los archivos no usan librerias externas

El repo no tiene librerias de PDF ni Excel y `CLAUDE.md` pide acordar las nuevas
con el equipo, asi que `formatos.py` los escribe con la biblioteca estandar. Lo
que eso significa para quien los use:

- **CSV**: un texto que empieza con `=`, `+`, `-` o `@` se entrega con un
  apostrofo antepuesto para que Excel no lo ejecute como formula.
- **XLSX**: los textos van como texto, nunca como formula. Verificado abriendolo
  con Quick Look de macOS y comprobando que el XML esta bien formado; **no se ha
  abierto en Excel ni en Calc**.
- **PDF**: fuente Courier (ancho fijo, asi las columnas se alinean sin medir
  glifos). Las columnas muy anchas se recortan con "…". Sin graficas: para eso estan
  las opciones de Highcharts. Verificado con `pdftotext` y renderizado.

## Graficas para Highcharts

`GET /api/v1/graficas/{pareto|tendencia|tasas}` devuelve `{"opciones": {...}}`,
listo para `Highcharts.chart("contenedor", opciones)`. Solo JSON (con `Accept:
application/xml` responde 406). La tendencia trae cinco series alineadas con las
categorias: *Observado*, *Tendencia*, *Pronostico* y sus dos limites. Los meses sin
dato van como `null`: Highcharts deja el hueco en vez de dibujar un cero falso.

## Tendencias, pronosticos y anomalias (RN-09)

Todo es estadistica que se puede reproducir a mano y **orienta la revision humana;
no determina causas**.

**Series mensuales** (`medida`: `tasa`, `devoluciones`, `costo`; `meses` de 6 a 36;
opcionalmente `dimension` + `referencia_id` para un proveedor, tienda, producto o lote).

- **La tasa se mide por cohorte de venta**: lo vendido en un mes y lo que de eso se
  devolvio, sin importar cuando llego la devolucion.
- **Solo entran meses que ya maduraron.** Las ventas de los ultimos dias aun pueden
  devolverse (plazo de `politicas_devolucion`, RN-16); contarlas haria parecer que la
  tasa baja. Con el plazo de 30 dias, hoy 21 de noviembre el ultimo mes utilizable
  es septiembre. Las series de devoluciones y costo solo excluyen el mes en curso.
- **Un mes con menos de 20 unidades vendidas** queda como `muestra_insuficiente` y no
  entra al calculo.

**`/analitica/tendencias`**: regresion lineal. Dice `sube`, `baja` o `estable`, y solo
afirma una direccion si el cambio es distinguible del ruido (prueba t al 95 %). Con
menos de 6 meses utilizables responde `sin_datos`.

**`/analitica/pronosticos`**: extrapolacion lineal con **intervalo de prediccion del
95 %**, hasta 6 meses. Cuidados:

- `confiable` solo es verdadero si la recta explica al menos 30 % de la variacion.
- No considera estacionalidad ni cambios futuros (lo dice en la `advertencia`).
- Los limites no bajan de 0 y una tasa no pasa de 100.
- Es el pronostico de los meses **siguientes al ultimo mes utilizable**, no de hoy.
- Incluye un promedio movil de 3 meses como referencia plana.

**`/analitica/anomalias`**: puntaje z **robusto** (mediana y MAD), que un valor extremo
no distorsiona. Anomalia con |z| ≥ 3.5.

- `tipo=objetos`: la tasa de cada proveedor, tienda, producto o lote contra sus pares.
  Necesita 5 objetos con 20 unidades vendidas o mas; los demas se cuentan en
  `omitidos_por_muestra`.
- `tipo=meses`: cada mes contra la tendencia de su propia serie, para que una serie
  que sube de forma regular no marque como anomalo su ultimo mes.

**`/analitica/factores`** (RF-23, RF-24): analisis de **varios factores a la vez**. Las tasas por
una sola dimension pueden esconder que el problema esta en una combinacion (por ejemplo, un
proveedor solo en una tienda). Cruza dos factores con venta (`por` y `con`: proveedor, tienda,
producto o lote; distintos entre si) y para cada combinacion devuelve:

- la tasa (unidades devueltas entre vendidas) y cuantas veces supera el promedio global;
- su **intervalo de confianza de Wilson del 95 %**: una combinacion es `distinguible` solo si el
  extremo bajo del intervalo supera la tasa promedio, para que pocas ventas no parezcan culpables;
- la tasa de cada factor por separado y una **lectura** explicable: `combinacion` (supera a los dos
  factores por separado), `factor_a`, `factor_b`, `ambos_factores` o `sin_atribucion`.

Las combinaciones con menos de 20 unidades vendidas no se juzgan (`omitidas_por_muestra`). Con
`solo_distinguibles=true` se listan solo las que destacan y `limite` acota la lista (por omision 20).
Es una senal para decidir donde investigar, no una causa (RN-09); `ruta` y `transportista` quedan
fuera porque no existe "vendido por ruta".

**`/analitica/alertas-fraude`** (RF-25): frecuencia alta en 90 dias, multiples rechazos o
monto reembolsado elevado. Son indicadores preventivos; no acusan ni bloquean.

## Relacion con `analisis-auditoria` (8008)

El Pareto y las alertas de fraude ahora tambien viven aqui, calculados directo en
PostgreSQL (siempre al dia, sin el paso de sincronizar). `analisis-auditoria` **sigue
funcionando igual**: se retira de ahi al separar la auditoria, y para entonces los
clientes ya pueden pasarse a estas rutas.

## Ejemplos

```
GET /api/v1/reportes/devoluciones?formato=xlsx&desde=2026-10-01&hasta=2026-10-31
GET /api/v1/reportes/pareto?dimension=proveedor&medida=costo&formato=pdf
GET /api/v1/graficas/tendencia?medida=tasa&dimension=proveedor&referencia_id=2&horizonte=3
GET /api/v1/analitica/anomalias?tipo=objetos&por=tienda
GET /api/v1/analitica/factores?por=proveedor&con=tienda&solo_distinguibles=true
```

## Lo que no hace todavia

- La web sigue usando sus propios `/reportes/*.csv`; migrarla a este servicio es un
  paso aparte.
- No hay reportes de investigaciones ni de acciones correctivas (viven en `causa-raiz`).
- Los pronosticos no modelan estacionalidad.
