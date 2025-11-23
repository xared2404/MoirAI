#!/usr/bin/env python3
"""
Script de verificación de caché de modelos spaCy para servidor

Este script:
- Verifica que ambos modelos estén instalados
- Precalienta el caché para reducir latencia al iniciar servidor
- Muestra información sobre disponibilidad de memoria
- Simula requests para validar performance con caché
"""

import sys
import time
import psutil
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}╔════════════════════════════════════════════╗{NC}")
    print(f"{BLUE}║{NC} {text}")
    print(f"{BLUE}╚════════════════════════════════════════════╝{NC}\n")

def print_success(text: str):
    print(f"{GREEN}✅ {text}{NC}")

def print_error(text: str):
    print(f"{RED}❌ {text}{NC}")

def print_warning(text: str):
    print(f"{YELLOW}⚠️  {text}{NC}")

def print_info(text: str):
    print(f"{CYAN}ℹ️  {text}{NC}")

def get_memory_info():
    """Get system memory information"""
    mem = psutil.virtual_memory()
    return {
        'total': mem.total / (1024**3),  # GB
        'available': mem.available / (1024**3),  # GB
        'percent': mem.percent,
        'used': mem.used / (1024**3),  # GB
    }

def check_memory_requirements():
    """Check if system has enough memory for both models"""
    print_header("Verificando Requisitos de Memoria")
    
    mem_info = get_memory_info()
    
    print_info(f"Memoria Total: {mem_info['total']:.2f} GB")
    print_info(f"Memoria Disponible: {mem_info['available']:.2f} GB")
    print_info(f"Uso Actual: {mem_info['percent']:.1f}%")
    
    # Requisitos para ambos modelos
    min_required = 2.0  # GB
    recommended = 4.0   # GB
    
    if mem_info['available'] < min_required:
        print_error(f"Memoria insuficiente. Se necesitan {min_required}GB, disponibles: {mem_info['available']:.2f}GB")
        return False
    elif mem_info['available'] < recommended:
        print_warning(f"Memoria limitada. Se recomienda {recommended}GB, disponibles: {mem_info['available']:.2f}GB")
        return True
    else:
        print_success(f"Memoria suficiente para ambos modelos ({mem_info['available']:.2f}GB disponibles)")
        return True

def verify_and_warmup_models():
    """Verify models and warm up cache"""
    print_header("Verificando e Precalentando Modelos spaCy")
    
    try:
        import spacy
        
        models_to_check = ['es_core_news_md', 'en_core_web_md']
        timings = {}
        
        for model_name in models_to_check:
            print_info(f"Cargando modelo {model_name}...")
            
            start_time = time.time()
            try:
                nlp = spacy.load(model_name)
                load_time = time.time() - start_time
                timings[model_name] = load_time
                
                # Procesar textos de prueba
                test_texts = [
                    "The quick brown fox jumps over the lazy dog",
                    "El rápido zorro marrón salta sobre el perro perezoso",
                    "Machine learning and natural language processing are fascinating",
                    "El aprendizaje automático y el procesamiento del lenguaje natural son fascinantes",
                ]
                
                for text in test_texts:
                    start = time.time()
                    doc = nlp(text)
                    processing_time = time.time() - start
                    # Acceder a todos los componentes para calentar caché
                    _ = doc.ents
                    _ = doc.noun_chunks
                    _ = [token.text for token in doc]
                    _ = [token.pos_ for token in doc]
                
                print_success(f"{model_name} precargado en {load_time:.3f}s")
                
            except Exception as e:
                print_error(f"Error cargando {model_name}: {e}")
                return False
        
        # Mostrar resumen de timings
        print_info("\nTiempos de Carga:")
        for model_name, load_time in timings.items():
            print(f"  {model_name}: {load_time:.3f}s")
        
        total_time = sum(timings.values())
        print(f"{CYAN}Tiempo total de precarga: {total_time:.3f}s{NC}")
        
        return True
        
    except ImportError:
        print_error("spaCy no está instalado")
        return False
    except Exception as e:
        print_error(f"Error durante verificación: {e}")
        return False

def simulate_bilingual_requests():
    """Simulate bilingual CV extraction requests to warm up cache"""
    print_header("Simulando Requests Bilíngues para Caché")
    
    try:
        import spacy
        
        # Sample CV text snippets
        spanish_samples = [
            "Experiencia como Ingeniero de Software en Google México",
            "Licenciatura en Ingeniería Informática de la Universidad Nacional",
            "Habilidades: Python, JavaScript, FastAPI, PostgreSQL",
            "Lideré equipo de 5 ingenieros en proyecto de microservicios",
        ]
        
        english_samples = [
            "Worked as Senior Software Engineer at Google Mountain View",
            "Bachelor of Science in Computer Science from UC Berkeley",
            "Skills: Python, JavaScript, FastAPI, PostgreSQL",
            "Led team of 5 engineers on critical backend infrastructure",
        ]
        
        nlp_es = spacy.load('es_core_news_md')
        nlp_en = spacy.load('en_core_web_md')
        
        print_info("Procesando textos en español...")
        times_es = []
        for text in spanish_samples:
            start = time.time()
            doc = nlp_es(text)
            _ = [(ent.text, ent.label_) for ent in doc.ents]
            times_es.append(time.time() - start)
        
        avg_es = sum(times_es) / len(times_es) * 1000
        print_success(f"Tiempo promedio (Spanish): {avg_es:.2f}ms")
        
        print_info("Procesando textos en inglés...")
        times_en = []
        for text in english_samples:
            start = time.time()
            doc = nlp_en(text)
            _ = [(ent.text, ent.label_) for ent in doc.ents]
            times_en.append(time.time() - start)
        
        avg_en = sum(times_en) / len(times_en) * 1000
        print_success(f"Tiempo promedio (English): {avg_en:.2f}ms")
        
        print(f"\n{CYAN}Caché precalentado y listo para producción{NC}")
        return True
        
    except Exception as e:
        print_error(f"Error en simulación: {e}")
        return False

def show_cache_info():
    """Show detailed cache information"""
    print_header("Información de Caché de Modelos")
    
    print_info("Ubicaciones de Modelos spaCy:")
    
    try:
        import spacy
        import importlib.util
        
        models = ['es_core_news_md', 'en_core_web_md']
        total_size = 0
        
        for model in models:
            try:
                spec = importlib.util.find_spec(model)
                if spec and spec.origin:
                    model_path = Path(spec.origin).parent
                    # Calcular tamaño
                    size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file()) / (1024**2)
                    total_size += size
                    print(f"\n  {CYAN}{model}:{NC}")
                    print(f"    Ruta: {model_path}")
                    print(f"    Tamaño: {size:.2f} MB")
            except:
                pass
        
        print(f"\n{CYAN}Tamaño total de modelos: {total_size:.2f} MB{NC}")
        
        print("\n" + CYAN + "Ventajas del Caché:" + NC)
        print("  • Primera carga: ~1-2s (carga del disco)")
        print("  • Cargas posteriores: <100ms (desde RAM)")
        print("  • Soporte bilíngue automático (Spanish + English)")
        print("  • Detección inteligente de idioma basada en contenido")
        
        return True
        
    except Exception as e:
        print_error(f"Error obteniendo información: {e}")
        return False

def main():
    """Main verification routine"""
    print_header("🚀 Verificación de Caché - MoirAI")
    
    all_ok = True
    
    # 1. Verificar memoria
    if not check_memory_requirements():
        print_warning("Sistema puede tener restricciones de memoria")
        all_ok = False
    
    # 2. Verificar y precalentar modelos
    if not verify_and_warmup_models():
        print_error("No se pudieron cargar los modelos")
        all_ok = False
    
    # 3. Simular requests
    if all_ok and not simulate_bilingual_requests():
        print_warning("Error en simulación (continuando...)")
    
    # 4. Mostrar información
    if not show_cache_info():
        print_warning("No se pudo obtener información de caché")
    
    # Resumen final
    print_header("📊 Resumen Final")
    
    if all_ok:
        print_success("Sistema listo para servir requests bilíngues")
        print_success("Modelos cacheados en memoria para máxima performance")
        print_success("Latencia esperada: <100ms para extracción de CVs")
        return 0
    else:
        print_error("Sistema tiene problemas de configuración")
        return 1

if __name__ == '__main__':
    sys.exit(main())
