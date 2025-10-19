# Documentación Completa - Backend Synco API

## Información General
- **Base URL**: `http://localhost:8000`
- **Versión**: 1.0.0
- **Autenticación**: JWT + Cookies de sesión
- **Sistema de Roles**: admin, coach, player, visitor

---

## 🔐 Sistema de Roles y Permisos

### Roles Disponibles

1. **admin** - Administrador completo
2. **coach** - Entrenador/Coach  
3. **player** - Jugador
4. **visitor** - Usuario sin roles asignados (automático)

### Permisos por Rol

#### Admin
- `users.list` - Listar usuarios
- `users.view` - Ver usuarios
- `users.edit` - Editar usuarios
- `users.delete` - Eliminar usuarios
- `users.manage_roles` - Gestionar roles
- `events.create` - Crear eventos
- `events.edit` - Editar eventos
- `events.delete` - Eliminar eventos
- `events.view` - Ver eventos
- `calendar.manage` - Gestionar calendario
- `attendance.manage` - Gestionar asistencia

#### Coach
- `users.view` - Ver usuarios
- `events.create` - Crear eventos
- `events.edit` - Editar eventos
- `events.view` - Ver eventos
- `attendance.manage` - Gestionar asistencia

#### Player
- `events.view` - Ver eventos
- `attendance.self` - Gestionar su propia asistencia

#### Visitor (sin roles)
- `events.view` - Ver eventos

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

### GET /debug/google-calendar-permissions
**Descripción**: Verificar permisos de Google Calendar
**Respuesta**: `Object`

### GET /debug/mongodb
**Descripción**: Verificar conexión a MongoDB
**Respuesta**: `Object`

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

---

## 🎯 Endpoints de Eventos

### GET /eventos
**Descripción**: Obtener eventos de un calendario
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
- `max_results` (int, default=50): Número máximo de eventos (1-100)
- `days_ahead` (int, default=90): Días hacia adelante (1-365)
**Respuesta**: `List[EventResponse]`

### GET /eventos/{calendar_id}
**Descripción**: Obtener eventos de un calendario específico por ID
**Parámetros**:
- `calendar_id` (string): ID del calendario
**Parámetros Query**:
- `max_results` (int, default=50): Número máximo de eventos (1-100)
- `days_ahead` (int, default=90): Días hacia adelante (1-365)
**Respuesta**: `List[EventResponse]`

### GET /eventos/{event_id}
**Descripción**: Obtener un evento específico
**Autenticación**: Requerida
**Permisos**: `events.view`
**Parámetros**:
- `event_id` (string): ID del evento
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
**Respuesta**: `EventResponse`

### POST /eventos
**Descripción**: Crear un nuevo evento
**Autenticación**: Requerida
**Permisos**: `events.create`
**Body**: `EventCreateRequest`
```json
{
  "summary": "string",
  "description": "string",
  "start_datetime": "2024-01-01T10:00:00",
  "end_datetime": "2024-01-01T11:00:00",
  "location": "string",
  "calendar_id": "primary"
}
```
**Respuesta**: `EventResponse`

### PUT /eventos/{event_id}
**Descripción**: Actualizar un evento existente
**Autenticación**: Requerida
**Permisos**: `events.edit`
**Parámetros**:
- `event_id` (string): ID del evento
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
**Body**: `EventUpdateRequest`
```json
{
  "summary": "string",
  "description": "string",
  "start_datetime": "2024-01-01T10:00:00",
  "end_datetime": "2024-01-01T11:00:00",
  "location": "string"
}
```
**Respuesta**: `EventResponse`

### DELETE /eventos/{event_id}
**Descripción**: Eliminar un evento
**Autenticación**: Requerida
**Permisos**: `events.delete`
**Parámetros**:
- `event_id` (string): ID del evento
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
**Respuesta**: `EventDeleteResponse`
```json
{
  "message": "string",
  "event_id": "string",
  "deleted": true
}
```

### GET /eventos-con-asistencia
**Descripción**: Obtener eventos con información de asistencia
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
- `max_results` (int, default=50): Número máximo de eventos (1-100)
- `days_ahead` (int, default=90): Días hacia adelante (1-365)
**Respuesta**: `List[dict]` (eventos con datos de asistencia)

### GET /eventos-con-asistencia-detallada
**Descripción**: Obtener eventos con información de asistencia en formato EventResponse
**Autenticación**: Requerida
**Permisos**: `events.view`
**Parámetros Query**:
- `calendar_id` (string, default="primary"): ID del calendario
- `max_results` (int, default=50): Número máximo de eventos (1-100)
- `days_ahead` (int, default=90): Días hacia adelante (1-365)
**Respuesta**: `List[EventResponse]` (eventos con campos attendees y non_attendees poblados)

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
**Autenticación**: Requerida
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
    "picture": "string",
    "nickname": "string",
    "roles": ["string"]
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

## 👨‍💼 Endpoints de Administración de Usuarios

### GET /admin/users
**Descripción**: Obtener lista de todos los usuarios
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Parámetros Query**:
- `skip` (int, default=0): Número de usuarios a saltar
- `limit` (int, default=100): Número máximo de usuarios
**Respuesta**: `UserListResponse`

### GET /admin/users/{user_id}
**Descripción**: Obtener información detallada de un usuario específico
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Parámetros**:
- `user_id` (string): ID del usuario
**Respuesta**: `UserModel`

### PUT /admin/users/{user_id}
**Descripción**: Actualizar información de un usuario
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Parámetros**:
- `user_id` (string): ID del usuario
**Body**: `UserUpdateRequest`
```json
{
  "nickname": "string",
  "roles": ["string"],
  "is_active": true
}
```
**Respuesta**: `UserModel`

### PUT /admin/users/{user_id}/roles
**Descripción**: Actualizar roles de un usuario
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Parámetros**:
- `user_id` (string): ID del usuario
**Body**: `UserRoleUpdateRequest`
```json
{
  "roles": ["string"]
}
```
**Respuesta**: `UserModel`

### PUT /admin/users/{user_id}/nickname
**Descripción**: Actualizar nickname de un usuario
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Parámetros**:
- `user_id` (string): ID del usuario
**Body**: `UserNicknameUpdateRequest`
```json
{
  "nickname": "string"
}
```
**Respuesta**: `UserModel`

### GET /admin/roles
**Descripción**: Obtener lista de roles disponibles y sus permisos
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Respuesta**: `Object`
```json
{
  "roles": ["admin", "coach", "player", "visitor"],
  "permissions": {
    "admin": ["users.list", "users.view", ...],
    "coach": ["users.view", "events.create", ...],
    "player": ["events.view", "attendance.self"],
    "visitor": ["events.view"]
  }
}
```

### GET /admin/permissions/{user_id}
**Descripción**: Obtener permisos específicos de un usuario
**Autenticación**: Requerida
**Permisos**: `users.manage_roles` (solo admin)
**Parámetros**:
- `user_id` (string): ID del usuario
**Respuesta**: `Object`
```json
{
  "user_id": "string",
  "user_email": "string",
  "user_nickname": "string",
  "roles": ["string"],
  "permissions": ["string"],
  "is_active": true
}
```

---

## 📋 Modelos de Datos

### UserModel
```json
{
  "id": "string",
  "google_id": "string",
  "email": "string",
  "name": "string",
  "picture": "string",
  "nickname": "string",
  "roles": ["string"],
  "is_active": true,
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
  "start": {
    "dateTime": "2024-01-01T10:00:00Z",
    "timeZone": "America/Santiago"
  },
  "end": {
    "dateTime": "2024-01-01T11:00:00Z",
    "timeZone": "America/Santiago"
  },
  "location": "string",
  "status": "string",
  "htmlLink": "string",
  "created": "string",
  "updated": "string",
  "attendees": ["string"],
  "non_attendees": ["string"]
}
```

**Nota**: Los campos `attendees` y `non_attendees` están incluidos en EventResponse para futura migración desde EventAttendanceModel. Por ahora coexisten ambos sistemas:
- `attendees`: Lista de nombres de usuarios que asistirán al evento
- `non_attendees`: Lista de nombres de usuarios que NO asistirán al evento
- Estos campos se poblan automáticamente en `/eventos/{event_id}` y `/eventos-con-asistencia-detallada`
- En otros endpoints pueden aparecer como arrays vacíos `[]`

### EventCreateRequest
```json
{
  "summary": "string",
  "description": "string",
  "start_datetime": "2024-01-01T10:00:00",
  "end_datetime": "2024-01-01T11:00:00",
  "location": "string",
  "calendar_id": "primary"
}
```

### EventUpdateRequest
```json
{
  "summary": "string",
  "description": "string",
  "start_datetime": "2024-01-01T10:00:00",
  "end_datetime": "2024-01-01T11:00:00",
  "location": "string"
}
```

### EventDeleteResponse
```json
{
  "message": "string",
  "event_id": "string",
  "deleted": true
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

1. **Autenticación**: Los endpoints protegidos requieren token válido
2. **Permisos**: Cada endpoint verifica permisos específicos según el rol
3. **Visitors**: Usuarios sin roles tienen permisos limitados automáticamente
4. **CORS**: Configurado para desarrollo local y producción
5. **MongoDB**: Conexión automática en cada request
6. **Google Calendar**: Requiere credenciales válidas para eventos
7. **PKCE**: Implementado para seguridad OAuth
8. **Silent Login**: Solo funciona si el usuario ya está logueado en Google

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

---

## 🔒 Manejo de Errores

### Códigos de Error Comunes

- **401 Unauthorized**: Token inválido o expirado
- **403 Forbidden**: Usuario no tiene permisos para la acción
- **404 Not Found**: Recurso no encontrado
- **400 Bad Request**: Datos inválidos
- **503 Service Unavailable**: Google Calendar Service no disponible

### Ejemplo de Manejo de Errores

```javascript
try {
  const response = await fetch('/admin/users', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      // Token inválido, redirigir a login
      redirectToLogin();
    } else if (response.status === 403) {
      // Sin permisos
      showError('No tienes permisos para acceder a esta función');
    } else {
      // Otro error
      const error = await response.json();
      showError(error.detail);
    }
    return;
  }
  
  const data = await response.json();
  // Procesar datos...
  
} catch (error) {
  console.error('Error:', error);
  showError('Error de conexión');
}
```

---

## 🎯 Implementación Sugerida en Frontend

### Verificación de Permisos
```javascript
// Verificar si usuario puede crear eventos
const canCreateEvents = user.roles.includes('admin') || user.roles.includes('coach');

// Verificar si usuario es admin
const isAdmin = user.roles.includes('admin');

// Verificar si usuario es visitor
const isVisitor = !user.roles || user.roles.length === 0;
```

### Manejo de Roles
```javascript
// Obtener roles disponibles
async function getAvailableRoles() {
  const response = await fetch('/admin/roles', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
}

// Actualizar roles de usuario
async function updateUserRoles(userId, roles) {
  const response = await fetch(`/admin/users/${userId}/roles`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ roles })
  });
  return await response.json();
}
```

### Gestión de Eventos
```javascript
// Crear evento
async function createEvent(eventData) {
  const response = await fetch('/eventos', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(eventData)
  });
  return await response.json();
}

// Actualizar evento
async function updateEvent(eventId, eventData) {
  const response = await fetch(`/eventos/${eventId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(eventData)
  });
  return await response.json();
}

// Eliminar evento
async function deleteEvent(eventId) {
  const response = await fetch(`/eventos/${eventId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
}
```

---

## 📊 Resumen de Endpoints por Categoría

### Públicos (sin autenticación)
- `GET /` - Root
- `GET /health` - Health check
- `GET /debug/*` - Debug endpoints
- `GET /items` - Items CRUD
- `GET /calendarios` - Calendarios
- `GET /eventos` - Eventos (lectura)
- `GET /eventos/{calendar_id}` - Eventos por calendario
- `GET /eventos-con-asistencia` - Eventos con asistencia
- `POST /asistir` - Registrar asistencia
- `GET /asistencia/{event_id}` - Obtener asistencia
- `GET /asistencias` - Todas las asistencias
- `DELETE /cancelar-asistencia/{event_id}` - Cancelar asistencia
- `GET /auth/google/silent` - Silent login
- `GET /auth/google/login` - Login normal
- `GET /auth/google/callback` - OAuth callback

### Con Autenticación
- `GET /eventos/{event_id}` - Obtener evento específico
- `POST /eventos` - Crear evento
- `PUT /eventos/{event_id}` - Actualizar evento
- `DELETE /eventos/{event_id}` - Eliminar evento
- `POST /auth/google` - Auth API directa
- `GET /auth/me` - Usuario actual
- `POST /auth/refresh` - Renovar token
- `POST /auth/revoke` - Revocar token
- `POST /auth/check-session` - Verificar sesión
- `GET /auth/session` - Sesión desde cookie
- `POST /auth/logout` - Cerrar sesión

### Solo Admin
- `GET /admin/users` - Listar usuarios
- `GET /admin/users/{user_id}` - Obtener usuario
- `PUT /admin/users/{user_id}` - Actualizar usuario
- `PUT /admin/users/{user_id}/roles` - Actualizar roles
- `PUT /admin/users/{user_id}/nickname` - Actualizar nickname
- `GET /admin/roles` - Roles disponibles
- `GET /admin/permissions/{user_id}` - Permisos de usuario

---

Esta documentación incluye todos los endpoints realmente implementados en el backend, con el sistema de roles actualizado (admin, coach, player, visitor) y los nuevos endpoints CRUD para eventos.
