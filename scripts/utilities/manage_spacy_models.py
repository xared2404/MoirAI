#!/usr/bin/env python3
"""
Gestor de modelos spaCy cacheados para MoirAI

Propósito:
- Listar modelos instalados y su tamaño
- Verificar integridad de modelos
- Limpiar caché de descargas
- Obtener información de uso de disco
- Pre-calentar modelos para producción
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BLUE}╔════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║{NC} {text}")
    print(f"{BLUE}╚════════════════════════════════════════════╝{NC}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}❌ {text}{NC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{NC}")

def print_info(text: str):
    """Print info message"""
    print(f"{CYAN}ℹ️  {text}{NC}")

def get_spacy_model_path() -> Path:
    """Get spaCy models directory"""
    try:
        import spacy
        # Obtener directorio de spacy
        spacy_path = Path(spacy.__file__).parent
        models_path = spacy_path.parent / "site-packages"
        return models_path
    except:
        # Fallback a ubicación estándar
        return Path.home() / ".cache" / "spacy"

def get_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except:
        pass
    return total

def format_size(bytes_size: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def check_model_installed(model_name: str) -> bool:
    """Check if spaCy model is installed and loadable"""
    try:
        import spacy
        spacy.load(model_name)
        return True
    except:
        return False

def list_models() -> Dict[str, Dict]:
    """List all installed spaCy models with info"""
    print_info("Buscando modelos instalados...")
    
    models = {}
    required_models = ['es_core_news_md', 'en_core_web_md']
    
    try:
        import spacy
        
        for model_name in required_models:
            try:
                nlp = spacy.load(model_name)
                
                # Obtener información del modelo
                meta = nlp.meta
                
                # Encontrar directorio del modelo
                model_path = None
                try:
                    # Intenta obtener la ruta del modelo
                    import importlib.util
                    spec = importlib.util.find_spec(model_name)
                    if spec and spec.origin:
                        model_path = Path(spec.origin).parent
                except:
                    pass
                
                size_bytes = get_directory_size(model_path) if model_path else 0
                
                models[model_name] = {
                    'installed': True,
                    'version': meta.get('version', 'unknown'),
                    'language': meta.get('lang', 'unknown'),
                    'size': format_size(size_bytes),
                    'size_bytes': size_bytes,
                    'path': str(model_path) if model_path else 'unknown',
                }
            except Exception as e:
                models[model_name] = {
                    'installed': False,
                    'error': str(e),
                }
    except Exception as e:
        print_error(f"Error accessing spaCy: {e}")
        return models
    
    return models

def verify_models() -> bool:
    """Verify all required models are installed and working"""
    print_header("Verificando Integridad de Modelos spaCy")
    
    models = list_models()
    all_ok = True
    
    for model_name, info in models.items():
        if info.get('installed'):
            print_success(f"{model_name}: Instalado ({info['version']})")
            print_info(f"  Tamaño: {info['size']}")
            print_info(f"  Idioma: {info['language']}")
            print_info(f"  Ruta: {info['path']}")
        else:
            print_error(f"{model_name}: NO instalado")
            print_warning(f"  Error: {info.get('error', 'unknown')}")
            all_ok = False
    
    return all_ok

def install_models():
    """Install all required spaCy models"""
    print_header("Instalando Modelos spaCy Necesarios")
    
    required_models = ['es_core_news_md', 'en_core_web_md']
    
    for model_name in required_models:
        if check_model_installed(model_name):
            print_success(f"Modelo {model_name} ya está instalado")
        else:
            print_info(f"Instalando {model_name}...")
            try:
                result = subprocess.run(
                    ['python', '-m', 'spacy', 'download', model_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print_success(f"Modelo {model_name} instalado correctamente")
                else:
                    print_error(f"Error instalando {model_name}")
                    print_warning(result.stderr)
            except Exception as e:
                print_error(f"Excepción al instalar {model_name}: {e}")

def get_total_cache_size() -> Tuple[int, str]:
    """Calculate total size of all models"""
    models = list_models()
    total = sum(info.get('size_bytes', 0) for info in models.values() if info.get('installed'))
    return total, format_size(total)

def warm_up_cache():
    """Pre-load all models to warm up cache"""
    print_header("Pre-calentando Caché de Modelos spaCy")
    
    required_models = ['es_core_news_md', 'en_core_web_md']
    
    try:
        import spacy
        
        for model_name in required_models:
            print_info(f"Cargando {model_name}...")
            try:
                nlp = spacy.load(model_name)
                
                # Pre-processar texto de prueba
                test_texts = [
                    "This is a test in English",
                    "Esta es una prueba en español",
                ]
                
                for text in test_texts:
                    doc = nlp(text)
                    # Acceder a diferentes componentes para calentar caché
                    _ = doc.ents
                    _ = doc.noun_chunks
                    _ = [token.text for token in doc]
                
                print_success(f"{model_name} precargado en caché")
                
            except Exception as e:
                print_error(f"Error precargando {model_name}: {e}")
                
    except Exception as e:
        print_error(f"Error en warm-up: {e}")

def show_statistics():
    """Show cache statistics"""
    print_header("Estadísticas de Caché de Modelos spaCy")
    
    models = list_models()
    
    print_info("Modelos Instalados:")
    for model_name, info in models.items():
        status = "✓" if info.get('installed') else "✗"
        size_str = info.get('size', 'desconocido')
        print(f"  {status} {model_name}: {size_str}")
    
    total_bytes, total_str = get_total_cache_size()
    print(f"\n{CYAN}Uso Total de Disco:{NC} {total_str}")
    
    # Mostrar configuración del servidor
    print(f"\n{CYAN}Configuración Recomendada para Servidor:{NC}")
    print(f"  • RAM mínima: 2GB (para cargar ambos modelos)")
    print(f"  • Espacio en disco: ~150MB (ambos modelos)")
    print(f"  • Tiempo de inicio: ~2-3s (primera carga)")
    print(f"  • Tiempo de carga posterior: <100ms (desde caché)")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Gestor de modelos spaCy cacheados para MoirAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  python manage_spacy_models.py verify     # Verificar modelos
  python manage_spacy_models.py list       # Listar modelos instalados
  python manage_spacy_models.py install    # Instalar modelos faltantes
  python manage_spacy_models.py warmup     # Pre-calentar caché
  python manage_spacy_models.py stats      # Mostrar estadísticas
        '''
    )
    
    parser.add_argument(
        'command',
        choices=['verify', 'list', 'install', 'warmup', 'stats', 'all'],
        help='Comando a ejecutar'
    )
    
    args = parser.parse_args()
    
    print_header("🚀 Gestor de Modelos spaCy - MoirAI")
    
    if args.command == 'verify':
        success = verify_models()
        return 0 if success else 1
    
    elif args.command == 'list':
        models = list_models()
        print_info("Modelos encontrados:")
        for model_name, info in models.items():
            if info.get('installed'):
                print_success(f"  {model_name} v{info['version']}")
                print_info(f"    Tamaño: {info['size']}")
            else:
                print_error(f"  {model_name}: NO INSTALADO")
    
    elif args.command == 'install':
        install_models()
        verify_models()
    
    elif args.command == 'warmup':
        warm_up_cache()
    
    elif args.command == 'stats':
        show_statistics()
    
    elif args.command == 'all':
        # Ejecutar todas las verificaciones
        verify_models()
        warm_up_cache()
        show_statistics()
    
    print()
    return 0

if __name__ == '__main__':
    sys.exit(main())
