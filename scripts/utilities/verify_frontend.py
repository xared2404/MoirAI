#!/usr/bin/env python3
"""
Verificación de la estructura del frontend
Script para verificar que todos los archivos del frontend estén en su lugar
"""

import sys
from pathlib import Path

def check_frontend_structure():
    """Verifica que la estructura del frontend sea correcta"""
    
    print("🔍 Verificando estructura del frontend MoirAI...")
    print()
    
    base_path = Path(__file__).parent / "app" / "frontend"
    
    required_files = {
        "templates/index.html": "Página principal (landing page)",
        "static/css/styles.css": "Estilos CSS",
        "static/js/main.js": "JavaScript interactivo",
    }
    
    required_dirs = {
        "templates": "Plantillas HTML",
        "static": "Archivos estáticos",
        "static/css": "Estilos CSS",
        "static/js": "Scripts JavaScript",
        "static/images": "Imágenes",
    }
    
    all_ok = True
    
    # Verificar directorios
    print("📁 Verificando directorios:")
    for dir_name, description in required_dirs.items():
        dir_path = base_path / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}: {description}")
        else:
            print(f"  ❌ {dir_name}: {description} - NO ENCONTRADO")
            all_ok = False
    
    print()
    
    # Verificar archivos
    print("📄 Verificando archivos:")
    for file_name, description in required_files.items():
        file_path = base_path / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  ✅ {file_name}: {description} ({file_size:,} bytes)")
        else:
            print(f"  ❌ {file_name}: {description} - NO ENCONTRADO")
            all_ok = False
    
    print()
    
    # Verificar integración con FastAPI
    print("🔗 Verificando integración con FastAPI:")
    main_py = Path(__file__).parent / "app" / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = {
            "StaticFiles": "Montaje de archivos estáticos",
            "landing_page": "Función landing page",
            "/static": "Ruta de estáticos",
            "frontend": "Referencia al directorio frontend",
        }
        
        for check, description in checks.items():
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NO ENCONTRADO")
                all_ok = False
    else:
        print("  ❌ app/main.py no encontrado")
        all_ok = False
    
    print()
    
    # Verificar documentación
    print("📚 Verificando documentación:")
    docs_file = Path(__file__).parent / "docs" / "FRONTEND_README.md"
    if docs_file.exists():
        print("  ✅ FRONTEND_README.md encontrado")
    else:
        print("  ⚠️  FRONTEND_README.md no encontrado")
    
    print()
    print("=" * 60)
    
    if all_ok:
        print("✅ ¡Todo está correctamente configurado!")
        print()
        print("📋 Próximos pasos:")
        print("  1. Ejecuta: uvicorn app.main:app --reload")
        print("  2. Abre: http://localhost:8000/")
        print("  3. ¡Disfruta tu landing page!")
        return 0
    else:
        print("❌ Algunos archivos faltan. Por favor revisa la estructura.")
        return 1

if __name__ == "__main__":
    sys.exit(check_frontend_structure())
