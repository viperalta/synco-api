from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uvicorn
import os
import json
import base64
from dotenv import load_dotenv
from google_calendar_service import GoogleCalendarService

# Cargar variables de entorno
load_dotenv()

# Escribir credenciales/token desde variables de entorno a /tmp para entornos serverless (Vercel)
def ensure_google_files_from_env():
    # Debug: Mostrar todas las variables de entorno relacionadas con Google
    print("=== DEBUG: Variables de entorno Google ===")
    print(f"GOOGLE_CREDENTIALS_JSON presente: {bool(os.getenv('GOOGLE_CREDENTIALS_JSON'))}")
    print(f"GOOGLE_TOKEN_JSON presente: {bool(os.getenv('GOOGLE_TOKEN_JSON'))}")
    print(f"GOOGLE_TOKEN_BASE64 presente: {bool(os.getenv('GOOGLE_TOKEN_BASE64'))}")
    print(f"GOOGLE_CREDENTIALS_FILE: {os.getenv('GOOGLE_CREDENTIALS_FILE')}")
    print(f"GOOGLE_TOKEN_FILE: {os.getenv('GOOGLE_TOKEN_FILE')}")
    print(f"GOOGLE_SCOPES: {os.getenv('GOOGLE_SCOPES')}")
    
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    token_base64 = os.getenv("GOOGLE_TOKEN_BASE64")

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_FILE", "/tmp/credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_FILE", "/tmp/token.json")

    # Helper para asegurar el directorio destino
    def ensure_parent_dir(path: str):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    # Procesar credenciales JSON explícitas
    if credentials_json:
        try:
            # Validar que es JSON válido
            json.loads(credentials_json)
            ensure_parent_dir(credentials_path)
            with open(credentials_path, "w") as f:
                f.write(credentials_json)
            os.environ["GOOGLE_CREDENTIALS_FILE"] = credentials_path
            print(f"Credenciales cargadas desde GOOGLE_CREDENTIALS_JSON: {credentials_path}")
        except json.JSONDecodeError as e:
            print(f"Error: GOOGLE_CREDENTIALS_JSON no es un JSON válido: {e}")
        except Exception as e:
            print(f"Error al procesar credenciales: {e}")
    
    # También permitir que GOOGLE_CREDENTIALS_FILE contenga JSON inline
    raw_credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
    if raw_credentials_file:
        # Limpiar comillas simples adicionales que pueden venir de Vercel
        cleaned_credentials = raw_credentials_file.strip()
        if cleaned_credentials.startswith("'") and cleaned_credentials.endswith("'"):
            cleaned_credentials = cleaned_credentials[1:-1]
        
        if cleaned_credentials.startswith("{"):
            try:
                json.loads(cleaned_credentials)
                ensure_parent_dir("/tmp/credentials.json")
                with open("/tmp/credentials.json", "w") as f:
                    f.write(cleaned_credentials)
                os.environ["GOOGLE_CREDENTIALS_FILE"] = "/tmp/credentials.json"
                print("Credenciales detectadas como JSON inline en GOOGLE_CREDENTIALS_FILE; escritas a /tmp/credentials.json")
            except Exception as e:
                print(f"Error al interpretar GOOGLE_CREDENTIALS_FILE como JSON: {e}")

    # Procesar token JSON explícito
    if token_json:
        try:
            # Validar que es JSON válido
            json.loads(token_json)
            ensure_parent_dir(token_path)
            with open(token_path, "w") as f:
                f.write(token_json)
            os.environ["GOOGLE_TOKEN_FILE"] = token_path
            print(f"Token cargado desde GOOGLE_TOKEN_JSON: {token_path}")
        except json.JSONDecodeError as e:
            print(f"Error: GOOGLE_TOKEN_JSON no es un JSON válido: {e}")
        except Exception as e:
            print(f"Error al procesar token: {e}")
    elif token_base64:
        try:
            ensure_parent_dir(token_path)
            binary = base64.b64decode(token_base64)
            # Si viene en base64 y queremos mantener extensión binaria, usamos el path dado
            with open(token_path, "wb") as f:
                f.write(binary)
            os.environ["GOOGLE_TOKEN_FILE"] = token_path
            print(f"Token cargado desde base64: {token_path}")
        except Exception as e:
            print(f"Error al procesar token base64: {e}")
    
    # También permitir que GOOGLE_TOKEN_FILE contenga JSON inline
    raw_token_file = os.getenv("GOOGLE_TOKEN_FILE")
    if raw_token_file:
        # Limpiar comillas simples adicionales que pueden venir de Vercel
        cleaned_token = raw_token_file.strip()
        if cleaned_token.startswith("'") and cleaned_token.endswith("'"):
            cleaned_token = cleaned_token[1:-1]
        
        if cleaned_token.startswith("{"):
            try:
                json.loads(cleaned_token)
                ensure_parent_dir("/tmp/token.json")
                with open("/tmp/token.json", "w") as f:
                    f.write(cleaned_token)
                os.environ["GOOGLE_TOKEN_FILE"] = "/tmp/token.json"
                print("Token detectado como JSON inline en GOOGLE_TOKEN_FILE; escrito a /tmp/token.json")
            except Exception as e:
                print(f"Error al interpretar GOOGLE_TOKEN_FILE como JSON: {e}")


ensure_google_files_from_env()

# Crear instancia de FastAPI
app = FastAPI(
    title="Synco API",
    description="API REST con FastAPI para Synco",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool = True

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    is_active: bool

class MessageResponse(BaseModel):
    message: str
    status: str

class EventResponse(BaseModel):
    id: str
    summary: str
    description: str
    start: Dict
    end: Dict
    location: str
    status: str
    htmlLink: str
    created: str
    updated: str

class CalendarResponse(BaseModel):
    id: str
    summary: str
    description: str
    primary: bool
    accessRole: str
    backgroundColor: str
    foregroundColor: str

# Base de datos en memoria (para ejemplo)
items_db: List[Item] = [
    Item(id=1, name="Producto 1", description="Descripción del producto 1", price=29.99),
    Item(id=2, name="Producto 2", description="Descripción del producto 2", price=49.99),
]

# Inicializar servicio de Google Calendar
google_calendar_service = None
try:
    # Solo usar archivos temporales generados desde variables de entorno
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    token_file = os.getenv('GOOGLE_TOKEN_FILE')
    
    if not credentials_file or not token_file:
        raise Exception("Variables de entorno GOOGLE_CREDENTIALS_FILE y GOOGLE_TOKEN_FILE no configuradas")
    
    print(f"Intentando inicializar Google Calendar Service...")
    print(f"Archivo de credenciales: {credentials_file}")
    print(f"Archivo de token: {token_file}")
    print(f"Archivo de credenciales existe: {os.path.exists(credentials_file)}")
    print(f"Archivo de token existe: {os.path.exists(token_file)}")
    
    google_calendar_service = GoogleCalendarService(credentials_file, token_file)
    print("Google Calendar Service inicializado correctamente")
except Exception as e:
    print(f"Error: No se pudo inicializar Google Calendar Service: {e}")
    print("Verifica que las variables de entorno estén configuradas:")
    print("- GOOGLE_CREDENTIALS_JSON: Contenido JSON completo de credentials.json")
    print("- GOOGLE_TOKEN_JSON: Contenido JSON completo del token")
    print("Usa 'python convert_to_env_format.py' para generar el formato correcto")

# Rutas de la API

@app.get("/", response_model=MessageResponse)
async def root():
    """Endpoint raíz de la API"""
    return MessageResponse(
        message="¡Bienvenido a Synco API!",
        status="success"
    )

@app.get("/health", response_model=MessageResponse)
async def health_check():
    """Endpoint para verificar el estado de la API"""
    return MessageResponse(
        message="API funcionando correctamente",
        status="healthy"
    )

@app.get("/debug/env")
async def debug_env():
    """Endpoint de debug para verificar variables de entorno (solo para desarrollo)"""
    return {
        "google_credentials_json_present": bool(os.getenv('GOOGLE_CREDENTIALS_JSON')),
        "google_token_json_present": bool(os.getenv('GOOGLE_TOKEN_JSON')),
        "google_token_base64_present": bool(os.getenv('GOOGLE_TOKEN_BASE64')),
        "google_credentials_file": os.getenv('GOOGLE_CREDENTIALS_FILE'),
        "google_token_file": os.getenv('GOOGLE_TOKEN_FILE'),
        "google_scopes": os.getenv('GOOGLE_SCOPES'),
        "credentials_file_exists": os.path.exists(os.getenv('GOOGLE_CREDENTIALS_FILE', '')),
        "token_file_exists": os.path.exists(os.getenv('GOOGLE_TOKEN_FILE', '')),
        "google_service_initialized": google_calendar_service is not None
    }

@app.get("/items", response_model=List[ItemResponse])
async def get_items():
    """Obtener todos los items"""
    return items_db

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Obtener un item específico por ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item no encontrado")

@app.post("/items", response_model=ItemResponse)
async def create_item(item: Item):
    """Crear un nuevo item"""
    # Generar nuevo ID
    new_id = max([i.id for i in items_db], default=0) + 1
    item.id = new_id
    items_db.append(item)
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: Item):
    """Actualizar un item existente"""
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            item.id = item_id
            items_db[i] = item
            return item
    raise HTTPException(status_code=404, detail="Item no encontrado")

@app.delete("/items/{item_id}", response_model=MessageResponse)
async def delete_item(item_id: int):
    """Eliminar un item"""
    for i, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(i)
            return MessageResponse(
                message=f"Item {item_id} eliminado correctamente",
                status="success"
            )
    raise HTTPException(status_code=404, detail="Item no encontrado")

# Rutas de Google Calendar

@app.get("/calendarios", response_model=List[CalendarResponse])
async def get_calendarios():
    """Obtener lista de calendarios disponibles"""
    if not google_calendar_service:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de Google Calendar no disponible. Verifica la configuración."
        )
    
    try:
        calendarios = google_calendar_service.list_calendars()
        return calendarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener calendarios: {str(e)}")

@app.get("/eventos", response_model=List[EventResponse])
async def get_eventos(
    calendar_id: str = Query(default="primary", description="ID del calendario"),
    max_results: int = Query(default=50, ge=1, le=100, description="Número máximo de eventos"),
    days_ahead: int = Query(default=90, ge=1, le=365, description="Días hacia adelante para buscar eventos")
):
    """
    Obtener eventos de un calendario específico
    
    - **calendar_id**: ID del calendario (por defecto 'primary')
    - **max_results**: Número máximo de eventos a retornar (1-100, por defecto 50)
    - **days_ahead**: Días hacia adelante para buscar eventos (1-365, por defecto 90 días = 3 meses)
    """
    if not google_calendar_service:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de Google Calendar no disponible. Verifica la configuración."
        )
    
    try:
        # Calcular fechas de búsqueda
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)
        
        eventos = google_calendar_service.get_events(
            calendar_id=calendar_id,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )
        
        return eventos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")

@app.get("/eventos/{calendar_id}", response_model=List[EventResponse])
async def get_eventos_por_calendario(
    calendar_id: str,
    max_results: int = Query(default=50, ge=1, le=100, description="Número máximo de eventos"),
    days_ahead: int = Query(default=90, ge=1, le=365, description="Días hacia adelante para buscar eventos")
):
    """
    Obtener eventos de un calendario específico por ID
    
    - **calendar_id**: ID del calendario en la URL
    - **max_results**: Número máximo de eventos a retornar (1-100)
    - **days_ahead**: Días hacia adelante para buscar eventos (1-365)
    """
    if not google_calendar_service:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de Google Calendar no disponible. Verifica la configuración."
        )
    
    try:
        # Calcular fechas de búsqueda
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)
        
        eventos = google_calendar_service.get_events(
            calendar_id=calendar_id,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )
        
        return eventos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")

# Función para ejecutar localmente
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
