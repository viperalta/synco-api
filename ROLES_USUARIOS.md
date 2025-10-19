# Sistema de Roles y Usuarios - Documentación Frontend

## Resumen

Este documento describe el sistema de roles y usuarios implementado en el backend, incluyendo los nuevos endpoints de administración y la estructura de datos para el manejo de usuarios con roles y nicknames.

## Estructura de Usuario Actualizada

### Campos del Usuario

```typescript
interface User {
  id: string;                    // ID único del usuario
  google_id: string;            // ID de Google
  email: string;                 // Email del usuario
  name: string;                  // Nombre completo de Google
  picture?: string;              // URL de la foto de perfil
  nickname: string;              // Nombre que se mostrará en la interfaz (NUEVO)
  roles: string[];               // Lista de roles del usuario (NUEVO)
  is_active: boolean;            // Estado del usuario
  created_at: string;            // Fecha de creación
  updated_at: string;            // Fecha de última actualización
}
```

### Campos Nuevos

- **`nickname`**: String que representa el nombre que se mostrará en diferentes lugares de la interfaz. Inicia como string vacío `""` para usuarios nuevos.
- **`roles`**: Array de strings que contiene los roles asignados al usuario. Inicia como array vacío `[]` para usuarios nuevos.

## Roles Disponibles

### Lista de Roles

1. **`admin`** - Administrador completo
2. **`moderator`** - Moderador con permisos limitados  
3. **`player`** - Jugador básico
4. **`viewer`** - Solo lectura

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

#### Moderator
- `users.view` - Ver usuarios
- `events.create` - Crear eventos
- `events.edit` - Editar eventos
- `events.view` - Ver eventos
- `attendance.manage` - Gestionar asistencia

#### Player
- `events.view` - Ver eventos
- `attendance.self` - Gestionar su propia asistencia

#### Viewer
- `events.view` - Ver eventos

## Endpoints de Administración

### Autenticación Requerida

Todos los endpoints de administración requieren:
- Token de acceso válido en el header `Authorization: Bearer <token>`
- Rol de `admin` para acceder

### 1. Listar Usuarios

**GET** `/admin/users`

Obtiene la lista de todos los usuarios con paginación.

#### Parámetros de Query
- `skip` (opcional): Número de usuarios a saltar (default: 0)
- `limit` (opcional): Número máximo de usuarios a retornar (default: 100, max: 1000)

#### Respuesta
```typescript
interface UserListResponse {
  users: User[];
  total: number;
  skip: number;
  limit: number;
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch('/admin/users?skip=0&limit=50', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const data = await response.json();
```

### 2. Obtener Usuario Específico

**GET** `/admin/users/{user_id}`

Obtiene información detallada de un usuario específico.

#### Parámetros de Ruta
- `user_id`: ID del usuario a consultar

#### Respuesta
```typescript
interface UserResponse {
  // Objeto User completo
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch(`/admin/users/${userId}`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const user = await response.json();
```

### 3. Actualizar Usuario

**PUT** `/admin/users/{user_id}`

Actualiza información de un usuario (nickname, roles, estado activo).

#### Parámetros de Ruta
- `user_id`: ID del usuario a actualizar

#### Body
```typescript
interface UserUpdateRequest {
  nickname?: string;      // Nuevo nickname (opcional)
  roles?: string[];       // Nueva lista de roles (opcional)
  is_active?: boolean;    // Nuevo estado activo (opcional)
}
```

#### Respuesta
```typescript
interface UserResponse {
  // Objeto User actualizado
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch(`/admin/users/${userId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    nickname: 'Nuevo Nickname',
    roles: ['player', 'moderator'],
    is_active: true
  })
});
const updatedUser = await response.json();
```

### 4. Actualizar Solo Roles

**PUT** `/admin/users/{user_id}/roles`

Actualiza únicamente los roles de un usuario.

#### Parámetros de Ruta
- `user_id`: ID del usuario

#### Body
```typescript
interface UserRoleUpdateRequest {
  roles: string[];  // Lista de roles a asignar
}
```

#### Respuesta
```typescript
interface UserResponse {
  // Objeto User con roles actualizados
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch(`/admin/users/${userId}/roles`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    roles: ['admin']
  })
});
const updatedUser = await response.json();
```

### 5. Actualizar Solo Nickname

**PUT** `/admin/users/{user_id}/nickname`

Actualiza únicamente el nickname de un usuario.

#### Parámetros de Ruta
- `user_id`: ID del usuario

#### Body
```typescript
interface UserNicknameUpdateRequest {
  nickname: string;  // Nuevo nickname
}
```

#### Respuesta
```typescript
interface UserResponse {
  // Objeto User con nickname actualizado
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch(`/admin/users/${userId}/nickname`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    nickname: 'Nuevo Nickname'
  })
});
const updatedUser = await response.json();
```

### 6. Obtener Roles Disponibles

**GET** `/admin/roles`

Obtiene la lista de roles disponibles y sus permisos.

#### Respuesta
```typescript
interface RolesResponse {
  roles: string[];
  permissions: {
    [role: string]: string[];
  };
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch('/admin/roles', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const rolesData = await response.json();
```

### 7. Obtener Permisos de Usuario

**GET** `/admin/permissions/{user_id}`

Obtiene los permisos específicos de un usuario basados en sus roles.

#### Parámetros de Ruta
- `user_id`: ID del usuario

#### Respuesta
```typescript
interface UserPermissionsResponse {
  user_id: string;
  user_email: string;
  user_nickname: string;
  roles: string[];
  permissions: string[];
  is_active: boolean;
}
```

#### Ejemplo de Uso
```javascript
const response = await fetch(`/admin/permissions/${userId}`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const permissions = await response.json();
```

## Manejo de Usuarios Existentes

### Compatibilidad con Producción

Los usuarios existentes en producción que no tienen los campos `nickname` y `roles` serán manejados de la siguiente manera:

1. **Al consultar**: Los campos aparecerán como `null` o `undefined` en la respuesta
2. **Al actualizar**: Se pueden agregar estos campos usando los endpoints de administración
3. **Nuevos usuarios**: Automáticamente tendrán `nickname: ""` y `roles: []`

### Recomendaciones para el Frontend

1. **Verificación de campos**: Siempre verificar si `nickname` y `roles` existen antes de usarlos
2. **Valores por defecto**: Usar valores por defecto cuando los campos no existan:
   ```typescript
   const displayName = user.nickname || user.name || 'Usuario';
   const userRoles = user.roles || [];
   ```
3. **Actualización gradual**: Permitir que los administradores actualicen usuarios existentes para agregar nickname y roles

## Códigos de Error

### Errores Comunes

- **401 Unauthorized**: Token inválido o expirado
- **403 Forbidden**: Usuario no tiene permisos de administrador
- **404 Not Found**: Usuario no encontrado
- **400 Bad Request**: Datos inválidos (ej: roles no válidos)

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
      // Sin permisos de administrador
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

## Consideraciones de Seguridad

1. **Autenticación obligatoria**: Todos los endpoints requieren token válido
2. **Autorización por roles**: Solo usuarios con rol `admin` pueden acceder
3. **Validación de datos**: Los roles se validan contra la lista de roles disponibles
4. **Logs de auditoría**: Todas las operaciones quedan registradas con timestamps

## Implementación Sugerida en Frontend

### 1. Componente de Lista de Usuarios

```typescript
interface UserListProps {
  accessToken: string;
}

const UserList: React.FC<UserListProps> = ({ accessToken }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchUsers();
  }, []);
  
  const fetchUsers = async () => {
    try {
      const response = await fetch('/admin/users', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Renderizar lista de usuarios...
};
```

### 2. Componente de Edición de Usuario

```typescript
interface UserEditProps {
  userId: string;
  accessToken: string;
  onUserUpdated: (user: User) => void;
}

const UserEdit: React.FC<UserEditProps> = ({ userId, accessToken, onUserUpdated }) => {
  const [user, setUser] = useState<User | null>(null);
  const [nickname, setNickname] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  
  const updateUser = async () => {
    try {
      const response = await fetch(`/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nickname,
          roles: selectedRoles
        })
      });
      
      if (response.ok) {
        const updatedUser = await response.json();
        onUserUpdated(updatedUser);
      }
    } catch (error) {
      console.error('Error updating user:', error);
    }
  };
  
  // Renderizar formulario de edición...
};
```

## Conclusión

Este sistema de roles y usuarios proporciona una base sólida para la gestión de permisos en la aplicación. Los endpoints están diseñados para ser seguros, escalables y fáciles de usar desde el frontend. La compatibilidad con usuarios existentes asegura que la migración sea suave y sin interrupciones.
