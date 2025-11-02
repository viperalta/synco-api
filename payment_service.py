"""
Servicio para gestión de pagos
Maneja la lógica de negocio para pagos de usuarios
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from models import PaymentModel, PaymentCreateRequest, PaymentUpdateRequest, PaymentResponse, PaymentListResponse
from s3_service import s3_service
import re

class PaymentService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.payments
    
    async def create_payment(self, user_id: str, payment_data: PaymentCreateRequest) -> PaymentResponse:
        """
        Crea un nuevo pago
        
        Args:
            user_id: ID del usuario que realiza el pago
            payment_data: Datos del pago
        
        Returns:
            PaymentResponse con los datos del pago creado
        """
        # Validar formato del período
        if not self._validate_period_format(payment_data.period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        # Obtener información del usuario
        from user_service import user_service
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # Usar payment_date si se proporciona, si no usar created_at
        from datetime import datetime
        payment_date = payment_data.payment_date if payment_data.payment_date else datetime.utcnow()
        
        # Crear modelo de pago
        payment = PaymentModel(
            user_id=ObjectId(user_id),  # Convertir string a ObjectId
            user_name=user.name,  # Nombre del usuario
            user_nickname=user.nickname,  # Nickname del usuario
            amount=payment_data.amount,
            period=payment_data.period,
            payment_date=payment_date,
            notes=payment_data.notes,
            status="pending"
        )
        
        # Insertar en la base de datos
        result = await self.collection.insert_one(payment.dict(by_alias=True, exclude={"id"}))
        
        # Obtener el pago creado
        created_payment = await self.collection.find_one({"_id": result.inserted_id})
        
        return self._payment_to_response(created_payment)
    
    async def get_payment_by_id(self, payment_id: str, user_id: Optional[str] = None) -> Optional[PaymentResponse]:
        """
        Obtiene un pago por su ID
        
        Args:
            payment_id: ID del pago
            user_id: ID del usuario (opcional, para verificar permisos)
        
        Returns:
            PaymentResponse o None si no existe
        """
        query = {"_id": ObjectId(payment_id)}
        if user_id:
            query["user_id"] = ObjectId(user_id)  # Convertir string a ObjectId
        
        payment = await self.collection.find_one(query)
        if payment:
            return self._payment_to_response(payment)
        return None
    
    async def get_user_payments(self, user_id: str, skip: int = 0, limit: int = 100) -> PaymentListResponse:
        """
        Obtiene todos los pagos de un usuario específico
        
        Args:
            user_id: ID del usuario
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
        
        Returns:
            PaymentListResponse con la lista de pagos
        """
        # Contar total de pagos
        total = await self.collection.count_documents({"user_id": ObjectId(user_id)})
        
        # Obtener pagos ordenados por fecha de creación (más recientes primero)
        cursor = self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).skip(skip).limit(limit)
        payments = await cursor.to_list(length=limit)
        
        payment_responses = [self._payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def get_user_payments_by_period(self, user_id: str, period: str, skip: int = 0, limit: int = 100) -> PaymentListResponse:
        """
        Obtiene los pagos de un usuario específico filtrados por período
        
        Args:
            user_id: ID del usuario
            period: Período en formato YYYYMM
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
        
        Returns:
            PaymentListResponse con la lista de pagos
        """
        # Validar formato del período
        if not self._validate_period_format(period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        query = {
            "user_id": ObjectId(user_id),
            "period": period
        }
        
        # Contar total de pagos
        total = await self.collection.count_documents(query)
        
        # Obtener pagos ordenados por fecha de creación (más recientes primero)
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        payments = await cursor.to_list(length=limit)
        
        payment_responses = [self._payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def get_payments_by_period(self, period: str, skip: int = 0, limit: int = 100) -> PaymentListResponse:
        """
        Obtiene todos los pagos de un período específico
        
        Args:
            period: Período en formato YYYYMM
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
        
        Returns:
            PaymentListResponse con la lista de pagos
        """
        # Validar formato del período
        if not self._validate_period_format(period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        # Contar total de pagos
        total = await self.collection.count_documents({"period": period})
        
        # Obtener pagos ordenados por fecha de creación (más recientes primero)
        cursor = self.collection.find({"period": period}).sort("created_at", -1).skip(skip).limit(limit)
        payments = await cursor.to_list(length=limit)
        
        payment_responses = [self._payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def get_all_payments(self, skip: int = 0, limit: int = 100, status: Optional[str] = None, period: Optional[str] = None) -> PaymentListResponse:
        """
        Obtiene todos los pagos (solo para administradores)
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
            status: Filtrar por estado (opcional)
            period: Filtrar por período (opcional)
        
        Returns:
            PaymentListResponse con la lista de pagos
        """
        query = {}
        if status:
            query["status"] = status
        if period:
            query["period"] = period
        
        # Contar total de pagos
        total = await self.collection.count_documents(query)
        
        # Obtener pagos ordenados por fecha de creación (más recientes primero)
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        payments = await cursor.to_list(length=limit)
        
        payment_responses = [self._payment_to_response(payment) for payment in payments]
        
        return PaymentListResponse(
            payments=payment_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def update_payment(self, payment_id: str, user_id: str, update_data: PaymentUpdateRequest) -> Optional[PaymentResponse]:
        """
        Actualiza un pago existente
        
        Args:
            payment_id: ID del pago
            user_id: ID del usuario (para verificar permisos)
            update_data: Datos a actualizar
        
        Returns:
            PaymentResponse actualizado o None si no existe
        """
        # Validar período si se proporciona
        if update_data.period and not self._validate_period_format(update_data.period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        # Preparar datos de actualización
        update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        # Actualizar el pago
        result = await self.collection.update_one(
            {"_id": ObjectId(payment_id), "user_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            # Obtener el pago actualizado
            updated_payment = await self.collection.find_one({"_id": ObjectId(payment_id)})
            return self._payment_to_response(updated_payment)
        
        return None
    
    async def verify_payment(self, payment_id: str, verified_by: str, status: str, notes: Optional[str] = None) -> Optional[PaymentResponse]:
        """
        Verifica un pago (solo para administradores)
        
        Args:
            payment_id: ID del pago
            verified_by: ID del usuario que verifica
            status: Estado de verificación (verified, rejected)
            notes: Notas adicionales
        
        Returns:
            PaymentResponse actualizado o None si no existe
        """
        if status not in ["verified", "rejected"]:
            raise ValueError("Estado de verificación inválido. Debe ser 'verified' o 'rejected'")
        
        update_data = {
            "status": status,
            "verified_by": ObjectId(verified_by),  # Convertir string a ObjectId
            "verified_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if notes:
            update_data["notes"] = notes
        
        # Actualizar el pago
        result = await self.collection.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            # Obtener el pago actualizado
            updated_payment = await self.collection.find_one({"_id": ObjectId(payment_id)})
            return self._payment_to_response(updated_payment)
        
        return None
    
    async def delete_payment(self, payment_id: str, user_id: str) -> bool:
        """
        Elimina un pago
        
        Args:
            payment_id: ID del pago
            user_id: ID del usuario (para verificar permisos)
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        # Obtener el pago para eliminar también el archivo de S3
        payment = await self.collection.find_one({"_id": ObjectId(payment_id), "user_id": ObjectId(user_id)})
        
        if payment:
            # Eliminar archivo de S3 si existe
            if payment.get("receipt_image_key"):
                s3_service.delete_file(payment["receipt_image_key"])
            
            # Eliminar el pago de la base de datos
            result = await self.collection.delete_one({"_id": ObjectId(payment_id), "user_id": ObjectId(user_id)})
            return result.deleted_count > 0
        
        return False
    
    async def update_payment_receipt(self, payment_id: str, user_id: str, file_key: str) -> Optional[PaymentResponse]:
        """
        Actualiza la información del comprobante de un pago
        
        Args:
            payment_id: ID del pago
            user_id: ID del usuario
            file_key: Clave del archivo en S3
        
        Returns:
            PaymentResponse actualizado o None si no existe
        """
        # Generar URL de descarga
        try:
            download_info = s3_service.generate_download_url(file_key)
            receipt_url = download_info["download_url"]
        except Exception as e:
            raise ValueError(f"Error generando URL de descarga: {e}")
        
        # Actualizar el pago
        update_data = {
            "receipt_image_key": file_key,
            "receipt_image_url": receipt_url,
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {"_id": ObjectId(payment_id), "user_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            # Obtener el pago actualizado
            updated_payment = await self.collection.find_one({"_id": ObjectId(payment_id)})
            return self._payment_to_response(updated_payment)
        
        return None
    
    def _validate_period_format(self, period: str) -> bool:
        """
        Valida que el formato del período sea YYYYMM
        
        Args:
            period: Período a validar
        
        Returns:
            True si el formato es válido, False en caso contrario
        """
        pattern = r'^\d{6}$'
        if not re.match(pattern, period):
            return False
        
        # Validar que sea un año y mes válidos
        year = int(period[:4])
        month = int(period[4:6])
        
        if year < 2000 or year > 2100:
            return False
        
        if month < 1 or month > 12:
            return False
        
        return True
    
    def _payment_to_response(self, payment: Dict[str, Any]) -> PaymentResponse:
        """
        Convierte un documento de MongoDB a PaymentResponse
        
        Args:
            payment: Documento de MongoDB
        
        Returns:
            PaymentResponse
        """
        return PaymentResponse(
            id=str(payment["_id"]),
            user_id=str(payment["user_id"]),  # Convertir ObjectId a string
            user_name=payment.get("user_name", "Usuario no disponible"),  # Nombre del usuario con fallback
            user_nickname=payment.get("user_nickname"),  # Nickname del usuario
            amount=payment["amount"],
            period=payment["period"],
            payment_date=payment["payment_date"],
            receipt_image_url=payment.get("receipt_image_url"),
            status=payment["status"],
            notes=payment.get("notes"),
            verified_by=str(payment.get("verified_by")) if payment.get("verified_by") else None,  # Convertir ObjectId a string
            verified_at=payment.get("verified_at"),
            created_at=payment["created_at"],
            updated_at=payment["updated_at"]
        )
    
    async def get_payment_statistics(self, user_id: Optional[str] = None, period: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de pagos
        
        Args:
            user_id: ID del usuario (opcional)
            period: Período específico (opcional)
        
        Returns:
            Dict con estadísticas
        """
        query = {}
        if user_id:
            query["user_id"] = ObjectId(user_id)
        if period:
            query["period"] = period
        
        # Contar por estado
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }}
        ]
        
        stats = await self.collection.aggregate(pipeline).to_list(length=None)
        
        # Calcular totales
        total_payments = await self.collection.count_documents(query)
        total_amount = sum(stat["total_amount"] for stat in stats)
        
        return {
            "total_payments": total_payments,
            "total_amount": total_amount,
            "by_status": {stat["_id"]: {"count": stat["count"], "amount": stat["total_amount"]} for stat in stats}
        }
