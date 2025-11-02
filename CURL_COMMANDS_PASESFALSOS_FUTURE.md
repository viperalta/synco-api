# Comandos curl para configurar webhooks en api.pasesfalsos.cl

## 🔧 Variables de Entorno Necesarias

Agrega estas variables en Vercel (opcionales pero recomendadas):

```bash
# URL base de tu API (ya configurada por defecto)
WEBHOOK_BASE_URL=https://api.pasesfalsos.cl

# Token de seguridad para webhooks (opcional)
WEBHOOK_TOKEN=pasesfalsos-webhook-token

# Token de seguridad para cron jobs (opcional)
CRON_TOKEN=pasesfalsos-cron-token
```

## 🚀 Comandos curl para Producción

### 1. Configurar Watch Inicial (Calendario Principal)

```bash
curl -X POST "https://api.pasesfalsos.cl/webhook/setup-watch?calendar_id=primary" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 2. Configurar Watch para Calendario Específico

```bash
# Reemplaza CALENDAR_ID con el ID de tu calendario específico
curl -X POST "https://api.pasesfalsos.cl/webhook/setup-watch?calendar_id=CALENDAR_ID" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Verificar Estado del Watch

```bash
curl -X GET "https://api.pasesfalsos.cl/webhook/watch-info" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

### 4. Renovar Watch Manualmente

```bash
curl -X POST "https://api.pasesfalsos.cl/webhook/renew-watch?calendar_id=primary" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 5. Probar Cron Job Manualmente

```bash
curl -X POST "https://api.pasesfalsos.cl/webhook/cron-renew" \
  -H "Content-Type: application/json"
```

## 🧪 Comandos de Prueba

### Probar Webhook Endpoint

```bash
curl -X POST "https://api.pasesfalsos.cl/webhook/google-calendar" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceId": "test-resource-id",
    "resourceUri": "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch",
    "eventType": "sync",
    "token": "pasesfalsos-webhook-token"
  }'
```

### Verificar Salud de la API

```bash
curl -X GET "https://api.pasesfalsos.cl/health"
```

### Verificar Variables de Entorno

```bash
curl -X GET "https://api.pasesfalsos.cl/debug/env"
```

## 📋 Pasos para Activar el Sistema

### 1. Desplegar Código Actualizado

```bash
# Hacer commit de los cambios
git add .
git commit -m "Configure webhook system for api.pasesfalsos.cl"
git push origin main

# Desplegar en Vercel
vercel --prod
```

### 2. Configurar Variables de Entorno (Opcional)

En el dashboard de Vercel, agrega:
- `WEBHOOK_TOKEN=pasesfalsos-webhook-token`
- `CRON_TOKEN=pasesfalsos-cron-token`

### 3. Configurar Watch Inicial

```bash
# Obtener token de acceso primero (usando tu sistema de auth)
# Luego ejecutar:
curl -X POST "https://api.pasesfalsos.cl/webhook/setup-watch?calendar_id=primary" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 4. Verificar Configuración

```bash
curl -X GET "https://api.pasesfalsos.cl/webhook/watch-info" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

## 🔄 Cron Job Automático

El cron job está configurado para ejecutarse **diariamente a las 9:00 AM UTC** y renovar automáticamente el watch.

**Endpoint del cron**: `https://api.pasesfalsos.cl/webhook/cron-renew`

## 📊 Monitoreo

### Verificar Estado del Sistema

```bash
# Estado general
curl -X GET "https://api.pasesfalsos.cl/health"

# Información del webhook
curl -X GET "https://api.pasesfalsos.cl/webhook/watch-info" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"

# Variables de entorno
curl -X GET "https://api.pasesfalsos.cl/debug/env"
```

### Verificar Eventos Sincronizados

```bash
# Obtener eventos del calendario
curl -X GET "https://api.pasesfalsos.cl/eventos" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

## 🐛 Troubleshooting

### Si el watch no se configura:

1. Verificar que tienes permisos de administrador
2. Verificar que las credenciales de Google Calendar están configuradas
3. Revisar logs de Vercel

### Si las notificaciones no llegan:

1. Verificar que el endpoint está desplegado
2. Verificar que Google puede acceder a `https://api.pasesfalsos.cl/webhook/google-calendar`
3. Revisar logs de Google Calendar API

### Si el cron job no ejecuta:

1. Verificar que tienes plan Pro de Vercel (cron jobs requieren plan de pago)
2. Verificar configuración en `vercel.json`
3. Revisar logs de Vercel cron

## ✅ Checklist de Activación

- [ ] Código desplegado en Vercel
- [ ] Variables de entorno configuradas (opcional)
- [ ] Watch inicial configurado
- [ ] Estado del watch verificado
- [ ] Cron job funcionando (verificar después de 24 horas)
- [ ] Notificaciones llegando (crear evento de prueba)

## 🎯 Resultado Esperado

Una vez configurado correctamente:

1. **Google Calendar** enviará notificaciones a `https://api.pasesfalsos.cl/webhook/google-calendar`
2. **Los eventos** se sincronizarán automáticamente con MongoDB
3. **El watch** se renovará automáticamente cada día a las 9:00 AM UTC
4. **Los eventos** estarán disponibles en los endpoints existentes de tu API
