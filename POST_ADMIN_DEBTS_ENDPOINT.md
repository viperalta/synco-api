# Endpoint: POST /admin/debts

## Descripción
Permite a un administrador crear o actualizar un registro de deuda para un período específico. Este endpoint registra cuánto debe pagar cada jugador para un período mensual dado. Si ya existe una deuda para ese período, la sobrescribe con la nueva información.

## Método HTTP
**POST**

## URL
```
/admin/debts
```

## Autenticación
Requiere token JWT de autenticación en el header `Authorization`.

### Headers Requeridos
```
Authorization: Bearer <tu_access_token>
Content-Type: application/json
```

## Permisos
Solo usuarios con rol **admin** pueden acceder a este endpoint.

## Request Body

### Estructura
```json
{
  "period": "202510",
  "debtors": [
    {
      "user_id": "string",
      "user_name": "string",
      "user_nickname": "string | null",
      "amount": 0.0
    }
  ]
}
```

### Campos

#### Nivel Principal
| Campo | Tipo | Requerido | Descripción | Validaciones |
|-------|------|-----------|-------------|--------------|
| `period` | string | ✅ Sí | Período en formato YYYYMM | Debe ser 6 dígitos, año entre 2000-2100, mes 01-12 |
| `debtors` | array | ✅ Sí | Lista de deudores | Mínimo 1 elemento |

#### Campo `debtors` (array de objetos)
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `user_id` | string | ✅ Sí | ID del usuario (ObjectId de MongoDB) |
| `user_name` | string | ✅ Sí | Nombre completo del usuario |
| `user_nickname` | string | ❌ No | Apodo del usuario (opcional) |
| `amount` | float | ✅ Sí | Monto de la deuda (en moneda local) |

## Ejemplos de Request

### Ejemplo 1: Un solo deudor
```json
{
  "period": "202510",
  "debtors": [
    {
      "user_id": "65f8a1b2c3d4e5f6a7b8c9d0",
      "user_name": "Juan Pérez",
      "user_nickname": "Juancho",
      "amount": 15000
    }
  ]
}
```

### Ejemplo 2: Múltiples deudores
```json
{
  "period": "202510",
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
    },
    {
      "user_id": "65f8a1b2c3d4e5f6a7b8c9d2",
      "user_name": "Carlos López",
      "user_nickname": "Carlitos",
      "amount": 18000
    }
  ]
}
```

### Ejemplo 3: Sin nickname
```json
{
  "period": "202511",
  "debtors": [
    {
      "user_id": "65f8a1b2c3d4e5f6a7b8c9d3",
      "user_name": "Ana Martínez",
      "amount": 13500
    }
  ]
}
```

## Response

### Estructura de Respuesta Exitosa (HTTP 200)
```json
{
  "id": "65f9a2b3c4d5e6f7a8b9c0d1",
  "period": "202510",
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
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Campos de Respuesta
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | ID del documento de deuda (ObjectId) |
| `period` | string | Período de la deuda (YYYYMM) |
| `debtors` | array | Lista de deudores con la misma estructura del request |
| `total_debt` | float | Suma total de todas las deudas del período (calculado automáticamente) |
| `created_at` | datetime | Fecha y hora de creación (ISO 8601) |
| `updated_at` | datetime | Fecha y hora de última actualización (ISO 8601) |

## Códigos de Respuesta HTTP

| Código | Descripción |
|--------|-------------|
| 200 | ✅ Deuda creada exitosamente |
| 400 | ❌ Error de validación (formato de período inválido, campos requeridos faltantes) |
| 401 | ❌ No autenticado (token inválido o faltante) |
| 403 | ❌ Sin permisos (usuario no es admin) |
| 500 | ❌ Error interno del servidor |

## Validaciones

### Validación de Período
El formato `YYYYMM` debe cumplir:
- Exactamente 6 dígitos
- Los primeros 4 dígitos representan el año (2000-2100)
- Los últimos 2 dígitos representan el mes (01-12)

**Ejemplos válidos:**
- `202510` → Octubre 2025
- `202312` → Diciembre 2023
- `202501` → Enero 2025

**Ejemplos inválidos:**
- `2510` → Solo 4 dígitos
- `202500` → Mes 00 no existe
- `202513` → Mes 13 no existe
- `199910` → Año anterior a 2000

### Reglas de Negocio
1. **Unicidad de Período**: Solo puede existir un registro de deuda por período. Si ya existe una deuda para el período, se actualizará con la nueva información (se sobrescribe).

2. **Lista de Deudores**: Debe contener al menos 1 deudor.

3. **Monto Positivo**: Aunque no está explícitamente validado en el modelo, se recomienda usar montos positivos.

4. **Comportamiento Upsert**: Si el período ya existe, actualiza la deuda; si no existe, la crea. Siempre devuelve el estado final (creada o actualizada).

## Ejemplos de Errores

~~### Error 400: Período ya existe~~ _(Ya no ocurre, ahora sobrescribe)_

### Error 400: Formato de período inválido
```json
{
  "detail": "Formato de período inválido. Debe ser YYYYMM (ej: 202510)"
}
```

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

## Ejemplos con cURL

### Ejemplo 1: Crear deuda básica
```bash
curl -X POST http://localhost:8000/admin/debts \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "period": "202510",
    "debtors": [
      {
        "user_id": "65f8a1b2c3d4e5f6a7b8c9d0",
        "user_name": "Juan Pérez",
        "user_nickname": "Juancho",
        "amount": 15000
      }
    ]
  }'
```

### Ejemplo 2: Crear deuda con múltiples jugadores
```bash
curl -X POST http://localhost:8000/admin/debts \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "period": "202510",
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
      "amount": 12000
    },
    {
      "user_id": "65f8a1b2c3d4e5f6a7b8c9d2",
      "user_name": "Carlos López",
      "user_nickname": "Carlitos",
      "amount": 18000
    }
  ]
}
EOF
```

## Ejemplo con JavaScript/Fetch

```javascript
async function createDebt(period, debtors) {
  const response = await fetch('http://localhost:8000/admin/debts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      period: period,
      debtors: debtors
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Uso
const debt = await createDebt('202510', [
  {
    user_id: '65f8a1b2c3d4e5f6a7b8c9d0',
    user_name: 'Juan Pérez',
    user_nickname: 'Juancho',
    amount: 15000
  },
  {
    user_id: '65f8a1b2c3d4e5f6a7b8c9d1',
    user_name: 'María García',
    amount: 12000
  }
]);
```

## Flujo de Uso

1. **Obtener lista de usuarios** (si no los tienes):
   ```
   GET /admin/users
   ```

2. **Crear la deuda**:
   ```
   POST /admin/debts
   ```

3. **Verificar la deuda creada**:
   ```
   GET /admin/debts/202510
   ```

4. **Jugadores consultan su deuda**:
   ```
   GET /player/debt/202510
   ```

## Notas Importantes

1. **Período único con sobrescritura**: Solo puede haber un registro de deuda por período. Si ya existe, este endpoint la sobrescribe automáticamente con los nuevos datos.

2. **No verifica existencia de usuarios**: El endpoint NO valida si los `user_id` existen en la base de datos. Se recomienda verificar esto antes de crear la deuda.

3. **Cálculo automático**: El campo `total_debt` se calcula automáticamente sumando todos los montos de los deudores.

4. **Timestamps automáticos**: Los campos `created_at` y `updated_at` se generan automáticamente y están en formato UTC. Si actualizas una deuda existente, `created_at` se mantiene igual y `updated_at` se actualiza.

5. **Integración con sistema de pagos**: Estas deudas se pueden usar para verificar pagos en el sistema de pagos existente.

6. **Sobrescritura automática**: Desde el frontend siempre envía la versión más actualizada. El endpoint sobrescribe la deuda existente sin necesidad de eliminarla primero.

## Endpoints Relacionados

- `GET /admin/debts` - Listar todas las deudas
- `GET /admin/debts/{period}` - Ver deuda de un período
- `PUT /admin/debts/{period}` - Actualizar deuda de un período
- `DELETE /admin/debts/{period}` - Eliminar deuda de un período
- `GET /player/debt/{period}` - Consultar mi deuda (jugador)

