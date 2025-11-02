# Implementación de Gestión de Deudas

## Resumen
Se ha implementado un sistema completo de gestión de deudas que permite al administrador registrar, actualizar, eliminar y consultar las deudas de los jugadores por período mensual.

## Modelo de Datos

### Deuda (`DebtModel`)
- `id`: ID único del documento en MongoDB
- `period`: Período en formato YYYYMM (ej: 202510)
- `debtors`: Lista de deudores con sus deudas
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

### Información de Deudor (`DebtorInfo`)
- `user_id`: ID del usuario
- `user_name`: Nombre del usuario
- `user_nickname`: Apodo del usuario (opcional)
- `amount`: Monto de la deuda

## Endpoints Administrativos

Todos los endpoints administrativos requieren rol de administrador.

### 1. Crear Deuda
**POST** `/admin/debts`

Permite crear un registro de deuda para un período específico con la lista de deudores.

**Request:**
```json
{
  "period": "202510",
  "debtors": [
    {
      "user_id": "65f1234...",
      "user_name": "Juan Pérez",
      "user_nickname": "Juancho",
      "amount": 15000
    },
    {
      "user_id": "65f5678...",
      "user_name": "María García",
      "user_nickname": null,
      "amount": 12000
    }
  ]
}
```

### 2. Listar Todas las Deudas
**GET** `/admin/debts`

Obtiene todas las deudas registradas con paginación.

**Query Parameters:**
- `skip`: Número de registros a saltar (default: 0)
- `limit`: Número máximo de registros (default: 100, max: 1000)

### 3. Obtener Deuda por Período
**GET** `/admin/debts/{period}`

Obtiene las deudas de un período específico.

**Ejemplo:**
```
GET /admin/debts/202510
```

### 4. Actualizar Deuda
**PUT** `/admin/debts/{period}`

Actualiza la lista de deudores para un período específico.

**Request:**
```json
{
  "debtors": [
    {
      "user_id": "65f1234...",
      "user_name": "Juan Pérez",
      "user_nickname": "Juancho",
      "amount": 18000
    }
  ]
}
```

### 5. Eliminar Deuda
**DELETE** `/admin/debts/{period}`

Elimina el registro de deuda para un período específico.

## Endpoint de Jugador

### Consultar Mi Deuda
**GET** `/player/debt/{period}`

Permite a un jugador consultar su deuda para un período específico. Solo requiere autenticación.

**Ejemplo:**
```
GET /player/debt/202510
```

**Response:**
```json
{
  "period": "202510",
  "amount": 15000,
  "user_name": "Juan Pérez",
  "user_nickname": "Juancho"
}
```

Si el jugador no tiene deuda registrada para ese período, se retorna un 404.

## Archivos Creados/Modificados

### Nuevos Archivos
- `debt_service.py`: Servicio de negocio para gestión de deudas

### Archivos Modificados
- `models.py`: Agregados modelos de deuda (ya estaba en el código)
- `main.py`: Agregados endpoints de deuda y imports necesarios

## Validaciones

1. **Formato de Período**: Debe ser YYYYMM (6 dígitos)
2. **Año válido**: Entre 2000 y 2100
3. **Mes válido**: Entre 1 y 12
4. **Unicidad**: Solo puede haber un registro de deuda por período

## Estructura de Base de Datos

La colección `debts` en MongoDB almacena los registros de deuda con la siguiente estructura:

```json
{
  "_id": ObjectId("..."),
  "period": "202510",
  "debtors": [
    {
      "user_id": "65f1234...",
      "user_name": "Juan Pérez",
      "user_nickname": "Juancho",
      "amount": 15000
    }
  ],
  "created_at": ISODate("2025-01-15T10:30:00Z"),
  "updated_at": ISODate("2025-01-15T10:30:00Z")
}
```

## Uso en el Frontend

### Para Administradores
1. Crear deuda: Enviar POST a `/admin/debts` con el período y lista de deudores
2. Ver todas las deudas: GET `/admin/debts?skip=0&limit=100`
3. Ver deuda de un período: GET `/admin/debts/202510`
4. Actualizar deuda: PUT `/admin/debts/202510`
5. Eliminar deuda: DELETE `/admin/debts/202510`

### Para Jugadores
1. Consultar mi deuda: GET `/player/debt/202510`

## Ejemplos de Uso con cURL

### Crear Deuda (Admin)
```bash
curl -X POST http://localhost:8000/admin/debts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "period": "202510",
    "debtors": [
      {
        "user_id": "65f1234...",
        "user_name": "Juan Pérez",
        "user_nickname": "Juancho",
        "amount": 15000
      }
    ]
  }'
```

### Consultar Mi Deuda (Jugador)
```bash
curl -X GET http://localhost:8000/player/debt/202510 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Listar Todas las Deudas (Admin)
```bash
curl -X GET "http://localhost:8000/admin/debts?skip=0&limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Notas Importantes

1. Solo los usuarios con rol `player` tienen deuda asignada
2. Un período es único (YYYYMM)
3. La deuda se almacena por período, no por usuario
4. Cada registro de deuda contiene un arreglo de todos los deudores de ese período

