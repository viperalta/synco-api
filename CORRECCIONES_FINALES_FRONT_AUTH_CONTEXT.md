# CORRECCIONES FINALES FRONT AUTH CONTEXT

## 📋 Resumen del Estado Actual

El `authcontext.js` del frontend ha implementado **correctamente la mayoría de las correcciones** necesarias para el flujo de sesión de 30 días. Solo quedan **3 problemas menores** que requieren ajustes finales.

---

## ✅ **Correcciones Ya Implementadas Correctamente**

### 1. **Silent Login Corregido** ✅
```javascript
// ✅ CORRECTO - GET con query parameter
const response = await fetch(
  `${getBackendUrl()}/auth/google/silent?email=${encodeURIComponent(email)}`,
  { method: 'GET', credentials: 'include' }
);
```

### 2. **Migración a useRef** ✅
```javascript
// ✅ CORRECTO - Variables de control persistentes
const sessionCheckPromiseRef = useRef(null);
const lastSessionCheckRef = useRef(0);
const tokenRefreshPromiseRef = useRef(null);
const lastTokenRefreshRef = useRef(0);
```

### 3. **Verificación JWT Expiration** ✅
```javascript
// ✅ CORRECTO - Solo usa exp del JWT
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

### 4. **Eliminación de getNewAccessToken** ✅
- ✅ Función eliminada
- ✅ No hay llamadas a `/auth/token`

### 5. **Reintento Automático en 401** ✅
```javascript
// ✅ CORRECTO - Renovación y reintento
if (response.status === 401) {
  try {
    await refreshAccessToken();
    // ... reintento con nuevo token
  } catch (e) {
    throw new Error('Token de autenticación inválido o expirado');
  }
}
```

---

## ⚠️ **Correcciones Finales Requeridas**

### 1. **Eliminar Completamente token_expiry**

**❌ Problema encontrado:**
```javascript
// Líneas 345-347 en getAuthToken()
if (userData.token_expiry) {
  localStorage.setItem('token_expiry', userData.token_expiry);
}
```

**✅ Corrección:**
```javascript
// ELIMINAR estas líneas completamente
// if (userData.token_expiry) {
//   localStorage.setItem('token_expiry', userData.token_expiry);
// }
```

**📝 Acción:** Buscar y eliminar **todas** las referencias a `token_expiry` en el archivo.

---

### 2. **Corregir initializeTokens()**

**❌ Problema actual:**
```javascript
const initializeTokens = () => {
  const savedToken = localStorage.getItem('access_token');
  const savedRefresh = localStorage.getItem('refresh_token');
  
  if (savedRefresh) {
    setRefreshToken(savedRefresh);
  }

  if (savedToken) {
    // ❌ PROBLEMA: Llama isAccessTokenExpired() antes de setAccessToken
    if (!isAccessTokenExpired()) { // accessToken es null aquí
      console.log('🔑 Token válido encontrado en localStorage');
      setAccessToken(savedToken);
      return true;
    } else {
      console.log('⏰ Token expirado en localStorage, limpiando...');
      localStorage.removeItem('access_token');
    }
  }
  
  return false;
};
```

**✅ Corrección:**
```javascript
const initializeTokens = () => {
  const savedToken = localStorage.getItem('access_token');
  const savedRefresh = localStorage.getItem('refresh_token');
  
  if (savedRefresh) {
    setRefreshToken(savedRefresh);
  }

  if (savedToken) {
    // ✅ CORRECTO: Setear token primero, luego verificar
    setAccessToken(savedToken);
    
    // Verificar expiración después de setear el token
    if (isAccessTokenExpired()) {
      console.log('⏰ Token expirado en localStorage, limpiando...');
      setAccessToken(null);
      localStorage.removeItem('access_token');
      return false;
    }
    
    console.log('🔑 Token válido encontrado en localStorage');
    return true;
  } else {
    console.log('❌ No hay tokens guardados en localStorage');
  }
  
  return false;
};
```

---

### 3. **Optimizar getAuthToken()**

**❌ Problema actual:**
```javascript
// Lógica confusa con múltiples intentos y fallbacks
const getAuthToken = async () => {
  // ... código complejo con múltiples paths
};
```

**✅ Corrección simplificada:**
```javascript
const getAuthToken = async () => {
  // 1. Si tenemos un token válido, usarlo directamente
  if (accessToken && !isAccessTokenExpired()) {
    return accessToken;
  }
  
  // 2. Evitar llamadas simultáneas
  if (tokenRefreshPromiseRef.current) {
    return await tokenRefreshPromiseRef.current;
  }
  
  // 3. Verificar cooldown
  const now = Date.now();
  if (now - lastTokenRefreshRef.current < TOKEN_REFRESH_COOLDOWN) {
    return accessToken || null;
  }
  
  lastTokenRefreshRef.current = now;
  
  tokenRefreshPromiseRef.current = (async () => {
    try {
      // Prioridad 1: Renovar con refresh_token
      if (refreshToken || localStorage.getItem('refresh_token')) {
        return await refreshAccessToken();
      }
      
      // Prioridad 2: Obtener token fresco desde /auth/session
      const response = await fetch(`${getBackendUrl()}/auth/session`, {
        credentials: 'include',
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
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
  })();
  
  return await tokenRefreshPromiseRef.current;
};
```

---

## 🔍 **Búsqueda y Reemplazo Requerida**

### Eliminar todas las referencias a token_expiry:

```bash
# Buscar estas líneas y ELIMINARLAS:
- "token_expiry"
- "setTokenExpiry"
- "localStorage.setItem('token_expiry'"
- "localStorage.getItem('token_expiry'"
- "userData.token_expiry"
```

### Verificar que no queden referencias:
```javascript
// ❌ ELIMINAR si aparecen:
if (userData.token_expiry) { ... }
setTokenExpiry(userData.token_expiry);
localStorage.setItem('token_expiry', userData.token_expiry);
localStorage.getItem('token_expiry');
```

---

## 📋 **Checklist Final**

### Correcciones Críticas
- [ ] **Eliminar todas las referencias a `token_expiry`**
- [ ] **Corregir `initializeTokens()` - setear token antes de verificar expiración**
- [ ] **Simplificar `getAuthToken()` - lógica más clara y directa**

### Verificación de Funcionamiento
- [ ] Silent login funciona con `GET /auth/google/silent?email=...`
- [ ] Renovación automática cada 24h con `POST /auth/refresh`
- [ ] Reintento automático en errores 401
- [ ] Persistencia correcta: `access_token`, `refresh_token`, `user_email`
- [ ] Logout limpia completamente el estado

### Limpieza Final
- [ ] No hay referencias a `token_expiry` en todo el archivo
- [ ] No hay llamadas a endpoints inexistentes
- [ ] Variables de control usan `useRef` correctamente
- [ ] Logs excesivos removidos para producción

---

## 🎯 **Snippet Completo de initializeTokens Corregido**

```javascript
const initializeTokens = () => {
  const savedToken = localStorage.getItem('access_token');
  const savedRefresh = localStorage.getItem('refresh_token');
  
  console.log('🔍 Inicializando tokens desde localStorage...');
  console.log('📦 Token guardado:', !!savedToken);
  console.log('📦 Refresh token guardado:', !!savedRefresh);
  
  if (savedRefresh) {
    setRefreshToken(savedRefresh);
  }

  if (savedToken) {
    // Setear token primero
    setAccessToken(savedToken);
    
    // Verificar expiración después de setear
    if (isAccessTokenExpired()) {
      console.log('⏰ Token expirado en localStorage, limpiando...');
      setAccessToken(null);
      localStorage.removeItem('access_token');
      return false;
    }
    
    console.log('🔑 Token válido encontrado en localStorage');
    return true;
  } else {
    console.log('❌ No hay tokens guardados en localStorage');
  }
  
  return false;
};
```

---

## 🎯 **Snippet Completo de getAuthToken Optimizado**

```javascript
const getAuthToken = async () => {
  console.log('🔑 getAuthToken llamado - accessToken:', !!accessToken, 'expired:', isAccessTokenExpired());
  
  // 1. Token válido existente
  if (accessToken && !isAccessTokenExpired()) {
    console.log('✅ Usando token existente válido');
    return accessToken;
  }
  
  // 2. Evitar llamadas simultáneas
  if (tokenRefreshPromiseRef.current) {
    console.log('⏳ Esperando llamada de token en progreso...');
    return await tokenRefreshPromiseRef.current;
  }
  
  // 3. Verificar cooldown
  const now = Date.now();
  if (now - lastTokenRefreshRef.current < TOKEN_REFRESH_COOLDOWN) {
    console.log('⏰ Cooldown activo, usando token existente si está disponible');
    return accessToken || null;
  }
  
  lastTokenRefreshRef.current = now;
  
  tokenRefreshPromiseRef.current = (async () => {
    try {
      // Prioridad 1: Renovar con refresh_token
      if (refreshToken || localStorage.getItem('refresh_token')) {
        console.log('🔄 Intentando renovar con refresh_token...');
        return await refreshAccessToken();
      }
      
      // Prioridad 2: Obtener token fresco desde /auth/session
      console.log('🔄 Obteniendo token fresco desde /auth/session...');
      const response = await fetch(`${getBackendUrl()}/auth/session`, {
        credentials: 'include',
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.access_token) {
          console.log('✅ Token fresco obtenido desde /auth/session');
          setAccessToken(data.access_token);
          localStorage.setItem('access_token', data.access_token);
          return data.access_token;
        }
      }
      
      console.log('⚠️ No se pudo obtener token fresco');
      return null;
    } finally {
      tokenRefreshPromiseRef.current = null;
    }
  })();
  
  return await tokenRefreshPromiseRef.current;
};
```

---

## 🚨 **Puntos Críticos Finales**

1. **NUNCA usar `token_expiry`** - el JWT ya contiene `exp`
2. **Siempre setear el token ANTES de verificar expiración**
3. **Mantener lógica simple y clara** en `getAuthToken()`
4. **Priorizar `refresh_token` sobre `/auth/session`**
5. **Usar `useRef` para todas las variables de control**

---

## 📊 **Estado Final Esperado**

Con estas 3 correcciones finales, el `authcontext.js` estará **100% alineado** con el backend y funcionará perfectamente para:

- ✅ **Sesión de 30 días** con `refresh_token`
- ✅ **Renovación automática** cada 24h
- ✅ **Silent login** correcto
- ✅ **Reintento automático** en errores 401
- ✅ **Persistencia correcta** de tokens
- ✅ **Logout completo** y limpio

**¡Solo faltan estos 3 ajustes menores para completar la implementación!** 🎉
