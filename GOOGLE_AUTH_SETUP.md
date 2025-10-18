# Configuración de Autenticación Google OAuth

## 📋 Pasos para implementar autenticación de Google

### 1. Configurar Google Cloud Console

1. **Crear credenciales OAuth 2.0 para aplicación web:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Selecciona tu proyecto existente
   - Ve a **APIs & Services** > **Credentials**
   - Haz clic en **+ CREATE CREDENTIALS** > **OAuth client ID**
   - Selecciona **Web application** (no Desktop)
   - Configura los URIs autorizados:
     - **Authorized JavaScript origins**: 
       - `https://pasesfalsos.cl`
       - `http://localhost:3000` (para desarrollo)
     - **Authorized redirect URIs**: 
       - `https://pasesfalsos.cl/auth/callback`
       - `http://localhost:3000/auth/callback` (para desarrollo)
   - Descarga el archivo JSON de credenciales

2. **Anota los valores importantes:**
   - `client_id` (lo necesitarás para el frontend)
   - `client_secret` (lo necesitarás para el backend)

### 2. Configurar variables de entorno en Vercel

En Vercel Dashboard → Project → Settings → Environment Variables, agrega:

```
JWT_SECRET_KEY=tu-clave-secreta-super-segura-para-jwt
GOOGLE_CLIENT_ID=tu-google-client-id
GOOGLE_CLIENT_SECRET=tu-google-client-secret
```

### 3. Endpoints de la API

#### POST `/auth/google`
Autenticar usuario con Google OAuth

**Request:**
```json
{
  "access_token": "token_de_google"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
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

#### GET `/auth/me`
Obtener información del usuario actual (requiere token JWT)

**Headers:**
```
Authorization: Bearer <jwt_token>
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

#### POST `/auth/logout`
Cerrar sesión (el cliente debe eliminar el token)

**Response:**
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

### 4. Implementación en el Frontend React

#### Instalar dependencias:
```bash
npm install @google-cloud/oauth2 google-auth-library
# o
yarn add @google-cloud/oauth2 google-auth-library
```

#### Configurar Google OAuth en React:

1. **Crear archivo de configuración** (`src/config/google.js`):
```javascript
export const GOOGLE_CONFIG = {
  clientId: process.env.REACT_APP_GOOGLE_CLIENT_ID,
  redirectUri: window.location.origin + '/auth/callback',
  scope: 'openid email profile'
};
```

2. **Crear contexto de autenticación** (`src/contexts/AuthContext.js`):
```javascript
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Verificar si hay token guardado
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUserProfile(token);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async (token) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('access_token');
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (googleAccessToken) => {
    try {
      const response = await fetch('/api/auth/google', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          access_token: googleAccessToken
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        setUser(data.user);
        return true;
      } else {
        throw new Error('Authentication failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const value = {
    user,
    loginWithGoogle,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

3. **Crear componente de login** (`src/components/GoogleLogin.js`):
```javascript
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const GoogleLogin = () => {
  const { loginWithGoogle } = useAuth();

  const handleGoogleLogin = async () => {
    try {
      // Usar Google Identity Services
      const client = google.accounts.oauth2.initCodeClient({
        client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
        scope: 'openid email profile',
        ux_mode: 'popup',
        callback: async (response) => {
          // Intercambiar código por token
          const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID,
              client_secret: process.env.REACT_APP_GOOGLE_CLIENT_SECRET,
              code: response.code,
              grant_type: 'authorization_code',
              redirect_uri: window.location.origin + '/auth/callback'
            })
          });

          const tokenData = await tokenResponse.json();
          
          if (tokenData.access_token) {
            await loginWithGoogle(tokenData.access_token);
          }
        }
      });

      client.requestCode();
    } catch (error) {
      console.error('Google login error:', error);
    }
  };

  return (
    <button onClick={handleGoogleLogin}>
      Iniciar sesión con Google
    </button>
  );
};

export default GoogleLogin;
```

4. **Crear componente de rutas protegidas** (`src/components/ProtectedRoute.js`):
```javascript
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Cargando...</div>;
  }

  return user ? children : <Navigate to="/login" />;
};

export default ProtectedRoute;
```

5. **Configurar variables de entorno en React** (`.env`):
```
REACT_APP_GOOGLE_CLIENT_ID=tu-google-client-id
REACT_APP_API_URL=https://tu-api.vercel.app
```

6. **Usar en tu App.js**:
```javascript
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import GoogleLogin from './components/GoogleLogin';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './components/Dashboard';

function AppContent() {
  const { user, logout } = useAuth();

  return (
    <Router>
      <div>
        {user ? (
          <div>
            <p>Hola, {user.name}!</p>
            <button onClick={logout}>Cerrar sesión</button>
            <Routes>
              <Route path="/" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
            </Routes>
          </div>
        ) : (
          <GoogleLogin />
        )}
      </div>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
```

### 5. Pruebas

#### Probar autenticación con curl:
```bash
# 1. Obtener token de Google (usar Google OAuth Playground o frontend)
# 2. Autenticar con tu API
curl -X POST "https://tu-api.vercel.app/auth/google" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "tu_google_access_token"}'

# 3. Usar el JWT token para acceder a rutas protegidas
curl -H "Authorization: Bearer tu_jwt_token" \
  "https://tu-api.vercel.app/auth/me"
```

### 6. Seguridad

- ✅ CORS configurado para dominios específicos
- ✅ JWT tokens con expiración
- ✅ Validación de tokens en cada request
- ✅ Almacenamiento seguro de credenciales en Vercel
- ✅ Verificación de tokens de Google

### 7. Solución de problemas

#### Error: "Invalid client"
- Verifica que el `GOOGLE_CLIENT_ID` esté correcto
- Asegúrate de que el dominio esté en "Authorized JavaScript origins"

#### Error: "CORS policy"
- Verifica que el dominio del frontend esté en la lista de `allow_origins`

#### Error: "JWT token invalid"
- Verifica que `JWT_SECRET_KEY` esté configurado
- Asegúrate de que el token no haya expirado

#### Error: "User not found"
- Verifica que la conexión a MongoDB esté funcionando
- Revisa los logs de la API en Vercel
