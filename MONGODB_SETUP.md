# Configuración de MongoDB Atlas para Synco API

Esta guía te ayudará a configurar MongoDB Atlas para tu API de Synco.

## Pasos para Configurar MongoDB Atlas

### 1. Crear Cluster en MongoDB Atlas

1. Ve a [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Crea una cuenta o inicia sesión
3. Crea un nuevo cluster (puedes usar el tier gratuito)
4. Espera a que el cluster esté listo

### 2. Configurar Acceso a la Base de Datos

1. Ve a "Database Access" en el menú lateral
2. Haz clic en "Add New Database User"
3. Crea un usuario con:
   - Username: `synco_user` (o el que prefieras)
   - Password: Genera una contraseña segura
   - Database User Privileges: "Read and write to any database"

### 3. Configurar Acceso de Red

1. Ve a "Network Access" en el menú lateral
2. Haz clic en "Add IP Address"
3. Para desarrollo local: Agrega tu IP actual
4. Para producción: Agrega `0.0.0.0/0` (permite acceso desde cualquier IP)

### 4. Obtener String de Conexión

1. Ve a "Clusters" en el menú lateral
2. Haz clic en "Connect" en tu cluster
3. Selecciona "Connect your application"
4. Copia el string de conexión
5. Reemplaza `<password>` con la contraseña del usuario que creaste

### 5. Configurar Variables de Entorno

#### Para Desarrollo Local:
Crea un archivo `.env` en la raíz del proyecto:

```env
# MongoDB Atlas
MONGODB_URL=mongodb+srv://synco_user:tu_password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=synco_db
```

#### Para Vercel (Producción):
1. Ve a tu proyecto en Vercel
2. Settings > Environment Variables
3. Agrega:
   - `MONGODB_URL` = tu string de conexión completo
   - `MONGODB_DATABASE` = `synco_db`

### 6. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 7. Probar la Conexión

Ejecuta la API localmente:

```bash
python main.py
```

Deberías ver en la consola:
```
✅ MongoDB conectado exitosamente
```

## Estructura de la Base de Datos

La API creará automáticamente las siguientes colecciones:

### `items`
Almacena los items/productos de la API
```json
{
  "_id": "ObjectId",
  "name": "string",
  "description": "string",
  "price": "number",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `calendar_events`
Almacena eventos de Google Calendar sincronizados
```json
{
  "_id": "ObjectId",
  "google_event_id": "string",
  "summary": "string",
  "description": "string",
  "start_date": "string",
  "end_date": "string",
  "start_datetime": "string",
  "end_datetime": "string",
  "location": "string",
  "status": "string",
  "html_link": "string",
  "is_all_day": "boolean",
  "calendar_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `calendars`
Almacena información de calendarios de Google Calendar
```json
{
  "_id": "ObjectId",
  "google_calendar_id": "string",
  "summary": "string",
  "description": "string",
  "primary": "boolean",
  "access_role": "string",
  "background_color": "string",
  "foreground_color": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Endpoints Actualizados

Todos los endpoints de `/items` ahora usan MongoDB:

- `GET /items` - Obtener items con paginación
- `GET /items/{item_id}` - Obtener item específico
- `POST /items` - Crear nuevo item
- `PUT /items/{item_id}` - Actualizar item
- `DELETE /items/{item_id}` - Eliminar item

### Parámetros de Paginación

```bash
# Obtener items con paginación
GET /items?skip=0&limit=10
```

## Solución de Problemas

### Error de Conexión
- Verifica que la URL de MongoDB sea correcta
- Asegúrate de que tu IP esté en la lista de acceso de red
- Verifica que el usuario y contraseña sean correctos

### Error de Autenticación
- Verifica que el usuario tenga permisos de lectura y escritura
- Asegúrate de que la contraseña no tenga caracteres especiales que necesiten encoding

### Error de Red
- Para producción, asegúrate de agregar `0.0.0.0/0` en Network Access
- Verifica que el cluster esté activo y funcionando

## Monitoreo

Puedes monitorear tu base de datos desde:
- MongoDB Atlas Dashboard
- Logs de la aplicación (muestran estado de conexión)
- Endpoint `/debug/env` para verificar variables de entorno
