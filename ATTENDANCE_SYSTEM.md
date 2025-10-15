# Sistema de Asistencia a Eventos - Synco API

Este documento describe el sistema de asistencia a eventos implementado en la API de Synco.

## Descripción General

El sistema permite a los usuarios registrar su asistencia a eventos de Google Calendar, manteniendo un registro de quién asistirá a cada evento.

## Estructura de Datos

### Colección `event_attendances`

```json
{
  "_id": "ObjectId",
  "event_id": "string",  // ID del evento de Google Calendar
  "attendees": ["string"], // Array de nombres de usuarios
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Endpoints Disponibles

### 1. POST `/asistir`

Registrar asistencia de un usuario a un evento.

**Request Body:**
```json
{
  "event_id": "553qlrcqug1p5hrufgku8baecv",
  "user_name": "Juan Pérez"
}
```

**Response (200):**
```json
{
  "event_id": "553qlrcqug1p5hrufgku8baecv",
  "attendees": ["Juan Pérez"],
  "total_attendees": 1,
  "message": "Usuario 'Juan Pérez' agregado exitosamente a la lista de asistentes"
}
```

**Response (409) - Usuario ya existe:**
```json
{
  "detail": "El usuario 'Juan Pérez' ya está registrado para asistir a este evento"
}
```

### 2. GET `/asistencia/{event_id}`

Obtener la lista de asistentes de un evento específico.

**Response (200):**
```json
{
  "event_id": "553qlrcqug1p5hrufgku8baecv",
  "attendees": ["Juan Pérez", "María García", "Carlos López"],
  "total_attendees": 3,
  "message": "Total de asistentes: 3"
}
```

**Response (200) - Sin asistentes:**
```json
{
  "event_id": "553qlrcqug1p5hrufgku8baecv",
  "attendees": [],
  "total_attendees": 0,
  "message": "No hay asistentes registrados para este evento"
}
```

### 3. GET `/asistencias`

Obtener todas las asistencias registradas con paginación.

**Query Parameters:**
- `skip` (opcional): Número de registros a saltar (default: 0)
- `limit` (opcional): Número máximo de registros (default: 100, max: 1000)

**Response (200):**
```json
[
  {
    "_id": "ObjectId",
    "event_id": "553qlrcqug1p5hrufgku8baecv",
    "attendees": ["Juan Pérez", "María García"],
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
]
```

### 4. DELETE `/asistencia/{event_id}/{user_name}`

Cancelar asistencia de un usuario a un evento.

**Response (200):**
```json
{
  "message": "Asistencia de 'Juan Pérez' cancelada exitosamente",
  "status": "success"
}
```

**Response (404) - Usuario no encontrado:**
```json
{
  "detail": "Usuario no encontrado en la lista de asistentes"
}
```

## Ejemplos de Uso

### Registrar Asistencia

```bash
curl -X POST "http://localhost:8000/asistir" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "553qlrcqug1p5hrufgku8baecv",
    "user_name": "Juan Pérez"
  }'
```

### Obtener Asistentes de un Evento

```bash
curl "http://localhost:8000/asistencia/553qlrcqug1p5hrufgku8baecv"
```

### Obtener Todas las Asistencias

```bash
curl "http://localhost:8000/asistencias?skip=0&limit=10"
```

### Cancelar Asistencia

```bash
curl -X DELETE "http://localhost:8000/asistencia/553qlrcqug1p5hrufgku8baecv/Juan%20Pérez"
```

## Flujo de Trabajo

1. **Obtener Eventos**: Usa `/eventos` para obtener la lista de eventos disponibles
2. **Registrar Asistencia**: Usa `/asistir` con el `event_id` y `user_name`
3. **Verificar Asistencia**: Usa `/asistencia/{event_id}` para ver quién asistirá
4. **Cancelar si es necesario**: Usa `DELETE /asistencia/{event_id}/{user_name}`

## Validaciones

- **Usuario duplicado**: No se puede registrar el mismo usuario dos veces para el mismo evento
- **Event ID válido**: El `event_id` debe ser un ID válido de Google Calendar
- **Nombre de usuario**: El `user_name` no puede estar vacío

## Códigos de Estado HTTP

- **200**: Operación exitosa
- **404**: Recurso no encontrado (usuario no en lista, evento no existe)
- **409**: Conflicto (usuario ya registrado)
- **500**: Error interno del servidor

## Integración con Google Calendar

Los `event_id` utilizados deben corresponder a eventos reales obtenidos del endpoint `/eventos`. El sistema no valida automáticamente que el evento exista, por lo que es responsabilidad del cliente usar IDs válidos.

## Consideraciones de Rendimiento

- Las consultas están optimizadas con índices en `event_id`
- Se implementa paginación para evitar cargar demasiados registros
- Los arrays de asistentes se mantienen en memoria para acceso rápido

## Monitoreo

Puedes monitorear el uso del sistema a través de:
- Logs de la aplicación
- Métricas de MongoDB Atlas
- Endpoint `/debug/env` para verificar configuración
