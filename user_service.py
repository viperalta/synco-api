"""
Servicio para manejar usuarios en MongoDB
"""
from typing import Optional, List
from datetime import datetime
from models import UserModel, GoogleUserInfo
from mongodb_config import mongodb_config

class UserService:
    def __init__(self):
        self.collection_name = "users"
    
    async def get_collection(self):
        """Obtener colección de usuarios"""
        return mongodb_config.get_collection(self.collection_name)
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[UserModel]:
        """Obtener usuario por Google ID"""
        try:
            collection = await self.get_collection()
            user_data = await collection.find_one({"google_id": google_id})
            if user_data:
                return UserModel(**user_data)
            return None
        except Exception as e:
            print(f"Error al obtener usuario por Google ID: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Obtener usuario por email"""
        try:
            collection = await self.get_collection()
            user_data = await collection.find_one({"email": email})
            if user_data:
                return UserModel(**user_data)
            return None
        except Exception as e:
            print(f"Error al obtener usuario por email: {e}")
            return None
    
    async def create_user(self, google_user_info: GoogleUserInfo) -> UserModel:
        """Crear nuevo usuario"""
        try:
            collection = await self.get_collection()
            
            # Verificar si el usuario ya existe
            existing_user = await self.get_user_by_google_id(google_user_info.id)
            if existing_user:
                return existing_user
            
            # Crear nuevo usuario
            user_data = {
                "google_id": google_user_info.id,
                "email": google_user_info.email,
                "name": google_user_info.name,
                "picture": google_user_info.picture,
                "nickname": "",  # Campo vacío por defecto
                "roles": [],  # Arreglo vacío por defecto
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            
            return UserModel(**user_data)
            
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            raise e
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserModel]:
        """Actualizar usuario"""
        try:
            from bson import ObjectId
            collection = await self.get_collection()
            
            update_data["updated_at"] = datetime.utcnow()
            
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                user_data = await collection.find_one({"_id": ObjectId(user_id)})
                return UserModel(**user_data)
            return None
            
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            return None
    
    async def get_or_create_user(self, google_user_info: GoogleUserInfo) -> UserModel:
        """Obtener usuario existente o crear uno nuevo"""
        # Intentar obtener usuario existente
        user = await self.get_user_by_google_id(google_user_info.id)
        
        if user:
            # Actualizar información si es necesario
            update_data = {}
            if user.name != google_user_info.name:
                update_data["name"] = google_user_info.name
            if user.picture != google_user_info.picture:
                update_data["picture"] = google_user_info.picture
            
            if update_data:
                user = await self.update_user(str(user.id), update_data)
            
            return user
        else:
            # Crear nuevo usuario
            return await self.create_user(google_user_info)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> tuple[List[UserModel], int]:
        """Obtener todos los usuarios con paginación"""
        try:
            collection = await self.get_collection()
            
            # Contar total de usuarios
            total = await collection.count_documents({})
            
            # Obtener usuarios con paginación
            cursor = collection.find({}).skip(skip).limit(limit)
            users = []
            async for user_data in cursor:
                users.append(UserModel(**user_data))
            
            return users, total
        except Exception as e:
            print(f"Error al obtener usuarios: {e}")
            return [], 0
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Obtener usuario por ID"""
        try:
            from bson import ObjectId
            collection = await self.get_collection()
            user_data = await collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return UserModel(**user_data)
            return None
        except Exception as e:
            print(f"Error al obtener usuario por ID: {e}")
            return None
    
    async def update_user_roles(self, user_id: str, roles: List[str]) -> Optional[UserModel]:
        """Actualizar roles de un usuario"""
        try:
            from bson import ObjectId
            collection = await self.get_collection()
            
            update_data = {
                "roles": roles,
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                user_data = await collection.find_one({"_id": ObjectId(user_id)})
                return UserModel(**user_data)
            return None
            
        except Exception as e:
            print(f"Error al actualizar roles del usuario: {e}")
            return None
    
    async def update_user_nickname(self, user_id: str, nickname: str) -> Optional[UserModel]:
        """Actualizar nickname de un usuario"""
        try:
            from bson import ObjectId
            collection = await self.get_collection()
            
            update_data = {
                "nickname": nickname,
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                user_data = await collection.find_one({"_id": ObjectId(user_id)})
                return UserModel(**user_data)
            return None
            
        except Exception as e:
            print(f"Error al actualizar nickname del usuario: {e}")
            return None
    
    async def has_role(self, user_id: str, role: str) -> bool:
        """Verificar si un usuario tiene un rol específico"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            return role in user.roles
        except Exception as e:
            print(f"Error al verificar rol del usuario: {e}")
            return False

# Instancia global del servicio
user_service = UserService()
