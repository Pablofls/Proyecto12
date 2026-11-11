# Guia de seguridad para los servicios del tercer parcial

Como proteger un endpoint nuevo con lo que ya trae `shared/seguridad.py`. Todo
lo de esta guia esta probado en `services/auth/tests/test_operaciones.py` y en
`services/devoluciones/tests/`.

## 1. Roles: nombra siempre quien puede entrar

```python
from shared.seguridad import (ANALISTA, SUPERVISOR, RECOLECTOR, OPERADOR_ALMACEN,
                              ROLES_BASE, TODOS_LOS_ROLES, requiere_jwt)

@api.post("/recolecciones/<int:id>/confirmar")
@requiere_jwt(RECOLECTOR, SUPERVISOR)
def confirmar(id): ...
```

| Escribes | Entran |
|---|---|
| `@requiere_jwt(RECOLECTOR, SUPERVISOR)` | Solo esos roles |
| `@requiere_jwt()` (sin roles) | Los 7 roles originales (`ROLES_BASE`). **Los de campo no** |
| `@requiere_jwt(*ROLES_BASE, OPERADOR_ALMACEN)` | Los originales mas el operador |
| `@requiere_jwt(*TODOS_LOS_ROLES)` | Los 10 roles (usalo poco: casi nada debe ser para todos) |

Un rol que no esta en la lista recibe `403 sin_permiso`, con los roles
permitidos en `detalles`.

## 2. Sucursal: filtra y comprueba

El JWT trae `tienda_id` (migracion 015). `None` = el usuario opera en todas las
sucursales. La sucursal de una devolucion es la de su venta (`ventas.tienda_id`).

**En un listado** agrega la condicion:

```python
from shared.seguridad import condicion_tienda

condicion, valores = condicion_tienda("v.tienda_id")   # la columna la escribes tu
if condicion:
    condiciones.append(condicion)
    parametros += valores
```

**En un registro concreto** (detalle, modificar, confirmar):

```python
from shared.seguridad import exigir_tienda

exigir_tienda(fila["tienda_id"])   # 403 fuera_de_sucursal si no es su tienda
```

`exigir_tienda` no escribe en la bitacora; si quieres dejar constancia, atrapa
el `ErrorApi`, registra y vuelve a lanzarlo (ejemplo en
`services/devoluciones/app.py`, `_exigir_visible`).

## 3. Operaciones criticas: exige la reconfirmacion

Para aprobar un reembolso, aprobar una disposicion, reincorporar al inventario
o cerrar una investigacion, el usuario debe confirmar su contrasena:

1. El cliente (web, Android, escritorio) llama a auth:
   `POST /api/v1/auth/autorizar-operacion` con `operacion`, `recurso_id` y
   `password`. Recibe `token_operacion`.
2. Envia ese permiso a tu servicio en el header `X-Autorizacion-Operacion`.
3. Tu endpoint lo exige **antes** de escribir:

```python
from shared.seguridad import ENCARGADO_REEMBOLSOS, exigir_autorizacion_operacion

@api.post("/reembolsos/<int:devolucion_id>/aprobar")
@requiere_jwt(ENCARGADO_REEMBOLSOS)
def aprobar(devolucion_id):
    exigir_autorizacion_operacion("aprobar_reembolso", devolucion_id)
    ...  # ya puedes escribir
```

El permiso vale para **una** operacion, sobre **ese** registro, en **esa**
sesion, durante 5 minutos, y se borra de Redis al usarse. Por eso tambien
impide que dos peticiones simultaneas aprueben dos veces lo mismo: solo una
obtiene el permiso.

| Respuesta | Cuando |
|---|---|
| `403 autorizacion_operacion_requerida` | No mando el header |
| `403 autorizacion_operacion_invalida` | Vencido, falsificado, de otro registro, otra operacion u otra sesion |
| `403 autorizacion_operacion_usada` | Ya se uso (doble clic, reintento) |
| `403 sin_permiso` | Su rol no puede autorizar esa operacion |

Para agregar una operacion nueva: agregala a `OPERACIONES_CRITICAS` en
`shared/seguridad.py` **y** a la enumeracion de
`services/auth/contratos/autorizar_operacion.xsd`.

## Cuentas para probar

| Cuenta | Rol | Sucursal |
|---|---|---|
| `luis.recolector@demo.mx` | Recolector | Tienda Centro |
| `marta.almacen@demo.mx` | Operador de Almacen | Tienda Centro |
| `jorge.supervisor@demo.mx` | Supervisor | Todas |
| `carla.reembolsos@demo.mx` | Encargado de Reembolsos | Todas |
