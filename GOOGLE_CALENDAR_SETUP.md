# Configuración de Google Calendar API

## 📋 Pasos para configurar Google Calendar API

### 1. Crear proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Anota el **Project ID** para referencia futura

### 2. Habilitar Google Calendar API

1. En el menú lateral, ve a **APIs & Services** > **Library**
2. Busca "Google Calendar API"
3. Haz clic en **Google Calendar API**
4. Haz clic en **Enable**

### 3. Crear credenciales OAuth 2.0

1. Ve a **APIs & Services** > **Credentials**
2. Haz clic en **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Si es la primera vez, configura la pantalla de consentimiento:
   - Selecciona **External** (a menos que tengas Google Workspace)
   - Completa la información requerida
   - Agrega tu email en "Test users"
4. Para el tipo de aplicación, selecciona **Desktop application**
5. Dale un nombre a tu aplicación (ej: "Synco API")
6. Haz clic en **Create**
7. **Descarga el archivo JSON** - este será tu `credentials.json`

### 4. Configurar el archivo de credenciales

1. Copia el archivo descargado a la raíz de tu proyecto
2. Renómbralo a `credentials.json`
3. Asegúrate de que esté en `.gitignore` (ya está incluido)

### 5. Configurar variables de entorno

1. Copia `env.example` a `.env`:
```bash
cp env.example .env
```

2. Edita `.env` con tus configuraciones:
```env
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar.readonly
DEFAULT_CALENDAR_ID=primary
```

### 6. Primera autenticación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la API:
```bash
python main.py
```

3. La primera vez que accedas a un endpoint de Google Calendar, se abrirá tu navegador para autenticarte
4. Autoriza la aplicación
5. Se creará automáticamente el archivo `token.json` con tus credenciales

## 🔧 Endpoints disponibles

### Obtener calendarios
```bash
GET /calendarios
```

### Obtener eventos (calendario principal)
```bash
GET /eventos
```

### Obtener eventos con parámetros
```bash
GET /eventos?calendar_id=primary&max_results=20&days_ahead=7
```

### Obtener eventos de calendario específico
```bash
GET /eventos/tu-calendar-id@group.calendar.google.com
```

## 🧪 Pruebas

### 1. Verificar configuración
```bash
curl http://localhost:8000/calendarios
```

### 2. Obtener eventos
```bash
curl http://localhost:8000/eventos
```

### 3. Obtener eventos con parámetros
```bash
curl "http://localhost:8000/eventos?max_results=5&days_ahead=7"
```

## 🔒 Seguridad

- **NUNCA** subas `credentials.json` o `token.json` a Git
- Estos archivos ya están en `.gitignore`
- Para producción, usa variables de entorno de Vercel

## 🚀 Deploy en Vercel

1. En Vercel Dashboard, ve a tu proyecto
2. Ve a **Settings** > **Environment Variables**
3. Agrega las variables de entorno necesarias:

   - `GOOGLE_CREDENTIALS_JSON` → Contenido de `credentials.json` (JSON completo)
   - `GOOGLE_TOKEN_JSON` → Contenido JSON del token (ver paso de conversión)
   - `GOOGLE_SCOPES` → `https://www.googleapis.com/auth/calendar.readonly`
   - `DEFAULT_CALENDAR_ID` → `primary` (opcional)

   Alternativa si prefieres el token como binario:
   - `GOOGLE_TOKEN_BASE64` → `token.json` binario codificado en base64

4. La app escribe estos valores a `/tmp/credentials.json` y `/tmp/token.json` automáticamente al iniciar.
5. No subas `credentials.json` ni `token.json` al repositorio.

### Conversión del token a JSON (recomendada)

Ejecuta en local para convertir el pickle binario a JSON compatible:

```bash
python convert_token_pickle_to_json.py > token-google.json
```

Luego copia el contenido de `token-google.json` a `GOOGLE_TOKEN_JSON`.

Alternativa base64 para el binario:

```bash
python - << 'PY'
import base64
print(base64.b64encode(open('token.json','rb').read()).decode())
PY
```

Copia el resultado a `GOOGLE_TOKEN_BASE64`.

## ❗ Solución de problemas

### Error: "FileNotFoundError: credentials.json"
- Asegúrate de tener el archivo `credentials.json` en la raíz del proyecto
- Verifica que el archivo no esté corrupto

### Error: "Invalid credentials"
- Elimina `token.json` y vuelve a autenticarte
- Verifica que las credenciales OAuth estén correctas

### Error: "Access denied"
- Verifica que la API de Google Calendar esté habilitada
- Asegúrate de que el usuario esté en "Test users" si usas OAuth externo

### Error: "Calendar not found"
- Usa `GET /calendarios` para ver los IDs disponibles
- Verifica que tengas permisos de lectura en el calendario
