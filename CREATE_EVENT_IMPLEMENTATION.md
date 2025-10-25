# 📋 Ejemplo de Uso del Endpoint POST /eventos

## 🚀 Implementación Completada

He implementado exitosamente el método `create_event` faltante que ahora:

1. ✅ **Crea eventos en Google Calendar** usando la API de Google
2. ✅ **Guarda eventos en MongoDB** en la colección `events`
3. ✅ **Maneja errores** de ambas operaciones
4. ✅ **Retorna respuesta completa** con todos los datos del evento

## 🔧 Cambios Realizados

### 1. **GoogleCalendarService** (`google_calendar_service.py`)
```python
def create_event(self, calendar_id: str, event_data: Dict) -> Dict:
    """
    Crear un nuevo evento en Google Calendar
    
    Args:
        calendar_id: ID del calendario donde crear el evento
        event_data: Datos del evento a crear
    
    Returns:
        Evento creado
    """
    try:
        if not self.service:
            raise Exception("Servicio de Google Calendar no inicializado")
        
        # Crear el evento en Google Calendar
        created_event = self.service.events().insert(
            calendarId=calendar_id,
            body=event_data
        ).execute()
        
        logger.info(f"Evento creado exitosamente en calendario {calendar_id} con ID: {created_event.get('id')}")
        return created_event
        
    except HttpError as error:
        logger.error(f"Error de Google Calendar API al crear evento: {error}")
        raise Exception(f"Error al crear evento en Google Calendar: {error}")
    except Exception as e:
        logger.error(f"Error inesperado al crear evento: {e}")
        raise
```

### 2. **Endpoint POST /eventos** (`main.py`)
```python
@app.post("/eventos", response_model=EventResponse)
async def create_evento(
    event_request: EventCreateRequest,
    token_data: TokenData = Depends(verify_token)
):
    """
    Crear un nuevo evento en Google Calendar y MongoDB
    
    - **event_request**: Datos del evento a crear
    - Guarda el evento tanto en Google Calendar como en la colección 'events' de MongoDB
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
        
        # Guardar evento en MongoDB
        mongo_event_data = {
            'google_event_id': created_event['id'],
            'summary': created_event['summary'],
            'description': created_event.get('description', ''),
            'start_datetime': event_request.start_datetime,
            'end_datetime': event_request.end_datetime,
            'location': created_event.get('location', ''),
            'status': created_event['status'],
            'html_link': created_event['htmlLink'],
            'is_all_day': False,  # Por defecto no es evento de todo el día
            'calendar_id': event_request.calendar_id
        }
        
        # Guardar en MongoDB
        mongo_event = await calendar_event_service.create_event(mongo_event_data)
        
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
```

## 📝 Ejemplo de Uso

### **Request:**
```bash
curl -X POST "https://tu-api.com/eventos" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Reunión de Equipo",
    "description": "Reunión semanal del equipo de desarrollo",
    "start_datetime": "2024-01-15T10:00:00",
    "end_datetime": "2024-01-15T11:00:00",
    "location": "Sala de Conferencias A",
    "calendar_id": "primary"
  }'
```

### **Response:**
```json
{
  "id": "abc123def456",
  "summary": "Reunión de Equipo",
  "description": "Reunión semanal del equipo de desarrollo",
  "start": {
    "dateTime": "2024-01-15T10:00:00",
    "timeZone": "America/Santiago"
  },
  "end": {
    "dateTime": "2024-01-15T11:00:00",
    "timeZone": "America/Santiago"
  },
  "location": "Sala de Conferencias A",
  "status": "confirmed",
  "htmlLink": "https://calendar.google.com/event?eid=abc123def456",
  "created": "2024-01-15T09:00:00.000Z",
  "updated": "2024-01-15T09:00:00.000Z",
  "attendees": [],
  "non_attendees": []
}
```

## 🗄️ Datos Guardados en MongoDB

El evento también se guarda en la colección `events` de MongoDB con la siguiente estructura:

```json
{
  "_id": "ObjectId(...)",
  "google_event_id": "abc123def456",
  "summary": "Reunión de Equipo",
  "description": "Reunión semanal del equipo de desarrollo",
  "start_datetime": "2024-01-15T10:00:00",
  "end_datetime": "2024-01-15T11:00:00",
  "location": "Sala de Conferencias A",
  "status": "confirmed",
  "html_link": "https://calendar.google.com/event?eid=abc123def456",
  "is_all_day": false,
  "calendar_id": "primary",
  "created_at": "2024-01-15T09:00:00.000Z",
  "updated_at": "2024-01-15T09:00:00.000Z"
}
```

## ✅ Características Implementadas

- **Doble Persistencia**: Eventos guardados en Google Calendar Y MongoDB
- **Manejo de Errores**: Captura errores de ambas operaciones
- **Validación de Permisos**: Requiere permiso `events.create`
- **Autenticación**: Requiere token JWT válido
- **Logging**: Registra todas las operaciones importantes
- **Respuesta Completa**: Retorna todos los datos del evento creado
- **Compatibilidad**: Mantiene compatibilidad con el sistema existente

## 🔄 Flujo de Operación

1. **Validación**: Token JWT y permisos
2. **Google Calendar**: Crear evento usando Google Calendar API
3. **MongoDB**: Guardar evento en colección `events`
4. **Respuesta**: Retornar datos completos del evento
5. **Logging**: Registrar operación exitosa

¡El endpoint ahora está completamente funcional y guarda eventos en ambos sistemas!
