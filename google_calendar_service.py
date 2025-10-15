"""
Servicio para interactuar con Google Calendar API
"""
import os
import pickle
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autenticar con Google Calendar API"""
        creds = None
        
        # Cargar credenciales existentes (admite pickle o JSON)
        if os.path.exists(self.token_file):
            # Intentar cargar como pickle primero
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                # Si no es pickle, intentar como JSON autorizado de usuario
                try:
                    from google.oauth2.credentials import Credentials
                    creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
                except Exception as e:
                    raise Exception(
                        f"No se pudo cargar el token desde '{self.token_file}' como pickle ni JSON: {e}"
                    )
        
        # Si no hay credenciales válidas, hacer el flujo de OAuth
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Archivo de credenciales no encontrado: {self.credentials_file}\n"
                        "Por favor, descarga el archivo credentials.json desde Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=8080)
            
            # Guardar credenciales para la próxima vez (en entorno efímero está bien)
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception:
                # En entornos sin permiso de escritura, continuar sin bloquear
                logger.warning("No se pudieron persistir las credenciales en token_file; se continuará en memoria.")
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Autenticación con Google Calendar exitosa")
        except Exception as e:
            logger.error(f"Error al autenticar con Google Calendar: {e}")
            raise
    
    
    
    def list_calendars(self) -> List[Dict]:
        """Obtener lista de calendarios disponibles"""
        try:
            if not self.service:
                raise Exception("Servicio de Google Calendar no inicializado")
            
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            formatted_calendars = []
            for calendar in calendars:
                formatted_calendar = {
                    'id': calendar.get('id'),
                    'summary': calendar.get('summary'),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'accessRole': calendar.get('accessRole', ''),
                    'backgroundColor': calendar.get('backgroundColor', ''),
                    'foregroundColor': calendar.get('foregroundColor', '')
                }
                formatted_calendars.append(formatted_calendar)
            
            return formatted_calendars
            
        except HttpError as error:
            logger.error(f"Error al obtener calendarios: {error}")
            raise Exception(f"Error al obtener calendarios: {error}")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            raise
    
    def get_events(self, calendar_id: str = 'primary', max_results: int = 30, 
                   time_min: Optional[datetime] = None, time_max: Optional[datetime] = None) -> List[Dict]:
        """
        Obtener eventos de un calendario específico
        
        Args:
            calendar_id: ID del calendario (por defecto 'primary')
            max_results: Número máximo de eventos a retornar
            time_min: Fecha/hora mínima para buscar eventos
            time_max: Fecha/hora máxima para buscar eventos
        
        Returns:
            Lista de eventos
        """
        try:
            if not self.service:
                raise Exception("Servicio de Google Calendar no inicializado")
            
            # Configurar parámetros de tiempo
            if time_min is None:
                time_min = datetime.utcnow()
            if time_max is None:
                time_max = time_min + timedelta(days=30)
            
            # Convertir a formato RFC3339
            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z'
            
            # Obtener eventos
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Formatear eventos para respuesta
            formatted_events = []
            for event in events:
                formatted_event = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'Sin título'),
                    'description': event.get('description', ''),
                    'start': event.get('start', {}),
                    'end': event.get('end', {}),
                    'location': event.get('location', ''),
                    'status': event.get('status', ''),
                    'htmlLink': event.get('htmlLink', ''),
                    'created': event.get('created', ''),
                    'updated': event.get('updated', '')
                }
                formatted_events.append(formatted_event)
            
            logger.info(f"Obtenidos {len(formatted_events)} eventos del calendario {calendar_id}")
            return formatted_events
            
        except HttpError as error:
            logger.error(f"Error de Google Calendar API: {error}")
            raise Exception(f"Error al obtener eventos: {error}")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            raise
