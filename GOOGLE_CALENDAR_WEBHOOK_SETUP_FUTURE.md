# Configuración de Webhooks de Google Calendar

Este documento explica cómo configurar y usar el sistema de webhooks de Google Calendar para recibir notificaciones automáticas cuando se crean, modifican o eliminan eventos.

## 📋 Resumen de la Implementación

Se ha implementado un sistema completo de webhooks que incluye:

1. **Servicio de Webhook** (`google_webhook_service.py`) - Maneja la configuración y procesamiento de webhooks
2. **Endpoints de API** - Para configurar, renovar y recibir notificaciones
3. **Cron Job Automático** - Renueva el watch diariamente a las 9:00 AM
4. **Persistencia en MongoDB** - Los eventos se sincronizan automáticamente

## 🔧 Variables de Entorno Requeridas

Agrega estas variables de entorno en Vercel:

```bash
# URL base de tu API (reemplaza con tu dominio de Vercel)
WEBHOOK_BASE_URL=https://tu-proyecto.vercel.app

# Token opcional para seguridad del webhook
WEBHOOK_TOKEN=tu-token-secreto-webhook

# Token opcional para seguridad del cron job
CRON_TOKEN=tu-token-secreto-cron

# Las variables existentes de Google Calendar
GOOGLE_CREDENTIALS_JSON=...
GOOGLE_TOKEN_JSON=...
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar
```

## 🚀 Pasos para Configurar

### 1. Desplegar la API

```bash
# Hacer commit de los cambios
git add .
git commit -m "Add Google Calendar webhook system"
git push origin main

# Desplegar en Vercel
vercel --prod
```

### 2. Configurar el Watch Inicial

Una vez desplegado, configura el watch inicial usando el endpoint de administración:

```bash
# POST a /webhook/setup-watch
curl -X POST "https://tu-proyecto.vercel.app/webhook/setup-watch?calendar_id=primary" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Verificar la Configuración

```bash
# GET a /webhook/watch-info
curl -X GET "https://tu-proyecto.vercel.app/webhook/watch-info" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

## 📡 Endpoints Disponibles

### `/webhook/google-calendar` (POST)
- **Propósito**: Recibe notificaciones de Google Calendar
- **Autenticación**: Token de webhook (opcional)
- **Uso**: Llamado automáticamente por Google

### `/webhook/setup-watch` (POST)
- **Propósito**: Configurar watch para un calendario
- **Autenticación**: Requiere admin
- **Parámetros**: `calendar_id` (query param)

### `/webhook/watch-info` (GET)
- **Propósito**: Obtener información del watch actual
- **Autenticación**: Requiere admin

### `/webhook/renew-watch` (POST)
- **Propósito**: Renovar watch manualmente
- **Autenticación**: Requiere admin
- **Parámetros**: `calendar_id` (query param)

### `/webhook/cron-renew` (POST)
- **Propósito**: Renovar watch automáticamente (cron job)
- **Autenticación**: Ninguna (llamado por Vercel)
- **Programación**: Diario a las 9:00 AM UTC

## ⏰ Cron Job Automático

El cron job está configurado en `vercel.json` para ejecutarse diariamente:

```json
{
  "crons": [
    {
      "path": "/webhook/cron-renew",
      "schedule": "0 9 * * *"
    }
  ]
}
```

**Horario**: Todos los días a las 9:00 AM UTC
**Acción**: Renueva automáticamente el watch de Google Calendar

## 🔄 Flujo de Funcionamiento

1. **Configuración Inicial**:
   - Se configura un watch en Google Calendar
   - Google envía notificaciones a `/webhook/google-calendar`

2. **Recepción de Notificaciones**:
   - Google envía POST con datos del cambio
   - El sistema procesa la notificación
   - Se sincronizan los eventos con MongoDB

3. **Renovación Automática**:
   - Cron job ejecuta `/webhook/cron-renew` diariamente
   - Se detiene el watch anterior
   - Se configura un nuevo watch

## 📊 Tipos de Notificaciones

El sistema maneja estos tipos de eventos:

- **`sync`**: Sincronización inicial o completa
- **`create`**: Nuevo evento creado
- **`update`**: Evento modificado
- **`delete`**: Evento eliminado

## 🗄️ Persistencia en MongoDB

Los eventos se guardan en la colección `calendar_events` con esta estructura:

```json
{
  "_id": "ObjectId",
  "google_event_id": "string",
  "summary": "string",
  "description": "string",
  "start_datetime": "ISO datetime",
  "end_datetime": "ISO datetime",
  "location": "string",
  "status": "string",
  "html_link": "string",
  "is_all_day": "boolean",
  "calendar_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 🔒 Seguridad

- **Token de Webhook**: Opcional pero recomendado para validar notificaciones
- **Autenticación Admin**: Requerida para configurar/renovar watches
- **Token de Cron**: Opcional para validar llamadas del cron job

## 🧪 Pruebas

### Probar el Webhook Manualmente

```bash
# Simular notificación de Google
curl -X POST "https://tu-proyecto.vercel.app/webhook/google-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceId": "test-resource-id",
    "resourceUri": "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch",
    "eventType": "sync",
    "token": "tu-webhook-token"
  }'
```

### Verificar Eventos en MongoDB

```bash
# GET eventos sincronizados
curl -X GET "https://tu-proyecto.vercel.app/eventos" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Watch no se configura**:
   - Verificar credenciales de Google Calendar
   - Verificar permisos de administrador
   - Revisar logs de Vercel

2. **Notificaciones no llegan**:
   - Verificar URL del webhook en Vercel
   - Verificar que el endpoint esté desplegado
   - Revisar logs de Google Calendar API

3. **Cron job no ejecuta**:
   - Verificar configuración en `vercel.json`
   - Verificar que el proyecto esté en plan Pro de Vercel
   - Revisar logs de Vercel cron

### Logs Importantes

```bash
# Ver logs de Vercel
vercel logs

# Ver logs específicos del webhook
vercel logs --filter="webhook"
```

## 📈 Monitoreo

### Métricas a Monitorear

- **Frecuencia de notificaciones**: ¿Llegan las notificaciones?
- **Tiempo de procesamiento**: ¿Se procesan rápidamente?
- **Errores de sincronización**: ¿Hay eventos que no se sincronizan?
- **Renovación del watch**: ¿Se renueva automáticamente?

### Alertas Recomendadas

- Watch expirado por más de 25 horas
- Errores frecuentes en procesamiento de webhooks
- Falta de notificaciones por más de 2 días

## 🔄 Mantenimiento

### Tareas Regulares

1. **Verificar estado del watch** (semanal)
2. **Revisar logs de errores** (diario)
3. **Monitorear métricas de sincronización** (diario)
4. **Actualizar tokens si es necesario** (según expiración)

### Limpieza de Datos

```bash
# Eliminar eventos antiguos (opcional)
# Implementar limpieza automática de eventos > 1 año
```

## 📚 Referencias

- [Google Calendar API - Push Notifications](https://developers.google.com/calendar/api/guides/push)
- [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)
- [FastAPI Webhooks](https://fastapi.tiangolo.com/tutorial/request-files/)

## ✅ Checklist de Implementación

- [x] Servicio de webhook creado
- [x] Endpoints de API implementados
- [x] Cron job configurado en vercel.json
- [x] Persistencia en MongoDB implementada
- [x] Documentación completa
- [ ] Variables de entorno configuradas en Vercel
- [ ] Watch inicial configurado
- [ ] Pruebas realizadas
- [ ] Monitoreo configurado
