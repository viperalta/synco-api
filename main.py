from fastapi import FastAPI, HTTPException, Query, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uvicorn
import os
import json
import base64
import httpx
from urllib.parse import urlencode
from dotenv import load_dotenv
from google_calendar_service import GoogleCalendarService
from mongodb_config import mongodb_config
from models import ItemModel, ItemCreate, ItemUpdate, AttendanceRequest, AttendanceResponse, EventAttendanceModel, UserModel, TokenResponse, GoogleUserInfo, TokenRefreshRequest, TokenRefreshResponse, TokenRevokeRequest, UserUpdateRequest, UserListResponse, UserRoleUpdateRequest, UserNicknameUpdateRequest, EventCreateRequest, EventUpdateRequest, EventDeleteResponse
from database_services import item_service, calendar_event_service, calendar_service, event_attendance_service
from event_formatter import format_event_description_with_attendance, extract_original_description, is_all_day_event
from auth import create_access_token, create_refresh_token, verify_token, verify_token_string, verify_refresh_token, get_google_user_info, TokenData, ACCESS_TOKEN_EXPIRE_MINUTES
from user_service import user_service
from refresh_token_service import refresh_token_service
from session_service import session_service
from pkce_utils import generate_pkce_pair, generate_state, generate_nonce
from permissions import permission_checker

# Cargar variables de entorno
load_dotenv()

# Configuración OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3003")

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

# Sin eventos de startup/shutdown - cada request maneja su propia conexión

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Desarrollo local React
        "http://localhost:3003",  # Desarrollo local (tu puerto actual)
        "https://pasesfalsos.cl",  # Dominio de producción
        "https://www.pasesfalsos.cl"  # Dominio con www
    ],
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
    attendees: Optional[List[str]] = []  # Lista de asistentes (opcional)
    non_attendees: Optional[List[str]] = []  # Lista de no asistentes (opcional)

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

@app.get("/debug/google-calendar-permissions")
async def debug_google_calendar_permissions():
    """Endpoint de debug para verificar permisos de Google Calendar"""
    if not google_calendar_service:
        return {"error": "Google Calendar Service no inicializado"}
    
    try:
        # Intentar obtener un evento para verificar permisos de lectura
        events = google_calendar_service.get_events(max_results=1)
        read_permission = len(events) > 0
        
        # Intentar obtener información del servicio para verificar permisos de escritura
        service_info = {
            "service_available": google_calendar_service.service is not None,
            "scopes": google_calendar_service.scopes,
            "read_permission": read_permission,
            "write_permission": "calendar" in str(google_calendar_service.scopes)
        }
        
        return service_info
        
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "scopes": google_calendar_service.scopes if google_calendar_service else None
        }

@app.get("/debug/version")
async def debug_version():
    """Endpoint para verificar la versión del código desplegado"""
    return {
        "version": "v2.1.0",
        "fix_applied": "verify_token_string function added",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/debug/auth")
async def debug_auth(request: Request):
    """Endpoint de debug para verificar autenticación"""
    debug_info = {
        "auth_header_present": bool(request.headers.get('authorization')),
        "auth_header_value": request.headers.get('authorization', '')[:50] + "..." if request.headers.get('authorization') else None,
        "session_token_present": bool(request.cookies.get('session_token')),
        "user_found": False,
        "user_id": None,
        "user_email": None,
        "user_roles": None,
        "debug_steps": [],
        "errors": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Debug: Mostrar headers
        print(f"=== DEBUG AUTH: Headers ===")
        print(f"Authorization header: {request.headers.get('authorization')}")
        print(f"Cookies: {dict(request.cookies)}")
        
        # Intentar obtener usuario desde Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                debug_info["debug_steps"].append("Token extraído del header")
                print(f"=== DEBUG: Verificando token: {token[:20]}... ===")
                
                token_data = verify_token_string(token)
                debug_info["debug_steps"].append(f"Token verificado: {token_data}")
                print(f"=== DEBUG: Token data: {token_data} ===")
                
                user = await user_service.get_user_by_email(token_data.email)
                debug_info["debug_steps"].append(f"Usuario buscado por email: {token_data.email}")
                print(f"=== DEBUG: Usuario encontrado: {bool(user)} ===")
                
                if user:
                    debug_info["user_found"] = True
                    debug_info["user_id"] = str(user.id)
                    debug_info["user_email"] = user.email
                    debug_info["user_roles"] = user.roles
                    debug_info["debug_steps"].append("Usuario encontrado exitosamente")
                    return debug_info
                else:
                    debug_info["errors"].append(f"Usuario no encontrado para email: {token_data.email}")
                    
            except Exception as e:
                debug_info["errors"].append(f"Error verificando token: {str(e)}")
                debug_info["errors"].append(f"Error type: {type(e).__name__}")
                print(f"=== DEBUG: Error verificando token: {e} ===")
                print(f"=== DEBUG: Error type: {type(e).__name__} ===")
                import traceback
                print(f"=== DEBUG: Traceback: {traceback.format_exc()} ===")
        
        # Intentar desde sesión
        debug_info["debug_steps"].append("Intentando desde sesión")
        user = await get_current_user_from_session(request)
        if user:
            debug_info["user_found"] = True
            debug_info["user_id"] = str(user.id)
            debug_info["user_email"] = user.email
            debug_info["user_roles"] = user.roles
            debug_info["debug_steps"].append("Usuario encontrado desde sesión")
        
        return debug_info
        
    except Exception as e:
        debug_info["errors"].append(f"Error general: {str(e)}")
        debug_info["errors"].append(f"Error type: {type(e).__name__}")
        return debug_info

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

# Funciones auxiliares para actualización de Google Calendar

async def update_google_calendar_event_description(event_id: str, attendees: List[str], non_attendees: List[str] = None, calendar_id: str = "primary"):
    """
    Actualizar la descripción de un evento en Google Calendar con información de asistencia
    
    Args:
        event_id: ID del evento a actualizar
        attendees: Lista de asistentes
        non_attendees: Lista de no asistentes (opcional)
        calendar_id: ID del calendario (por defecto 'primary')
    """
    try:
        print(f"🔄 Iniciando actualización de evento {event_id} en Google Calendar")
        print(f"📋 Asistentes a procesar: {attendees}")
        print(f"📋 No asistentes a procesar: {non_attendees or []}")
        
        # 1. Obtener el evento actual de Google Calendar
        print(f"📥 Obteniendo evento actual de Google Calendar...")
        current_event = google_calendar_service.get_event(calendar_id, event_id)
        print(f"📄 Evento obtenido: {current_event.get('summary', 'Sin título')}")
        
        # 2. Extraer descripción original
        original_description = extract_original_description(current_event.get('description', ''))
        print(f"📝 Descripción original: '{original_description[:100]}...' (truncada)")
        
        # 3. Formatear nueva descripción con asistencia
        print(f"🎨 Formateando nueva descripción...")
        new_description = format_event_description_with_attendance(
            attendees=attendees,
            non_attendees=non_attendees or [],
            original_description=original_description,
            event_start=current_event.get('start', {})
        )
        print(f"📝 Nueva descripción: '{new_description[:200]}...' (truncada)")
        
        # 4. Preparar datos para actualización
        event_data = {
            'summary': current_event.get('summary', ''),
            'description': new_description,
            'start': current_event.get('start', {}),
            'end': current_event.get('end', {}),
            'location': current_event.get('location', ''),
            'status': current_event.get('status', 'confirmed')
        }
        print(f"📦 Datos preparados para actualización")
        
        # 5. Actualizar el evento
        print(f"💾 Enviando actualización a Google Calendar...")
        updated_event = google_calendar_service.update_event(calendar_id, event_id, event_data)
        print(f"✅ Evento {event_id} actualizado exitosamente en Google Calendar")
        print(f"📊 Total de asistentes procesados: {len(attendees)}")
        print(f"📊 Total de no asistentes procesados: {len(non_attendees or [])}")
        
        return updated_event
        
    except Exception as e:
        print(f"❌ Error al actualizar evento {event_id} en Google Calendar: {e}")
        print(f"🔍 Tipo de error: {type(e).__name__}")
        import traceback
        print(f"📋 Traceback completo: {traceback.format_exc()}")
        raise

# Rutas de Asistencia a Eventos

@app.post("/asistir", response_model=AttendanceResponse)
async def asistir_evento(attendance_request: AttendanceRequest):
    """
    Registrar asistencia o no asistencia de un usuario a un evento
    
    - **event_id**: ID del evento de Google Calendar
    - **user_name**: Nombre del usuario
    - **will_attend**: True si asiste, False si no asiste (por defecto True)
    """
    try:
        # 1. Registrar asistencia/no asistencia en MongoDB
        result = await event_attendance_service.add_attendance(
            attendance_request.event_id, 
            attendance_request.user_name,
            attendance_request.will_attend
        )
        
        # 2. Actualizar descripción en Google Calendar
        if google_calendar_service:
            try:
                await update_google_calendar_event_description(
                    attendance_request.event_id, 
                    result.attendees,
                    result.non_attendees,
                    calendar_id="d7dd701e2bb45dee1e2863fddb2b15354bd4f073a1350338cb66b9ee7789f9bb@group.calendar.google.com"
                )
            except Exception as calendar_error:
                # Log del error pero no fallar la operación
                print(f"⚠️ Error al actualizar Google Calendar: {calendar_error}")
                # Agregar advertencia al mensaje de respuesta
                result.message += f" (Advertencia: No se pudo actualizar Google Calendar: {str(calendar_error)})"
        
        return result
    except ValueError as e:
        # Usuario ya existe
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar asistencia: {str(e)}")

@app.get("/asistencia/{event_id}", response_model=AttendanceResponse)
async def obtener_asistencia_evento(event_id: str):
    """
    Obtener la lista de asistentes y no asistentes de un evento específico
    
    - **event_id**: ID del evento de Google Calendar
    """
    try:
        attendance = await event_attendance_service.get_attendance(event_id)
        if not attendance:
            return AttendanceResponse(
                event_id=event_id,
                attendees=[],
                non_attendees=[],
                total_attendees=0,
                total_non_attendees=0,
                message="No hay registros de asistencia para este evento"
            )
        
        return AttendanceResponse(
            event_id=event_id,
            attendees=attendance.attendees,
            non_attendees=attendance.non_attendees,
            total_attendees=len(attendance.attendees),
            total_non_attendees=len(attendance.non_attendees),
            message=f"Total de asistentes: {len(attendance.attendees)}, Total de no asistentes: {len(attendance.non_attendees)}"
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

class CancelAttendanceRequest(BaseModel):
    user_name: str

@app.delete("/cancelar-asistencia/{event_id}", response_model=MessageResponse)
async def cancelar_asistencia(event_id: str, request: CancelAttendanceRequest):
    """
    Cancelar asistencia de un usuario a un evento
    
    - **event_id**: ID del evento de Google Calendar
    - **user_name**: Nombre del usuario (en el body)
    """
    try:
        # 1. Remover asistencia de MongoDB
        removed = await event_attendance_service.remove_attendance(event_id, request.user_name)
        if not removed:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en la lista de asistentes")
        
        # 2. Obtener lista actualizada de asistentes y no asistentes
        attendance = await event_attendance_service.get_attendance(event_id)
        updated_attendees = attendance.attendees if attendance else []
        updated_non_attendees = attendance.non_attendees if attendance else []
        
        # 3. Actualizar descripción en Google Calendar
        if google_calendar_service:
            try:
                await update_google_calendar_event_description(
                    event_id, 
                    updated_attendees,
                    updated_non_attendees,
                    calendar_id="d7dd701e2bb45dee1e2863fddb2b15354bd4f073a1350338cb66b9ee7789f9bb@group.calendar.google.com"
                )
            except Exception as calendar_error:
                # Log del error pero no fallar la operación
                print(f"⚠️ Error al actualizar Google Calendar: {calendar_error}")
        
        return MessageResponse(
            message=f"Asistencia de '{request.user_name}' cancelada exitosamente",
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
                    "non_attendees": attendance.non_attendees,
                    "total_attendees": len(attendance.attendees),
                    "total_non_attendees": len(attendance.non_attendees),
                    "created_at": attendance.created_at.isoformat() if attendance.created_at else None,
                    "updated_at": attendance.updated_at.isoformat() if attendance.updated_at else None
                }
                eventos_con_asistencia.append(evento_con_asistencia)
        
        return eventos_con_asistencia
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos con asistencia: {str(e)}")

# Función para obtener usuario actual desde sesión o Authorization header
async def get_current_user_from_request(request: Request) -> Optional[UserModel]:
    """Obtener usuario desde Authorization header o cookie de sesión"""
    # Intentar obtener usuario desde Authorization header primero
    auth_header = request.headers.get("authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            print(f"=== DEBUG: Verificando token: {token[:20]}... ===")
            token_data = verify_token_string(token)
            print(f"=== DEBUG: Token data: {token_data} ===")
            user = await user_service.get_user_by_email(token_data.email)
            print(f"=== DEBUG: Usuario encontrado: {bool(user)} ===")
            if user:
                return user
        except Exception as e:
            print(f"=== DEBUG: Error verificando token: {e} ===")
            print(f"=== DEBUG: Error type: {type(e).__name__} ===")
            import traceback
            print(f"=== DEBUG: Traceback: {traceback.format_exc()} ===")
    
    # Si no se pudo obtener desde header, intentar desde sesión
    return await get_current_user_from_session(request)

# Función para obtener usuario actual desde sesión
async def get_current_user_from_session(request: Request) -> Optional[UserModel]:
    """Obtener usuario actual desde cookie de sesión"""
    session_token = request.cookies.get("session_token")
    print(f"=== DEBUG: Cookie session_token encontrada: {bool(session_token)} ===")
    if session_token:
        print(f"=== DEBUG: Token (primeros 10 chars): {session_token[:10]}... ===")
    
    if not session_token:
        print("=== DEBUG: No hay session_token en cookies ===")
        return None
    
    user = await session_service.get_session(session_token)
    print(f"=== DEBUG: Usuario encontrado desde sesión: {bool(user)} ===")
    if user:
        print(f"=== DEBUG: Usuario email: {user.email} ===")
    
    return user

# Rutas de Autenticación

class GoogleAuthRequest(BaseModel):
    access_token: str

@app.post("/auth/google", response_model=TokenResponse)
async def google_auth(auth_request: GoogleAuthRequest):
    """
    Autenticar usuario con Google OAuth
    """
    try:
        # 1. Obtener información del usuario desde Google
        google_user_info = await get_google_user_info(auth_request.access_token)
        
        # 2. Crear o obtener usuario en la base de datos
        user = await user_service.get_or_create_user(GoogleUserInfo(**google_user_info))
        
        # 3. Crear tokens JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # 4. Guardar refresh token en la base de datos
        await refresh_token_service.create_refresh_token(str(user.id), refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # En segundos
            user=user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error en autenticación: {str(e)}"
        )

@app.get("/auth/me", response_model=UserModel)
async def get_current_user(token_data: TokenData = Depends(verify_token)):
    """
    Obtener información del usuario actual
    """
    try:
        user = await user_service.get_user_by_email(token_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(e)}"
        )

@app.post("/auth/refresh", response_model=TokenRefreshResponse)
async def refresh_token_endpoint(request: TokenRefreshRequest):
    """
    Renovar access token usando refresh token
    """
    try:
        # 1. Verificar refresh token
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 2. Verificar que el refresh token existe en la base de datos
        stored_token = await refresh_token_service.get_refresh_token(request.refresh_token)
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired"
            )
        
        # 3. Crear nuevo access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user_id, "email": email},
            expires_delta=access_token_expires
        )
        
        return TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error renovando token: {str(e)}"
        )

@app.post("/auth/revoke")
async def revoke_token(request: TokenRevokeRequest):
    """
    Revocar refresh token
    """
    try:
        success = await refresh_token_service.revoke_refresh_token(request.refresh_token)
        
        if success:
            return {"message": "Token revocado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token no encontrado"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revocando token: {str(e)}"
        )

@app.post("/auth/check-session")
async def check_session(request: TokenRefreshRequest):
    """
    Verificar si hay una sesión activa usando refresh token
    """
    try:
        # 1. Verificar refresh token
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # 2. Verificar que el refresh token existe en la base de datos
        stored_token = await refresh_token_service.get_refresh_token(request.refresh_token)
        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired"
            )
        
        # 3. Obtener usuario
        user = await user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 4. Crear nuevo access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user_id, "email": email},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=request.refresh_token,  # Mantener el mismo refresh token
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error verificando sesión: {str(e)}"
        )

@app.get("/auth/session")
async def get_session(request: Request):
    """
    Verificar sesión activa desde cookie
    """
    print(f"=== DEBUG: Todas las cookies recibidas: {dict(request.cookies)} ===")
    
    # Verificar conexión a MongoDB
    try:
        await mongodb_config.get_database().command("ping")
    except Exception as e:
        print(f"Reconectando a MongoDB en /auth/session: {e}")
        await mongodb_config.connect()
    
    user = await get_current_user_from_session(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No hay sesión activa"
        )
    
    # Crear access token para el usuario
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.get("/auth/google/silent")
async def google_silent_login(email: str = Query(..., description="Email del usuario para silent login")):
    """
    Silent login con Google (sin UI)
    """
    try:
        # Generar PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        state = generate_state()
        nonce = generate_nonce()
        
        # Guardar PKCE parameters temporalmente (en producción usar Redis)
        # Por ahora los pasamos en el state
        pkce_data = {
            "code_verifier": code_verifier,
            "email": email
        }
        encoded_pkce = base64.urlsafe_b64encode(json.dumps(pkce_data).encode()).decode()
        
        # Construir URL de Google OAuth
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=openid email profile&"
            f"prompt=none&"
            f"login_hint={email}&"
            f"state={encoded_pkce}&"
            f"nonce={nonce}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256&"
            f"include_granted_scopes=true"
        )
        
        return RedirectResponse(url=google_auth_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en silent login: {str(e)}"
        )

@app.get("/auth/google/login")
async def google_login(
    prompt: str = Query(None, description="Prompt type: consent, select_account, none (opcional)"),
    login_hint: str = Query(None, description="Email del usuario para sugerir cuenta"),
    request: Request = None
):
    """
    Login normal con Google (con UI)
    Usa login_hint para mejorar la experiencia del usuario
    """
    try:
        # Log para debugging
        print(f"=== DEBUG: Parámetros recibidos ===")
        print(f"prompt inicial: {prompt}")
        print(f"login_hint: {login_hint}")
        
        # Si no se especifica prompt, determinar automáticamente
        if prompt is None:
            # Verificar si hay una sesión activa
            session_token = request.cookies.get("session_token")
            if session_token:
                try:
                    # Verificar si la sesión es válida
                    session_data = await session_service.get_session(session_token)
                    if session_data and session_data.get("is_valid", False):
                        # Usuario ya registrado con sesión válida, usar prompt=none
                        prompt = "none"
                        # Obtener email del usuario para login_hint
                        login_hint = session_data.get("user_email")
                        print(f"Usuario registrado con sesión válida - usando prompt=none, login_hint={login_hint}")
                    else:
                        # Sesión inválida, verificar si el usuario existe en la base de datos
                        user_email = session_data.get("user_email") if session_data else None
                        if user_email:
                            try:
                                # Verificar si el usuario existe en la base de datos
                                existing_user = await user_service.get_user_by_email(user_email)
                                if existing_user:
                                    prompt = "none"
                                    login_hint = user_email
                                    print(f"Usuario encontrado en BD por email {user_email} - usando prompt=none, login_hint={login_hint}")
                                else:
                                    prompt = "select_account"
                                    print(f"Usuario no encontrado en BD por email {user_email} - usando prompt=select_account")
                            except Exception as e:
                                prompt = "select_account"
                                print(f"Error al verificar usuario en BD: {e} - usando prompt=select_account")
                        else:
                            prompt = "select_account"
                            print(f"No hay email en sesión - usando prompt=select_account")
                except Exception as e:
                    # Error al verificar sesión, usar select_account
                    prompt = "select_account"
                    print(f"Error al verificar sesión: {e} - usando prompt=select_account")
            else:
                # No hay sesión, usar select_account
                prompt = "select_account"
                print(f"No hay sesión - usando prompt=select_account")
        
        print(f"prompt final: {prompt}")
        print(f"login_hint final: {login_hint}")
        print(f"================================")
        
        # Generar PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        state = generate_state()
        nonce = generate_nonce()
        
        # Guardar PKCE parameters temporalmente
        pkce_data = {
            "code_verifier": code_verifier,
            "prompt": prompt
        }
        encoded_pkce = base64.urlsafe_b64encode(json.dumps(pkce_data).encode()).decode()
        
        # Construir URL de Google OAuth
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=openid email profile&"
            f"prompt={prompt}&"
            f"state={encoded_pkce}&"
            f"nonce={nonce}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256&"
            f"include_granted_scopes=true"
        )
        
        # Agregar login_hint si está disponible
        if login_hint:
            google_auth_url += f"&login_hint={login_hint}"
        
        # Log de la URL generada para debugging
        print(f"=== DEBUG: URL de Google OAuth ===")
        print(f"URL completa: {google_auth_url}")
        print(f"Prompt en URL: {prompt}")
        print(f"Login hint en URL: {login_hint}")
        print(f"================================")
        
        return RedirectResponse(url=google_auth_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en login: {str(e)}"
        )

@app.get("/auth/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
    error: str = Query(None, description="Error parameter"),
    request: Request = None
):
    """
    Callback de Google OAuth con PKCE
    """
    print(f"=== DEBUG: Callback de Google ejecutado ===")
    print(f"=== DEBUG: Code presente: {bool(code)} ===")
    print(f"=== DEBUG: State presente: {bool(state)} ===")
    print(f"=== DEBUG: Error: {error} ===")
    
    try:
        # Verificar si hay error
        if error:
            # Redirigir al frontend con error
            frontend_url = f"{FRONTEND_URL}?login=error&message={error}"
            return RedirectResponse(url=frontend_url)
        
        # Decodificar state para obtener PKCE data
        try:
            pkce_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
            code_verifier = pkce_data["code_verifier"]
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Intercambiar código por tokens
        token_data = await exchange_code_for_tokens(code, code_verifier)
        
        # Obtener información del usuario
        user_info = await get_google_user_info(token_data["access_token"])
        
        # Verificar conexión a MongoDB antes de crear usuario
        try:
            # Intentar reconectar si es necesario
            await mongodb_config.get_database().command("ping")
        except Exception as e:
            print(f"Reconectando a MongoDB: {e}")
            # Forzar reconexión
            await mongodb_config.connect()
        
        # Crear o obtener usuario
        user = await user_service.get_or_create_user(GoogleUserInfo(**user_info))
        
        # Crear sesión
        session_token = await session_service.create_session(user)
        print(f"=== DEBUG: Sesión creada, token: {session_token[:10]}... ===")
        
        # Redirigir inmediatamente al frontend estableciendo la cookie
        response = RedirectResponse(url=f"{FRONTEND_URL}?login=success")
        print(f"=== DEBUG: Redirigiendo a: {FRONTEND_URL}?login=success ===")
        
        # Establecer cookie de sesión usando el session_service
        session_service.set_session_cookie(response, session_token)
        print(f"=== DEBUG: Cookie establecida en respuesta ===")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Redirigir al frontend con error
        frontend_url = f"{FRONTEND_URL}?login=error&message={str(e)}"
        return RedirectResponse(url=frontend_url)

async def exchange_code_for_tokens(code: str, code_verifier: str) -> dict:
    """
    Intercambiar código de autorización por tokens usando PKCE
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "code_verifier": code_verifier
                }
            )
            
            if not response.is_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error exchanging code for tokens: {response.text}"
                )
            
            return response.json()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exchanging tokens: {str(e)}"
        )

@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    """
    Cerrar sesión (limpiar cookie y revocar tokens)
    """
    try:
        # Obtener usuario actual
        user = await get_current_user_from_session(request)
        
        if user:
            # Revocar sesiones del usuario
            await session_service.revoke_user_sessions(str(user.id))
            
            # Revocar refresh tokens del usuario
            await refresh_token_service.revoke_all_user_tokens(str(user.id))
        
        # Limpiar cookie de sesión
        session_service.clear_session_cookie(response)
        
        return {"message": "Sesión cerrada exitosamente"}
        
    except Exception as e:
        print(f"=== ERROR en logout: {str(e)} ===")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cerrando sesión: {str(e)}"
        )

# Rutas de Administración de Usuarios

@app.get("/admin/users", response_model=UserListResponse)
async def get_all_users_admin(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    request: Request = None
):
    """
    Obtener lista de todos los usuarios (solo administradores)
    
    - **skip**: Número de usuarios a saltar
    - **limit**: Número máximo de usuarios a retornar
    """
    try:
        # Obtener usuario desde Authorization header o sesión
        user = await get_current_user_from_request(request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay sesión activa"
            )
        
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(user.id))
        
        users, total = await user_service.get_all_users(skip=skip, limit=limit)
        
        return UserListResponse(
            users=users,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuarios: {str(e)}"
        )

@app.get("/admin/users/{user_id}", response_model=UserModel)
async def get_user_admin(
    user_id: str,
    request: Request = None
):
    """
    Obtener información detallada de un usuario específico (solo administradores)
    
    - **user_id**: ID del usuario a consultar
    """
    try:
        # Obtener usuario desde Authorization header o sesión
        user = await get_current_user_from_request(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay sesión activa"
            )
        
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(user.id))
        
        target_user = await user_service.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return target_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(e)}"
        )

@app.put("/admin/users/{user_id}", response_model=UserModel)
async def update_user_admin(
    user_id: str,
    update_request: UserUpdateRequest,
    request: Request = None
):
    """
    Actualizar información de un usuario (solo administradores)
    
    - **user_id**: ID del usuario a actualizar
    - **update_request**: Datos a actualizar (nickname, roles, is_active)
    """
    try:
        # Obtener usuario desde Authorization header o sesión
        user = await get_current_user_from_request(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay sesión activa"
            )
        
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(user.id))
        
        # Verificar que el usuario existe
        existing_user = await user_service.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Validar roles si se están actualizando
        if update_request.roles is not None:
            if not permission_checker.validate_roles(update_request.roles):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uno o más roles no son válidos"
                )
        
        # Preparar datos de actualización
        update_data = {}
        if update_request.nickname is not None:
            update_data["nickname"] = update_request.nickname
        if update_request.roles is not None:
            update_data["roles"] = update_request.roles
        if update_request.is_active is not None:
            update_data["is_active"] = update_request.is_active
        
        # Actualizar usuario
        updated_user = await user_service.update_user(user_id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar usuario"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )

@app.put("/admin/users/{user_id}/roles", response_model=UserModel)
async def update_user_roles_admin(
    user_id: str,
    role_request: UserRoleUpdateRequest,
    request: Request = None
):
    """
    Actualizar roles de un usuario (solo administradores)
    
    - **user_id**: ID del usuario
    - **role_request**: Lista de roles a asignar
    """
    try:
        # Obtener usuario desde Authorization header o sesión
        user = await get_current_user_from_request(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay sesión activa"
            )
        
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(user.id))
        
        # Validar roles
        if not permission_checker.validate_roles(role_request.roles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más roles no son válidos"
            )
        
        # Actualizar roles
        updated_user = await user_service.update_user_roles(user_id, role_request.roles)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar roles: {str(e)}"
        )

@app.put("/admin/users/{user_id}/nickname", response_model=UserModel)
async def update_user_nickname_admin(
    user_id: str,
    nickname_request: UserNicknameUpdateRequest,
    request: Request = None
):
    """
    Actualizar nickname de un usuario (solo administradores)
    
    - **user_id**: ID del usuario
    - **nickname_request**: Nuevo nickname
    """
    try:
        # Obtener usuario desde Authorization header o sesión
        user = await get_current_user_from_request(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay sesión activa"
            )
        
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(user.id))
        
        # Actualizar nickname
        updated_user = await user_service.update_user_nickname(user_id, nickname_request.nickname)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar nickname: {str(e)}"
        )

@app.get("/admin/roles")
async def get_available_roles(request: Request = None):
    """
    Obtener lista de roles disponibles (solo administradores)
    """
    try:
        # Obtener usuario desde Authorization header o sesión
        user = await get_current_user_from_request(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No hay sesión activa"
            )
        
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(user.id))
        
        roles = permission_checker.get_available_roles()
        role_permissions = {}
        
        for role in roles:
            role_permissions[role] = permission_checker.get_role_permissions(role)
        
        # Agregar permisos de visitors
        role_permissions["visitor"] = permission_checker.get_visitor_permissions()
        
        return {
            "roles": roles + ["visitor"],  # Incluir visitor en la lista
            "permissions": role_permissions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener roles: {str(e)}"
        )

@app.get("/admin/permissions/{user_id}")
async def get_user_permissions(
    user_id: str,
    token_data: TokenData = Depends(verify_token)
):
    """
    Obtener permisos de un usuario específico (solo administradores)
    
    - **user_id**: ID del usuario
    """
    try:
        # Verificar permisos de administrador
        await permission_checker.require_admin(str(token_data.user_id))
        
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener todos los permisos del usuario
        user_permissions = set()
        for role in user.roles:
            role_perms = permission_checker.get_role_permissions(role)
            user_permissions.update(role_perms)
        
        return {
            "user_id": user_id,
            "user_email": user.email,
            "user_nickname": user.nickname,
            "roles": user.roles,
            "permissions": sorted(list(user_permissions)),
            "is_active": user.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener permisos: {str(e)}"
        )

# Rutas de Gestión de Eventos

@app.post("/eventos", response_model=EventResponse)
async def create_evento(
    event_request: EventCreateRequest,
    token_data: TokenData = Depends(verify_token)
):
    """
    Crear un nuevo evento en Google Calendar
    
    - **event_request**: Datos del evento a crear
    """
    try:
        # Verificar permisos para crear eventos
        await permission_checker.require_permission(str(token_data.user_id), "events.create")
        
        if not google_calendar_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de Google Calendar no disponible"
            )
        
        # Preparar datos del evento para Google Calendar
        event_data = {
            'summary': event_request.summary,
            'description': event_request.description or '',
            'location': event_request.location or '',
            'start': {
                'dateTime': event_request.start_datetime,
                'timeZone': 'America/Santiago'
            },
            'end': {
                'dateTime': event_request.end_datetime,
                'timeZone': 'America/Santiago'
            }
        }
        
        # Crear evento en Google Calendar
        created_event = google_calendar_service.create_event(
            event_request.calendar_id, 
            event_data
        )
        
        return EventResponse(
            id=created_event['id'],
            summary=created_event['summary'],
            description=created_event.get('description', ''),
            start=created_event['start'],
            end=created_event['end'],
            location=created_event.get('location', ''),
            status=created_event['status'],
            htmlLink=created_event['htmlLink'],
            created=created_event['created'],
            updated=created_event['updated'],
            attendees=[],  # Nuevo evento sin asistentes
            non_attendees=[]  # Nuevo evento sin no asistentes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear evento: {str(e)}"
        )

@app.put("/eventos/{event_id}", response_model=EventResponse)
async def update_evento(
    event_id: str,
    event_request: EventUpdateRequest,
    calendar_id: str = Query(default="primary"),
    token_data: TokenData = Depends(verify_token)
):
    """
    Actualizar un evento existente en Google Calendar
    
    - **event_id**: ID del evento a actualizar
    - **event_request**: Datos a actualizar
    - **calendar_id**: ID del calendario (por defecto "primary")
    """
    try:
        # Verificar permisos para editar eventos
        await permission_checker.require_permission(str(token_data.user_id), "events.edit")
        
        if not google_calendar_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de Google Calendar no disponible"
            )
        
        # Obtener evento actual
        current_event = google_calendar_service.get_event(calendar_id, event_id)
        if not current_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Preparar datos de actualización
        update_data = {}
        if event_request.summary is not None:
            update_data['summary'] = event_request.summary
        if event_request.description is not None:
            update_data['description'] = event_request.description
        if event_request.location is not None:
            update_data['location'] = event_request.location
        if event_request.start_datetime is not None:
            update_data['start'] = {
                'dateTime': event_request.start_datetime,
                'timeZone': 'America/Santiago'
            }
        if event_request.end_datetime is not None:
            update_data['end'] = {
                'dateTime': event_request.end_datetime,
                'timeZone': 'America/Santiago'
            }
        
        # Actualizar evento en Google Calendar
        updated_event = google_calendar_service.update_event(calendar_id, event_id, update_data)
        
        return EventResponse(
            id=updated_event['id'],
            summary=updated_event['summary'],
            description=updated_event.get('description', ''),
            start=updated_event['start'],
            end=updated_event['end'],
            location=updated_event.get('location', ''),
            status=updated_event['status'],
            htmlLink=updated_event['htmlLink'],
            created=updated_event['created'],
            updated=updated_event['updated'],
            attendees=[],  # Por defecto vacío, se puede poblar después
            non_attendees=[]  # Por defecto vacío, se puede poblar después
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar evento: {str(e)}"
        )

@app.delete("/eventos/{event_id}", response_model=EventDeleteResponse)
async def delete_evento(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    token_data: TokenData = Depends(verify_token)
):
    """
    Eliminar un evento de Google Calendar
    
    - **event_id**: ID del evento a eliminar
    - **calendar_id**: ID del calendario (por defecto "primary")
    """
    try:
        # Verificar permisos para eliminar eventos
        await permission_checker.require_permission(str(token_data.user_id), "events.delete")
        
        if not google_calendar_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de Google Calendar no disponible"
            )
        
        # Verificar que el evento existe
        current_event = google_calendar_service.get_event(calendar_id, event_id)
        if not current_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Eliminar evento de Google Calendar
        google_calendar_service.delete_event(calendar_id, event_id)
        
        return EventDeleteResponse(
            message=f"Evento '{current_event.get('summary', 'Sin título')}' eliminado exitosamente",
            event_id=event_id,
            deleted=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar evento: {str(e)}"
        )

@app.get("/eventos/{event_id}", response_model=EventResponse)
async def get_evento(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    token_data: TokenData = Depends(verify_token)
):
    """
    Obtener un evento específico de Google Calendar
    
    - **event_id**: ID del evento
    - **calendar_id**: ID del calendario (por defecto "primary")
    """
    try:
        # Verificar permisos para ver eventos
        await permission_checker.require_permission(str(token_data.user_id), "events.view")
        
        if not google_calendar_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de Google Calendar no disponible"
            )
        
        # Obtener evento de Google Calendar
        event = google_calendar_service.get_event(calendar_id, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento no encontrado"
            )
        
        # Obtener datos de asistencia si existen
        attendees = []
        non_attendees = []
        try:
            attendance = await event_attendance_service.get_attendance(event['id'])
            if attendance:
                attendees = attendance.attendees
                non_attendees = attendance.non_attendees
        except Exception:
            # Si hay error obteniendo asistencia, continuar con arrays vacíos
            pass
        
        return EventResponse(
            id=event['id'],
            summary=event['summary'],
            description=event.get('description', ''),
            start=event['start'],
            end=event['end'],
            location=event.get('location', ''),
            status=event['status'],
            htmlLink=event['htmlLink'],
            created=event['created'],
            updated=event['updated'],
            attendees=attendees,  # Datos de asistencia si existen
            non_attendees=non_attendees  # Datos de no asistencia si existen
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener evento: {str(e)}"
        )

@app.get("/eventos-con-asistencia-detallada", response_model=List[EventResponse])
async def get_eventos_con_asistencia_detallada(
    calendar_id: str = Query(default="primary", description="ID del calendario"),
    max_results: int = Query(default=50, ge=1, le=100, description="Número máximo de eventos"),
    days_ahead: int = Query(default=90, ge=1, le=365, description="Días hacia adelante para buscar eventos"),
    token_data: TokenData = Depends(verify_token)
):
    """
    Obtener eventos de Google Calendar con información de asistencia incluida en EventResponse
    
    - **calendar_id**: ID del calendario (por defecto 'primary')
    - **max_results**: Número máximo de eventos a retornar (1-100, por defecto 50)
    - **days_ahead**: Días hacia adelante para buscar eventos (1-365, por defecto 90 días)
    
    Retorna eventos con campos attendees y non_attendees poblados
    """
    try:
        # Verificar permisos para ver eventos
        await permission_checker.require_permission(str(token_data.user_id), "events.view")
        
        if not google_calendar_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de Google Calendar no disponible. Verifica la configuración."
            )
        
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
        
        # Crear lista de EventResponse con asistencia incluida
        eventos_con_asistencia = []
        for evento in eventos:
            event_id = evento.get("id")
            
            # Obtener datos de asistencia si existen
            attendees = []
            non_attendees = []
            if event_id in attendance_dict:
                attendance = attendance_dict[event_id]
                attendees = attendance.attendees
                non_attendees = attendance.non_attendees
            
            # Crear EventResponse con asistencia incluida
            evento_response = EventResponse(
                id=evento['id'],
                summary=evento['summary'],
                description=evento.get('description', ''),
                start=evento['start'],
                end=evento['end'],
                location=evento.get('location', ''),
                status=evento['status'],
                htmlLink=evento['htmlLink'],
                created=evento['created'],
                updated=evento['updated'],
                attendees=attendees,
                non_attendees=non_attendees
            )
            
            eventos_con_asistencia.append(evento_response)
        
        return eventos_con_asistencia
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener eventos con asistencia detallada: {str(e)}"
        )

# Función para ejecutar localmente
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
