# Synco API - FastAPI

## Descripción
API REST desarrollada con FastAPI para deployar en Vercel.

## Estructura del proyecto
```
synco-api/
├── main.py              # Archivo principal de la API
├── requirements.txt     # Dependencias de Python
├── vercel.json         # Configuración para Vercel
└── README.md           # Este archivo
```

## Instalación y ejecución local

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la API localmente
```bash
python main.py
```

O usando uvicorn directamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Acceder a la documentación
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints disponibles

### Endpoints básicos
- `GET /` - Endpoint raíz
- `GET /health` - Verificación de salud de la API

### CRUD de Items
- `GET /items` - Obtener todos los items
- `GET /items/{item_id}` - Obtener un item específico
- `POST /items` - Crear un nuevo item
- `PUT /items/{item_id}` - Actualizar un item
- `DELETE /items/{item_id}` - Eliminar un item

### Google Calendar API
- `GET /calendarios` - Obtener lista de calendarios disponibles
- `GET /eventos` - Obtener eventos del calendario principal
- `GET /eventos/{calendar_id}` - Obtener eventos de un calendario específico

**Parámetros para endpoints de eventos:**
- `calendar_id` - ID del calendario (por defecto 'primary')
- `max_results` - Número máximo de eventos (1-100, por defecto 10)
- `days_ahead` - Días hacia adelante para buscar (1-365, por defecto 30)

## Deploy en Vercel

### 1. Instalar Vercel CLI
```bash
npm i -g vercel
```

### 2. Login en Vercel
```bash
vercel login
```

### 3. Deploy
```bash
vercel
```

### 4. Deploy de producción
```bash
vercel --prod
```

### 5. Variables de entorno necesarias

**OBLIGATORIO**: Configura estas variables tanto para desarrollo local como para producción:

#### Para Vercel (Production/Preview):
Configura en Vercel → Project → Settings → Environment Variables:

- `GOOGLE_CREDENTIALS_JSON` → Contenido completo de tu `credentials.json` (JSON)
- `GOOGLE_TOKEN_JSON` → Contenido JSON del token (ver conversión más abajo)

#### Para desarrollo local:
Crea un archivo `.env` en la raíz del proyecto con las mismas variables.

**Nota importante**: La API ahora requiere variables de entorno en todos los entornos. No lee archivos físicos del sistema de archivos.

### 6. Convertir el token de pickle a JSON (recomendado)

Tu token local generado por la primera autenticación se guarda como pickle binario. Convierte ese token a JSON para usarlo fácilmente en Vercel:

```bash
python convert_token_pickle_to_json.py > token-google.json
```

El archivo `token-google.json` contendrá un JSON con `refresh_token`, `client_id`, etc. Copia su contenido a la variable `GOOGLE_TOKEN_JSON` en Vercel.

Alternativa (si prefieres mantener el binario):

```bash
python - << 'PY'
import base64
print(base64.b64encode(open('token.json','rb').read()).decode())
PY
```

Copia el resultado a `GOOGLE_TOKEN_BASE64` en Vercel.

## Pruebas con curl

### Verificar que la API funciona
```bash
curl http://localhost:8000/
```

### Obtener todos los items
```bash
curl http://localhost:8000/items
```

### Crear un nuevo item
```bash
curl -X POST "http://localhost:8000/items" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Nuevo Producto",
       "description": "Descripción del nuevo producto",
       "price": 99.99
     }'
```

### Obtener un item específico
```bash
curl http://localhost:8000/items/1
```

### Google Calendar API

#### Obtener calendarios disponibles
```bash
curl http://localhost:8000/calendarios
```

#### Obtener eventos del calendario principal
```bash
curl http://localhost:8000/eventos
```

#### Obtener eventos con parámetros
```bash
curl "http://localhost:8000/eventos?max_results=5&days_ahead=7"
```

#### Obtener eventos de calendario específico
```bash
curl http://localhost:8000/eventos/tu-calendar-id@group.calendar.google.com
```

## Configuración de Google Calendar

Para usar los endpoints de Google Calendar, sigue la guía completa en [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)

**Resumen rápido:**
1. Crear proyecto en Google Cloud Console
2. Habilitar Google Calendar API
3. Crear credenciales OAuth 2.0
4. Descargar `credentials.json`
5. Configurar variables de entorno

## ⚠️ Solución de Error 503

Si recibes error 503 en los endpoints de Google Calendar, consulta la guía detallada en [ENV_SETUP.md](ENV_SETUP.md) para configurar correctamente las variables de entorno en entornos serverless.

**Solución rápida:**
1. Usa `python convert_to_env_format.py` para generar las variables de entorno
2. Configura `GOOGLE_CREDENTIALS_JSON` y `GOOGLE_TOKEN_JSON` en Vercel
3. Asegúrate de que el JSON esté en una sola línea sin saltos de línea

## Variables de entorno (OBLIGATORIO)
Debes crear un archivo `.env` para variables de entorno:
```env
# Google Calendar API (OBLIGATORIO)
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
GOOGLE_TOKEN_JSON={"token":"...","refresh_token":"...",...}

# Otras variables opcionales
DATABASE_URL=your_database_url
API_KEY=your_api_key
```

## 🔒 Seguridad
- Los archivos sensibles (`.env`, `credentials.json`, `token.json`) están protegidos por `.gitignore`
- Nunca subas credenciales reales al repositorio
- Para producción, usa variables de entorno de Vercel
