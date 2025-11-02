# Endpoint: GET /player/debt/{period}

## Descripción
Permite a un jugador autenticado consultar su deuda personal para un período específico. El jugador solo puede ver su propia deuda.

## Método HTTP
**GET**

## URL
```
/player/debt/{period}
```

Donde `{period}` es el período en formato YYYYMM (ej: 202510 = octubre 2025)

## Autenticación
Requiere token JWT de autenticación en el header `Authorization`.

### Headers Requeridos
```
Authorization: Bearer <tu_access_token>
```

## Permisos
Cualquier usuario autenticado puede acceder a este endpoint para consultar su propia deuda.

## Parámetros de URL

| Parámetro | Tipo | Ubicación | Descripción | Formato |
|-----------|------|-----------|-------------|---------|
| `period` | string | Path | Período en formato YYYYMM | 6 dígitos, año 2000-2100, mes 01-12 |

### Ejemplos de URL
- `GET /player/debt/202510` → Octubre 2025
- `GET /player/debt/202311` → Noviembre 2023
- `GET /player/debt/202412` → Diciembre 2024

## Estructura de la Respuesta

### Respuesta Exitosa (200)

```json
{
  "period": "202510",
  "amount": 15000,
  "user_name": "Juan Pérez",
  "user_nickname": "Juancho"
}
```

### Campos de Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `period` | string | Período consultado (YYYYMM) |
| `amount` | float | Monto de la deuda del jugador para ese período |
| `user_name` | string | Nombre completo del jugador |
| `user_nickname` | string \| null | Apodo del jugador (opcional) |

### Ejemplo 1: Con nickname
```json
{
  "period": "202510",
  "amount": 15000,
  "user_name": "Juan Pérez",
  "user_nickname": "Juancho"
}
```

### Ejemplo 2: Sin nickname
```json
{
  "period": "202510",
  "amount": 12000,
  "user_name": "María García",
  "user_nickname": null
}
```

## Respuestas de Error

### 404: No tiene deuda para ese período
```json
{
  "detail": "No tienes deuda registrada para este período"
}
```

Esto ocurre cuando:
- El jugador no está en la lista de deudores de ese período
- No existe ningún registro de deuda para ese período

### 400: Formato de período inválido
```json
{
  "detail": "Formato de período inválido. Debe ser YYYYMM (ej: 202510)"
}
```

### 401: No autenticado
```json
{
  "detail": "No autenticado"
}
```

### 500: Error interno
```json
{
  "detail": "Error obteniendo tu deuda: [mensaje de error]"
}
```

## Códigos de Respuesta HTTP

| Código | Descripción |
|--------|-------------|
| 200 | ✅ Deuda obtenida exitosamente |
| 400 | ❌ Formato de período inválido |
| 401 | ❌ No autenticado (token inválido o faltante) |
| 404 | ❌ No tiene deuda registrada para ese período |
| 500 | ❌ Error interno del servidor |

## Cómo Funciona

1. El jugador envía un GET con el período deseado
2. El servidor extrae el `user_id` del token JWT
3. Busca el registro de deuda para ese período
4. Busca al jugador en la lista de deudores de ese período
5. Devuelve los datos del jugador si está en la lista

### Lógica del Backend
```
1. Autenticar usuario (extraer user_id del token)
2. Validar formato del período (YYYYMM)
3. Buscar deuda del período
4. Si existe deuda:
   - Buscar al usuario en la lista de deudores
   - Si está en la lista → Devolver sus datos
   - Si NO está en la lista → 404
5. Si NO existe deuda del período → 404
```

## Ejemplos de Uso con cURL

### Ejemplo 1: Consultar deuda básica
```bash
curl 'http://localhost:8000/player/debt/202510' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

### Ejemplo 2: Con formato completo
```bash
curl -X GET 'http://localhost:8000/player/debt/202510' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer TU_TOKEN_AQUI' \
  -H 'Content-Type: application/json'
```

### Ejemplo 3: Diferentes períodos
```bash
# Octubre 2025
curl 'http://localhost:8000/player/debt/202510' \
  -H 'Authorization: Bearer TU_TOKEN'

# Noviembre 2025
curl 'http://localhost:8000/player/debt/202511' \
  -H 'Authorization: Bearer TU_TOKEN'

# Diciembre 2025
curl 'http://localhost:8000/player/debt/202512' \
  -H 'Authorization: Bearer TU_TOKEN'
```

## Ejemplo con JavaScript/Fetch

```javascript
async function getMyDebt(period) {
  const response = await fetch(
    `http://localhost:8000/player/debt/${period}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    if (response.status === 404) {
      console.log('No tengo deuda para este período');
      return null;
    }
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// Uso
const myDebt = await getMyDebt('202510');
if (myDebt) {
  console.log(`Debo: ${myDebt.amount}`);
  console.log(`Período: ${myDebt.period}`);
  console.log(`Nombre: ${myDebt.user_name}`);
}
```

## Ejemplo con React

```javascript
import { useState, useEffect } from 'react';

function MyDebt({ period, token }) {
  const [debt, setDebt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDebt() {
      try {
        const response = await fetch(
          `http://localhost:8000/player/debt/${period}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (!response.ok) {
          if (response.status === 404) {
            setDebt(null);
            setError('No tienes deuda para este período');
            return;
          }
          throw new Error('Error al obtener deuda');
        }

        const data = await response.json();
        setDebt(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDebt();
  }, [period, token]);

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!debt) return <div>No tienes deuda registrada para {period}</div>;

  return (
    <div>
      <h2>Mi Deuda - {debt.period}</h2>
      <p>Período: {debt.period}</p>
      <p>Monto: ${debt.amount.toLocaleString()}</p>
      <p>Nombre: {debt.user_name}</p>
      {debt.user_nickname && (
        <p>Apodo: {debt.user_nickname}</p>
      )}
    </div>
  );
}
```

## Casos de Uso

### 1. Consultar mi deuda del mes actual
```bash
curl 'http://localhost:8000/player/debt/202510' \
  -H 'Authorization: Bearer TOKEN'
```

### 2. Verificar deuda de un período pasado
```bash
curl 'http://localhost:8000/player/debt/202309' \
  -H 'Authorization: Bearer TOKEN'
```

### 3. Consultar deuda de un mes futuro (si ya fue registrada)
```bash
curl 'http://localhost:8000/player/debt/202512' \
  -H 'Authorization: Bearer TOKEN'
```

## Flujo de Trabajo Típico

```
1. Usuario abre la app
2. Selector de período (dropdown)
3. Selecciona "Octubre 2025" (202510)
4. App hace GET /player/debt/202510
5. Servidor devuelve:
   - period: "202510"
   - amount: 15000
   - user_name: "Juan Pérez"
   - user_nickname: "Juancho"
6. App muestra: "Debes $15,000 de Octubre 2025"
```

## Validaciones

### Formato de Período
- Debe ser exactamente 6 dígitos
- Formato: YYYYMM
- Año entre 2000 y 2100
- Mes entre 01 y 12

**Ejemplos válidos:**
- `202510` → Octubre 2025
- `202312` → Diciembre 2023
- `202501` → Enero 2025

**Ejemplos inválidos:**
- `2510` → Solo 4 dígitos
- `202500` → Mes 00 no existe
- `202513` → Mes 13 no existe

## Seguridad

### Lo que el endpoint garantiza:

✅ **Solo puedes ver tu propia deuda**
- El servidor extrae tu `user_id` del token JWT
- Solo te devuelve la información si estás en la lista de deudores

✅ **No puedes ver deudas de otros jugadores**
- Aunque conozcas el período, solo ves tu deuda
- No hay forma de ver las deudas de otros

✅ **Autenticación obligatoria**
- Requiere token JWT válido
- Sin token → 401 Unauthorized

### Lo que el endpoint NO hace:

❌ No permite ver todas las deudas del período
❌ No permite ver deudas de otros jugadores
❌ No permite modificar deudas (solo lectura)

## Diferencias con Otros Endpoints

| Endpoint | Quién puede usarlo | Qué devuelve |
|----------|-------------------|--------------|
| `GET /player/debt/{period}` | Jugador (cualquier usuario autenticado) | Deuda personal del jugador |
| `GET /admin/debts/{period}` | Solo administradores | Todas las deudas del período (todos los jugadores) |
| `GET /admin/debts` | Solo administradores | Todas las deudas de todos los períodos |

## Notas Importantes

1. **Solo tu deuda**: Este endpoint solo devuelve la deuda del usuario autenticado
2. **Seguridad**: El `user_id` se extrae automáticamente del token JWT
3. **404 normal**: Recibir 404 es normal si el admin aún no ha registrado deudas para ese período
4. **Período flexible**: Puedes consultar cualquier período (pasado, presente o futuro)
5. **Nickname opcional**: El campo `user_nickname` puede ser null

## Integración con el Sistema de Pagos

Este endpoint se usa típicamente junto con el sistema de pagos:

```
1. Jugador consulta su deuda: GET /player/debt/202510
2. Ve que debe $15,000
3. Registra un pago: POST /payments
4. Sube comprobante: POST /payments/{payment_id}/upload-url
5. Admin verifica el pago: PUT /admin/payments/{payment_id}/verify
```

## Endpoints Relacionados

- `GET /admin/debts/{period}` - Ver todas las deudas de un período (admin)
- `GET /admin/debts` - Listar todas las deudas (admin)
- `POST /payments` - Registrar un pago (jugador)
- `GET /payments` - Ver mis pagos (jugador)

## Troubleshooting

### Pregunta: ¿Por qué recibo 404?
**Respuesta**: No tienes deuda registrada para ese período. El admin debe crear el registro primero con POST /admin/debts.

### Pregunta: ¿Por qué veo 401?
**Respuesta**: Tu token JWT expiró o es inválido. Debes iniciar sesión de nuevo.

### Pregunta: ¿Puedo ver la deuda de otros jugadores?
**Respuesta**: No. Este endpoint solo devuelve TU deuda personal.

### Pregunta: ¿Qué pasa si el admin me agrega con un user_id incorrecto?
**Respuesta**: No aparecerás en los resultados. El admin debe usar tu `user_id` correcto.

