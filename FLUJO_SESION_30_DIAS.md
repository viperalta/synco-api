# Flujo de Sesión de 30 Días - Synco API

## 📋 Resumen del Sistema

El sistema implementa un flujo de autenticación con **refresh tokens** que permite mantener al usuario logueado por **30 días** sin necesidad de hacer login nuevamente.

### Configuración Actual
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 horas
REFRESH_TOKEN_EXPIRE_DAYS=30      # 30 días
```

---

## 🔄 Flujo Completo

### 1. **Login Inicial** (Día 0)

**Frontend → Backend:**
```javascript
POST /auth/google
{
  "access_token": "google_access_token"
}
```

**Backend → Frontend:**
```json
{
  "access_token": "jwt_access_token_24h",
  "refresh_token": "jwt_refresh_token_30d",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "68f321cf18f9864c728fcb08",
    "email": "viperalta@gmail.com",
    "name": "Vicente Peralta",
    "roles": ["admin", "player"],
    "is_active": true
  }
}
```

**Frontend debe guardar:**
```javascript
localStorage.setItem('access_token', data.access_token);    // 24h
localStorage.setItem('refresh_token', data.refresh_token);  // 30d
```

---

### 2. **Uso Normal** (Días 0-1)

**Frontend hace requests autenticados:**
```javascript
fetch('/admin/users', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
})
```

---

### 3. **Renovación Automática** (Cada 24 horas)

**Cuando access_token expira, Frontend debe:**

**Paso 1: Detectar expiración**
```javascript
function isAccessTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return Date.now() >= payload.exp * 1000;
  } catch {
    return true;
  }
}
```

**Paso 2: Renovar automáticamente**
```javascript
POST /auth/refresh
{
  "refresh_token": "jwt_refresh_token_30d"
}
```

**Respuesta:**
```json
{
  "access_token": "nuevo_jwt_access_token_24h",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Paso 3: Actualizar storage**
```javascript
localStorage.setItem('access_token', newAccessToken);
// refresh_token se mantiene igual
```

---

### 4. **Verificación de Sesión Activa**

**Frontend puede verificar si la sesión sigue activa:**
```javascript
POST /auth/check-session
{
  "refresh_token": "jwt_refresh_token_30d"
}
```

**Respuesta (si sesión activa):**
```json
{
  "access_token": "nuevo_jwt_access_token_24h",
  "refresh_token": "jwt_refresh_token_30d",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { ... }
}
```

**Respuesta (si sesión expirada):**
```json
{
  "detail": "Refresh token not found or expired"
}
```

---

## 🎯 Implementación Frontend Requerida

### Clase AuthManager Sugerida

```javascript
class AuthManager {
  constructor() {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  // Verificar si access_token está expirado
  isAccessTokenExpired() {
    if (!this.accessToken) return true;
    
    try {
      const payload = JSON.parse(atob(this.accessToken.split('.')[1]));
      return Date.now() >= payload.exp * 1000;
    } catch {
      return true;
    }
  }

  // Renovar access_token automáticamente
  async refreshAccessToken() {
    if (!this.refreshToken) {
      this.logout();
      return false;
    }

    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        this.accessToken = data.access_token;
        localStorage.setItem('access_token', data.access_token);
        return true;
      } else {
        this.logout();
        return false;
      }
    } catch (error) {
      this.logout();
      return false;
    }
  }

  // Interceptor para requests automático
  async makeAuthenticatedRequest(url, options = {}) {
    if (this.isAccessTokenExpired()) {
      const refreshed = await this.refreshAccessToken();
      if (!refreshed) {
        throw new Error('Session expired');
      }
    }

    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.accessToken}`
      }
    });
  }

  // Verificar sesión activa
  async checkSession() {
    if (!this.refreshToken) return false;

    try {
      const response = await fetch('/auth/check-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        this.accessToken = data.access_token;
        localStorage.setItem('access_token', data.access_token);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // Redirigir a login
    window.location.href = '/login';
  }
}
```

---

## 📅 Timeline de la Sesión

```
Día 0: Login inicial
├── access_token: 24h ✅
└── refresh_token: 30d ✅

Día 1: Access token expira
├── Frontend detecta expiración ✅
├── Usa refresh_token para renovar ✅
└── Nuevo access_token: +24h ✅

Día 2: Access token expira
├── Frontend detecta expiración ✅
├── Usa refresh_token para renovar ✅
└── Nuevo access_token: +24h ✅

... (se repite cada 24h)

Día 30: Refresh token expira
├── Frontend intenta renovar ❌
├── Backend rechaza (refresh_token expirado) ❌
└── Usuario debe hacer login nuevamente 🔄
```

---

## ✅ Checklist para Frontend

### Almacenamiento
- [ ] Guardar `access_token` en localStorage
- [ ] Guardar `refresh_token` en localStorage
- [ ] No almacenar tokens en sessionStorage (se pierden al cerrar navegador)

### Detección de Expiración
- [ ] Verificar si `access_token` está expirado antes de cada request
- [ ] Implementar función `isAccessTokenExpired()`

### Renovación Automática
- [ ] Llamar `/auth/refresh` cuando `access_token` expira
- [ ] Actualizar `access_token` en localStorage
- [ ] Mantener `refresh_token` sin cambios

### Manejo de Errores
- [ ] Si `/auth/refresh` falla → logout automático
- [ ] Si `refresh_token` expira → logout automático
- [ ] Redirigir a login cuando sesión expira

### Requests Autenticados
- [ ] Usar interceptor para renovar tokens automáticamente
- [ ] Incluir `Authorization: Bearer <token>` en headers
- [ ] Manejar errores 401/403 apropiadamente

### Verificación de Sesión
- [ ] Verificar sesión activa al cargar la app
- [ ] Usar `/auth/check-session` para validar tokens
- [ ] Mostrar estado de autenticación al usuario

---

## 🚨 Puntos Críticos

1. **Nunca almacenar tokens en sessionStorage** - se pierden al cerrar navegador
2. **Siempre verificar expiración** antes de hacer requests
3. **Manejar errores de renovación** - logout automático si falla
4. **Usar HTTPS en producción** - tokens viajan en headers
5. **Limpiar tokens al logout** - remover de localStorage

---

## 🔧 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/auth/google` | POST | Login inicial con Google |
| `/auth/refresh` | POST | Renovar access_token |
| `/auth/check-session` | POST | Verificar sesión activa |
| `/auth/logout` | POST | Cerrar sesión |
| `/auth/me` | GET | Obtener usuario actual |
| `/admin/users` | GET | Listar usuarios (admin) |
| `/admin/users/{id}` | PUT | Actualizar usuario (admin) |

---

## 📝 Notas Importantes

- **Access Token**: Válido por 24 horas, se renueva automáticamente
- **Refresh Token**: Válido por 30 días, permite renovar access tokens
- **Sesión efectiva**: 30 días sin necesidad de login
- **Renovación**: Automática cada 24 horas
- **Seguridad**: Solo un refresh token activo por usuario
- **Compatibilidad**: Funciona con conexión reutilizada (optimización implementada)
