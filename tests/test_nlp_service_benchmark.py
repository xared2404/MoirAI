#!/usr/bin/env python3
"""
Script de análisis de rendimiento y benchmarking del NLPService
Mide tiempos de ejecución y genera estadísticas
"""

import time
import json
from statistics import mean, stdev, median
from app.services.nlp_service import NLPService, _clean_text


class NLPServiceBenchmark:
    """Clase para realizar benchmarking del NLPService"""
    
    def __init__(self):
        self.nlp_service = NLPService()
        self.results = {}
    
    def benchmark_clean_text(self, iterations: int = 1000):
        """Benchmark de la función _clean_text"""
        print("\n" + "="*80)
        print(f"BENCHMARK: _clean_text ({iterations} iteraciones)")
        print("="*80)
        
        test_texts = [
            "Python",
            "Machine Learning & AI/ML",
            "C++ Developer con experiencia en Node.js y C#",
            "Proyecto de análisis de datos con Pandas, NumPy y Scikit-learn",
            "Desarrollador full-stack: React, Vue.js, Angular, Django, FastAPI",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10,
        ]
        
        times_by_text = {}
        
        for text in test_texts:
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                _clean_text(text)
                end = time.perf_counter()
                times.append(end - start)
            
            avg_time = mean(times)
            times_by_text[text[:50]] = {
                "avg_ms": avg_time * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
                "median_ms": median(times) * 1000,
                "stdev_ms": stdev(times) * 1000 if len(times) > 1 else 0,
                "total_time_ms": sum(times) * 1000
            }
            
            print(f"\n📝 '{text[:50]}...'")
            print(f"   Promedio:  {avg_time*1000:.4f} ms")
            print(f"   Min/Max:   {min(times)*1000:.4f} / {max(times)*1000:.4f} ms")
            print(f"   Mediana:   {median(times)*1000:.4f} ms")
        
        self.results["clean_text"] = times_by_text
        return times_by_text
    
    def benchmark_tfidf_cosine(self, iterations: int = 100):
        """Benchmark de la función _tfidf_cosine"""
        print("\n" + "="*80)
        print(f"BENCHMARK: _tfidf_cosine ({iterations} iteraciones)")
        print("="*80)
        
        test_pairs = [
            ("Python", "Python"),
            ("Python developer", "Python programmer"),
            ("Machine learning", "Artificial intelligence"),
            (
                "Desarrollador con experiencia en Python, SQL y Machine Learning",
                "Backend engineer con conocimiento en Django y PostgreSQL"
            ),
        ]
        
        times_by_pair = {}
        
        for text_a, text_b in test_pairs:
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                self.nlp_service._tfidf_cosine(text_a, text_b)
                end = time.perf_counter()
                times.append(end - start)
            
            avg_time = mean(times)
            key = f"{text_a[:30]}... vs {text_b[:30]}..."
            times_by_pair[key] = {
                "avg_ms": avg_time * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
                "median_ms": median(times) * 1000,
                "stdev_ms": stdev(times) * 1000 if len(times) > 1 else 0,
            }
            
            print(f"\n🔍 '{key}'")
            print(f"   Promedio:  {avg_time*1000:.4f} ms")
            print(f"   Min/Max:   {min(times)*1000:.4f} / {max(times)*1000:.4f} ms")
        
        self.results["tfidf_cosine"] = times_by_pair
        return times_by_pair
    
    def benchmark_matching_items(self, iterations: int = 500):
        """Benchmark de la función _matching_items"""
        print("\n" + "="*80)
        print(f"BENCHMARK: _matching_items ({iterations} iteraciones)")
        print("="*80)
        
        test_cases = [
            (
                ["Python", "Java", "C++"],
                "Buscamos desarrollador Python con experiencia en Java",
                "Pequeña lista (3 items)"
            ),
            (
                ["Python", "Java", "C++", "JavaScript", "TypeScript", "Go", "Rust"],
                "Backend developer con Python, Java y experiencia en microservicios",
                "Lista mediana (7 items)"
            ),
            (
                [f"Skill_{i}" for i in range(50)],
                "Buscamos un experto en Skill_5, Skill_10, Skill_25 y Skill_45",
                "Lista grande (50 items)"
            ),
        ]
        
        times_by_case = {}
        
        for items, text, description in test_cases:
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                self.nlp_service._matching_items(items, text)
                end = time.perf_counter()
                times.append(end - start)
            
            avg_time = mean(times)
            times_by_case[description] = {
                "avg_ms": avg_time * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
                "median_ms": median(times) * 1000,
                "num_items": len(items),
                "text_length": len(text),
            }
            
            print(f"\n✓ {description}")
            print(f"   Promedio:      {avg_time*1000:.4f} ms")
            print(f"   Num items:     {len(items)}")
            print(f"   Text length:   {len(text)}")
        
        self.results["matching_items"] = times_by_case
        return times_by_case
    
    def benchmark_calculate_match_score(self, iterations: int = 50):
        """Benchmark del método calculate_match_score completo"""
        print("\n" + "="*80)
        print(f"BENCHMARK: calculate_match_score ({iterations} iteraciones)")
        print("="*80)
        
        test_cases = [
            {
                "skills": ["Python", "SQL"],
                "projects": ["API REST"],
                "job_desc": "Python developer needed",
                "description": "Caso simple (2 skills, 1 project)"
            },
            {
                "skills": ["Python", "Java", "C++", "JavaScript", "Go"],
                "projects": [
                    "Sistema de recomendación en Python",
                    "API REST con FastAPI",
                    "Microservicio en Go"
                ],
                "job_desc": "Buscamos full-stack developer con experiencia en Python, Java y sistemas distribuidos",
                "description": "Caso intermedio (5 skills, 3 projects)"
            },
            {
                "skills": [f"Skill_{i}" for i in range(15)],
                "projects": [f"Proyecto_{i}: descripción detallada del proyecto" for i in range(10)],
                "job_desc": "Descripción larga de trabajo " * 20,
                "description": "Caso complejo (15 skills, 10 projects)"
            },
        ]
        
        times_by_case = {}
        
        for test_case in test_cases:
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                self.nlp_service.calculate_match_score(
                    test_case["skills"],
                    test_case["projects"],
                    test_case["job_desc"]
                )
                end = time.perf_counter()
                times.append(end - start)
            
            avg_time = mean(times)
            times_by_case[test_case["description"]] = {
                "avg_ms": avg_time * 1000,
                "min_ms": min(times) * 1000,
                "max_ms": max(times) * 1000,
                "median_ms": median(times) * 1000,
                "stdev_ms": stdev(times) * 1000 if len(times) > 1 else 0,
                "num_skills": len(test_case["skills"]),
                "num_projects": len(test_case["projects"]),
                "job_desc_length": len(test_case["job_desc"]),
            }
            
            print(f"\n🎯 {test_case['description']}")
            print(f"   Promedio:       {avg_time*1000:.4f} ms")
            print(f"   Min/Max:        {min(times)*1000:.4f} / {max(times)*1000:.4f} ms")
            print(f"   Num skills:     {len(test_case['skills'])}")
            print(f"   Num projects:   {len(test_case['projects'])}")
        
        self.results["calculate_match_score"] = times_by_case
        return times_by_case
    
    def benchmark_stress_test(self):
        """Prueba de estrés con muchas llamadas simultaneas"""
        print("\n" + "="*80)
        print("STRESS TEST: 1000 llamadas secuenciales")
        print("="*80)
        
        skills_list = [
            ["Python", "SQL", "Machine Learning"],
            ["Java", "Spring Boot", "Kubernetes"],
            ["JavaScript", "React", "Node.js"],
        ]
        
        projects_list = [
            ["Proyecto A", "Proyecto B"],
            ["Proyecto C"],
            ["Proyecto D", "Proyecto E", "Proyecto F"],
        ]
        
        job_descs = [
            "Backend developer con Python",
            "Frontend engineer con React",
            "DevOps engineer con Kubernetes",
        ]
        
        start_total = time.perf_counter()
        
        for i in range(1000):
            skills = skills_list[i % len(skills_list)]
            projects = projects_list[i % len(projects_list)]
            job_desc = job_descs[i % len(job_descs)]
            
            self.nlp_service.calculate_match_score(skills, projects, job_desc)
        
        end_total = time.perf_counter()
        total_time = end_total - start_total
        avg_per_call = total_time / 1000
        
        print(f"\n✓ 1000 llamadas completadas")
        print(f"  Tiempo total:     {total_time:.4f} s")
        print(f"  Tiempo promedio:  {avg_per_call*1000:.4f} ms por llamada")
        print(f"  Llamadas/segundo: {1000/total_time:.2f}")
        
        self.results["stress_test"] = {
            "total_calls": 1000,
            "total_time_s": total_time,
            "avg_per_call_ms": avg_per_call * 1000,
            "calls_per_second": 1000 / total_time
        }
        
        return self.results["stress_test"]
    
    def generate_benchmark_report(self):
        """Genera reporte de benchmarking"""
        print("\n" + "="*80)
        print("REPORTE DE BENCHMARKING")
        print("="*80)
        
        report_file = "/Users/sparkmachine/MoirAI/nlp_service_benchmark_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Reporte detallado guardado en: {report_file}")
        
        # Mostrar resumen
        print("\n📊 RESUMEN DE BENCHMARKS:")
        for test_name, results in self.results.items():
            print(f"\n{test_name}:")
            if isinstance(results, dict):
                if "avg_ms" in results:
                    print(f"  Tiempo promedio: {results['avg_ms']:.4f} ms")
                elif "total_time_s" in results:
                    print(f"  Tiempo total: {results['total_time_s']:.4f} s")
                    print(f"  Llamadas/segundo: {results['calls_per_second']:.2f}")
    
    def run_all_benchmarks(self):
        """Ejecuta todos los benchmarks"""
        print("\n" + "🔥 "*40)
        print("INICIANDO BENCHMARKING DEL NLPService")
        print("🔥 "*40)
        
        self.benchmark_clean_text(iterations=1000)
        self.benchmark_tfidf_cosine(iterations=100)
        self.benchmark_matching_items(iterations=500)
        self.benchmark_calculate_match_score(iterations=50)
        self.benchmark_stress_test()
        
        self.generate_benchmark_report()
        
        print("\n" + "⚡ "*40)
        print("BENCHMARKING COMPLETADO")
        print("⚡ "*40 + "\n")


def main():
    """Función principal"""
    benchmark = NLPServiceBenchmark()
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()
