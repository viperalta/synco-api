"""
Utilidades para formatear eventos de Google Calendar con información de asistencia
"""
from datetime import datetime
from typing import List, Dict, Optional


def format_event_description_with_attendance(
    attendees: List[str], 
    original_description: str = "",
    event_start: Optional[Dict] = None
) -> str:
    """
    Formatear la descripción del evento con información de asistencia
    
    Args:
        attendees: Lista de nombres de asistentes
        original_description: Descripción original del evento
        event_start: Información de inicio del evento (para detectar si es todo el día)
    
    Returns:
        Descripción formateada con información de asistencia
    """
    # Detectar si es evento de todo el día
    is_all_day = False
    if event_start and 'date' in event_start and 'dateTime' not in event_start:
        is_all_day = True
    
    # Crear sección de asistencia
    attendance_section = create_attendance_section(attendees, is_all_day)
    
    # Combinar con descripción original
    if original_description and original_description.strip():
        # Separar descripción original de sección de asistencia si ya existe
        lines = original_description.split('\n')
        filtered_lines = []
        in_attendance_section = False
        
        for line in lines:
            if line.strip().startswith('--- ASISTENCIA ---'):
                in_attendance_section = True
                break
            elif not in_attendance_section:
                filtered_lines.append(line)
        
        original_desc_clean = '\n'.join(filtered_lines).strip()
        if original_desc_clean:
            return f"{original_desc_clean}\n\n{attendance_section}"
        else:
            return attendance_section
    else:
        return attendance_section


def create_attendance_section(attendees: List[str], is_all_day: bool = False) -> str:
    """
    Crear la sección de asistencia para la descripción del evento
    
    Args:
        attendees: Lista de nombres de asistentes
        is_all_day: Si el evento es de todo el día
    
    Returns:
        Sección de asistencia formateada
    """
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    total_attendees = len(attendees)
    
    # Header de la sección
    section = "--- ASISTENCIA ---\n"
    
    # Información básica
    if is_all_day:
        section += f"📅 Evento de todo el día\n"
    else:
        section += f"⏰ Evento con horario específico\n"
    
    section += f"👥 Total de asistentes: {total_attendees}\n"
    section += f"🕒 Última actualización: {current_time}\n\n"
    
    # Lista de asistentes
    if attendees:
        section += "✅ ASISTENTES CONFIRMADOS:\n"
        for i, attendee in enumerate(attendees, 1):
            section += f"{i}. {attendee}\n"
    else:
        section += "❌ No hay asistentes confirmados aún\n"
    
    return section


def extract_original_description(event_description: str) -> str:
    """
    Extraer la descripción original del evento sin la sección de asistencia
    
    Args:
        event_description: Descripción completa del evento
    
    Returns:
        Descripción original sin sección de asistencia
    """
    if not event_description:
        return ""
    
    lines = event_description.split('\n')
    original_lines = []
    
    for line in lines:
        if line.strip().startswith('--- ASISTENCIA ---'):
            break
        original_lines.append(line)
    
    return '\n'.join(original_lines).strip()


def parse_attendance_from_description(event_description: str) -> List[str]:
    """
    Extraer lista de asistentes desde la descripción del evento
    
    Args:
        event_description: Descripción del evento
    
    Returns:
        Lista de nombres de asistentes
    """
    if not event_description:
        return []
    
    attendees = []
    lines = event_description.split('\n')
    in_attendance_section = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('--- ASISTENCIA ---'):
            in_attendance_section = True
            continue
        
        if in_attendance_section and line.startswith('✅ ASISTENTES CONFIRMADOS:'):
            continue
        
        if in_attendance_section and line and not line.startswith('📅') and not line.startswith('⏰') and not line.startswith('👥') and not line.startswith('🕒') and not line.startswith('❌'):
            # Es una línea de asistente (formato: "1. Nombre" o "Nombre")
            if '. ' in line:
                attendee = line.split('. ', 1)[1].strip()
            else:
                attendee = line.strip()
            
            if attendee and attendee not in ['--- ASISTENCIA ---']:
                attendees.append(attendee)
    
    return attendees


def is_all_day_event(event_start: Dict) -> bool:
    """
    Determinar si un evento es de todo el día
    
    Args:
        event_start: Información de inicio del evento
    
    Returns:
        True si es evento de todo el día, False en caso contrario
    """
    return 'date' in event_start and 'dateTime' not in event_start
