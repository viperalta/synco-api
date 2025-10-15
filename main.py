from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uvicorn
import os
from dotenv import load_dotenv
from google_calendar_service import GoogleCalendarService

# Cargar variables de entorno
load_dotenv()

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
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    token_file = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
    google_calendar_service = GoogleCalendarService(credentials_file, token_file)
except Exception as e:
    print(f"Advertencia: No se pudo inicializar Google Calendar Service: {e}")
    print("Asegúrate de tener el archivo credentials.json configurado")

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
    max_results: int = Query(default=10, ge=1, le=100, description="Número máximo de eventos"),
    days_ahead: int = Query(default=30, ge=1, le=365, description="Días hacia adelante para buscar eventos")
):
    """
    Obtener eventos de un calendario específico
    
    - **calendar_id**: ID del calendario (por defecto 'primary')
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

@app.get("/eventos/{calendar_id}", response_model=List[EventResponse])
async def get_eventos_por_calendario(
    calendar_id: str,
    max_results: int = Query(default=10, ge=1, le=100, description="Número máximo de eventos"),
    days_ahead: int = Query(default=30, ge=1, le=365, description="Días hacia adelante para buscar eventos")
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
