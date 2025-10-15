# Configuración de Variables de Entorno

Este documento explica cómo configurar las variables de entorno para la API de Synco. **IMPORTANTE**: La API ahora requiere variables de entorno tanto para desarrollo local como para producción.

## Configuración Obligatoria

La API está configurada para usar **exclusivamente** variables de entorno JSON. No lee archivos físicos `credentials.json` o `token.json` del sistema de archivos.

## Configuración para Entornos Serverless (Vercel, Netlify, etc.)

### 1. Obtener las Credenciales

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a "APIs & Services" > "Credentials"
4. Crea o descarga las credenciales como JSON
5. Copia todo el contenido del archivo JSON

### 2. Obtener el Token de Autorización

Ejecuta el flujo OAuth localmente para obtener el token:

```bash
python convert_token_pickle_to_json.py
```

O usa el script de conversión:

```bash
python convert_to_env_format.py
```

### 3. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con:

```env
# Credenciales de Google Cloud Console (contenido JSON completo)
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"tu-proyecto",...}

# Token de autorización (contenido JSON completo)
GOOGLE_TOKEN_JSON={"token":"...","refresh_token":"...",...}
```

### 4. Para Vercel

En el dashboard de Vercel:

1. Ve a tu proyecto
2. Settings > Environment Variables
3. Agrega:
   - `GOOGLE_CREDENTIALS_JSON` con el contenido JSON completo
   - `GOOGLE_TOKEN_JSON` con el contenido JSON completo

## Configuración para Desarrollo Local

**IMPORTANTE**: Incluso para desarrollo local, debes configurar las variables de entorno:

1. Crea un archivo `.env` en la raíz del proyecto
2. Configura las variables `GOOGLE_CREDENTIALS_JSON` y `GOOGLE_TOKEN_JSON`
3. La API generará archivos temporales automáticamente desde estas variables

## Verificación

Para verificar que la configuración funciona:

1. Ejecuta la API localmente:
   ```bash
   python main.py
   ```

2. Verifica los logs para confirmar que las credenciales se cargan correctamente

3. Prueba los endpoints:
   - `GET /calendarios` - Lista de calendarios
   - `GET /eventos` - Eventos del calendario

## Solución de Problemas

### Error 503: Servicio no disponible

- Verifica que `GOOGLE_CREDENTIALS_JSON` esté configurado
- Verifica que `GOOGLE_TOKEN_JSON` esté configurado
- Asegúrate de que el JSON sea válido (sin saltos de línea)

### Error de autenticación

- Verifica que las credenciales sean correctas
- Asegúrate de que el token no haya expirado
- Verifica que los scopes sean correctos

### Error de JSON inválido

- Usa el script `convert_to_env_format.py` para generar el formato correcto
- Asegúrate de que el JSON esté en una sola línea
- No incluyas saltos de línea en las variables de entorno

## Scripts de Ayuda

- `convert_to_env_format.py` - Convierte archivos existentes a formato de variables de entorno
- `convert_token_pickle_to_json.py` - Convierte token pickle a JSON
