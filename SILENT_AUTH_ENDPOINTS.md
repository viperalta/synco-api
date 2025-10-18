# Endpoints de Silent Authentication con PKCE

## 🎯 **Nuevos Endpoints Implementados**

### **1. GET `/auth/session` - Verificar sesión activa**
**Descripción:** Verifica si hay una sesión activa usando cookies httpOnly.

**Headers:**
```
Cookie: session_token=tu_session_token
```

**Response (200):**
```json
{
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

**Response (401):**
```json
{
  "detail": "No hay sesión activa"
}
```

### **2. GET `/auth/google/silent?email=usuario@dominio.com` - Silent Login**
**Descripción:** Inicia silent login con Google (sin UI) usando el email del usuario.

**Query Parameters:**
- `email` (required): Email del usuario para silent login

**Response:** Redirección a Google OAuth con `prompt=none`

**Uso en frontend:**
```javascript
// Abrir en iframe oculto
const iframe = document.createElement('iframe');
iframe.style.display = 'none';
iframe.src = `/api/auth/google/silent?email=${encodeURIComponent(email)}`;
document.body.appendChild(iframe);
```

### **3. GET `/auth/google/login?prompt=consent` - Login Normal**
**Descripción:** Inicia login normal con Google (con UI).

**Query Parameters:**
- `prompt` (optional): Tipo de prompt
  - `consent` (default): Mostrar pantalla de consentimiento
  - `select_account`: Mostrar selector de cuentas
  - `none`: Sin UI (para silent login)

**Response:** Redirección a Google OAuth

**Uso en frontend:**
```javascript
// Login normal
window.location.href = '/api/auth/google/login';

// Cambiar cuenta
window.location.href = '/api/auth/google/login?prompt=select_account';
```

### **4. GET `/auth/google/callback` - Callback de OAuth**
**Descripción:** Maneja el callback de Google OAuth con PKCE.

**Query Parameters:**
- `code`: Código de autorización de Google
- `state`: State parameter con datos PKCE
- `error` (optional): Error de Google

**Response:** Página HTML que notifica al frontend via postMessage

**HTML de éxito:**
```html
<script>
  (window.opener || window.parent).postMessage({type: 'LOGIN_OK'}, '*');
  window.close();
</script>
```

**HTML de error:**
```html
<script>
  (window.opener || window.parent).postMessage({type: 'LOGIN_FAILED', error: 'error_code'}, '*');
  window.close();
</script>
```

### **5. POST `/auth/logout` - Cerrar sesión**
**Descripción:** Cierra la sesión del usuario (limpia cookies y revoca tokens).

**Headers:**
```
Cookie: session_token=tu_session_token
```

**Response (200):**
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

## 🔧 **Configuración de Variables de Entorno**

Agrega estas variables a tu archivo `.env`:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:3003

# Para producción:
# GOOGLE_REDIRECT_URI=https://api.pasesfalsos.cl/auth/google/callback
# FRONTEND_URL=https://pasesfalsos.cl
```

## 🎯 **Flujo de Autenticación**

### **1. Primera visita:**
1. Frontend llama `GET /auth/session`
2. Si 401 → No hay sesión
3. Frontend muestra botón "Iniciar sesión"
4. Usuario hace clic → `GET /auth/google/login`
5. Google OAuth → `GET /auth/google/callback`
6. Callback establece cookie y notifica frontend
7. Frontend verifica sesión → Usuario logueado

### **2. Visitas posteriores:**
1. Frontend llama `GET /auth/session`
2. Si 200 → Usuario logueado automáticamente ✅
3. Si 401 → Intentar silent login
4. Silent login exitoso → Usuario logueado ✅
5. Silent login falla → Mostrar botón de login

### **3. Silent Login:**
1. Frontend abre iframe con `GET /auth/google/silent?email=...`
2. Google OAuth con `prompt=none` y `login_hint=email`
3. Si usuario tiene sesión activa en Google → Callback exitoso
4. Si no → Google responde con error
5. Frontend recibe notificación via postMessage

## 🔒 **Características de Seguridad**

### **1. PKCE (Proof Key for Code Exchange)**
- ✅ **code_verifier**: Generado aleatoriamente
- ✅ **code_challenge**: SHA256 hash del code_verifier
- ✅ **code_challenge_method**: S256
- ✅ **Protección contra ataques**: CSRF, replay, etc.

### **2. Cookies httpOnly**
- ✅ **httpOnly**: No accesible desde JavaScript
- ✅ **Secure**: Solo HTTPS en producción
- ✅ **SameSite**: Lax para subdominios
- ✅ **Domain**: .pasesfalsos.cl para subdominios

### **3. State y Nonce**
- ✅ **State**: Protección CSRF
- ✅ **Nonce**: Protección replay
- ✅ **Validación**: En el callback

## 🧪 **Testing**

### **1. Probar sesión activa:**
```bash
curl -H "Cookie: session_token=tu_session_token" \
  http://localhost:8000/auth/session
```

### **2. Probar silent login:**
```bash
# Abrir en navegador
http://localhost:8000/auth/google/silent?email=usuario@dominio.com
```

### **3. Probar login normal:**
```bash
# Abrir en navegador
http://localhost:8000/auth/google/login
```

### **4. Probar logout:**
```bash
curl -X POST -H "Cookie: session_token=tu_session_token" \
  http://localhost:8000/auth/logout
```

## 📋 **Configuración de Google Cloud Console**

### **Authorized JavaScript origins:**
```
http://localhost:3003
https://pasesfalsos.cl
```

### **Authorized redirect URIs:**
```
http://localhost:8000/auth/google/callback
https://api.pasesfalsos.cl/auth/google/callback
```

## 🚀 **Deploy a Producción**

### **1. Variables de entorno en Vercel:**
```
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
GOOGLE_REDIRECT_URI=https://api.pasesfalsos.cl/auth/google/callback
FRONTEND_URL=https://pasesfalsos.cl
```

### **2. Configurar subdominios:**
- **API**: `api.pasesfalsos.cl`
- **Frontend**: `pasesfalsos.cl`
- **Cookies**: Domain `.pasesfalsos.cl`

### **3. HTTPS obligatorio:**
- Las cookies `Secure` requieren HTTPS
- Google OAuth requiere HTTPS en producción

## ✅ **Beneficios del Nuevo Sistema**

1. **🔐 Seguridad mejorada**: PKCE + cookies httpOnly
2. **⚡ UX mejorada**: Silent login para usuarios registrados
3. **🌐 Soporte subdominios**: Cookies compartidas entre subdominios
4. **📱 Compatible SPA**: Diseñado para Single Page Applications
5. **🔄 Renovación automática**: Sesiones de 30 días
6. **🛡️ Protección CSRF**: State y nonce parameters
7. **📊 Escalable**: Funciona con múltiples usuarios simultáneos
