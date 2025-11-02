"""
Servicio para gestión de deudas
Maneja la lógica de negocio para deudas de usuarios
"""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from models import DebtModel, DebtCreateRequest, DebtUpdateRequest, DebtResponse, DebtListResponse, DebtorInfo, PlayerDebtResponse
import re

class DebtService:
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.debts
    
    async def create_debt(self, debt_data: DebtCreateRequest) -> DebtResponse:
        """
        Crea o actualiza una deuda para un período (upsert)
        
        Args:
            debt_data: Datos de la deuda
        
        Returns:
            DebtResponse con los datos de la deuda creada o actualizada
        """
        # Validar formato del período
        if not self._validate_period_format(debt_data.period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        # Preparar datos de la deuda
        debt_dict = {
            "period": debt_data.period,
            "debtors": [debtor.dict() for debtor in debt_data.debtors],
            "updated_at": datetime.utcnow()
        }
        
        # Verificar si ya existe una deuda para este período
        existing_debt = await self.collection.find_one({"period": debt_data.period})
        
        if existing_debt:
            # Actualizar la deuda existente
            await self.collection.update_one(
                {"period": debt_data.period},
                {"$set": debt_dict}
            )
            # Obtener la deuda actualizada
            updated_debt = await self.collection.find_one({"period": debt_data.period})
            return self._debt_to_response(updated_debt)
        else:
            # Crear nueva deuda
            debt_dict["created_at"] = datetime.utcnow()
            # Insertar en la base de datos
            result = await self.collection.insert_one(debt_dict)
            # Obtener la deuda creada
            created_debt = await self.collection.find_one({"_id": result.inserted_id})
            return self._debt_to_response(created_debt)
    
    async def get_debt_by_period(self, period: str) -> Optional[DebtResponse]:
        """
        Obtiene una deuda por período
        
        Args:
            period: Período en formato YYYYMM
        
        Returns:
            DebtResponse o None si no existe
        """
        # Validar formato del período
        if not self._validate_period_format(period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        debt = await self.collection.find_one({"period": period})
        if debt:
            return self._debt_to_response(debt)
        return None
    
    async def get_player_debt(self, user_id: str, period: str) -> Optional[PlayerDebtResponse]:
        """
        Obtiene la deuda de un jugador específico para un período
        
        Args:
            user_id: ID del usuario
            period: Período en formato YYYYMM
        
        Returns:
            PlayerDebtResponse o None si no tiene deuda
        """
        # Validar formato del período
        if not self._validate_period_format(period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        debt = await self.collection.find_one({"period": period})
        if not debt:
            return None
        
        # Buscar el usuario en la lista de deudores
        debtor_info = None
        for debtor in debt.get("debtors", []):
            if debtor["user_id"] == user_id:
                debtor_info = debtor
                break
        
        if not debtor_info:
            return None
        
        return PlayerDebtResponse(
            period=period,
            amount=debtor_info["amount"],
            user_name=debtor_info["user_name"],
            user_nickname=debtor_info.get("user_nickname")
        )
    
    async def get_all_debts(self, skip: int = 0, limit: int = 100) -> DebtListResponse:
        """
        Obtiene todas las deudas (solo para administradores)
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a devolver
        
        Returns:
            DebtListResponse con la lista de deudas
        """
        # Contar total de deudas
        total = await self.collection.count_documents({})
        
        # Obtener deudas ordenadas por período (más recientes primero)
        cursor = self.collection.find({}).sort("period", -1).skip(skip).limit(limit)
        debts = await cursor.to_list(length=limit)
        
        debt_responses = [self._debt_to_response(debt) for debt in debts]
        
        return DebtListResponse(
            debts=debt_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def update_debt(self, period: str, update_data: DebtUpdateRequest) -> Optional[DebtResponse]:
        """
        Actualiza una deuda existente
        
        Args:
            period: Período en formato YYYYMM
            update_data: Datos a actualizar
        
        Returns:
            DebtResponse actualizado o None si no existe
        """
        # Validar formato del período
        if not self._validate_period_format(period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        # Preparar datos de actualización
        update_dict = {
            "debtors": [debtor.dict() for debtor in update_data.debtors],
            "updated_at": datetime.utcnow()
        }
        
        # Actualizar la deuda
        result = await self.collection.update_one(
            {"period": period},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            # Obtener la deuda actualizada
            updated_debt = await self.collection.find_one({"period": period})
            return self._debt_to_response(updated_debt)
        
        return None
    
    async def delete_debt(self, period: str) -> bool:
        """
        Elimina una deuda
        
        Args:
            period: Período en formato YYYYMM
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        # Validar formato del período
        if not self._validate_period_format(period):
            raise ValueError("Formato de período inválido. Debe ser YYYYMM (ej: 202510)")
        
        # Eliminar la deuda
        result = await self.collection.delete_one({"period": period})
        return result.deleted_count > 0
    
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
    
    def _debt_to_response(self, debt: Dict[str, Any]) -> DebtResponse:
        """
        Convierte un documento de MongoDB a DebtResponse
        
        Args:
            debt: Documento de MongoDB
        
        Returns:
            DebtResponse
        """
        # Calcular el total de deuda
        total_debt = sum(debtor["amount"] for debtor in debt.get("debtors", []))
        
        return DebtResponse(
            id=str(debt["_id"]),
            period=debt["period"],
            debtors=debt.get("debtors", []),
            total_debt=total_debt,
            created_at=debt["created_at"],
            updated_at=debt["updated_at"]
        )

# Instancia global del servicio de deudas
debt_service = None

async def get_debt_service() -> DebtService:
    """Obtener instancia del servicio de deudas"""
    global debt_service
    if debt_service is None:
        from mongodb_config import mongodb_config
        # Conectar MongoDB si no está conectado
        if mongodb_config.database is None:
            await mongodb_config.connect()
        debt_service = DebtService(mongodb_config.get_database())
    return debt_service

