"""
Servicios para operaciones de base de datos MongoDB
"""
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from models import ItemModel, ItemCreate, ItemUpdate, CalendarEventModel, CalendarModel, EventAttendanceModel, AttendanceRequest, AttendanceResponse
from mongodb_config import mongodb_config
import logging

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class ItemService:
    def __init__(self):
        self._collection = None
        self._collection_name = "items"
    
    @property
    def collection(self):
        if self._collection is None:
            # El middleware se encarga de la reconexión
            self._collection = mongodb_config.get_collection(self._collection_name)
        return self._collection
    
    async def create_item(self, item: ItemCreate) -> ItemModel:
        """Crear un nuevo item"""
        item_dict = item.dict()
        item_dict["created_at"] = datetime.utcnow()
        item_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(item_dict)
        created_item = await self.collection.find_one({"_id": result.inserted_id})
        return ItemModel(**created_item)
    
    async def get_item(self, item_id: str) -> Optional[ItemModel]:
        """Obtener un item por ID"""
        if not ObjectId.is_valid(item_id):
            return None
        
        item = await self.collection.find_one({"_id": ObjectId(item_id)})
        return ItemModel(**item) if item else None
    
    async def get_items(self, skip: int = 0, limit: int = 100) -> List[ItemModel]:
        """Obtener todos los items con paginación"""
        cursor = self.collection.find().skip(skip).limit(limit)
        items = []
        async for item in cursor:
            items.append(ItemModel(**item))
        return items
    
    async def update_item(self, item_id: str, item: ItemUpdate) -> Optional[ItemModel]:
        """Actualizar un item"""
        if not ObjectId.is_valid(item_id):
            return None
        
        update_data = {k: v for k, v in item.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_item = await self.collection.find_one({"_id": ObjectId(item_id)})
            return ItemModel(**updated_item)
        return None
    
    async def delete_item(self, item_id: str) -> bool:
        """Eliminar un item"""
        if not ObjectId.is_valid(item_id):
            return False
        
        result = await self.collection.delete_one({"_id": ObjectId(item_id)})
        return result.deleted_count > 0

class CalendarEventService:
    def __init__(self):
        self._collection = None
        self._collection_name = "calendar_events"
    
    @property
    def collection(self):
        if self._collection is None:
            # El middleware se encarga de la reconexión
            self._collection = mongodb_config.get_collection(self._collection_name)
        return self._collection
    
    async def create_event(self, event_data: dict) -> CalendarEventModel:
        """Crear un nuevo evento de calendario"""
        event_dict = event_data.copy()
        event_dict["created_at"] = datetime.utcnow()
        event_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(event_dict)
        created_event = await self.collection.find_one({"_id": result.inserted_id})
        return CalendarEventModel(**created_event)
    
    async def get_events_by_calendar(self, calendar_id: str, skip: int = 0, limit: int = 100) -> List[CalendarEventModel]:
        """Obtener eventos por calendario"""
        cursor = self.collection.find({"calendar_id": calendar_id}).skip(skip).limit(limit)
        events = []
        async for event in cursor:
            events.append(CalendarEventModel(**event))
        return events
    
    async def get_all_events(self, skip: int = 0, limit: int = 100) -> List[CalendarEventModel]:
        """Obtener todos los eventos"""
        cursor = self.collection.find().skip(skip).limit(limit)
        events = []
        async for event in cursor:
            events.append(CalendarEventModel(**event))
        return events
    
    async def update_event(self, event_id: str, event_data: dict) -> Optional[CalendarEventModel]:
        """Actualizar un evento"""
        if not ObjectId.is_valid(event_id):
            return None
        
        update_data = event_data.copy()
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_event = await self.collection.find_one({"_id": ObjectId(event_id)})
            return CalendarEventModel(**updated_event)
        return None
    
    async def delete_event(self, event_id: str) -> bool:
        """Eliminar un evento"""
        if not ObjectId.is_valid(event_id):
            return False
        
        result = await self.collection.delete_one({"_id": ObjectId(event_id)})
        return result.deleted_count > 0

class CalendarService:
    def __init__(self):
        self._collection = None
        self._collection_name = "calendars"
    
    @property
    def collection(self):
        if self._collection is None:
            # El middleware se encarga de la reconexión
            self._collection = mongodb_config.get_collection(self._collection_name)
        return self._collection
    
    async def create_calendar(self, calendar_data: dict) -> CalendarModel:
        """Crear un nuevo calendario"""
        calendar_dict = calendar_data.copy()
        calendar_dict["created_at"] = datetime.utcnow()
        calendar_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(calendar_dict)
        created_calendar = await self.collection.find_one({"_id": result.inserted_id})
        return CalendarModel(**created_calendar)
    
    async def get_calendars(self, skip: int = 0, limit: int = 100) -> List[CalendarModel]:
        """Obtener todos los calendarios"""
        cursor = self.collection.find().skip(skip).limit(limit)
        calendars = []
        async for calendar in cursor:
            calendars.append(CalendarModel(**calendar))
        return calendars
    
    async def get_calendar_by_google_id(self, google_calendar_id: str) -> Optional[CalendarModel]:
        """Obtener calendario por Google Calendar ID"""
        calendar = await self.collection.find_one({"google_calendar_id": google_calendar_id})
        return CalendarModel(**calendar) if calendar else None

class EventAttendanceService:
    def __init__(self):
        self._collection = None
        self._collection_name = "event_attendances"
    
    @property
    def collection(self):
        if self._collection is None:
            # El middleware se encarga de la reconexión
            self._collection = mongodb_config.get_collection(self._collection_name)
        return self._collection
    
    async def add_attendance(self, event_id: str, user_name: str) -> AttendanceResponse:
        """Agregar un usuario a la lista de asistentes de un evento"""
        # Buscar si ya existe un registro para este evento
        existing_attendance = await self.collection.find_one({"event_id": event_id})
        
        if existing_attendance:
            # Verificar si el usuario ya está en la lista
            if user_name in existing_attendance["attendees"]:
                raise ValueError(f"El usuario '{user_name}' ya está registrado para asistir a este evento")
            
            # Agregar el usuario a la lista existente
            await self.collection.update_one(
                {"event_id": event_id},
                {
                    "$push": {"attendees": user_name},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Obtener el registro actualizado
            updated_attendance = await self.collection.find_one({"event_id": event_id})
            attendees = updated_attendance["attendees"]
        else:
            # Crear nuevo registro para este evento
            attendance_data = {
                "event_id": event_id,
                "attendees": [user_name],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.collection.insert_one(attendance_data)
            attendees = [user_name]
        
        return AttendanceResponse(
            event_id=event_id,
            attendees=attendees,
            total_attendees=len(attendees),
            message=f"Usuario '{user_name}' agregado exitosamente a la lista de asistentes"
        )
    
    async def get_attendance(self, event_id: str) -> Optional[EventAttendanceModel]:
        """Obtener la lista de asistentes de un evento"""
        attendance = await self.collection.find_one({"event_id": event_id})
        return EventAttendanceModel(**attendance) if attendance else None
    
    async def get_all_attendances(self, skip: int = 0, limit: int = 100) -> List[EventAttendanceModel]:
        """Obtener todas las asistencias con paginación"""
        cursor = self.collection.find().skip(skip).limit(limit)
        attendances = []
        async for attendance in cursor:
            attendances.append(EventAttendanceModel(**attendance))
        return attendances
    
    async def remove_attendance(self, event_id: str, user_name: str) -> bool:
        """Remover un usuario de la lista de asistentes"""
        result = await self.collection.update_one(
            {"event_id": event_id},
            {
                "$pull": {"attendees": user_name},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    async def delete_event_attendance(self, event_id: str) -> bool:
        """Eliminar completamente el registro de asistencia de un evento"""
        result = await self.collection.delete_one({"event_id": event_id})
        return result.deleted_count > 0

# Instancias globales de servicios (inicialización perezosa)
_item_service = None
_calendar_event_service = None
_calendar_service = None
_event_attendance_service = None

def get_item_service() -> ItemService:
    global _item_service
    if _item_service is None:
        _item_service = ItemService()
    return _item_service

def get_calendar_event_service() -> CalendarEventService:
    global _calendar_event_service
    if _calendar_event_service is None:
        _calendar_event_service = CalendarEventService()
    return _calendar_event_service

def get_calendar_service() -> CalendarService:
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service

def get_event_attendance_service() -> EventAttendanceService:
    global _event_attendance_service
    if _event_attendance_service is None:
        _event_attendance_service = EventAttendanceService()
    return _event_attendance_service

# Instancias para compatibilidad (inicialización perezosa)
class LazyService:
    def __init__(self, service_getter):
        self._service_getter = service_getter
        self._service = None
        self._initialized = False
    
    def __getattr__(self, name):
        if not self._initialized:
            # Crear el servicio de manera síncrona para evitar problemas con event loops
            self._service = self._service_getter()
            self._initialized = True
        
        return getattr(self._service, name)

item_service = LazyService(get_item_service)
calendar_event_service = LazyService(get_calendar_event_service)
calendar_service = LazyService(get_calendar_service)
event_attendance_service = LazyService(get_event_attendance_service)
