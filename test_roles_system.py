#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de roles y usuarios
"""
import asyncio
import sys
import os

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_service import user_service
from permissions import permission_checker
from models import GoogleUserInfo

async def test_user_creation():
    """Probar creación de usuario con nuevos campos"""
    print("🧪 Probando creación de usuario...")
    
    # Simular datos de Google
    google_user_info = GoogleUserInfo(
        id="test_google_id_123",
        email="test@example.com",
        name="Usuario de Prueba",
        picture="https://example.com/picture.jpg",
        verified_email=True
    )
    
    try:
        # Crear usuario
        user = await user_service.create_user(google_user_info)
        print(f"✅ Usuario creado exitosamente:")
        print(f"   - ID: {user.id}")
        print(f"   - Email: {user.email}")
        print(f"   - Name: {user.name}")
        print(f"   - Nickname: '{user.nickname}'")
        print(f"   - Roles: {user.roles}")
        print(f"   - Is Active: {user.is_active}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        return None

async def test_user_roles_update(user):
    """Probar actualización de roles"""
    if not user:
        print("⚠️ No hay usuario para probar roles")
        return
    
    print("\n🧪 Probando actualización de roles...")
    
    try:
        # Actualizar roles
        updated_user = await user_service.update_user_roles(str(user.id), ["admin", "moderator"])
        if updated_user:
            print(f"✅ Roles actualizados exitosamente:")
            print(f"   - Roles: {updated_user.roles}")
        else:
            print("❌ Error actualizando roles")
            
    except Exception as e:
        print(f"❌ Error actualizando roles: {e}")

async def test_user_nickname_update(user):
    """Probar actualización de nickname"""
    if not user:
        print("⚠️ No hay usuario para probar nickname")
        return
    
    print("\n🧪 Probando actualización de nickname...")
    
    try:
        # Actualizar nickname
        updated_user = await user_service.update_user_nickname(str(user.id), "Jugador Test")
        if updated_user:
            print(f"✅ Nickname actualizado exitosamente:")
            print(f"   - Nickname: '{updated_user.nickname}'")
        else:
            print("❌ Error actualizando nickname")
            
    except Exception as e:
        print(f"❌ Error actualizando nickname: {e}")

async def test_permissions(user):
    """Probar sistema de permisos"""
    if not user:
        print("⚠️ No hay usuario para probar permisos")
        return
    
    print("\n🧪 Probando sistema de permisos...")
    
    try:
        # Verificar permisos específicos
        has_admin_permission = await permission_checker.check_permission(str(user.id), "users.manage_roles")
        has_view_permission = await permission_checker.check_permission(str(user.id), "events.view")
        has_invalid_permission = await permission_checker.check_permission(str(user.id), "invalid.permission")
        
        print(f"✅ Verificación de permisos:")
        print(f"   - users.manage_roles: {has_admin_permission}")
        print(f"   - events.view: {has_view_permission}")
        print(f"   - invalid.permission: {has_invalid_permission}")
        
        # Obtener roles disponibles
        available_roles = permission_checker.get_available_roles()
        print(f"   - Roles disponibles: {available_roles}")
        
    except Exception as e:
        print(f"❌ Error probando permisos: {e}")

async def test_user_list():
    """Probar listado de usuarios"""
    print("\n🧪 Probando listado de usuarios...")
    
    try:
        users, total = await user_service.get_all_users(skip=0, limit=10)
        print(f"✅ Listado de usuarios:")
        print(f"   - Total usuarios: {total}")
        print(f"   - Usuarios obtenidos: {len(users)}")
        
        for user in users:
            print(f"   - {user.email} (nickname: '{user.nickname}', roles: {user.roles})")
            
    except Exception as e:
        print(f"❌ Error listando usuarios: {e}")

async def cleanup_test_user(user):
    """Limpiar usuario de prueba"""
    if not user:
        return
    
    print("\n🧹 Limpiando usuario de prueba...")
    
    try:
        # Aquí podrías agregar lógica para eliminar el usuario de prueba
        # Por ahora solo mostramos un mensaje
        print(f"✅ Usuario de prueba '{user.email}' listo para limpieza manual")
        
    except Exception as e:
        print(f"❌ Error limpiando usuario: {e}")

async def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas del sistema de roles y usuarios...")
    print("=" * 60)
    
    # Probar creación de usuario
    user = await test_user_creation()
    
    # Probar actualización de roles
    await test_user_roles_update(user)
    
    # Probar actualización de nickname
    await test_user_nickname_update(user)
    
    # Probar sistema de permisos
    await test_permissions(user)
    
    # Probar listado de usuarios
    await test_user_list()
    
    # Limpiar
    await cleanup_test_user(user)
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas!")

if __name__ == "__main__":
    # Ejecutar pruebas
    asyncio.run(main())
