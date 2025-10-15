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

## Variables de entorno (opcional)
Puedes crear un archivo `.env` para variables de entorno:
```
DATABASE_URL=your_database_url
API_KEY=your_api_key
```
