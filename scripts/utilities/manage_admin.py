#!/usr/bin/env python3
"""
Script para gestionar la configuración de usuario admin desde .env

OPCIÓN 1: Configurar desde .env (RECOMENDADO)
   1. Editar .env:
      INIT_DEFAULT_ADMIN=true
      ADMIN_DEFAULT_NAME="Tu Nombre"
      ADMIN_DEFAULT_EMAIL="tu@email.com"
      ADMIN_DEFAULT_PASSWORD="TuContraseña123!"
   
   2. Ejecutar: python3 manage_admin.py --init-from-env
   
   3. Cambiar en .env: INIT_DEFAULT_ADMIN=false (para que no se recree)

OPCIÓN 2: Crear admin manualmente
   python3 manage_admin.py --create "Admin" "admin@example.com" "Password123!"

OPCIÓN 3: Listar admins existentes
   python3 manage_admin.py --list

OPCIÓN 4: Cambiar contraseña de admin
   python3 manage_admin.py --change-password "admin@example.com" "NewPassword123!"
"""

import sys
import argparse
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


def init_from_env():
    """Inicializar admin desde variables .env"""
    from app.core.config import settings
    from app.core.database import async_engine
    from app.core.admin_init import init_default_admin
    from sqlalchemy.ext.asyncio import AsyncSession
    import asyncio
    
    print("\n🔧 Inicializando admin desde .env...\n")
    
    if not settings.INIT_DEFAULT_ADMIN:
        print("❌ Error: INIT_DEFAULT_ADMIN=false en .env")
        print("   Cambiar a INIT_DEFAULT_ADMIN=true primero")
        return False
    
    async def run():
        async with AsyncSession(async_engine) as session:
            admin_id = await init_default_admin(session)
            if admin_id:
                print(f"\n✅ Admin creado exitosamente!")
                print(f"   Email: {settings.ADMIN_DEFAULT_EMAIL}")
                print(f"   Password: {settings.ADMIN_DEFAULT_PASSWORD}")
                print(f"\n⚠️  IMPORTANTE:")
                print(f"   1. Cambiar INIT_DEFAULT_ADMIN=false en .env")
                print(f"   2. Cambiar la contraseña en login")
                print(f"   3. En producción, usar OAuth2 o tokens seguros")
                return True
            else:
                print("❌ No se pudo crear el admin")
                return False
    
    return asyncio.run(run())


def create_admin(name, email, password):
    """Crear admin manualmente"""
    from app.core.database import async_engine
    from app.services.auth_service import auth_service
    from app.services.api_key_service import api_key_service
    from app.schemas import ApiKeyCreate
    from sqlalchemy.ext.asyncio import AsyncSession
    import asyncio
    
    print(f"\n🔧 Creando admin: {name} ({email})...\n")
    
    async def run():
        async with AsyncSession(async_engine) as session:
            try:
                # Crear usuario
                user_id, user_type = await auth_service.create_user(
                    session=session,
                    name=name,
                    email=email,
                    password=password,
                    role="admin"
                )
                
                # Crear API key
                api_key_data = ApiKeyCreate(
                    name=f"Clave principal - {name}",
                    description="API key de administrador",
                    expires_days=365
                )
                
                api_key_response = await api_key_service.create_api_key(
                    session=session,
                    user_id=user_id,
                    user_type=user_type,
                    user_email=email,
                    key_data=api_key_data
                )
                
                print(f"✅ Admin creado exitosamente!\n")
                print(f"📋 Datos de acceso:")
                print(f"   ID:       {user_id}")
                print(f"   Nombre:   {name}")
                print(f"   Email:    {email}")
                print(f"   Rol:      admin")
                print(f"\n🔑 API Key (guardar en lugar seguro):")
                print(f"   Prefijo:  {api_key_response.key_info.key_prefix}")
                print(f"   Key ID:   {api_key_response.key_info.key_id}")
                print(f"\n⚠️  IMPORTANTE:")
                print(f"   • Cambiar contraseña en login")
                print(f"   • Guardar API key en lugar seguro")
                print(f"   • En producción, usar OAuth2")
                return True
                
            except ValueError as e:
                if "email" in str(e).lower():
                    print(f"❌ Error: Email ya existe")
                else:
                    print(f"❌ Error: {e}")
                return False
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    return asyncio.run(run())


def list_admins():
    """Listar admins existentes"""
    from app.core.database import async_engine
    from app.models import Student
    from sqlmodel import select
    from sqlalchemy.ext.asyncio import AsyncSession
    import asyncio
    
    print("\n📋 Admins registrados:\n")
    
    async def run():
        async with AsyncSession(async_engine) as session:
            result = await session.execute(
                select(Student).where(Student.program == "Administration")
            )
            admins = result.scalars().all()
            
            if not admins:
                print("❌ No hay admins registrados\n")
                return False
            
            for admin in admins:
                print(f"  ID: {admin.id}")
                print(f"  Nombre: {admin.name}")
                print(f"  Email: {admin.email}")  # Este está encriptado
                print(f"  Creado: {admin.created_at if hasattr(admin, 'created_at') else 'N/A'}")
                print()
            
            return True
    
    return asyncio.run(run())


def change_password(email, new_password):
    """Cambiar contraseña de admin"""
    from app.core.database import async_engine
    from app.services.auth_service import auth_service
    from sqlalchemy.ext.asyncio import AsyncSession
    import asyncio
    
    print(f"\n🔧 Cambiando contraseña para: {email}\n")
    
    async def run():
        async with AsyncSession(async_engine) as session:
            try:
                user, user_type = await auth_service.find_user_by_email(session, email)
                
                if not user:
                    print(f"❌ Error: Usuario no encontrado")
                    return False
                
                if user_type != "admin":
                    print(f"❌ Error: El usuario no es admin (tipo: {user_type})")
                    return False
                
                # Actualizar contraseña
                user.hashed_password = auth_service._hash_password(new_password)
                session.add(user)
                await session.commit()
                
                print(f"✅ Contraseña actualizada exitosamente!\n")
                return True
                
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    return asyncio.run(run())


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Gestionar usuario admin desde .env",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--init-from-env",
        action="store_true",
        help="Inicializar admin desde variables .env"
    )
    
    parser.add_argument(
        "--create",
        nargs=3,
        metavar=("NAME", "EMAIL", "PASSWORD"),
        help="Crear nuevo admin (nombre, email, contraseña)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar admins existentes"
    )
    
    parser.add_argument(
        "--change-password",
        nargs=2,
        metavar=("EMAIL", "PASSWORD"),
        help="Cambiar contraseña de admin (email, nueva_contraseña)"
    )
    
    args = parser.parse_args()
    
    if not any([args.init_from_env, args.create, args.list, args.change_password]):
        parser.print_help()
        return 1
    
    try:
        if args.init_from_env:
            success = init_from_env()
        elif args.create:
            name, email, password = args.create
            success = create_admin(name, email, password)
        elif args.list:
            success = list_admins()
        elif args.change_password:
            email, password = args.change_password
            success = change_password(email, password)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada")
        return 1
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
