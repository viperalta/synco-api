# Documentación de Endpoints - Backend Synco API

## Información General
- **Base URL**: `http://localhost:8000`
- **Versión**: 1.0.0
- **Autenticación**: JWT + Cookies de sesión

---

## 🏠 Endpoints Generales

### GET /
**Descripción**: Endpoint raíz de la API
**Respuesta**: `MessageResponse`
```json
{
  "message": "¡Bienvenido a Synco API!",
  "status": "success"
}
```

### GET /health
**Descripción**: Verificar estado de la API
**Respuesta**: `MessageResponse`
```json
{
  "message": "API funcionando correctamente",
  "status": "healthy"
}
```

---

## 🔍 Endpoints de Debug

### GET /debug/env
**Descripción**: Verificar variables de entorno
**Respuesta**: `Object`
```json
{
  "google_credentials_json_present": false,
  "google_token_json_present": false,
  "google_credentials_file": "/tmp/credentials.json",
  "google_token_file": "/tmp/token.json",
  "google_service_initialized": true,
  "mongodb_url_present": true,
  "mongodb_database": "synco-test",
  "mongodb_connected": true
}
```

### GET /debug/google-calendar-permissions
**Descripción**: Verificar permisos de Google Calendar
**Respuesta**: `Object`
```json
{
  "service_available": true,
  "scopes": ["https://www.googleapis.com/auth/calendar"],
  "read_permission": true,
  "write_permission": true
}
```

### GET /debug/mongodb
**Descripción**: Verificar conexión a MongoDB
**Respuesta**: `Object`
```json
{
  "status": "success",
  "message": "MongoDB conectado y funcionando correctamente",
  "database": "synco-test"
}
```

---

## 📦 Endpoints de Items (CRUD)

### GET /items
**Descripción**: Obtener todos los items
**Parámetros Query**:
- `skip` (int, default=0): Número de items a saltar
- `limit` (int, default=100): Número máximo de items
**Respuesta**: `List[ItemModel]`

### GET /items/{item_id}
**Descripción**: Obtener un item específico
**Parámetros**:
- `item_id` (string): ID del item
**Respuesta**: `ItemModel`

### POST /items
**Descripción**: Crear un nuevo item
**Body**: `ItemCreate`
**Respuesta**: `ItemModel`

### PUT /items/{item_id}
**Descripción**: Actualizar un item existente
**Parámetros**:
- `item_id` (string): ID del item
**Body**: `ItemUpdate`
**Respuesta**: `ItemModel`

### DELETE /items/{item_id}
**Descripción**: Eliminar un item
**Parámetros**:
- `item_id` (string): ID del item
**Respuesta**: `MessageResponse`

---

## 📅 Endpoints de Google Calendar

### GET /calendarios
**Descripción**: Obtener lista de calendarios disponibles
**Respuesta**: `List[CalendarResponse]`

### GET /eventos
**Descripción**: Obtener eventos de un calendario
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
- `max_results` (int, default=50): Número máximo de eventos
- `days_ahead` (int, default=90): Días hacia adelante
**Respuesta**: `List[EventResponse]`

### GET /eventos/{calendar_id}
**Descripción**: Obtener eventos de un calendario específico
**Parámetros**:
- `calendar_id` (string): ID del calendario
**Parámetros Query**:
- `max_results` (int, default=50): Número máximo de eventos
- `days_ahead` (int, default=90): Días hacia adelante
**Respuesta**: `List[EventResponse]`

### GET /eventos-con-asistencia
**Descripción**: Obtener eventos con información de asistencia
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
- `max_results` (int, default=50): Número máximo de eventos
- `days_ahead` (int, default=90): Días hacia adelante
**Respuesta**: `List[dict]` (eventos con datos de asistencia)

---

## 👥 Endpoints de Asistencia a Eventos

### POST /asistir
**Descripción**: Registrar asistencia a un evento
**Body**: `AttendanceRequest`
```json
{
  "event_id": "string",
  "user_name": "string",
  "will_attend": true
}
```
**Respuesta**: `AttendanceResponse`

### GET /asistencia/{event_id}
**Descripción**: Obtener asistencia de un evento específico
**Parámetros**:
- `event_id` (string): ID del evento
**Respuesta**: `AttendanceResponse`

### GET /asistencias
**Descripción**: Obtener todas las asistencias
**Parámetros Query**:
- `skip` (int, default=0): Número de registros a saltar
- `limit` (int, default=100): Número máximo de registros
**Respuesta**: `List[EventAttendanceModel]`

### DELETE /cancelar-asistencia/{event_id}
**Descripción**: Cancelar asistencia de un usuario
**Parámetros**:
- `event_id` (string): ID del evento
**Body**: `CancelAttendanceRequest`
```json
{
  "user_name": "string"
}
```
**Respuesta**: `MessageResponse`

---

## 🔐 Endpoints de Autenticación

### POST /auth/google
**Descripción**: Autenticar usuario con Google OAuth (API directa)
**Body**: `GoogleAuthRequest`
```json
{
  "access_token": "string"
}
```
**Respuesta**: `TokenResponse`

### GET /auth/me
**Descripción**: Obtener información del usuario actual
**Headers**: `Authorization: Bearer <token>`
**Respuesta**: `UserModel`

### POST /auth/refresh
**Descripción**: Renovar access token usando refresh token
**Body**: `TokenRefreshRequest`
```json
{
  "refresh_token": "string"
}
```
**Respuesta**: `TokenRefreshResponse`

### POST /auth/revoke
**Descripción**: Revocar refresh token
**Body**: `TokenRevokeRequest`
```json
{
  "refresh_token": "string"
}
```
**Respuesta**: `Object`

### POST /auth/check-session
**Descripción**: Verificar sesión activa usando refresh token
**Body**: `TokenRefreshRequest`
```json
{
  "refresh_token": "string"
}
```
**Respuesta**: `TokenResponse`

### GET /auth/session
**Descripción**: Verificar sesión activa desde cookie
**Headers**: Cookie `session_token`
**Respuesta**: `Object`
```json
{
  "user": {
    "id": "string",
    "email": "string",
    "name": "string",
    "picture": "string"
  }
}
```

---

## 🌐 Endpoints de OAuth (Frontend)

### GET /auth/google/silent
**Descripción**: Silent login para usuarios registrados
**Parámetros Query**:
- `email` (string, required): Email del usuario
**Comportamiento**: 
- Si usuario logueado en Google → Redirige a callback
- Si no → Redirige a frontend con error
**Redirección**: `{FRONTEND_URL}?login=success` o `{FRONTEND_URL}?login=error`

### GET /auth/google/login
**Descripción**: Login normal con UI de Google
**Parámetros Query**:
- `prompt` (string, default="consent"): Tipo de prompt
**Comportamiento**: Redirige a Google OAuth con UI completa
**Redirección**: Google OAuth → Callback

### GET /auth/google/callback
**Descripción**: Callback de Google OAuth
**Parámetros Query**:
- `code` (string): Código de autorización
- `state` (string): Estado PKCE
- `error` (string, optional): Error de OAuth
**Comportamiento**: 
- Procesa respuesta de Google
- Establece cookie de sesión
- Redirige al frontend
**Redirección**: `{FRONTEND_URL}?login=success` o `{FRONTEND_URL}?login=error`

### POST /auth/logout
**Descripción**: Cerrar sesión
**Headers**: Cookie `session_token`
**Respuesta**: `Object`
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

---

## 📋 Modelos de Datos

### ItemModel
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "price": "number",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### UserModel
```json
{
  "id": "string",
  "email": "string",
  "name": "string",
  "picture": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### EventResponse
```json
{
  "id": "string",
  "summary": "string",
  "description": "string",
  "start": "object",
  "end": "object",
  "location": "string",
  "status": "string",
  "htmlLink": "string",
  "created": "string",
  "updated": "string"
}
```

### AttendanceResponse
```json
{
  "event_id": "string",
  "attendees": ["string"],
  "non_attendees": ["string"],
  "total_attendees": "number",
  "total_non_attendees": "number",
  "message": "string"
}
```

---

## 🔧 Configuración CORS

**Orígenes permitidos**:
- `http://localhost:3000`
- `http://localhost:3003`
- `https://pasesfalsos.cl`
- `https://www.pasesfalsos.cl`

**Headers permitidos**: `*`
**Métodos permitidos**: `*`
**Credentials**: `true`

---

## 📝 Notas Importantes

1. **Autenticación**: Los endpoints de autenticación usan cookies de sesión
2. **CORS**: Configurado para desarrollo local y producción
3. **MongoDB**: Conexión automática en cada request
4. **Google Calendar**: Requiere credenciales válidas
5. **PKCE**: Implementado para seguridad OAuth
6. **Silent Login**: Solo funciona si el usuario ya está logueado en Google

---

## 🚀 URLs para el Frontend

### Para Silent Login (usuarios registrados):
```
GET http://localhost:8000/auth/google/silent?email=usuario@email.com
```

### Para Login Normal (nuevos usuarios):
```
GET http://localhost:8000/auth/google/login
```

### Para Verificar Sesión:
```
GET http://localhost:8000/auth/session
```

### Para Logout:
```
POST http://localhost:8000/auth/logout
```
