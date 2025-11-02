# API de Pagos - Ejemplos de Uso

## Resumen
Esta documentación proporciona ejemplos prácticos de cómo usar la API de pagos implementada, incluyendo la subida de comprobantes a S3.

## Endpoints Disponibles

### 1. Crear Pago
**POST** `/payments`

```json
{
    "amount": 50000,
    "period": "202510",
    "payment_date": "2025-01-15T10:30:00Z",
    "notes": "Pago mensual enero 2025"
}
```

**Respuesta:**
```json
{
    "id": "507f1f77bcf86cd799439011",
    "user_id": "user123",
    "amount": 50000,
    "period": "202510",
    "payment_date": "2025-01-15T10:30:00Z",
    "receipt_image_url": null,
    "status": "pending",
    "notes": "Pago mensual enero 2025",
    "verified_by": null,
    "verified_at": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
}
```

### 2. Obtener Pagos del Usuario
**GET** `/payments?skip=0&limit=10`

**Respuesta:**
```json
{
    "payments": [
        {
            "id": "507f1f77bcf86cd799439011",
            "user_id": "user123",
            "amount": 50000,
            "period": "202510",
            "payment_date": "2025-01-15T10:30:00Z",
            "receipt_image_url": "https://s3.amazonaws.com/bucket/file.jpg",
            "status": "verified",
            "notes": "Pago mensual enero 2025",
            "verified_by": "admin123",
            "verified_at": "2025-01-15T11:00:00Z",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T11:00:00Z"
        }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
}
```

### 3. Obtener Pagos por Período
**GET** `/payments/period/202510`

### 4. Subir Comprobante (Flujo Completo)

#### Paso 1: Obtener URL de Subida
**POST** `/payments/{payment_id}/upload-url?file_extension=jpg&expires_in=3600`

**Respuesta:**
```json
{
    "upload_url": "https://s3.amazonaws.com/bucket/file.jpg?AWSAccessKeyId=...",
    "file_key": "payment-receipts/user123/payment_id_20250115_12345678.jpg",
    "expires_in": 3600
}
```

#### Paso 2: Subir Archivo a S3
```javascript
// Frontend - Subir archivo usando la URL prefirmada
const uploadFile = async (file, uploadUrl) => {
    const response = await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: {
            'Content-Type': file.type
        }
    });
    
    if (response.ok) {
        console.log('Archivo subido correctamente');
    }
};
```

#### Paso 3: Confirmar Subida
**POST** `/payments/{payment_id}/confirm-upload`

```json
{
    "file_key": "payment-receipts/user123/payment_id_20250115_12345678.jpg"
}
```

**Respuesta:**
```json
{
    "message": "Comprobante subido correctamente",
    "payment": {
        "id": "507f1f77bcf86cd799439011",
        "user_id": "user123",
        "amount": 50000,
        "period": "202510",
        "payment_date": "2025-01-15T10:30:00Z",
        "receipt_image_url": "https://s3.amazonaws.com/bucket/file.jpg",
        "status": "pending",
        "notes": "Pago mensual enero 2025",
        "verified_by": null,
        "verified_at": null,
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:35:00Z"
    }
}
```

### 5. Descargar Comprobante
**GET** `/payments/{payment_id}/download-url?expires_in=3600`

**Respuesta:**
```json
{
    "download_url": "https://s3.amazonaws.com/bucket/file.jpg?AWSAccessKeyId=...",
    "expires_in": 3600
}
```

### 6. Verificar Pago (Solo Administradores)
**PUT** `/admin/payments/{payment_id}/verify`

```json
{
    "status": "verified",
    "notes": "Comprobante verificado correctamente"
}
```

### 7. Obtener Estadísticas (Solo Administradores)
**GET** `/admin/payments/statistics?user_id=user123&period=202510`

**Respuesta:**
```json
{
    "total_payments": 5,
    "total_amount": 250000,
    "by_status": {
        "pending": {
            "count": 2,
            "amount": 100000
        },
        "verified": {
            "count": 3,
            "amount": 150000
        }
    }
}
```

## Ejemplos de Código Frontend

### React/JavaScript - Subir Comprobante
```javascript
const uploadReceipt = async (paymentId, file) => {
    try {
        // 1. Obtener URL de subida
        const uploadResponse = await fetch(
            `/api/payments/${paymentId}/upload-url?file_extension=${file.name.split('.').pop()}`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        const { upload_url, file_key } = await uploadResponse.json();
        
        // 2. Subir archivo a S3
        const uploadResult = await fetch(upload_url, {
            method: 'PUT',
            body: file,
            headers: {
                'Content-Type': file.type
            }
        });
        
        if (!uploadResult.ok) {
            throw new Error('Error subiendo archivo');
        }
        
        // 3. Confirmar subida
        const confirmResponse = await fetch(
            `/api/payments/${paymentId}/confirm-upload`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_key })
            }
        );
        
        const result = await confirmResponse.json();
        console.log('Comprobante subido:', result);
        
    } catch (error) {
        console.error('Error:', error);
    }
};
```

### React/JavaScript - Descargar Comprobante
```javascript
const downloadReceipt = async (paymentId) => {
    try {
        const response = await fetch(
            `/api/payments/${paymentId}/download-url`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );
        
        const { download_url } = await response.json();
        
        // Abrir URL de descarga
        window.open(download_url, '_blank');
        
    } catch (error) {
        console.error('Error:', error);
    }
};
```

### React/JavaScript - Listar Pagos
```javascript
const getPayments = async (skip = 0, limit = 10) => {
    try {
        const response = await fetch(
            `/api/payments?skip=${skip}&limit=${limit}`,
            {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );
        
        const data = await response.json();
        return data.payments;
        
    } catch (error) {
        console.error('Error:', error);
        return [];
    }
};
```

## Códigos de Error Comunes

### 400 Bad Request
- Formato de período inválido (debe ser YYYYMM)
- Monto inválido
- Fecha de pago inválida

### 401 Unauthorized
- Token de autenticación inválido o expirado
- Usuario no autenticado

### 403 Forbidden
- Usuario sin permisos de administrador para operaciones admin
- Acceso denegado al recurso

### 404 Not Found
- Pago no encontrado
- Archivo de comprobante no encontrado
- Usuario no encontrado

### 500 Internal Server Error
- Error de conexión con MongoDB
- Error de conexión con S3
- Error interno del servidor

## Consideraciones de Seguridad

### URLs Prefirmadas
- Las URLs tienen tiempo de expiración limitado (máximo 2 horas)
- Solo permiten operaciones específicas (PUT para subida, GET para descarga)
- Incluyen validación de Content-Type

### Validación de Archivos
- Solo se permiten extensiones específicas: jpg, jpeg, png, gif, pdf, doc, docx, txt
- El tamaño del archivo debe ser validado en el frontend
- El Content-Type se valida automáticamente

### Permisos
- Los usuarios solo pueden acceder a sus propios pagos
- Solo los administradores pueden ver todos los pagos
- Solo los administradores pueden verificar pagos

## Testing

### Pruebas con cURL
```bash
# Crear pago
curl -X POST "http://localhost:8000/payments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "period": "202510",
    "payment_date": "2025-01-15T10:30:00Z",
    "notes": "Pago de prueba"
  }'

# Obtener pagos
curl -X GET "http://localhost:8000/payments" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Obtener URL de subida
curl -X POST "http://localhost:8000/payments/PAYMENT_ID/upload-url?file_extension=jpg" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Notas Importantes

1. **Formato de Período**: Siempre usar formato YYYYMM (ej: 202510 para octubre 2025)
2. **Fechas**: Usar formato ISO 8601 para fechas
3. **Autenticación**: Todos los endpoints requieren token de autenticación
4. **Archivos**: Los comprobantes se almacenan en S3 con URLs prefirmadas
5. **Permisos**: Verificar que el usuario tenga los permisos necesarios
6. **Validación**: El frontend debe validar tipos de archivo y tamaños antes de subir
