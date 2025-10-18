# Implementación Frontend - Silent Authentication con PKCE

## 🎯 **Objetivo**
Implementar un sistema de autenticación que permita a usuarios registrados loguearse automáticamente sin mostrar la UI de Google, usando PKCE y silent authentication.

## 🔧 **Flujo de Autenticación**

### **1. Al cargar la aplicación (App.jsx)**
```javascript
useEffect(() => {
  checkExistingSession();
}, []);

const checkExistingSession = async () => {
  try {
    // 1. Verificar si hay sesión activa
    const response = await fetch('/api/auth/session', {
      credentials: 'include' // Importante para cookies
    });
    
    if (response.ok) {
      const userData = await response.json();
      setUser(userData.user);
      setLoading(false);
      return;
    }
    
    // 2. Si no hay sesión, intentar silent login
    const savedEmail = localStorage.getItem('user_email');
    if (savedEmail) {
      await attemptSilentLogin(savedEmail);
    } else {
      setLoading(false);
    }
  } catch (error) {
    console.error('Error checking session:', error);
    setLoading(false);
  }
};
```

### **2. Silent Login (sin UI de Google)**
```javascript
const attemptSilentLogin = async (email) => {
  try {
    // Abrir silent login en iframe oculto
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.src = `/api/auth/google/silent?email=${encodeURIComponent(email)}`;
    document.body.appendChild(iframe);
    
    // Escuchar respuesta del iframe
    const handleMessage = (event) => {
      if (event.data.type === 'LOGIN_OK') {
        // Silent login exitoso, verificar sesión
        checkExistingSession();
        document.body.removeChild(iframe);
        window.removeEventListener('message', handleMessage);
      } else if (event.data.type === 'LOGIN_FAILED') {
        // Silent login falló, mostrar UI normal
        setLoading(false);
        document.body.removeChild(iframe);
        window.removeEventListener('message', handleMessage);
      }
    };
    
    window.addEventListener('message', handleMessage);
    
    // Timeout después de 10 segundos
    setTimeout(() => {
      if (document.body.contains(iframe)) {
        document.body.removeChild(iframe);
        window.removeEventListener('message', handleMessage);
        setLoading(false);
      }
    }, 10000);
    
  } catch (error) {
    console.error('Error in silent login:', error);
    setLoading(false);
  }
};
```

### **3. Login Normal (con UI de Google)**
```javascript
const handleGoogleLogin = () => {
  // Redirigir al login normal (sin prompt=select_account)
  window.location.href = '/api/auth/google/login';
};

const handleChangeAccount = () => {
  // Login con selector de cuenta
  window.location.href = '/api/auth/google/login?prompt=select_account';
};
```

### **4. Logout**
```javascript
const handleLogout = async () => {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
    
    // Limpiar estado local
    setUser(null);
    localStorage.removeItem('user_email');
    
    // Recargar para limpiar cualquier estado
    window.location.reload();
  } catch (error) {
    console.error('Error logging out:', error);
  }
};
```

## 🎨 **Componentes React**

### **AuthProvider.jsx**
```javascript
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkExistingSession = async () => {
    try {
      const response = await fetch('/api/auth/session', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData.user);
        // Guardar email para silent login futuro
        localStorage.setItem('user_email', userData.user.email);
      }
    } catch (error) {
      console.error('Error checking session:', error);
    } finally {
      setLoading(false);
    }
  };

  const attemptSilentLogin = async (email) => {
    // Implementación del silent login (ver código arriba)
  };

  useEffect(() => {
    checkExistingSession();
  }, []);

  const value = {
    user,
    loading,
    handleGoogleLogin,
    handleChangeAccount,
    handleLogout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

### **LoginButton.jsx**
```javascript
import React from 'react';
import { useAuth } from '../contexts/AuthProvider';

const LoginButton = () => {
  const { handleGoogleLogin, handleChangeAccount, loading } = useAuth();

  if (loading) {
    return <div>Cargando...</div>;
  }

  return (
    <div>
      <button onClick={handleGoogleLogin}>
        Iniciar sesión con Google
      </button>
      <button onClick={handleChangeAccount}>
        Cambiar cuenta
      </button>
    </div>
  );
};

export default LoginButton;
```

### **App.jsx**
```javascript
import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthProvider';
import LoginButton from './components/LoginButton';
import Dashboard from './components/Dashboard';

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Verificando sesión...</div>;
  }

  return (
    <div>
      {user ? (
        <Dashboard user={user} />
      ) : (
        <LoginButton />
      )}
    </div>
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

## 🔧 **Configuración de Google OAuth**

### **Variables de entorno (.env)**
```bash
REACT_APP_GOOGLE_CLIENT_ID=tu_google_client_id
REACT_APP_API_URL=https://api.pasesfalsos.cl
```

### **Configuración de Google Cloud Console**
```
Authorized JavaScript origins:
- https://pasesfalsos.cl
- http://localhost:3003

Authorized redirect URIs:
- https://pasesfalsos.cl/api/auth/google/callback
- http://localhost:3003/api/auth/google/callback
```

## 🎯 **Flujo de Usuario Resultante**

### **Primera vez:**
1. Usuario visita la página
2. No hay sesión → Se muestra botón "Iniciar sesión"
3. Usuario hace clic → Redirige a Google (login normal)
4. Usuario autoriza → Vuelve con sesión activa

### **Visitas posteriores:**
1. Usuario visita la página
2. Hay cookie válida → Usuario logueado automáticamente ✅
3. **O** No hay cookie pero hay email guardado → Silent login
4. Silent login exitoso → Usuario logueado automáticamente ✅
5. Silent login falla → Se muestra botón "Iniciar sesión"

### **Cambiar cuenta:**
1. Usuario hace clic en "Cambiar cuenta"
2. Redirige a Google con `prompt=select_account`
3. Usuario selecciona otra cuenta → Nueva sesión

## 🔒 **Consideraciones de Seguridad**

1. **Cookies httpOnly**: El backend maneja las cookies de sesión
2. **PKCE**: Para seguridad en el flujo OAuth
3. **login_hint**: Mejora UX y seguridad
4. **postMessage**: Comunicación segura entre iframe y parent
5. **Credentials include**: Para enviar cookies en requests

## 🧪 **Testing**

### **Probar flujo completo:**
1. **Primera visita**: Debería mostrar botón de login
2. **Después del login**: Debería loguearse automáticamente
3. **Logout**: Debería limpiar sesión
4. **Silent login**: Debería funcionar sin UI de Google

### **Debug:**
```javascript
// En la consola del navegador
console.log('User:', user);
console.log('Loading:', loading);
console.log('Cookies:', document.cookie);
```

## 📋 **Checklist de Implementación**

- [ ] Configurar variables de entorno
- [ ] Implementar AuthProvider
- [ ] Implementar silent login con iframe
- [ ] Implementar login normal
- [ ] Implementar logout
- [ ] Configurar Google Cloud Console
- [ ] Probar flujo completo
- [ ] Probar silent login
- [ ] Probar cambio de cuenta
