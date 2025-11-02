# Configuración de Amazon S3 para Sistema de Pagos

## Resumen
Este documento explica cómo configurar un bucket privado de Amazon S3 para almacenar comprobantes de pagos de forma segura, utilizando URLs prefirmadas para subida y descarga de archivos.

## 1. Crear Bucket S3

### 1.1 Crear el Bucket
1. Accede a la consola de AWS S3
2. Haz clic en "Create bucket"
3. Configura el bucket con los siguientes parámetros:

**Configuración básica:**
- **Bucket name**: `synco-payment-receipts` (o el nombre que prefieras)
- **Region**: Selecciona la región más cercana a tus usuarios (ej: `us-east-1`, `us-west-2`, `eu-west-1`)

**Configuración de objetos:**
- **Versioning**: Deshabilitado (a menos que necesites versionado)
- **Server-side encryption**: Habilitado con AES-256

**Configuración de permisos:**
- **Block Public Access**: **HABILITADO** (muy importante para seguridad)
  - ✅ Block public access to buckets and objects granted through new access control lists (ACLs)
  - ✅ Block public access to buckets and objects granted through any access control lists (ACLs)
  - ✅ Block public access to buckets and objects granted through new public bucket or access point policies
  - ✅ Block public access to buckets and objects granted through any public bucket or access point policies

**Configuración avanzada:**
- **Object Lock**: Deshabilitado (a menos que necesites retención de objetos)

### 1.2 Configurar Política de Bucket
Después de crear el bucket, configura una política que permita solo acceso mediante URLs prefirmadas:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyPublicAccess",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::synco-payment-receipts",
                "arn:aws:s3:::synco-payment-receipts/*"
            ],
            "Condition": {
                "StringNotEquals": {
                    "aws:PrincipalServiceName": "s3.amazonaws.com"
                }
            }
        }
    ]
}
```

## 2. Crear Usuario IAM

### 2.1 Crear Usuario
1. Ve a IAM en la consola de AWS
2. Haz clic en "Users" → "Create user"
3. Nombre del usuario: `synco-s3-service`
4. Tipo de acceso: "Programmatic access"

### 2.2 Crear Política IAM
Crea una política personalizada con los siguientes permisos:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:HeadObject",
                "s3:ListObjectsV2"
            ],
            "Resource": [
                "arn:aws:s3:::synco-payment-receipts",
                "arn:aws:s3:::synco-payment-receipts/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GeneratePresignedUrl"
            ],
            "Resource": [
                "arn:aws:s3:::synco-payment-receipts",
                "arn:aws:s3:::synco-payment-receipts/*"
            ]
        }
    ]
}
```

### 2.3 Asignar Política al Usuario
1. Adjunta la política personalizada al usuario `synco-s3-service`
2. Genera las credenciales de acceso (Access Key ID y Secret Access Key)
3. **IMPORTANTE**: Guarda estas credenciales de forma segura

## 3. Configurar Variables de Entorno

### 3.1 Variables Requeridas
Agrega las siguientes variables a tu archivo `.env`:

```env
# Configuración AWS S3
AWS_ACCESS_KEY_ID=tu_access_key_id_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_access_key_aqui
AWS_REGION=us-east-1
S3_BUCKET_NAME=synco-payment-receipts
```

### 3.2 Variables Opcionales
```env
# Configuración adicional (opcional)
S3_UPLOAD_EXPIRY=3600  # Tiempo de expiración para URLs de subida (segundos)
S3_DOWNLOAD_EXPIRY=3600  # Tiempo de expiración para URLs de descarga (segundos)
```

## 4. Estructura de Archivos en S3

### 4.1 Organización de Archivos
Los archivos se organizan de la siguiente manera:
```
synco-payment-receipts/
├── payment-receipts/
│   ├── user_id_1/
│   │   ├── payment_id_1_20250101_12345678.jpg
│   │   ├── payment_id_2_20250102_87654321.png
│   │   └── ...
│   ├── user_id_2/
│   │   ├── payment_id_3_20250103_11223344.pdf
│   │   └── ...
│   └── ...
```

### 4.2 Convención de Nombres
- **Formato**: `{payment_id}_{timestamp}_{unique_id}.{extension}`
- **Ejemplo**: `507f1f77bcf86cd799439011_20250101_12345678.jpg`
- **Timestamp**: Formato YYYYMMDD_HHMMSS
- **Unique ID**: 8 caracteres aleatorios para evitar colisiones

## 5. Seguridad y Mejores Prácticas

### 5.1 Seguridad del Bucket
- ✅ **Bucket privado**: Sin acceso público
- ✅ **Encriptación**: AES-256 habilitada
- ✅ **Política restrictiva**: Solo acceso mediante URLs prefirmadas
- ✅ **Credenciales seguras**: Usuario IAM con permisos mínimos

### 5.2 Seguridad de URLs Prefirmadas
- **Tiempo de expiración**: Máximo 2 horas (7200 segundos)
- **Método específico**: PUT para subida, GET para descarga
- **Content-Type**: Validado según extensión del archivo
- **Validación**: Verificación de existencia del pago antes de generar URL

### 5.3 Validación de Archivos
- **Extensiones permitidas**: jpg, jpeg, png, gif, pdf, doc, docx, txt
- **Tamaño máximo**: Configurado en el frontend (recomendado: 10MB)
- **Content-Type**: Validado automáticamente por S3

## 6. Monitoreo y Logs

### 6.1 CloudTrail (Opcional)
Para auditoría completa, habilita CloudTrail:
1. Ve a CloudTrail en la consola de AWS
2. Crea un trail que incluya eventos de S3
3. Configura almacenamiento en CloudWatch Logs

### 6.2 CloudWatch Metrics
Monitorea métricas importantes:
- **Requests**: Número de requests PUT/GET
- **Errors**: Errores 4xx y 5xx
- **Data Transfer**: Bytes transferidos
- **Storage**: Tamaño del bucket

## 7. Costos Estimados

### 7.1 Costos por Uso
- **Storage**: $0.023 por GB/mes (región us-east-1)
- **Requests PUT**: $0.0004 por 1,000 requests
- **Requests GET**: $0.0004 por 1,000 requests
- **Data Transfer**: $0.09 por GB (primeros 10TB)

### 7.2 Estimación Mensual (100 usuarios, 200 pagos)
- **Storage**: ~$0.50 (asumiendo 20GB total)
- **Requests**: ~$0.20 (500 requests PUT/GET)
- **Total estimado**: ~$0.70/mes

## 8. Troubleshooting

### 8.1 Errores Comunes

**Error: "Access Denied"**
- Verificar credenciales AWS
- Verificar permisos IAM del usuario
- Verificar política del bucket

**Error: "Bucket does not exist"**
- Verificar nombre del bucket
- Verificar región
- Verificar que el bucket existe

**Error: "Invalid signature"**
- Verificar AWS_ACCESS_KEY_ID
- Verificar AWS_SECRET_ACCESS_KEY
- Verificar AWS_REGION

### 8.2 Logs de Debug
El servicio S3 incluye logs de debug que puedes habilitar:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 9. Implementación en Producción

### 9.1 Variables de Entorno en Producción
```env
# Producción
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=synco-payment-receipts-prod
```

### 9.2 Backup y Recuperación
- **Cross-Region Replication**: Configurar replicación a otra región
- **Lifecycle Policies**: Configurar transición a IA o Glacier para archivos antiguos
- **Versioning**: Habilitar si necesitas recuperación de archivos eliminados

### 9.3 Escalabilidad
- **CDN**: Considerar CloudFront para distribución global
- **Caching**: Implementar cache de URLs prefirmadas
- **Rate Limiting**: Implementar límites de requests por usuario

## 10. Testing

### 10.1 Pruebas Locales
```bash
# Instalar dependencias
pip install boto3 botocore

# Ejecutar tests
python -m pytest tests/test_s3_service.py
```

### 10.2 Pruebas de Integración
```bash
# Test de subida
curl -X POST "http://localhost:8000/payments/{payment_id}/upload-url?file_extension=jpg"

# Test de descarga
curl -X GET "http://localhost:8000/payments/{payment_id}/download-url"
```

## Conclusión

Esta configuración proporciona un sistema seguro y escalable para el almacenamiento de comprobantes de pagos, utilizando las mejores prácticas de seguridad de AWS S3 y URLs prefirmadas para controlar el acceso a los archivos.
