#!/usr/bin/env python3
"""
Script de validación del refactoring de OCC scraper

Verifica que todos los cambios necesarios hayan sido implementados correctamente:
1. job_scraper_worker.py - Métodos OCC-específicos agregados
2. occ_data_transformer.py - Nuevo archivo creado
3. app/schemas/job.py - Schemas creados
4. app/api/routes/jobs.py - Rutas creadas
5. job_posting.py - método to_dict_public() correcto

Uso:
    python verify_occ_refactoring.py
"""

import os
import ast
import sys
from pathlib import Path

def check_file_exists(path: str) -> bool:
    """Verificar que archivo existe"""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {path}")
    return exists

def check_method_exists(file_path: str, method_name: str) -> bool:
    """Verificar que método existe en archivo Python"""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                return True
        return False
    except Exception as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
        return False

def check_class_exists(file_path: str, class_name: str) -> bool:
    """Verificar que clase existe en archivo Python"""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return True
        return False
    except Exception as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🔍 VALIDACIÓN DE REFACTORING OCC SCRAPER")
    print("="*70 + "\n")
    
    root_path = "/Users/sparkmachine/MoirAI"
    all_checks_passed = True
    
    # PASO 1: Verificar archivos existen
    print("📋 PASO 1: Verificar archivos existen")
    print("-" * 70)
    
    files_to_check = [
        "app/services/job_scraper_worker.py",
        "app/services/occ_data_transformer.py",
        "app/schemas/job.py",
        "app/api/routes/jobs.py",
        "app/models/job_posting.py",
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(root_path, file_path)
        if not check_file_exists(full_path):
            all_checks_passed = False
    
    print()
    
    # PASO 2: Verificar métodos en job_scraper_worker.py
    print("📋 PASO 2: Verificar métodos OCC en job_scraper_worker.py")
    print("-" * 70)
    
    scraper_worker_file = os.path.join(root_path, "app/services/job_scraper_worker.py")
    methods_to_check = [
        "scrape_occ_jobs_by_skill",
        "scrape_occ_job_detail",
        "scrape_occ_batch",
    ]
    
    for method in methods_to_check:
        exists = check_method_exists(scraper_worker_file, method)
        status = "✅" if exists else "❌"
        print(f"{status} Método: {method}")
        if not exists:
            all_checks_passed = False
    
    print()
    
    # PASO 3: Verificar clase en occ_data_transformer.py
    print("📋 PASO 3: Verificar clase OCCDataTransformer")
    print("-" * 70)
    
    transformer_file = os.path.join(root_path, "app/services/occ_data_transformer.py")
    if check_class_exists(transformer_file, "OCCDataTransformer"):
        print("✅ Clase: OCCDataTransformer")
        
        # Verificar métodos principales
        methods = ["transform", "batch_transform", "transform_sync"]
        for method in methods:
            exists = check_method_exists(transformer_file, method)
            status = "✅" if exists else "❌"
            print(f"  {status} Método: {method}")
            if not exists:
                all_checks_passed = False
    else:
        print("❌ Clase: OCCDataTransformer no encontrada")
        all_checks_passed = False
    
    print()
    
    # PASO 4: Verificar schemas
    print("📋 PASO 4: Verificar Response Schemas")
    print("-" * 70)
    
    schemas_file = os.path.join(root_path, "app/schemas/job.py")
    schemas = [
        "JobDetailResponse",
        "JobSearchResponse",
        "JobScrapeRequest",
        "JobScrapeResponse",
    ]
    
    for schema in schemas:
        exists = check_class_exists(schemas_file, schema)
        status = "✅" if exists else "❌"
        print(f"{status} Schema: {schema}")
        if not exists:
            all_checks_passed = False
    
    print()
    
    # PASO 5: Verificar rutas de API
    print("📋 PASO 5: Verificar API Routes")
    print("-" * 70)
    
    routes_file = os.path.join(root_path, "app/api/routes/jobs.py")
    route_functions = [
        "trigger_occ_scraping",
        "search_jobs",
        "get_job_detail",
        "health_check",
    ]
    
    for func in route_functions:
        exists = check_method_exists(routes_file, func)
        status = "✅" if exists else "❌"
        print(f"{status} Ruta: {func}")
        if not exists:
            all_checks_passed = False
    
    print()
    
    # PASO 6: Verificar método to_dict_public
    print("📋 PASO 6: Verificar método to_dict_public en JobPosting")
    print("-" * 70)
    
    job_posting_file = os.path.join(root_path, "app/models/job_posting.py")
    exists = check_method_exists(job_posting_file, "to_dict_public")
    status = "✅" if exists else "❌"
    print(f"{status} Método: to_dict_public")
    if not exists:
        all_checks_passed = False
    
    print()
    
    # RESULTADO FINAL
    print("="*70)
    if all_checks_passed:
        print("✅ ¡TODAS LAS VALIDACIONES PASARON!")
        print("="*70)
        print("\nSiguientes pasos:")
        print("1. Ejecutar tests unitarios: pytest app/tests/")
        print("2. Verificar imports: python -m py_compile app/services/job_scraper_worker.py")
        print("3. Hacer commit: git add -A && git commit -m 'feat: OCC scraper integration'")
        return 0
    else:
        print("❌ ALGUNAS VALIDACIONES FALLARON")
        print("="*70)
        print("\nRe-ejecuta el refactoring y verifica los errores")
        return 1

if __name__ == "__main__":
    sys.exit(main())
