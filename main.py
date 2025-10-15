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
from mongodb_config import mongodb_config
from models import ItemModel, ItemCreate, ItemUpdate, AttendanceRequest, AttendanceResponse, EventAttendanceModel
from database_services import item_service, calendar_event_service, calendar_service, event_attendance_service

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
    description="API REST con FastAPI para Synco con MongoDB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Eventos de inicio y cierre de la aplicación
@app.on_event("startup")
async def startup_event():
    """Inicializar conexiones al iniciar la aplicación"""
    try:
        # Conectar a MongoDB
        await mongodb_config.connect()
        print("✅ MongoDB conectado exitosamente")
    except Exception as e:
        print(f"❌ Error al conectar con MongoDB: {e}")
        # No fallar la aplicación si MongoDB no está disponible
        print("⚠️ Continuando sin MongoDB (modo degradado)")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al finalizar la aplicación"""
    try:
        await mongodb_config.disconnect()
        print("✅ MongoDB desconectado")
    except Exception as e:
        print(f"❌ Error al desconectar MongoDB: {e}")

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

# Los items ahora se almacenan en MongoDB

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
    """Endpoint de debug para verificar variables de entorno"""
    return {
        "google_credentials_json_present": bool(os.getenv('GOOGLE_CREDENTIALS_JSON')),
        "google_token_json_present": bool(os.getenv('GOOGLE_TOKEN_JSON')),
        "google_token_base64_present": bool(os.getenv('GOOGLE_TOKEN_BASE64')),
        "google_credentials_file": os.getenv('GOOGLE_CREDENTIALS_FILE'),
        "google_token_file": os.getenv('GOOGLE_TOKEN_FILE'),
        "google_scopes": os.getenv('GOOGLE_SCOPES'),
        "credentials_file_exists": os.path.exists(os.getenv('GOOGLE_CREDENTIALS_FILE', '')),
        "token_file_exists": os.path.exists(os.getenv('GOOGLE_TOKEN_FILE', '')),
        "google_service_initialized": google_calendar_service is not None,
        "mongodb_url_present": bool(os.getenv('MONGODB_URL')),
        "mongodb_database": os.getenv('MONGODB_DATABASE'),
        "mongodb_connected": mongodb_config.database is not None
    }

@app.get("/debug/mongodb")
async def debug_mongodb():
    """Endpoint de debug específico para MongoDB"""
    try:
        # Intentar conectar si no está conectado
        if mongodb_config.database is None:
            await mongodb_config.connect()
        
        # Probar una operación simple
        collection = mongodb_config.get_collection("debug_test")
        result = await collection.insert_one({"test": "connection", "timestamp": datetime.utcnow()})
        
        # Limpiar
        await collection.delete_one({"_id": result.inserted_id})
        
        return {
            "status": "success",
            "message": "MongoDB conectado y funcionando correctamente",
            "database": mongodb_config.database_name,
            "test_inserted_id": str(result.inserted_id)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error de conexión a MongoDB: {str(e)}",
            "database": mongodb_config.database_name,
            "mongodb_url_present": bool(os.getenv('MONGODB_URL'))
        }

@app.get("/items", response_model=List[ItemModel])
async def get_items(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=1000)):
    """Obtener todos los items desde MongoDB"""
    try:
        items = await item_service.get_items(skip=skip, limit=limit)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener items: {str(e)}")

@app.get("/items/{item_id}", response_model=ItemModel)
async def get_item(item_id: str):
    """Obtener un item específico por ID desde MongoDB"""
    try:
        item = await item_service.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener item: {str(e)}")

@app.post("/items", response_model=ItemModel)
async def create_item(item: ItemCreate):
    """Crear un nuevo item en MongoDB"""
    try:
        created_item = await item_service.create_item(item)
        return created_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear item: {str(e)}")

@app.put("/items/{item_id}", response_model=ItemModel)
async def update_item(item_id: str, item: ItemUpdate):
    """Actualizar un item existente en MongoDB"""
    try:
        updated_item = await item_service.update_item(item_id, item)
        if not updated_item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar item: {str(e)}")

@app.delete("/items/{item_id}", response_model=MessageResponse)
async def delete_item(item_id: str):
    """Eliminar un item de MongoDB"""
    try:
        deleted = await item_service.delete_item(item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        return MessageResponse(
            message=f"Item {item_id} eliminado correctamente",
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar item: {str(e)}")

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

# Rutas de Asistencia a Eventos

@app.post("/asistir", response_model=AttendanceResponse)
async def asistir_evento(attendance_request: AttendanceRequest):
    """
    Registrar asistencia de un usuario a un evento
    
    - **event_id**: ID del evento de Google Calendar
    - **user_name**: Nombre del usuario que asistirá
    """
    try:
        result = await event_attendance_service.add_attendance(
            attendance_request.event_id, 
            attendance_request.user_name
        )
        return result
    except ValueError as e:
        # Usuario ya existe
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar asistencia: {str(e)}")

@app.get("/asistencia/{event_id}", response_model=AttendanceResponse)
async def obtener_asistencia_evento(event_id: str):
    """
    Obtener la lista de asistentes de un evento específico
    
    - **event_id**: ID del evento de Google Calendar
    """
    try:
        attendance = await event_attendance_service.get_attendance(event_id)
        if not attendance:
            return AttendanceResponse(
                event_id=event_id,
                attendees=[],
                total_attendees=0,
                message="No hay asistentes registrados para este evento"
            )
        
        return AttendanceResponse(
            event_id=event_id,
            attendees=attendance.attendees,
            total_attendees=len(attendance.attendees),
            message=f"Total de asistentes: {len(attendance.attendees)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener asistencia: {str(e)}")

@app.get("/asistencias", response_model=List[EventAttendanceModel])
async def obtener_todas_asistencias(
    skip: int = Query(default=0, ge=0), 
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    Obtener todas las asistencias registradas con paginación
    
    - **skip**: Número de registros a saltar
    - **limit**: Número máximo de registros a retornar
    """
    try:
        attendances = await event_attendance_service.get_all_attendances(skip=skip, limit=limit)
        return attendances
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener asistencias: {str(e)}")

@app.delete("/asistencia/{event_id}/{user_name}", response_model=MessageResponse)
async def cancelar_asistencia(event_id: str, user_name: str):
    """
    Cancelar asistencia de un usuario a un evento
    
    - **event_id**: ID del evento de Google Calendar
    - **user_name**: Nombre del usuario
    """
    try:
        removed = await event_attendance_service.remove_attendance(event_id, user_name)
        if not removed:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en la lista de asistentes")
        
        return MessageResponse(
            message=f"Asistencia de '{user_name}' cancelada exitosamente",
            status="success"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar asistencia: {str(e)}")

@app.get("/eventos-con-asistencia", response_model=List[dict])
async def get_eventos_con_asistencia(
    calendar_id: str = Query(default="primary", description="ID del calendario"),
    max_results: int = Query(default=50, ge=1, le=100, description="Número máximo de eventos"),
    days_ahead: int = Query(default=90, ge=1, le=365, description="Días hacia adelante para buscar eventos")
):
    """
    Obtener eventos de Google Calendar que tienen asistencia registrada
    
    - **calendar_id**: ID del calendario (por defecto 'primary')
    - **max_results**: Número máximo de eventos a retornar (1-100, por defecto 50)
    - **days_ahead**: Días hacia adelante para buscar eventos (1-365, por defecto 90 días)
    
    Retorna eventos con información de asistencia incluida
    """
    if not google_calendar_service:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de Google Calendar no disponible. Verifica la configuración."
        )
    
    try:
        # Obtener eventos de Google Calendar
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)
        
        eventos = google_calendar_service.get_events(
            calendar_id=calendar_id,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )
        
        # Obtener todas las asistencias registradas
        attendances = await event_attendance_service.get_all_attendances()
        
        # Crear un diccionario para búsqueda rápida por event_id
        attendance_dict = {att.event_id: att for att in attendances}
        
        # Filtrar solo eventos que tienen asistencia registrada
        eventos_con_asistencia = []
        for evento in eventos:
            event_id = evento.get("id")
            if event_id in attendance_dict:
                attendance = attendance_dict[event_id]
                # Agregar información de asistencia al evento
                evento_con_asistencia = evento.copy()
                evento_con_asistencia["asistencia"] = {
                    "attendees": attendance.attendees,
                    "total_attendees": len(attendance.attendees),
                    "created_at": attendance.created_at.isoformat() if attendance.created_at else None,
                    "updated_at": attendance.updated_at.isoformat() if attendance.updated_at else None
                }
                eventos_con_asistencia.append(evento_con_asistencia)
        
        return eventos_con_asistencia
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos con asistencia: {str(e)}")

# Función para ejecutar localmente
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
