# Sistema de Manejo de Tokens JWT

## 📋 **Resumen de cambios implementados**

Se ha implementado un sistema completo de manejo de tokens JWT con refresh tokens para mejorar la seguridad y experiencia del usuario.

## 🔧 **Configuración de variables de entorno**

Agrega estas variables a tu archivo `.env`:

```bash
# Tiempos de expiración de tokens
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 horas
REFRESH_TOKEN_EXPIRE_DAYS=30      # 30 días

# Clave secreta para JWT (cambiar en producción)
JWT_SECRET_KEY=tu-clave-secreta-super-segura-para-jwt
```

## 🎯 **Nuevos endpoints disponibles**

### **1. POST `/auth/google` - Autenticación con Google**
**Request:**
```json
{
  "access_token": "google_access_token"
}
```

**Response:**
```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token",
  "token_type": "bearer",
  "expires_in": 5184000,
  "user": {
    "id": "user_id",
    "google_id": "google_id",
    "email": "user@example.com",
    "name": "User Name",
    "picture": "https://...",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### **2. POST `/auth/refresh` - Renovar access token**
**Request:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_access_token",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

### **3. POST `/auth/revoke` - Revocar refresh token**
**Request:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Response:**
```json
{
  "message": "Token revocado exitosamente"
}
```

### **4. POST `/auth/logout` - Cerrar sesión (requiere autenticación)**
**Headers:**
```
Authorization: Bearer jwt_access_token
```

**Response:**
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

### **5. GET `/auth/me` - Obtener usuario actual (requiere autenticación)**
**Headers:**
```
Authorization: Bearer jwt_access_token
```

**Response:**
```json
{
  "id": "user_id",
  "google_id": "google_id",
  "email": "user@example.com",
  "name": "User Name",
  "picture": "https://...",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 🔐 **Características de seguridad**

### **1. Tipos de tokens**
- **Access Token**: Válido por 24 horas, para autenticación
- **Refresh Token**: Válido por 30 días, para renovar access tokens

### **2. Validación de tokens**
- Los tokens incluyen un campo `type` para distinguir entre access y refresh
- Los refresh tokens se almacenan en la base de datos para control de revocación
- Solo un refresh token activo por usuario (los anteriores se revocan automáticamente)

### **3. Revocación de tokens**
- Los refresh tokens se pueden revocar individualmente
- El logout revoca todos los tokens del usuario
- Los tokens expirados se limpian automáticamente

## 🧪 **Pruebas**

### **1. Probar autenticación completa:**
```bash
# 1. Autenticar con Google
curl -X POST "http://localhost:8000/auth/google" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "google_access_token"}'

# 2. Usar access token para acceder a rutas protegidas
curl -H "Authorization: Bearer jwt_access_token" \
  "http://localhost:8000/auth/me"

# 3. Renovar access token
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "jwt_refresh_token"}'

# 4. Cerrar sesión
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Authorization: Bearer jwt_access_token"
```

### **2. Verificar en la base de datos:**
```bash
# Verificar que los refresh tokens se guardan
curl http://localhost:8000/debug/mongodb
```

## 📱 **Implementación en el frontend**

### **1. Almacenar ambos tokens:**
```javascript
// Después del login exitoso
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

### **2. Renovar access token automáticamente:**
```javascript
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      return data.access_token;
    } else {
      // Refresh token expirado, redirigir a login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return null;
    }
  } catch (error) {
    console.error('Error renovando token:', error);
    return null;
  }
};
```

### **3. Interceptor para renovar tokens automáticamente:**
```javascript
const apiCall = async (url, method = 'GET', body = null) => {
  let accessToken = localStorage.getItem('access_token');
  
  const makeRequest = async (token) => {
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      ...(body && { body: JSON.stringify(body) })
    });
    
    return response;
  };

  let response = await makeRequest(accessToken);

  // Si el token expiró, intentar renovarlo
  if (response.status === 401 && accessToken) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await makeRequest(newToken);
    }
  }

  return response;
};
```

## 🚀 **Deploy a producción**

### **1. Variables de entorno en Vercel:**
```
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_SECRET_KEY=tu-clave-secreta-super-segura-para-jwt
```

### **2. Verificar que funciona:**
```bash
# Probar en producción
curl -X POST "https://tu-api.vercel.app/auth/google" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "google_access_token"}'
```

## ✅ **Beneficios del nuevo sistema**

1. **Sesiones más largas**: Access tokens válidos por 24 horas
2. **Seguridad mejorada**: Refresh tokens con revocación
3. **Mejor UX**: Renovación automática de tokens
4. **Control granular**: Revocación individual o masiva de tokens
5. **Limpieza automática**: Tokens expirados se eliminan automáticamente

## 🔧 **Mantenimiento**

### **Limpieza de tokens expirados:**
```python
# Ejecutar periódicamente (ej: cada día)
await refresh_token_service.cleanup_expired_tokens()
```

### **Monitoreo:**
- Revisar logs de autenticación
- Monitorear uso de refresh tokens
- Verificar limpieza de tokens expirados
