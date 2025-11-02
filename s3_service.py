"""
Servicio para manejo de archivos en Amazon S3
Incluye funciones para generar URLs prefirmadas para subida y descarga
"""
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

load_dotenv()

class S3Service:
    def __init__(self):
        # Configuración de S3 desde variables de entorno
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            raise ValueError("Faltan variables de entorno requeridas para S3: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME")
        
        # Inicializar cliente S3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
        
        # Verificar que el bucket existe (solo si las credenciales están disponibles)
        try:
            self._verify_bucket_exists()
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo verificar el bucket S3: {e}")
            print("⚠️  El servicio S3 se inicializará sin verificación del bucket")
            print("⚠️  Asegúrate de que las credenciales AWS estén configuradas correctamente")
    
    def _verify_bucket_exists(self):
        """Verifica que el bucket S3 existe y es accesible"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket S3 '{self.bucket_name}' verificado correctamente")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"Bucket '{self.bucket_name}' no existe")
            elif error_code == '403':
                raise ValueError(f"Sin permisos para acceder al bucket '{self.bucket_name}'")
            else:
                raise ValueError(f"Error verificando bucket: {e}")
        except NoCredentialsError:
            raise ValueError("Credenciales AWS no configuradas correctamente")
    
    def generate_upload_url(self, file_extension: str, user_id: str, payment_id: str, expires_in: int = 3600) -> Dict[str, Any]:
        """
        Genera una URL prefirmada para subir un archivo a S3
        
        Args:
            file_extension: Extensión del archivo (ej: 'jpg', 'png', 'pdf')
            user_id: ID del usuario
            payment_id: ID del pago
            expires_in: Tiempo de expiración en segundos (default: 1 hora)
        
        Returns:
            Dict con upload_url, file_key y expires_in
        """
        try:
            # Generar clave única para el archivo
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_key = f"payment-receipts/{user_id}/{payment_id}_{timestamp}_{unique_id}.{file_extension}"
            
            # Generar URL prefirmada para PUT
            upload_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': self._get_content_type(file_extension)
                },
                ExpiresIn=expires_in
            )
            
            return {
                "upload_url": upload_url,
                "file_key": file_key,
                "expires_in": expires_in
            }
            
        except ClientError as e:
            raise Exception(f"Error generando URL de subida: {e}")
    
    def generate_download_url(self, file_key: str, expires_in: int = 3600) -> Dict[str, Any]:
        """
        Genera una URL prefirmada para descargar un archivo de S3
        
        Args:
            file_key: Clave del archivo en S3
            expires_in: Tiempo de expiración en segundos (default: 1 hora)
        
        Returns:
            Dict con download_url y expires_in
        """
        try:
            # Verificar que el archivo existe
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            
            # Generar URL prefirmada para GET
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            
            return {
                "download_url": download_url,
                "expires_in": expires_in
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise ValueError(f"Archivo no encontrado: {file_key}")
            else:
                raise Exception(f"Error generando URL de descarga: {e}")
    
    def delete_file(self, file_key: str) -> bool:
        """
        Elimina un archivo de S3
        
        Args:
            file_key: Clave del archivo en S3
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            print(f"Error eliminando archivo {file_key}: {e}")
            return False
    
    def file_exists(self, file_key: str) -> bool:
        """
        Verifica si un archivo existe en S3
        
        Args:
            file_key: Clave del archivo en S3
        
        Returns:
            True si el archivo existe, False en caso contrario
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise Exception(f"Error verificando existencia del archivo: {e}")
    
    def get_file_info(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un archivo en S3
        
        Args:
            file_key: Clave del archivo en S3
        
        Returns:
            Dict con información del archivo o None si no existe
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return {
                "size": response['ContentLength'],
                "last_modified": response['LastModified'],
                "content_type": response.get('ContentType', 'unknown'),
                "etag": response['ETag']
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                raise Exception(f"Error obteniendo información del archivo: {e}")
    
    def _get_content_type(self, file_extension: str) -> str:
        """
        Obtiene el Content-Type basado en la extensión del archivo
        
        Args:
            file_extension: Extensión del archivo
        
        Returns:
            Content-Type apropiado
        """
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def list_user_files(self, user_id: str, prefix: str = "payment-receipts/") -> List[Dict[str, Any]]:
        """
        Lista archivos de un usuario específico
        
        Args:
            user_id: ID del usuario
            prefix: Prefijo para filtrar archivos
        
        Returns:
            Lista de archivos con sus metadatos
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{prefix}{user_id}/"
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'],
                        "etag": obj['ETag']
                    })
            
            return files
            
        except ClientError as e:
            raise Exception(f"Error listando archivos del usuario: {e}")

# Instancia global del servicio S3
s3_service = S3Service()
