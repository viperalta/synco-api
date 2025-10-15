# 🔄 Sincronización Automática con Google Calendar

## 📋 Descripción

Esta funcionalidad permite que cada vez que un jugador confirme o cancele su asistencia a un evento, la descripción del evento en Google Calendar se actualice automáticamente con la información de asistencia.

## ⚙️ Configuración Requerida

### 1. Permisos de Google Calendar
- **Cambiar scope**: De `calendar.readonly` a `calendar` (escritura)
- **Variable de entorno**: `GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar`

### 2. Archivos Modificados
- `google_calendar_service.py`: Agregados métodos `update_event()` y `get_event()`
- `event_formatter.py`: Nuevo archivo para formatear descripciones
- `main.py`: Endpoints modificados para sincronizar con Google Calendar

## 🔄 Flujo de Funcionamiento

### Al Confirmar Asistencia (`POST /asistir`):
1. **Registrar en MongoDB**: Se guarda la asistencia en la base de datos
2. **Obtener evento actual**: Se consulta el evento desde Google Calendar
3. **Extraer descripción original**: Se separa la descripción original de la sección de asistencia
4. **Formatear nueva descripción**: Se crea una descripción con la lista actualizada de asistentes
5. **Actualizar Google Calendar**: Se actualiza el evento con la nueva descripción

### Al Cancelar Asistencia (`DELETE /asistencia/{event_id}/{user_name}`):
1. **Remover de MongoDB**: Se elimina la asistencia de la base de datos
2. **Obtener lista actualizada**: Se consulta la lista actual de asistentes
3. **Actualizar Google Calendar**: Se actualiza el evento con la lista actualizada

## 📝 Formato de Descripción

### Estructura de la Descripción Actualizada:
```
Descripción original del evento (si existe)

--- ASISTENCIA ---
📅 Evento de todo el día (o ⏰ Evento con horario específico)
👥 Total de asistentes: X
🕒 Última actualización: DD/MM/YYYY HH:MM

✅ ASISTENTES CONFIRMADOS:
1. Nombre del Asistente 1
2. Nombre del Asistente 2
...
```

### Ejemplo:
```
Partido de fútbol contra el equipo rival

--- ASISTENCIA ---
⏰ Evento con horario específico
👥 Total de asistentes: 3
🕒 Última actualización: 15/10/2025 22:30

✅ ASISTENTES CONFIRMADOS:
1. Vicente
2. Cony
3. Lola
```

## 🛡️ Manejo de Errores

### Estrategia de Fallback:
- **Si falla Google Calendar**: La operación en MongoDB se mantiene exitosa
- **Log de errores**: Se registra el error pero no se interrumpe el flujo
- **Advertencia al usuario**: Se incluye una advertencia en la respuesta si no se pudo actualizar Google Calendar

### Ejemplo de Respuesta con Error:
```json
{
  "event_id": "553qlrcqug1p5hrufgku8baecv",
  "attendees": ["Vicente", "Cony"],
  "total_attendees": 2,
  "message": "Usuario 'Cony' agregado exitosamente a la lista de asistentes (Advertencia: No se pudo actualizar Google Calendar: Rate limit exceeded)"
}
```

## 🔧 Funciones Principales

### `update_google_calendar_event_description()`
- **Propósito**: Actualizar la descripción de un evento en Google Calendar
- **Parámetros**: `event_id`, `attendees`, `calendar_id` (opcional)
- **Funcionalidad**: 
  - Obtiene el evento actual
  - Extrae la descripción original
  - Formatea nueva descripción con asistencia
  - Actualiza el evento

### `format_event_description_with_attendance()`
- **Propósito**: Formatear descripción con información de asistencia
- **Parámetros**: `attendees`, `original_description`, `event_start`
- **Funcionalidad**:
  - Detecta si es evento de todo el día
  - Crea sección de asistencia formateada
  - Combina con descripción original

### `extract_original_description()`
- **Propósito**: Extraer descripción original sin sección de asistencia
- **Funcionalidad**: Separa la descripción original de la sección de asistencia

## 📊 Consideraciones Técnicas

### Rate Limiting:
- Google Calendar API tiene límites de requests por minuto
- Se implementa manejo de errores para evitar fallos por rate limiting

### Concurrencia:
- Múltiples confirmaciones simultáneas se manejan correctamente
- MongoDB se actualiza primero, luego Google Calendar

### Eventos de Todo el Día:
- Se detectan automáticamente por el formato `date` vs `dateTime`
- Se muestran con icono 📅 en lugar de ⏰

## 🚀 Beneficios

1. **Sincronización automática**: No requiere intervención manual
2. **Información actualizada**: Los usuarios ven la lista de asistentes en tiempo real
3. **Robustez**: Funciona aunque falle Google Calendar
4. **Flexibilidad**: Mantiene la descripción original del evento
5. **Transparencia**: Muestra cuándo fue la última actualización

## 🔍 Testing

### Endpoints Probados:
- ✅ `POST /asistir`: Confirma asistencia y actualiza Google Calendar
- ✅ `DELETE /asistencia/{event_id}/{user_name}`: Cancela asistencia y actualiza Google Calendar
- ✅ `GET /asistencia/{event_id}`: Consulta lista de asistentes

### Casos de Prueba:
- ✅ Confirmar asistencia de nuevo usuario
- ✅ Cancelar asistencia existente
- ✅ Manejo de errores de Google Calendar
- ✅ Preservación de descripción original
- ✅ Formato correcto para eventos de todo el día
