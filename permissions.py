"""
Sistema de permisos y roles para usuarios
"""
from typing import List
from fastapi import HTTPException, status
from user_service import user_service

# Definición de roles disponibles
AVAILABLE_ROLES = [
    "admin",           # Administrador completo
    "coach",           # Entrenador/Coach
    "player"           # Jugador
]

# Definición de permisos por rol
ROLE_PERMISSIONS = {
    "admin": [
        "users.list",
        "users.view",
        "users.edit",
        "users.delete",
        "users.manage_roles",
        "events.create",
        "events.edit",
        "events.delete",
        "events.view",
        "calendar.manage",
        "attendance.manage"
    ],
    "coach": [
        "users.view",
        "events.create",
        "events.edit",
        "events.view",
        "attendance.manage"
    ],
    "player": [
        "events.view",
        "attendance.self"
    ]
}

# Permisos para usuarios sin roles (visitors)
VISITOR_PERMISSIONS = [
    "events.view"
]

class PermissionChecker:
    """Clase para verificar permisos de usuarios"""
    
    @staticmethod
    async def check_permission(user_id: str, permission: str) -> bool:
        """
        Verificar si un usuario tiene un permiso específico
        
        Args:
            user_id: ID del usuario
            permission: Permiso a verificar
            
        Returns:
            bool: True si tiene el permiso, False en caso contrario
        """
        try:
            user = await user_service.get_user_by_id(user_id)
            if not user:
                return False
            
            # Verificar si el usuario está activo
            if not user.is_active:
                return False
            
            # Si el usuario no tiene roles, es un visitor
            if not user.roles or len(user.roles) == 0:
                return permission in VISITOR_PERMISSIONS
            
            # Verificar permisos por cada rol del usuario
            for role in user.roles:
                if role in ROLE_PERMISSIONS:
                    if permission in ROLE_PERMISSIONS[role]:
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error verificando permiso: {e}")
            return False
    
    @staticmethod
    async def require_permission(user_id: str, permission: str):
        """
        Requerir que un usuario tenga un permiso específico
        
        Args:
            user_id: ID del usuario
            permission: Permiso requerido
            
        Raises:
            HTTPException: Si el usuario no tiene el permiso
        """
        has_permission = await PermissionChecker.check_permission(user_id, permission)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para realizar esta acción: {permission}"
            )
    
    @staticmethod
    async def require_admin(user_id: str):
        """
        Requerir que un usuario sea administrador
        
        Args:
            user_id: ID del usuario
            
        Raises:
            HTTPException: Si el usuario no es administrador
        """
        await PermissionChecker.require_permission(user_id, "users.manage_roles")
    
    @staticmethod
    def get_available_roles() -> List[str]:
        """
        Obtener lista de roles disponibles
        
        Returns:
            List[str]: Lista de roles disponibles
        """
        return AVAILABLE_ROLES.copy()
    
    @staticmethod
    def get_role_permissions(role: str) -> List[str]:
        """
        Obtener permisos de un rol específico
        
        Args:
            role: Nombre del rol
            
        Returns:
            List[str]: Lista de permisos del rol
        """
        return ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def get_visitor_permissions() -> List[str]:
        """
        Obtener permisos de visitors (usuarios sin roles)
        
        Returns:
            List[str]: Lista de permisos de visitors
        """
        return VISITOR_PERMISSIONS.copy()
    
    @staticmethod
    def validate_roles(roles: List[str]) -> bool:
        """
        Validar que los roles sean válidos
        
        Args:
            roles: Lista de roles a validar
            
        Returns:
            bool: True si todos los roles son válidos
        """
        return all(role in AVAILABLE_ROLES for role in roles)

# Instancia global del verificador de permisos
permission_checker = PermissionChecker()
