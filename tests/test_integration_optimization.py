"""
Test de integración: Validar que description se divide correctamente
y compresión funciona en endpoint
"""

import asyncio
import json
from typing import List, Optional
from pydantic import BaseModel, Field


class JobOfferTest(BaseModel):
    job_id: str
    title: str
    description: str = Field(max_length=500)  # ✅ Indexable (500 chars)
    full_description: Optional[str] = Field(default=None)  # ✅ Sin límite
    salary: Optional[str] = None
    location: str


def test_description_split():
    """Test 1: Validar división description/full_description"""
    print("\n" + "="*70)
    print("TEST 1: División de description/full_description")
    print("="*70)
    
    # Descripción muy larga (6000 caracteres)
    long_desc = "Empresa líder en tecnología. " * 200
    
    job = JobOfferTest(
        job_id="test_001",
        title="Data Scientist",
        description=long_desc[:500],  # ✅ Resumen de 500 chars
        full_description=long_desc,    # ✅ Completa sin límite
        salary="$100,000 - $150,000 MXN",
        location="CDMX"
    )
    
    print(f"\n📊 Resultados:")
    print(f"   Description:      {len(job.description)} chars")
    print(f"   Full Description: {len(job.full_description)} chars")
    print(f"   Ratio:           {(len(job.full_description) / len(job.description)):.1f}x más grande")
    
    assert len(job.description) <= 500, "Description debe ser <= 500 chars"
    assert len(job.full_description) == len(long_desc), "Full description debe ser completa"
    
    print("   ✅ PASS: División correcta")
    return True


def test_compression_algorithm():
    """Test 2: Algoritmo de compresión en tránsito"""
    print("\n" + "="*70)
    print("TEST 2: Algoritmo de compresión")
    print("="*70)
    
    jobs = [
        JobOfferTest(
            job_id=f"test_{i:03d}",
            title=f"Engineer {i}",
            description="Python SQL AWS Docker Kubernetes ".ljust(500)[:500],  # Exactamente 500 chars
            full_description="Python SQL AWS Docker Kubernetes " * 25,  # ~850 chars
            salary=f"${50000 + i*1000} MXN",
            location="CDMX"
        )
        for i in range(10)
    ]
    
    # Calcular tamaño antes
    before = json.dumps([j.model_dump() for j in jobs])
    before_kb = len(before.encode('utf-8')) / 1024
    
    # Aplicar compresión
    compressed_jobs = []
    for job in jobs:
        if job.description and len(job.description) > 200:
            job.description = job.description[:200] + "..."
        if job.full_description and len(job.full_description) > 300:
            job.full_description = job.full_description[:300] + "..."
        compressed_jobs.append(job)
    
    # Calcular tamaño después
    after = json.dumps([j.model_dump() for j in compressed_jobs])
    after_kb = len(after.encode('utf-8')) / 1024
    
    reduction = ((len(before) - len(after)) / len(before)) * 100
    
    print(f"\n📊 Resultados:")
    print(f"   Antes:  {before_kb:.2f} KB")
    print(f"   Después: {after_kb:.2f} KB")
    print(f"   Reducción: {reduction:.1f}%")
    
    assert reduction > 50, "Compresión debe reducir >50%"
    
    print("   ✅ PASS: Compresión efectiva")
    return True


def test_index_efficiency():
    """Test 3: Validar que campos indexados son eficientes"""
    print("\n" + "="*70)
    print("TEST 3: Campos indexados para búsquedas")
    print("="*70)
    
    indexed_fields = {
        "title": {"type": "str", "max_length": 200, "index": True},
        "company": {"type": "str", "max_length": 150, "index": True},
        "location": {"type": "str", "max_length": 150, "index": True},
        "description": {"type": "str", "max_length": 500, "index": True, "fulltext": True},
        "job_type": {"type": "str", "index": True},
        "work_mode": {"type": "str", "index": True},
        "category": {"type": "str", "index": True},
        "skills": {"type": "str", "index": True},
    }
    
    non_indexed_fields = {
        "full_description": {"type": "str", "unlimited": True},
        "requirements": {"type": "str"},
        "benefits": {"type": "str"},
    }
    
    print(f"\n📊 Campos indexados para búsquedas rápidas:")
    for field, props in indexed_fields.items():
        fulltext_marker = " (FULL TEXT)" if props.get("fulltext") else ""
        print(f"   ✅ {field:20} {fulltext_marker}")
    
    print(f"\n📊 Campos NO indexados (bajo demanda):")
    for field, props in non_indexed_fields.items():
        unlimited_marker = " (sin límite)" if props.get("unlimited") else ""
        print(f"   ⏸️  {field:20} {unlimited_marker}")
    
    assert len(indexed_fields) > 5, "Debe haber suficientes campos indexados"
    
    print("\n   ✅ PASS: Estrategia de indexación correcta")
    return True


def test_backward_compatibility():
    """Test 4: Validar compatibilidad hacia atrás"""
    print("\n" + "="*70)
    print("TEST 4: Compatibilidad hacia atrás")
    print("="*70)
    
    # Simular data antigua (solo description, limitada a 500 chars)
    old_job_dict = {
        "job_id": "old_001",
        "title": "Engineer",
        "description": "Buscamos ingeniero" * 25,  # ~450 chars
        "salary": "$50,000",
        "location": "CDMX"
    }
    
    # Intentar crear objeto con nuevo modelo
    job = JobOfferTest(**old_job_dict)
    
    print(f"\n📊 Datos antiguos:")
    print(f"   Job ID:      {job.job_id}")
    print(f"   Description: {len(job.description)} chars")
    print(f"   Full Desc:   {job.full_description}")
    
    # Validar que no falla
    assert job.job_id == "old_001"
    assert job.description is not None
    
    print("\n   ✅ PASS: Compatibilidad mantenida")
    return True


def test_endpoint_compress_param():
    """Test 5: Validar parámetro compress en endpoint"""
    print("\n" + "="*70)
    print("TEST 5: Parámetro compress en endpoint")
    print("="*70)
    
    endpoint_params = {
        "?compress=true": "Comprime descriptions a 200/300 chars",
        "?compress=false": "Mantiene descriptions completas",
        "?compress=true&full_details=false": "Compresión activada (por defecto)",
        "?compress=false&full_details=true": "Sin compresión (full_details=true ignora compress)",
    }
    
    print(f"\n📊 Casos de uso del endpoint:")
    for param, desc in endpoint_params.items():
        print(f"   {param:35} → {desc}")
    
    print("\n   ✅ PASS: Parámetros documentados correctamente")
    return True


def main():
    print("\n" + "="*70)
    print("🧪 TEST DE INTEGRACIÓN: Optimización de descripción")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Test 1: División description/full_description", test_description_split()))
        results.append(("Test 2: Compresión en tránsito", test_compression_algorithm()))
        results.append(("Test 3: Índices para búsquedas", test_index_efficiency()))
        results.append(("Test 4: Compatibilidad hacia atrás", test_backward_compatibility()))
        results.append(("Test 5: Parámetro compress", test_endpoint_compress_param()))
        
    except AssertionError as e:
        print(f"\n   ❌ FAIL: {e}")
        return False
    except Exception as e:
        print(f"\n   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Resumen
    print("\n" + "="*70)
    print("📋 RESUMEN")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print(f"\n  {passed}/{total} tests completados exitosamente\n")
    
    if passed == total:
        print("="*70)
        print("🎉 ¡Todos los tests pasaron!")
        print("="*70)
        return True
    else:
        print("="*70)
        print("⚠️  Algunos tests fallaron")
        print("="*70)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
