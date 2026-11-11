# Guia de sincronizacion offline (para las apps Android y de escritorio)

Servicio `sincronizacion`, puerto **8020**. Swagger: `http://<IP-VM>:8020/docs`.

## Como lo usa la app

1. **Al capturar sin red**, la app guarda la operacion en su cola local con:
   - `id_operacion`: un UUID nuevo (`UUID.randomUUID()` en Android).
     **Se genera una sola vez y se reutiliza en cada reintento.**
   - `tipo`, `capturado_en` (fecha con zona horaria) y `datos`.
   - La muestra como **pendiente**, nunca como confirmada.
2. **Cuando vuelve la red**, manda la cola en orden (maximo 50 por envio):

```json
POST /api/v1/sincronizacion/operaciones
Authorization: Bearer <access_token>

{
  "dispositivo_id": "android-luis-01",
  "operaciones": [
    {"id_operacion": "6f1c...-...", "tipo": "estado_recoleccion",
     "capturado_en": "2026-11-10T09:15:00-06:00",
     "datos": {"recoleccion_id": 12, "estado_esperado": "asignada", "estado": "en_transito",
               "ubicacion": {"latitud": 25.6866, "longitud": -100.3161}}},
    {"id_operacion": "9a2b...-...", "tipo": "evidencia",
     "capturado_en": "2026-11-10T09:20:00-06:00",
     "datos": {"devolucion_id": 40, "comentario": "Caja abollada",
               "archivo": {"nombre": "caja.jpg", "contenido_base64": "...", "sha256": "..."}}}
  ]
}
```

3. **Con la respuesta**, por cada operacion:

| `estado` | Que hace la app |
|---|---|
| `aceptada` | Ahora si la marca como confirmada y la quita de la cola |
| `conflicto` | El servidor cambio mientras no habia red. Muestra `motivo.detalles` (por ejemplo `estado_servidor`) y deja que el usuario decida. Si quiere intentar otra cosa, es una operacion **nueva** con id nuevo |
| `rechazada` | Datos invalidos, sin permiso, otra sucursal o una operacion que solo se hace en linea. Muestra `motivo.mensaje` y la quita de la cola |
| `reintentar` | Falla temporal del servidor. La deja en la cola y la vuelve a mandar **con el mismo id** |

`repetida: true` significa que ya se habia recibido antes; no se aplico de nuevo.
Si la respuesta nunca llego, mandar lo mismo otra vez es seguro, o consultar
`GET /api/v1/sincronizacion/operaciones/<id_operacion>`.

## Tipos permitidos sin conexion

`GET /api/v1/sincronizacion/tipos` devuelve esta lista y si tu rol puede usar cada uno.

| Tipo | Roles | Datos |
|---|---|---|
| `estado_recoleccion` | Recolector, Coordinador | `recoleccion_id`, `estado_esperado`, `estado` (`en_transito`, `completada`, `fallida`), `ubicacion` opcional |
| `recepcion` | Operador de Almacen, Encargado del Centro | `devolucion_id`, `coincide_expediente` |
| `evidencia` | Recolector (etapa recoleccion), Operador de Almacen y Encargado (etapa recepcion) | `devolucion_id`, `comentario` y/o `archivo` (JPG, PNG o PDF hasta 5 MB, con su SHA-256) |

**Nunca offline** (siempre `rechazada` con `requiere_conexion`): autorizar
devolucion, programar recoleccion, aprobar reembolso, aprobar disposicion,
reincorporar inventario y cerrar investigacion. Esas pantallas deben llamar al
servicio correspondiente en linea.

## XML (app de escritorio)

Mismo endpoint con `Content-Type: application/xml`; las listas usan `<item>`.
Contrato: `services/sincronizacion/contratos/lote.xsd`.

```xml
<sincronizacion>
  <dispositivo_id>escritorio-1</dispositivo_id>
  <operaciones>
    <item>
      <id_operacion>6f1c...</id_operacion>
      <tipo>recepcion</tipo>
      <capturado_en>2026-11-10T09:15:00-06:00</capturado_en>
      <datos><devolucion_id>40</devolucion_id><coincide_expediente>true</coincide_expediente></datos>
    </item>
  </operaciones>
</sincronizacion>
```

## Limites

30 envios por minuto por usuario, 50 operaciones por envio, 16 MB por envio,
capturas de maximo 7 dias.
