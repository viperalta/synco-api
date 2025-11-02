# Cambios Realizados en el Sistema de Deudas

## ✅ Problemas Corregidos

### 1. Error 500 con `object AsyncIOMotorDatabase can't be used in 'await' expression`

**Problema**: El método `get_database()` de `mongodb_config` no es async, pero se estaba usando con `await`.

**Solución**: Corregido en `debt_service.py`, línea 244-252:
```python
async def get_debt_service() -> DebtService:
    """Obtener instancia del servicio de deudas"""
    global debt_service
    if debt_service is None:
        from mongodb_config import mongodb_config
        # Conectar MongoDB si no está conectado
        if mongodb_config.database is None:
            await mongodb_config.connect()
        debt_service = DebtService(mongodb_config.get_database())  # SIN await
    return debt_service
```

### 2. Error "Ya existe una deuda para el período"

**Problema**: El endpoint POST devolvía error si ya existía una deuda para ese período.

**Solución**: Cambiado el comportamiento para que haga **upsert** (actualiza si existe, crea si no existe). 

Ahora el método `create_debt()` en `debt_service.py` (líneas 17-57):
- Si existe: actualiza la deuda existente
- Si no existe: crea una nueva deuda

## 📝 Nuevo Comportamiento del POST /admin/debts

### Antes:
- ✅ Si el período NO existe → Crea nueva deuda
- ❌ Si el período YA existe → Error 400

### Ahora:
- ✅ Si el período NO existe → Crea nueva deuda
- ✅ Si el período YA existe → **Sobrescribe** la deuda existente

## 🔄 Cómo Funciona Ahora

Cuando envías un POST con el mismo período:

1. El endpoint detecta que ya existe una deuda para ese período
2. Actualiza los deudores con los nuevos datos
3. Actualiza el timestamp `updated_at`
4. Mantiene el mismo `created_at`
5. Devuelve la deuda actualizada

## 🚀 Reinicia el Servidor

**IMPORTANTE**: Para que los cambios tengan efecto, necesitas reiniciar el servidor de FastAPI:

```bash
# Si está corriendo, detén el proceso (Ctrl+C)
# Luego inicia de nuevo:
uvicorn main:app --reload
```

## 📋 Endpoints Actualizados

### POST /admin/debts
- Ahora funciona como **upsert**
- Siempre devuelve la deuda (creada o actualizada)
- No genera error si ya existe

### GET /admin/debts
- Lista todas las deudas con paginación
- Ordenadas por período descendente

### GET /admin/debts/{period}
- Obtiene una deuda específica
- Retorna 404 si no existe

### PUT /admin/debts/{period}
- Actualiza una deuda específica
- Requiere que ya exista

### DELETE /admin/debts/{period}
- Elimina una deuda específica
- Retorna 404 si no existe

## 🧪 Para Probar

Usa tu curl original (ahora funcionará):

```bash
curl 'http://localhost:8000/admin/debts' \
  -H 'Authorization: Bearer TU_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"period":"202510","debtors":[{"user_id":"68f410378788f0d19918bbd4","user_name":"Vicente Peralta","user_nickname":"PH Vicho","amount":45000},{"user_id":"68f3fee7c7c5e564146eef4d","user_name":"Vicente Peralta","user_nickname":"Vicho","amount":2000}]}'
```

Este comando ahora:
- ✅ Creará la deuda si no existe
- ✅ Sobrescribirá la deuda si ya existe
- ✅ Siempre devolverá éxito (200)

## 📝 Archivos Modificados

1. **debt_service.py**
   - Línea 17-57: Método `create_debt()` ahora hace upsert
   - Línea 244-252: Corregido `get_debt_service()` para no usar await incorrectamente

2. **POST_ADMIN_DEBTS_ENDPOINT.md**
   - Actualizado para reflejar el nuevo comportamiento de sobrescritura
   - Documentación del comportamiento upsert

## ✨ Beneficios

1. **Más flexible**: No necesitas verificar si existe antes de crear
2. **Más simple**: Desde el frontend solo envías el POST
3. **Más seguro**: Evita duplicados accidentales
4. **Mejor UX**: El admin siempre puede actualizar desde el mismo formulario

