# CORRECCIONES FRONT AUTH

## 📋 Resumen de Problemas Identificados

El `authcontext.js` del frontend tiene varios desajustes con la implementación del backend que impiden el funcionamiento correcto del flujo de sesión de 30 días.

---

## 🔧 Correcciones Requeridas

### 1. **Silent Login: Método y Payload Incorrectos**

**❌ Problema:**
```javascript
// Frontend actual (INCORRECTO)
const response = await fetch(`${getBackendUrl()}/auth/google/silent`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email })
});
```

**✅ Corrección:**
```javascript
// Frontend corregido
const response = await fetch(
  `${getBackendUrl()}/auth/google/silent?email=${encodeURIComponent(email)}`,
  { 
    method: 'GET', 
    credentials: 'include' 
  }
);
```

**📝 Explicación:** El backend define `GET /auth/google/silent` con `email` como query parameter, no como POST con body JSON.

---

### 2. **Eliminar Dependencia de `token_expiry`**

**❌ Problema:**
- Se persiste y usa `token_expiry` desde respuestas del backend
- El backend no devuelve este campo
- Se usa `tokenExpiry` en estado y localStorage

**✅ Corrección:**
```javascript
// Eliminar completamente tokenExpiry del estado
// Eliminar localStorage.setItem('token_expiry', ...)
// Eliminar localStorage.getItem('token_expiry')

// Usar solo esta función para verificar expiración:
const isAccessTokenExpired = () => {
  if (!accessToken) return true;
  try {
    const payload = JSON.parse(atob(accessToken.split('.')[1]));
    return Date.now() >= payload.exp * 1000;
  } catch {
    return true;
  }
};
```

**📝 Explicación:** El JWT ya contiene `exp` (timestamp de expiración). No necesitamos un campo adicional.

---

### 3. **Eliminar Endpoint Inexistente `/auth/token`**

**❌ Problema:**
```javascript
// Función que llama a endpoint inexistente
const getNewAccessToken = async () => {
  const response = await fetch(`${getBackendUrl()}/auth/token`, {
    method: 'POST',
    credentials: 'include',
    // ...
  });
};
```

**✅ Corrección:**
```javascript
// ELIMINAR completamente getNewAccessToken()
// Usar en su lugar:
// 1. POST /auth/refresh (con refresh_token)
// 2. GET /auth/session (para obtener token fresco desde cookie)
```

**📝 Explicación:** El endpoint `/auth/token` no existe en el backend. Usar los endpoints válidos.

---

### 4. **Control de Concurrencia con useRef**

**❌ Problema:**
```javascript
// Variables que se recrean en cada render
let sessionCheckPromise = null;
let lastSessionCheck = 0;
let tokenRefreshPromise = null;
let lastTokenRefresh = 0;
```

**✅ Corrección:**
```javascript
// Migrar a useRef para persistir entre renders
const sessionCheckPromiseRef = useRef(null);
const lastSessionCheckRef = useRef(0);
const tokenRefreshPromiseRef = useRef(null);
const lastTokenRefreshRef = useRef(0);

// Ejemplo de uso:
if (sessionCheckPromiseRef.current) {
  return await sessionCheckPromiseRef.current;
}

lastSessionCheckRef.current = Date.now();
sessionCheckPromiseRef.current = (async () => {
  // ... lógica de verificación
})();

const result = await sessionCheckPromiseRef.current;
sessionCheckPromiseRef.current = null;
return result;
```

**📝 Explicación:** Las variables `let` se recrean en cada render, causando múltiples ejecuciones simultáneas.

---

### 5. **Flujo de Renovación Correcto**

**✅ Implementación correcta:**

```javascript
const refreshAccessToken = async () => {
  const currentRefresh = refreshToken || localStorage.getItem('refresh_token');
  if (!currentRefresh) {
    await handleLogout();
    throw new Error('No refresh token');
  }

  const response = await fetch(`${getBackendUrl()}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: currentRefresh })
  });
  
  if (!response.ok) {
    await handleLogout();
    throw new Error('Refresh failed');
  }

  const data = await response.json();
  setAccessToken(data.access_token);
  localStorage.setItem('access_token', data.access_token);
  
  if (data.refresh_token) {
    setRefreshToken(data.refresh_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }
  
  return data.access_token;
};
```

---

### 6. **Reintento Automático en 401**

**✅ Implementación correcta:**

```javascript
const authenticatedApiCall = async (endpoint, options = {}) => {
  const token = await getAuthToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${getBackendUrl()}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      try {
        // Renovar token y reintentar
        await refreshAccessToken();
        const retryToken = localStorage.getItem('access_token');
        const retryHeaders = {
          'Content-Type': 'application/json',
          ...options.headers
        };
        if (retryToken) retryHeaders['Authorization'] = `Bearer ${retryToken}`;
        
        const retryResponse = await fetch(`${getBackendUrl()}${endpoint}`, {
          ...options,
          credentials: 'include',
          headers: retryHeaders
        });
        
        if (!retryResponse.ok) {
          throw new Error(`Error del servidor: ${retryResponse.status}`);
        }
        return retryResponse;
      } catch (e) {
        throw new Error('Token de autenticación inválido o expirado');
      }
    }
    // ... otros errores
  }
  
  return response;
};
```

---

### 7. **Verificar Endpoint `/auth/check-user`**

**❌ Problema:**
```javascript
const checkUserExists = async (email) => {
  const response = await authenticatedApiCall('/auth/check-user', {
    method: 'POST',
    body: JSON.stringify({ email })
  });
  // ...
};
```

**✅ Acción requerida:**
- Verificar que el backend expone `/auth/check-user`
- Si no existe, eliminar `checkUserExists` o cambiarlo por endpoint existente

---

### 8. **Limpieza de Código**

**✅ Eliminar:**
- Import sin uso: `apiCall` si no se utiliza
- Todas las referencias a `tokenExpiry`
- Función `getNewAccessToken()`
- Logs excesivos en producción

---

## 🎯 Snippets Finales Sugeridos

### Silent Login Corregido
```javascript
const attemptSilentLogin = async (email) => {
  try {
    const response = await fetch(
      `${getBackendUrl()}/auth/google/silent?email=${encodeURIComponent(email)}`,
      { method: 'GET', credentials: 'include' }
    );
    if (response.ok) {
      return await checkExistingSession();
    }
    return false;
  } catch {
    return false;
  }
};
```

### Obtener Token para Requests
```javascript
const getAuthToken = async () => {
  if (accessToken && !isAccessTokenExpired()) {
    return accessToken;
  }

  if (tokenRefreshPromiseRef.current) {
    return await tokenRefreshPromiseRef.current;
  }

  tokenRefreshPromiseRef.current = (async () => {
    try {
      // Intentar refrescar primero
      return await refreshAccessToken();
    } catch {
      // Como alternativa (si hay cookie de sesión válida)
      try {
        const resp = await fetch(`${getBackendUrl()}/auth/session`, {
          method: 'GET',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' }
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.access_token) {
            setAccessToken(data.access_token);
            localStorage.setItem('access_token', data.access_token);
            return data.access_token;
          }
        }
        return null;
      } finally {
        tokenRefreshPromiseRef.current = null;
      }
    } finally {
      tokenRefreshPromiseRef.current = null;
    }
  })();

  return await tokenRefreshPromiseRef.current;
};
```

---

## ✅ Checklist de Verificación

### Correcciones Críticas
- [ ] Silent login usa `GET /auth/google/silent?email=...` con `credentials: 'include'`
- [ ] Eliminado `token_expiry` de estado y localStorage
- [ ] Eliminado `getNewAccessToken()` y llamadas a `/auth/token`
- [ ] Variables de cooldown/promesas migradas a `useRef`
- [ ] Renovación en 401: `POST /auth/refresh` y reintento automático

### Persistencia Correcta
- [ ] `access_token` en localStorage (24h)
- [ ] `refresh_token` en localStorage (30d)
- [ ] `user_email` en localStorage (para silent login)

### Endpoints Válidos
- [ ] `POST /auth/refresh` para renovar access_token
- [ ] `GET /auth/session` para obtener token fresco desde cookie
- [ ] `GET /auth/google/silent?email=...` para silent login
- [ ] Verificar existencia de `/auth/check-user` o eliminarlo

### Limpieza
- [ ] Import sin uso (`apiCall`) eliminado
- [ ] Logs excesivos removidos para producción
- [ ] Código muerto eliminado

---

## 🚨 Puntos Críticos

1. **Nunca usar `token_expiry`** - el JWT ya contiene `exp`
2. **Siempre usar `credentials: 'include'`** para enviar cookies
3. **Manejar 401 con renovación automática** y reintento
4. **Usar `useRef` para variables de control** que deben persistir entre renders
5. **Verificar endpoints antes de usar** - no asumir que existen

---

## 📝 Notas Finales

Con estas correcciones, el frontend debería funcionar correctamente con el flujo de sesión de 30 días implementado en el backend. El usuario permanecerá logueado por 30 días con renovación automática del access_token cada 24 horas.
