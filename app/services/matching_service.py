"""
Servicios de matchmaking entre estudiantes y oportunidades laborales (ASYNC)
Algoritmos de compatibilidad y recomendación
Completamente asincrónico con AsyncSession
"""
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Student, JobMatchEvent
from app.schemas import JobItem, MatchResult, StudentPublic, MatchingCriteria
from app.services.text_vectorization_service import text_vectorization_service
from app.providers import job_provider_manager


class MatchingService:
    """Servicio principal de matching y recomendaciones"""
    
    def __init__(self):
        self.min_match_score = 0.1  # Puntuación mínima para considerar match
    
    def calculate_match_score(
        self,
        student_skills: List[str],
        student_projects: List[str],
        job_description: str,
        weights: Dict[str, float] = None
    ) -> Tuple[float, Dict]:
        """
        Calcular score de compatibilidad entre ESTUDIANTE y OFERTA DE TRABAJO.
        
        ✅ RESPONSABILIDAD CORRECTA: Aquí va la LÓGICA DE NEGOCIO
        (pesos, heurísticas, políticas).
        
        La función matemática pura (get_similarity) vive en text_vectorization_service.
        Esta función APLICA POLÍTICAS sobre esa función.
        
        Args:
            student_skills: Lista de habilidades del estudiante
            student_projects: Lista de proyectos/experiencias
            job_description: Descripción de la oferta
            weights: Dict opcional para pesos personalizados
            
        Returns:
            Tupla (score: float [0-1], details: dict)
        """
        # POLÍTICA #1: Pesos por defecto (35% skills, 65% projects)
        w = weights or {"skills": 0.35, "projects": 0.65}
        
        # POLÍTICA #2: Aumentar peso de projects si hay muchos
        # (Heurística: más experiencia proyectos → más relevante)
        num_projects = len([p for p in (student_projects or []) if p])
        if num_projects >= 3:
            w = w.copy()
            w["projects"] += 0.10
            w["skills"] = max(0, w.get("skills", 0) - 0.10)
        
        # Normalizar pesos para que sumen 1.0
        total_weight = max(1e-9, w.get("skills", 0) + w.get("projects", 0))
        w_normalized = {
            "skills": w.get("skills", 0) / total_weight,
            "projects": w.get("projects", 0) / total_weight
        }
        
        # Usar función MATEMÁTICA PURA de text_vectorization_service
        skills_text = " ".join([str(s).strip() for s in (student_skills or []) if s])
        projects_text = " ".join([str(p).strip() for p in (student_projects or []) if p])
        job_clean = str(job_description or "")[:50000]
        
        # Calcular similitud TF-IDF (función pura, sin negocio)
        skill_similarity = text_vectorization_service.get_similarity(skills_text, job_clean) if skills_text else 0.0
        project_similarity = text_vectorization_service.get_similarity(projects_text, job_clean) if projects_text else 0.0
        
        # Aplicar pesos (LÓGICA DE NEGOCIO)
        base_score = (skill_similarity * w_normalized["skills"]) + (project_similarity * w_normalized["projects"])
        base_score = max(0.0, min(base_score, 1.0))
        
        # Retornar con detalles para auditoría
        details = {
            "skill_similarity": round(float(skill_similarity), 6),
            "project_similarity": round(float(project_similarity), 6),
            "weights_used": w_normalized,
            "matching_skills": list(set([s for s in (student_skills or []) if s])),  # Unique
            "matching_projects": list(set([p for p in (student_projects or []) if p]))  # Unique
        }
        
        return base_score, details
    
    def build_student_query(self, student: Student) -> str:
        """Construir query de búsqueda basada en el perfil del estudiante"""
        skills = json.loads(student.skills or "[]")
        projects = json.loads(student.projects or "[]")
        
        # Seleccionar las mejores habilidades y proyectos para la query
        top_skills = skills[:5]  # Top 5 habilidades
        top_projects = projects[:3]  # Top 3 proyectos
        
        # Construir query combinando habilidades y proyectos
        query_parts = []
        
        if top_skills:
            query_parts.extend(top_skills)
        
        if top_projects:
            # Extraer palabras clave de proyectos
            for project in top_projects:
                project_keywords = self._extract_keywords_from_project(project)
                query_parts.extend(project_keywords[:2])  # Max 2 keywords por proyecto
        
        # Añadir términos genéricos si no hay suficiente información
        if not query_parts:
            if student.program:
                query_parts.append(student.program.lower())
            query_parts.extend(["intern", "junior", "trainee"])
        
        return " ".join(query_parts[:8])  # Limitar a 8 términos max
    
    def _extract_keywords_from_project(self, project_description: str) -> List[str]:
        """Extraer palabras clave relevantes de la descripción de un proyecto"""
        # Palabras clave técnicas comunes en proyectos
        tech_keywords = {
            "web", "mobile", "app", "api", "database", "dashboard", "machine learning",
            "data analysis", "visualization", "backend", "frontend", "fullstack",
            "automation", "algorithm", "prediction", "classification", "regression"
        }
        
        project_lower = project_description.lower()
        found_keywords = []
        
        for keyword in tech_keywords:
            if keyword in project_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:3]  # Max 3 keywords
    
    async def find_job_recommendations(self, session: AsyncSession, student_id: int, 
                                     location: Optional[str] = None,
                                     limit: int = 10) -> Dict[str, any]:
        """Encontrar recomendaciones de trabajos para un estudiante - ASYNC"""
        result = await session.execute(select(Student).where(Student.id == student_id))
        student = result.scalars().first()
        
        if not student:
            raise ValueError(f"Estudiante con ID {student_id} no encontrado")
        
        # Construir query de búsqueda
        search_query = self.build_student_query(student)
        
        # Buscar trabajos usando los proveedores
        raw_jobs = await job_provider_manager.search_all_providers(
            query=search_query,
            location=location,
            limit_per_provider=limit
        )
        
        # Calcular scores de matching
        scored_jobs = []
        for job in raw_jobs:
            score, details = self._calculate_job_match_score(student, job)
            if score >= self.min_match_score:
                job.match_score = round(score, 3)
                scored_jobs.append((job, score, details))
        
        # Ordenar por score descendente
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        # Tomar los mejores matches
        best_jobs = [job for job, score, details in scored_jobs[:limit]]
        
        # Registrar evento de matching
        match_event = JobMatchEvent(
            student_id=student_id,
            query=search_query,
            num_results=len(best_jobs),
            source="internal_matching"
        )
        session.add(match_event)
        await session.commit()
        
        return {
            "student_id": student_id,
            "jobs": best_jobs,
            "total_found": len(raw_jobs),
            "matches_found": len(best_jobs),
            "query_used": search_query,
            "generated_at": datetime.utcnow()
        }
    
    def _calculate_job_match_score(self, student: Student, job: JobItem) -> Tuple[float, Dict]:
        """
        Calcular score de compatibilidad entre estudiante y trabajo.
        
        SIMPLIFICADO: Solo usa TF-IDF matching sin boosts fringe.
        
        Algoritmo:
        1. Extrae skills y projects del estudiante
        2. Calcula similitud TF-IDF: skills vs job description
        3. Calcula similitud TF-IDF: projects vs job description
        4. Combina con pesos dinámicos (skills 35%, projects 65%)
        5. Retorna score final [0..1]
        
        Returns:
            (final_score, details) donde details contiene:
            - skill_similarity: similaridad TF-IDF de skills
            - project_similarity: similaridad TF-IDF de projects
            - matching_skills: skills que aparecen textuales en job description
            - matching_projects: projects que aparecen textuales en job description
            - weights_used: pesos usados para combinar
        """
        student_skills = json.loads(student.skills or "[]")
        student_projects = json.loads(student.projects or "[]")
        
        # --- Pesos dinámicos: ajustar según cantidad de proyectos
        # Lógica: projects = experiencia práctica (más importante)
        weights = {"skills": 0.35, "projects": 0.65}
        
        # Aumentar peso de projects si el estudiante tiene muchos
        num_projects = len([p for p in student_projects if p])
        if num_projects >= 3:
            weights["projects"] += 0.10
            weights["skills"] -= 0.10
        
        # Normalizar para que sumen 1.0
        total_w = weights["skills"] + weights["projects"]
        if total_w > 0:
            weights["skills"] /= total_w
            weights["projects"] /= total_w
        
        # Usar el nuevo calculate_match_score de esta clase (con lógica de negocio)
        job_description = f"{job.title} {job.description or ''}"
        base_score, match_details = self.calculate_match_score(
            student_skills, student_projects, job_description, weights=weights
        )
        
        # Retornar score directo sin boosts adicionales
        return base_score, match_details
    
    async def filter_students_by_criteria(self, session: AsyncSession, criteria: MatchingCriteria) -> List[MatchResult]:
        """Filtrar estudiantes basado en criterios específicos - ASYNC"""
        # Obtener todos los estudiantes activos
        result = await session.execute(
            select(Student).where(Student.is_active == True)
        )
        students = result.scalars().all()
        
        matched_students = []
        
        for student in students:
            student_skills = json.loads(student.skills or "[]")
            student_projects = json.loads(student.projects or "[]")
            
            # Verificar criterios de skills
            if criteria.skills:
                required_skills = [s.lower() for s in criteria.skills]
                student_skills_lower = [s.lower() for s in student_skills]
                
                matching_skills = [
                    skill for skill in required_skills
                    if any(req_skill in skill for req_skill in student_skills_lower)
                ]
                
                if len(matching_skills) < len(required_skills) * 0.5:  # Al menos 50% match
                    continue
            else:
                matching_skills = []
            
            # Verificar criterios de proyectos
            if criteria.projects:
                required_projects = [p.lower() for p in criteria.projects]
                student_projects_lower = [p.lower() for p in student_projects]
                
                matching_projects = []
                for req_proj in required_projects:
                    for stud_proj in student_projects_lower:
                        if req_proj in stud_proj:
                            matching_projects.append(stud_proj)
                            break
                
                if len(matching_projects) == 0:
                    continue
            else:
                matching_projects = []
            
            # Calcular score basado en matches
            skill_score = len(matching_skills) / max(len(criteria.skills or []), 1)
            project_score = len(matching_projects) / max(len(criteria.projects or []), 1)
            final_score = (skill_score * 0.7) + (project_score * 0.3)
            
            # Crear resultado de match
            student_public = StudentPublic(
                id=student.id,
                name=student.name,
                program=student.program,
                skills=student_skills,
                soft_skills=json.loads(student.soft_skills or "[]"),
                projects=student_projects
            )
            
            match_result = MatchResult(
                student=student_public,
                score=round(final_score, 3),
                matching_skills=matching_skills,
                matching_projects=matching_projects
            )
            
            matched_students.append(match_result)
        
        # Ordenar por score descendente
        matched_students.sort(key=lambda x: x.score, reverse=True)
        
        return matched_students
    
    async def get_featured_students(self, session: AsyncSession, limit: int = 10) -> List[StudentPublic]:
        """Obtener estudiantes destacados basado en métricas de calidad - ASYNC"""
        result = await session.execute(
            select(Student).where(Student.is_active == True)
        )
        students = result.scalars().all()
        
        scored_students = []
        
        for student in students:
            score = self._calculate_student_featured_score(student)
            scored_students.append((student, score))
        
        # Ordenar por score y tomar los mejores
        scored_students.sort(key=lambda x: x[1], reverse=True)
        
        featured = []
        for student, score in scored_students[:limit]:
            student_public = StudentPublic(
                id=student.id,
                name=student.name,
                program=student.program,
                skills=json.loads(student.skills or "[]"),
                soft_skills=json.loads(student.soft_skills or "[]"),
                projects=json.loads(student.projects or "[]")
            )
            featured.append(student_public)
        
        return featured
    
    def _calculate_student_featured_score(self, student: Student) -> float:
        """Calcular score para estudiante destacado"""
        skills = json.loads(student.skills or "[]")
        soft_skills = json.loads(student.soft_skills or "[]")
        projects = json.loads(student.projects or "[]")
        
        # Factores de scoring
        skill_score = min(len(skills) / 10.0, 1.0)  # Normalizado a 10 habilidades
        soft_skill_score = min(len(soft_skills) / 5.0, 1.0)  # Normalizado a 5 habilidades
        project_score = min(len(projects) / 3.0, 1.0)  # Normalizado a 3 proyectos
        
        # Bonus por actividad reciente
        activity_bonus = 0.0
        if student.last_active:
            days_since_active = (datetime.utcnow() - student.last_active).days
            if days_since_active <= 30:
                activity_bonus = 0.2 * (30 - days_since_active) / 30
        
        # Score final ponderado
        final_score = (
            skill_score * 0.4 +
            project_score * 0.3 +
            soft_skill_score * 0.2 +
            activity_bonus * 0.1
        )
        
        return min(final_score, 1.0)


# Instancia global del servicio
matching_service = MatchingService()
