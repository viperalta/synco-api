# Endpoint: GET /admin/debts

## Descripción
Permite a un administrador obtener todas las deudas registradas en el sistema con paginación. Las deudas se ordenan por período de forma descendente (más recientes primero).

## Método HTTP
**GET**

## URL
```
/admin/debts
```

## Autenticación
Requiere token JWT de autenticación en el header `Authorization`.

### Headers Requeridos
```
Authorization: Bearer <tu_access_token>
```

## Permisos
Solo usuarios con rol **admin** pueden acceder a este endpoint.

## Query Parameters

| Parámetro | Tipo | Requerido | Default | Descripción | Restricciones |
|-----------|------|-----------|---------|-------------|---------------|
| `skip` | integer | ❌ No | 0 | Número de registros a saltar | >= 0 |
| `limit` | integer | ❌ No | 100 | Número máximo de registros a devolver | 1 <= limit <= 1000 |

## Estructura de la Respuesta

### Campos de Respuesta
```json
{
  "debts": [...],
  "total": 0,
  "skip": 0,
  "limit": 100
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `debts` | array | Lista de objetos DebtResponse (ver estructura abajo) |
| `total` | integer | Total de registros de deuda en la base de datos |
| `skip` | integer | Número de registros saltados (valor del query param) |
| `limit` | integer | Número máximo de registros solicitados (valor del query param) |

### Estructura de Cada Elemento en `debts`

```json
{
  "id": "string",
  "period": "string",
  "debtors": [...],
  "total_debt": 0.0,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | ID único del documento en MongoDB (ObjectId) |
| `period` | string | Período en formato YYYYMM |
| `debtors` | array | Lista de deudores del período |
| `total_debt` | float | Suma total de todas las deudas del período |
| `created_at` | datetime | Fecha y hora de creación (ISO 8601 UTC) |
| `updated_at` | datetime | Fecha y hora de última actualización (ISO 8601 UTC) |

### Estructura de Cada Elemento en `debtors`

```json
{
  "user_id": "string",
  "user_name": "string",
  "user_nickname": "string | null",
  "amount": 0.0
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user_id` | string | ID del usuario |
| `user_name` | string | Nombre completo del usuario |
| `user_nickname` | string \| null | Apodo del usuario (opcional) |
| `amount` | float | Monto de la deuda |

## Ejemplo de Respuesta Completa

### Sin Deudas Registradas
```json
{
  "debts": [],
  "total": 0,
  "skip": 0,
  "limit": 100
}
```

### Con 2 Deudas Registradas
```json
{
  "debts": [
    {
      "id": "65fa1b2c3d4e5f6a7b8c9d2",
      "period": "202511",
      "debtors": [
        {
          "user_id": "65f8a1b2c3d4e5f6a7b8c9d0",
          "user_name": "Juan Pérez",
          "user_nickname": "Juancho",
          "amount": 15000
        },
        {
          "user_id": "65f8a1b2c3d4e5f6a7b8c9d1",
          "user_name": "María García",
          "user_nickname": null,
          "amount": 12000
        }
      ],
      "total_debt": 27000,
      "created_at": "2025-11-01T10:30:00Z",
      "updated_at": "2025-11-01T10:30:00Z"
    },
    {
      "id": "65fa1b2c3d4e5f6a7b8c9d1",
      "period": "202510",
      "debtors": [
        {
          "user_id": "65f8a1b2c3d4e5f6a7b8c9d2",
          "user_name": "Carlos López",
          "user_nickname": "Carlitos",
          "amount": 18000
        },
        {
          "user_id": "65f8a1b2c3d4e5f6a7b8c9d3",
          "user_name": "Ana Martínez",
          "user_nickname": null,
          "amount": 13500
        },
        {
          "user_id": "65f8a1b2c3d4e5f6a7b8c9d0",
          "user_name": "Juan Pérez",
          "user_nickname": "Juancho",
          "amount": 15000
        }
      ],
      "total_debt": 46500,
      "created_at": "2025-10-01T09:15:00Z",
      "updated_at": "2025-10-15T14:22:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 100
}
```

## Características de la Respuesta

### 1. Ordenamiento
- Las deudas se ordenan por **período descendente** (más recientes primero)
- Ejemplo de orden: 202511, 202510, 202509, ...

### 2. Paginación
El endpoint soporta paginación mediante los parámetros `skip` y `limit`:

**Página 1** (primeros 10 registros):
```
GET /admin/debts?skip=0&limit=10
```

**Página 2** (registros 11-20):
```
GET /admin/debts?skip=10&limit=10
```

**Página 3** (registros 21-30):
```
GET /admin/debts?skip=20&limit=10
```

### 3. Cálculo de `total_debt`
- El campo `total_debt` se calcula automáticamente sumando todos los montos de los deudores del período
- Es un campo calculado que refleja la suma total de deuda para ese período

### 4. Timestamps
- Ambos timestamps están en formato UTC
- `created_at`: No cambia nunca
- `updated_at`: Se actualiza cuando se modifica la deuda

## Códigos de Respuesta HTTP

| Código | Descripción |
|--------|-------------|
| 200 | ✅ Solicitud exitosa |
| 400 | ❌ Parámetros de consulta inválidos |
| 401 | ❌ No autenticado (token inválido o faltante) |
| 403 | ❌ Sin permisos (usuario no es admin) |
| 500 | ❌ Error interno del servidor |

## Ejemplos de Errores

### Error 401: No autenticado
```json
{
  "detail": "No autenticado"
}
```

### Error 403: Sin permisos
```json
{
  "detail": "No tienes permisos para realizar esta acción: users.manage_roles"
}
```

### Error 400: Parámetros inválidos
Si envías un `limit` mayor a 1000:
```json
{
  "detail": "Validation error: limit debe ser <= 1000"
}
```

## Ejemplos de Uso

### Ejemplo 1: Obtener todas las deudas
```bash
curl -X GET http://localhost:8000/admin/debts \
  -H "Authorization: Bearer TU_TOKEN"
```

### Ejemplo 2: Con paginación (primeros 10 registros)
```bash
curl -X GET "http://localhost:8000/admin/debts?skip=0&limit=10" \
  -H "Authorization: Bearer TU_TOKEN"
```

### Ejemplo 3: Segunda página (registros 11-20)
```bash
curl -X GET "http://localhost:8000/admin/debts?skip=10&limit=10" \
  -H "Authorization: Bearer TU_TOKEN"
```

### Ejemplo 4: Límite personalizado
```bash
curl -X GET "http://localhost:8000/admin/debts?limit=50" \
  -H "Authorization: Bearer TU_TOKEN"
```

## Ejemplo con JavaScript/Fetch

```javascript
async function getAllDebts(skip = 0, limit = 100) {
  const response = await fetch(
    `http://localhost:8000/admin/debts?skip=${skip}&limit=${limit}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Uso
const result = await getAllDebts(0, 10);
console.log(`Total de deudas: ${result.total}`);
console.log(`Mostrando ${result.debts.length} deudas`);

// Paginación manual
const page = 1;
const perPage = 10;
const debts = await getAllDebts((page - 1) * perPage, perPage);
```

## Casos de Uso

### 1. Listar Todas las Deudas del Sistema
Para ver todas las deudas registradas:
```
GET /admin/debts
```

### 2. Dashboard de Administración
Para mostrar un resumen de deudas:
```
GET /admin/debts?limit=5
```
(Devuelve las 5 deudas más recientes)

### 3. Exportar Todas las Deudas
Para exportar todos los registros:
```
GET /admin/debts?limit=1000
```

### 4. Historial de Deudas con Paginación
Para navegar por el historial:
```
GET /admin/debts?skip=0&limit=20   # Primera página
GET /admin/debts?skip=20&limit=20  # Segunda página
GET /admin/debts?skip=40&limit=20  # Tercera página
```

## Información de Paginación

La respuesta incluye metadatos de paginación:

- **`total`**: Total de registros en la base de datos (independiente de `skip` y `limit`)
- **`skip`**: Cuántos registros se saltaron (usado para la siguiente página)
- **`limit`**: Cuántos registros se solicitaron como máximo

### Cálculo de Páginas
```
totalPages = Math.ceil(total / limit)
currentPage = (skip / limit) + 1
```

### Verificar si hay más páginas
```javascript
const hasMorePages = (result.skip + result.limit) < result.total;
```

## Diferencias con Otros Endpoints

| Endpoint | Propósito | Datos Retornados |
|----------|-----------|------------------|
| `GET /admin/debts` | Ver todas las deudas | Lista completa con paginación |
| `GET /admin/debts/{period}` | Ver una deuda específica | Un solo registro de deuda |
| `GET /player/debt/{period}` | Ver mi deuda (jugador) | Deuda personal del jugador |

## Notas Importantes

1. **Ordenamiento**: Siempre devuelve los períodos más recientes primero
2. **Total**: El campo `total` refleja el total de registros en la BD, no los que se devolvieron en esta respuesta
3. **Performance**: Con muchas deudas, siempre usa paginación
4. **Límites**: El máximo permitido es 1000 registros por request
5. **Consistencia**: Los datos se ordenan por período, no por fecha de creación

## Endpoints Relacionados

- `POST /admin/debts` - Crear nueva deuda
- `GET /admin/debts/{period}` - Ver deuda de un período específico
- `PUT /admin/debts/{period}` - Actualizar deuda
- `DELETE /admin/debts/{period}` - Eliminar deuda
- `GET /player/debt/{period}` - Consultar mi deuda (jugador)

