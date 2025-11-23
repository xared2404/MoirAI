"""
Endpoints para gestión de estudiantes - CRUD completo (ASYNC)
Incluye operaciones para crear, leer, actualizar y eliminar estudiantes
considerando historias de usuario y flujos de trabajo académicos
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
import hashlib
from datetime import datetime, timedelta

from app.core.database import get_session
from app.models import Student, AuditLog, Company
from app.schemas import (
    StudentProfile, StudentCreate, StudentUpdate, StudentSkillsUpdate, ResumeUploadRequest,
    ResumeAnalysisResponse, UserContext, BaseResponse, PaginatedResponse,
    StudentPublic
)
from app.services.text_vectorization_service import text_vectorization_service, TermExtractor
from app.services.cv_extractor_v2_spacy import CVExtractorV2
from app.utils.file_processing import extract_text_from_upload, extract_text_from_upload_async, CVFileValidator
from app.middleware.auth import AuthService
from app.core.config import settings

router = APIRouter(prefix="/students", tags=["students"])


async def _log_audit_action(session: AsyncSession, action: str, resource: str, 
                     actor: UserContext, success: bool = True, 
                     details: str = None, error_message: str = None):
    """Helper para registrar acciones de auditoría de forma asincrónica"""
    audit_log = AuditLog(
        actor_role=actor.role,
        actor_id=str(actor.user_id) if actor.user_id else actor.email,
        action=action,
        resource=resource,
        success=success,
        details=details,
        error_message=error_message
    )
    session.add(audit_log)
    await session.commit()


def _extract_resume_analysis(resume_text: str) -> dict:
    """
    Procesar análisis de CV para extraer skills, soft_skills y proyectos estructurados.
    
    Usa analyze_document() de text_vectorization_service para obtener features,
    luego los procesa según la lógica de negocio del endpoint.
    
    Retorna:
        Dict con: {
            "skills": [...],
            "soft_skills": [...],
            "projects": [...],
            "confidence": float
        }
    """
    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "skills": [],
            "soft_skills": [],
            "projects": [],
            "confidence": 0.0
        }
    
    try:
        # Usar analyze_document (genérico) para obtener features
        doc_analysis = text_vectorization_service.analyze_document(resume_text)
        
        # Extraer skills de los términos técnicos
        # technical_terms es List[Tuple[term, relevance]]
        technical_terms = doc_analysis.get("technical_terms", [])
        skills = [term[0] if isinstance(term, tuple) else term 
                 for term in technical_terms]
        skills = skills[:settings.MAX_SKILLS_EXTRACTED]
        
        # Extraer soft_skills de las habilidades blandas detectadas
        # soft_skills es List[Tuple[skill, relevance]]
        soft_skills_detected = doc_analysis.get("soft_skills", [])
        soft_skills = [skill[0] if isinstance(skill, tuple) else skill 
                      for skill in soft_skills_detected]
        soft_skills = soft_skills[:settings.MAX_SOFT_SKILLS_EXTRACTED]
        
        # Extraer proyectos de las keyphrases
        # keyphrases es List[Tuple[phrase, score]]
        keyphrases = doc_analysis.get("keyphrases", [])
        projects = []
        project_keywords = {
            "proyecto", "project", "desarrollo", "developed", "created", "implementé",
            "sistema", "system", "aplicación", "application", "plataforma", "platform"
        }
        
        for phrase, score in keyphrases:
            phrase_lower = str(phrase).lower()
            if any(kw in phrase_lower for kw in project_keywords):
                projects.append(str(phrase))
                if len(projects) >= settings.MAX_PROJECTS_EXTRACTED:
                    break
        
        # Calcular confianza basada en elementos encontrados
        total_found = len(skills) + len(soft_skills) + len(projects)
        confidence = min(1.0, total_found / 10.0)
        
        return {
            "skills": skills,
            "soft_skills": soft_skills,
            "projects": projects,
            "confidence": round(confidence, 2)
        }
    
    except Exception as e:
        # Fallback: análisis básico con hardcoded skills
        print(f"⚠️ Error en _extract_resume_analysis: {str(e)}, usando fallback básico")
        
        resume_clean = resume_text.lower()
        technical_skills = {
            "python", "java", "javascript", "typescript", "csharp", "cpp", "rust", "go",
            "react", "vue", "angular", "fastapi", "django", "flask", "spring",
            "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws",
            "machine learning", "tensorflow", "pytorch", "pandas", "numpy",
            "sql", "rest", "api", "microservices", "linux", "git"
        }
        
        skills = [skill for skill in technical_skills if skill in resume_clean]
        skills = skills[:settings.MAX_SKILLS_EXTRACTED]
        
        return {
            "skills": skills,
            "soft_skills": [],
            "projects": [],
            "confidence": min(1.0, len(skills) / 10.0)
        }


def _extract_harvard_cv_fields(resume_text: str) -> dict:
    """
    Extrae campos estructurados del CV en formato Harvard.
    
    Retorna:
        Dict con: {
            "objective": str,
            "education": List[Dict],
            "experience": List[Dict],
            "certifications": List[str],
            "languages": List[str]
        }
    
    📌 Estrategia de extracción:
    - Objetivo: Primeras 2-3 líneas, hasta 500 caracteres
    - Educación: Busca keywords (grado, degree, university, institución) + años
    - Experiencia: Busca keywords (position, role, company) + períodos
    - Certificaciones: Busca keywords (certification, course, certified)
    - Idiomas: Busca keywords (language, español, english, idioma) + nivel
    """
    import re
    
    if not resume_text or len(resume_text.strip()) < 50:
        return {
            "objective": None,
            "education": [],
            "experience": [],
            "certifications": [],
            "languages": []
        }
    
    try:
        lines = resume_text.split('\n')
        text_lower = resume_text.lower()
        
        # 1️⃣ Extraer OBJETIVO: Primeras líneas que no sean headers
        objective = None
        objective_lines = []
        for i, line in enumerate(lines[:10]):  # Primeras 10 líneas
            clean_line = line.strip()
            if clean_line and not any(keyword in clean_line.lower() for keyword in 
                                     ['educación', 'education', 'experiencia', 'experience', 
                                      'habilidades', 'skills', 'certificado', 'certification']):
                objective_lines.append(clean_line)
                if len(' '.join(objective_lines)) > 500:
                    break
        
        if objective_lines:
            objective = ' '.join(objective_lines)[:500]
        
        # 2️⃣ Extraer EDUCACIÓN
        education = []
        education_keywords = ['degree', 'bachelor', 'master', 'phd', 'diploma', 'certificate',
                            'grado', 'licenciatura', 'maestría', 'doctorado', 'formación',
                            'university', 'instituto', 'instituto', 'colegio']
        
        # Buscar secciones de educación
        education_section_match = re.search(
            r'(educación|education|formación|training)[\s\n]+(.*?)(?:experiencia|experience|habilidades|skills|certificado|certification|$)',
            text_lower, re.DOTALL | re.IGNORECASE
        )
        
        if education_section_match:
            education_text = education_section_match.group(2)
            # Extraer bloques de educación (delimitados por líneas vacías o bullets)
            edu_blocks = re.split(r'\n\s*\n', education_text)
            
            for block in edu_blocks[:5]:  # Máximo 5 registros
                if any(kw in block.lower() for kw in education_keywords):
                    lines_in_block = [l.strip() for l in block.split('\n') if l.strip()]
                    
                    edu_record = {
                        "institution": "",
                        "degree": "",
                        "field_of_study": "",
                        "graduation_year": None
                    }
                    
                    # Buscar año de graduación
                    year_match = re.search(r'(20\d{2}|19\d{2})', ' '.join(lines_in_block))
                    if year_match:
                        edu_record["graduation_year"] = int(year_match.group(1))
                    
                    # Asignar líneas a campos (heurística simple)
                    if len(lines_in_block) >= 1:
                        edu_record["institution"] = lines_in_block[0]
                    if len(lines_in_block) >= 2:
                        edu_record["degree"] = lines_in_block[1]
                    if len(lines_in_block) >= 3:
                        edu_record["field_of_study"] = lines_in_block[2]
                    
                    if edu_record["institution"]:
                        education.append(edu_record)
        
        # 3️⃣ Extraer EXPERIENCIA
        experience = []
        exp_section_match = re.search(
            r'(experiencia|experience|trabajos|jobs|profesional)[\s\n]+(.*?)(?:educación|education|habilidades|skills|certificado|certification|$)',
            text_lower, re.DOTALL | re.IGNORECASE
        )
        
        if exp_section_match:
            exp_text = exp_section_match.group(2)
            exp_blocks = re.split(r'\n\s*\n', exp_text)
            
            for block in exp_blocks[:5]:  # Máximo 5 registros
                lines_in_block = [l.strip() for l in block.split('\n') if l.strip()]
                
                if len(lines_in_block) >= 1:
                    exp_record = {
                        "position": "",
                        "company": "",
                        "start_date": None,
                        "end_date": None,
                        "description": ""
                    }
                    
                    # Buscar fechas (formato: 2020-2022, 2020/2022, 2020 - 2022)
                    dates_match = re.search(r'(20\d{2})[/-]?(20\d{2})?', ' '.join(lines_in_block))
                    if dates_match:
                        exp_record["start_date"] = dates_match.group(1)
                        if dates_match.group(2):
                            exp_record["end_date"] = dates_match.group(2)
                    
                    # Asignar líneas a campos
                    exp_record["position"] = lines_in_block[0]  # Primera línea: posición
                    if len(lines_in_block) >= 2:
                        exp_record["company"] = lines_in_block[1]  # Segunda: empresa
                    if len(lines_in_block) >= 3:
                        exp_record["description"] = ' '.join(lines_in_block[2:])  # Resto: descripción
                    
                    if exp_record["position"]:
                        experience.append(exp_record)
        
        # 4️⃣ Extraer CERTIFICACIONES
        certifications = []
        cert_keywords = ['certification', 'course', 'certified', 'award', 'certificación',
                        'curso', 'certificado', 'reconocimiento']
        
        cert_section_match = re.search(
            r'(certificado|certification|cursos|courses|capacitación|training)[\s\n]+(.*?)(?:idiomas|languages|habilidades|skills|$)',
            text_lower, re.DOTALL | re.IGNORECASE
        )
        
        if cert_section_match:
            cert_text = cert_section_match.group(2)
            cert_lines = [l.strip() for l in cert_text.split('\n') if l.strip()]
            certifications = cert_lines[:10]  # Máximo 10
        
        # 5️⃣ Extraer IDIOMAS
        languages = []
        lang_keywords = ['language', 'speak', 'fluent', 'idioma', 'habla', 'fluido',
                        'english', 'spanish', 'français', 'alemán', 'portuguese']
        
        lang_section_match = re.search(
            r'(idioma|language|lengua)[\s\n]+(.*?)(?:$)',
            text_lower, re.DOTALL | re.IGNORECASE
        )
        
        if lang_section_match:
            lang_text = lang_section_match.group(2)
            lang_lines = [l.strip() for l in lang_text.split('\n') if l.strip()]
            languages = lang_lines[:10]  # Máximo 10
        
        return {
            "objective": objective,
            "education": education,
            "experience": experience,
            "certifications": certifications,
            "languages": languages
        }
    
    except Exception as e:
        print(f"⚠️ Error en _extract_harvard_cv_fields: {str(e)}")
        return {
            "objective": None,
            "education": [],
            "experience": [],
            "certifications": [],
            "languages": []
        }


def _convert_to_student_profile(student: Student) -> StudentProfile:
    """Convierte modelo Student a StudentProfile"""
    # Extraer first_name y last_name del nombre combinado si no están presentes
    first_name = student.first_name
    last_name = student.last_name
    
    if not first_name or not last_name:
        parts = student.name.split(' ', 1)
        if not first_name:
            first_name = parts[0] if parts else ""
        if not last_name:
            last_name = parts[1] if len(parts) > 1 else ""
    
    return StudentProfile(
        id=student.id,
        name=student.name,
        role="student",  # ✅ INCLUIR role para que frontend siempre sepa el rol
        first_name=first_name,
        last_name=last_name,
        email=student.get_email(),  # ✅ DESENCRIPTAR email antes de retornar
        phone=student.get_phone(),  # ✅ DESENCRIPTAR phone antes de retornar
        bio=student.bio,
        program=student.program,
        career=student.career,
        semester=student.semester,
        skills=json.loads(student.skills or "[]"),
        soft_skills=json.loads(student.soft_skills or "[]"),
        projects=json.loads(student.projects or "[]"),
        # ✅ Harvard CV Fields (NEW)
        objective=student.objective,
        education=json.loads(student.education or "[]") if student.education else None,
        experience=json.loads(student.experience or "[]") if student.experience else None,
        certifications=json.loads(student.certifications or "[]") if student.certifications else None,
        languages=json.loads(student.languages or "[]") if student.languages else None,
        cv_uploaded=student.cv_uploaded or False,
        cv_filename=student.cv_filename,
        cv_upload_date=student.cv_upload_date,
        created_at=student.created_at,
        last_active=student.last_active,
        is_active=student.is_active
    )


# === CREAR ESTUDIANTES ===

@router.post("/", response_model=StudentProfile, status_code=201)
async def create_student(
    student_data: StudentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Crear estudiante manualmente sin currículum
    
    Historia de usuario: Como administrador, quiero poder registrar estudiantes
    manualmente para casos donde no tienen currículum digital disponible.
    """
    # Verificar permisos: solo estudiantes y administradores
    if current_user.role not in ["student", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo estudiantes y administradores pueden crear perfiles"
        )
    # Verificar si ya existe estudiante con ese email
    existing = (await session.execute(
        select(Student).where(Student.email == student_data.email)
    )).scalars().first()
    
    if existing:
        await _log_audit_action(
            session, "CREATE_STUDENT", f"email:{student_data.email}",
            current_user, success=False, error_message="Email ya existe"
        )
        raise HTTPException(
            status_code=409,
            detail="Ya existe un estudiante registrado con ese email"
        )
    
    # Crear estudiante
    student = Student(
        name=student_data.name,
        email=student_data.email,
        program=student_data.program,
        consent_data_processing=student_data.consent_data_processing,
        skills=json.dumps(student_data.skills),  # Convertir lista a JSON
        soft_skills=json.dumps(student_data.soft_skills),  # Convertir lista a JSON
        projects=json.dumps(student_data.projects)  # Convertir lista a JSON
    )
    
    try:
        session.add(student)
        await session.commit()
        await session.refresh(student)
        
        await _log_audit_action(
            session, "CREATE_STUDENT", f"student_id:{student.id}",
            current_user, details=f"Estudiante {student.name} creado manualmente"
        )
        
        return _convert_to_student_profile(student)
        
    except Exception as e:
        session.rollback()
        await _log_audit_action(
            session, "CREATE_STUDENT", f"email:{student_data.email}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error creando estudiante: {str(e)}"
        )


@router.post("/upload_resume", response_model=ResumeAnalysisResponse)
async def upload_resume(
    meta: str = Form(..., description="JSON con datos del estudiante"),
    file: UploadFile = File(..., description="Archivo de currículum (PDF/DOCX/TXT)"),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Subir y analizar currículum de estudiante
    
    Historia de usuario: Como estudiante, quiero subir mi currículum para que
    el sistema extraiga automáticamente mis habilidades y proyectos.
    
    Flujo:
    - Si el estudiante NO EXISTE: crea un nuevo registro y lo asocia al email
    - Si el estudiante YA EXISTE: actualiza su CV y habilidades extraídas
    
    Extrae habilidades técnicas, blandas y proyectos usando NLP
    """
    # Verificar permisos: solo estudiantes y administradores
    if current_user.role not in ["student", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo estudiantes y administradores pueden subir currículums"
        )
    # Validar metadatos
    try:
        meta_dict = json.loads(meta)
        student_data = ResumeUploadRequest(**meta_dict)
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"email:{meta[:50] if meta else 'unknown'}...",
            current_user, success=False, error_message=f"JSON inválido: {str(e)}"
        )
        raise HTTPException(
            status_code=400, 
            detail=f"Metadatos JSON inválidos: {str(e)}"
        )
    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"email:{meta_dict.get('email', 'unknown')}",
            current_user, success=False, error_message=f"Validación fallida: {str(e)}"
        )
        raise HTTPException(
            status_code=400, 
            detail=f"Validación de metadatos fallida: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Unexpected error in metadata parsing: {str(e)}")
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"email:unknown",
            current_user, success=False, error_message=f"Error inesperado: {str(e)}"
        )
        raise HTTPException(
            status_code=400, 
            detail=f"Error procesando metadatos: {str(e)}"
        )
    
    # Verificar si ya existe estudiante con ese email (usando hash para comparación segura)
    email_hash = hashlib.sha256(student_data.email.lower().encode()).hexdigest()
    result = await session.execute(
        select(Student).where(Student.email_hash == email_hash)
    )
    existing = result.scalars().first()
    
    # Extraer texto del archivo (usando versión async para no bloquear)
    try:
        resume_text = await extract_text_from_upload_async(file)
        if len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="El currículum debe contener al menos 50 caracteres de texto"
            )
    except Exception as e:
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"email:{student_data.email}",
            current_user, success=False, error_message=f"Error procesando archivo: {str(e)}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Error procesando archivo: {str(e)}"
        )
    
    # Análisis NLP
    try:
        analysis = _extract_resume_analysis(resume_text)
        harvard_fields = _extract_harvard_cv_fields(resume_text)
        
        # ✅ FALLBACK UNSUPERVISED: Si regex no encontró campos clave → usa unsupervised extractor
        if (not harvard_fields.get("education") and 
            not harvard_fields.get("experience") and
            len(resume_text.split()) > 50):  # Solo si hay suficiente contenido
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info("🔄 Regex no encontró campos, intentando extracción con spaCy NLP...")
            
            try:
                # Usar CVExtractorV2 con soporte bilingual automático (es + en)
                extractor = CVExtractorV2()
                spacy_result = extractor.extract(resume_text)
                
                # Convertir resultado de CVExtractorV2 (dataclass) a dict compatible con el código existente
                harvard_fields = {
                    "objective": spacy_result.objective,
                    "education": [
                        {
                            "institution": edu.institution,
                            "degree": edu.degree,
                            "field_of_study": edu.field,
                            "graduation_year": edu.end_year  # end_year es el año de graduación
                        }
                        for edu in spacy_result.education
                    ],
                    "experience": [
                        {
                            "position": exp.position,
                            "company": exp.company,
                            "start_date": str(exp.start_year) if exp.start_year else None,
                            "end_date": str(exp.end_year) if exp.end_year else None,
                            "description": exp.description
                        }
                        for exp in spacy_result.experience
                    ],
                    "certifications": spacy_result.certifications,
                    "languages": spacy_result.languages if isinstance(spacy_result.languages, list) else list(spacy_result.languages.keys()),
                    "extraction_method": "spacy_nlp_v2",
                    "confidence": 0.75  # CVExtractorV2 proporciona confianza a nivel de campos individuales
                }
                logger.info(f"✅ Extracción spaCy NLP exitosa. Educación: {len(spacy_result.education)}, Experiencia: {len(spacy_result.experience)}")
            
            except Exception as e:
                logger.error(f"❌ Error en extracción spaCy NLP: {str(e)}")
                # Fallback: mantener resultado de regex (podría estar vacío)
    
    except Exception as e:
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"email:{student_data.email}",
            current_user, success=False, error_message=f"Error en análisis NLP: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error en análisis NLP: {str(e)}"
        )
    
    # Si el estudiante YA EXISTE: actualizar su CV y habilidades
    if existing:
        student = existing
        action_type = "UPDATE"
        
        # Actualizar datos
        if student_data.name:
            student.name = student_data.name
            # Actualizar first_name y last_name del nombre
            name_parts = student_data.name.split(' ', 1)
            student.first_name = name_parts[0] if len(name_parts) > 0 else ""
            student.last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        if student_data.program:
            student.program = student_data.program
        
        # Actualizar CV análisis
        student.profile_text = resume_text[:20000]
        student.skills = json.dumps(analysis["skills"])
        student.soft_skills = json.dumps(analysis["soft_skills"])
        student.projects = json.dumps(analysis["projects"])
        
        # ✅ Guardar campos Harvard CV (NEW)
        student.objective = harvard_fields["objective"]
        student.education = json.dumps(harvard_fields["education"])
        student.experience = json.dumps(harvard_fields["experience"])
        student.certifications = json.dumps(harvard_fields["certifications"])
        student.languages = json.dumps(harvard_fields["languages"])
        
        # ✅ Actualizar banderas de CV (FIX: persistencia en BD)
        student.cv_uploaded = True
        student.cv_filename = file.filename
        student.cv_upload_date = datetime.utcnow()
        
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"student_id:{student.id}",
            current_user, details=f"Currículum actualizado para {student.name}"
        )
    
    # Si el estudiante NO EXISTE: crear uno nuevo
    else:
        action_type = "CREATE"
        # Extraer first_name y last_name del nombre completo
        name_parts = student_data.name.split(' ', 1) if student_data.name else ["", ""]
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        student = Student(
            name=student_data.name,
            first_name=first_name,
            last_name=last_name,
            program=student_data.program,
            consent_data_processing=True,
            profile_text=resume_text[:20000],  # Limitar texto almacenado
            skills=json.dumps(analysis["skills"]),
            soft_skills=json.dumps(analysis["soft_skills"]),
            projects=json.dumps(analysis["projects"]),
            # ✅ Guardar campos Harvard CV (NEW)
            objective=harvard_fields["objective"],
            education=json.dumps(harvard_fields["education"]),
            experience=json.dumps(harvard_fields["experience"]),
            certifications=json.dumps(harvard_fields["certifications"]),
            languages=json.dumps(harvard_fields["languages"]),
            # ✅ Establecer banderas de CV (FIX: persistencia en BD)
            cv_uploaded=True,
            cv_filename=file.filename,
            cv_upload_date=datetime.utcnow()
        )
        
        # Usar set_email() para encriptar automáticamente
        student.set_email(student_data.email)
        
        session.add(student)
        
        await _log_audit_action(
            session, "UPLOAD_RESUME", f"email:{student_data.email}",
            current_user, details=f"Nuevo estudiante registrado: {student_data.name}"
        )
    
    await session.commit()
    await session.refresh(student)
    
    await _log_audit_action(
        session, "UPLOAD_RESUME", f"student_id:{student.id}",
        current_user, details=f"Currículum procesado para {student.name}"
    )
    
    # Preparar respuesta
    student_profile = _convert_to_student_profile(student)
    
    return ResumeAnalysisResponse(
        student=student_profile,
        extracted_skills=analysis["skills"],
        extracted_soft_skills=analysis["soft_skills"],
        extracted_projects=analysis["projects"],
        analysis_confidence=analysis["confidence"]
    )


# === LEER ESTUDIANTES ===

@router.get("/", response_model=List[StudentProfile])
async def list_students(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de registros"),
    program: Optional[str] = Query(None, description="Filtrar por programa académico"),
    active_only: bool = Query(True, description="Solo estudiantes activos"),
    search: Optional[str] = Query(None, description="Buscar por nombre o email"),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Listar estudiantes con filtros y paginación
    
    Historia de usuario: Como administrador, quiero ver una lista paginada
    de estudiantes con opciones de búsqueda y filtrado para gestionar eficientemente
    la base de datos estudiantil.
    """
    # Verificar permisos: solo estudiantes y administradores
    if current_user.role not in ["student", "admin", "company"]:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado para listar estudiantes"
        )
    query = select(Student)
    
    # Aplicar filtros
    if active_only:
        query = query.where(Student.is_active == True)
    
    if program:
        query = query.where(Student.program.ilike(f"%{program}%"))
    
    if search:
        search_filter = (
            Student.name.ilike(f"%{search}%") |
            Student.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    # Aplicar paginación
    query = query.offset(skip).limit(min(limit, settings.MAX_PAGE_SIZE))
    
    students = await session.execute(query).scalars().all()
    
    await _log_audit_action(
        session, "LIST_STUDENTS", f"count:{len(students)}",
        current_user, details=f"Listado con filtros: program={program}, search={search}"
    )
    
    return [_convert_to_student_profile(student) for student in students]


@router.get("/stats", response_model=dict)
async def get_students_stats(
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Obtener estadísticas de estudiantes
    
    Historia de usuario: Como administrador, quiero ver estadísticas generales
    sobre los estudiantes para tomar decisiones informadas.
    """
    # Solo administradores pueden ver estadísticas
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden ver estadísticas"
        )
    # Contadores básicos
    total_students = await session.execute(select(func.count(Student.id))).scalars().first()
    active_students = (await session.execute(
        select(func.count(Student.id)).where(Student.is_active == True)
    )).scalars().first()
    
    # Estudiantes por programa
    programs_query = (await session.execute(
        select(Student.program, func.count(Student.id))
        .where(Student.is_active == True)
        .group_by(Student.program)
    )).all()
    
    programs_stats = {program: count for program, count in programs_query if program}
    
    # Estudiantes recientes (últimos 30 días)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_students = (await session.execute(
        select(func.count(Student.id))
        .where(Student.created_at >= thirty_days_ago)
    )).scalars().first()
    
    stats = {
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": total_students - active_students,
        "students_by_program": programs_stats,
        "recent_registrations_30d": recent_students,
        "generated_at": datetime.utcnow()
    }
    
    await _log_audit_action(
        session, "VIEW_STATS", "students_stats",
        current_user, details="Consulta de estadísticas de estudiantes"
    )
    
    return stats


# ============================================================================
# SPECIFIC STUDENT ENDPOINTS (Must be before generic /{student_id})
# ============================================================================

@router.get("/profile", response_model=StudentProfile)
async def get_student_profile(
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener el perfil completo del estudiante actual
    
    Retorna:
    - Información personal del estudiante
    - Habilidades técnicas y blandas
    - Proyectos realizados
    - Fechas de creación y última actividad
    """
    try:
        # Verificar que es estudiante
        if current_user.role != "student":
            raise HTTPException(
                status_code=403,
                detail="Solo estudiantes pueden acceder a sus perfiles"
            )
        
        # Buscar estudiante
        student = (await session.execute(
            select(Student).where(Student.email_hash == hashlib.sha256(current_user.email.encode()).hexdigest())
        )).scalars().first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Perfil de estudiante no encontrado")
        
        profile = _convert_to_student_profile(student)
        
        await _log_audit_action(
            session, "GET_PROFILE", f"student_id:{student.id}",
            current_user, details="Perfil obtenido exitosamente"
        )
        
        return profile
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting profile: {e}")
        await _log_audit_action(
            session, "GET_PROFILE", f"student_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-applications", response_model=dict)
async def get_my_applications(
    status: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener todas las aplicaciones del estudiante actual
    
    Parámetros:
    - status: Filtrar por estado (pending, accepted, rejected, withdrawn)
    - limit: Número de resultados por página (default: 20)
    - offset: Número de registros a saltar (default: 0)
    
    Retorna:
    - Lista de aplicaciones con detalles del empleador
    - Información de scoring de compatibilidad
    - Estado y fecha de aplicación
    """
    try:
        # Verificar que es estudiante
        if current_user.role != "student":
            raise HTTPException(
                status_code=403,
                detail="Solo estudiantes pueden ver sus aplicaciones"
            )
        
        # Buscar estudiante
        student = (await session.execute(
            select(Student).where(Student.email_hash == hashlib.sha256(current_user.email.encode()).hexdigest())
        )).scalars().first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Perfil de estudiante no encontrado")
        
        # Construir query de aplicaciones
        from app.models import JobApplicationDB
        query = select(JobApplicationDB).where(JobApplicationDB.user_id == student.id)
        
        # Filtrar por estado si se proporciona
        if status:
            query = query.where(JobApplicationDB.status == status)
        
        # Obtener total de registros
        total_query = select(JobApplicationDB).where(JobApplicationDB.user_id == student.id)
        if status:
            total_query = total_query.where(JobApplicationDB.status == status)
        total = len((await session.execute(total_query)).scalars().all())
        
        # Aplicar paginación
        applications = (await session.execute(query.offset(offset).limit(limit))).scalars().all()
        # Enriquecer con detalles de empleos
        result = []
        for app in applications:
            from app.models import JobPosition
            job = await session.get(JobPosition, app.job_position_id)
            if job:
                result.append({
                    "id": app.id,
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "status": app.status,
                    "applied_date": app.application_date,
                    "updated_date": app.updated_at,
                    "match_score": getattr(app, 'match_score', None)
                })
        
        await _log_audit_action(
            session, "GET_APPLICATIONS", f"student_id:{student.id}",
            current_user, details=f"Obtenidas {len(result)} aplicaciones"
        )
        
        # Retornar wrapper con aplicaciones y total
        return {
            "applications": result,
            "total": total,
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting applications: {e}")
        await _log_audit_action(
            session, "GET_APPLICATIONS", f"student_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=dict)
async def get_student_recommendations(
    limit: int = Query(10),
    current_user: UserContext = Depends(AuthService.get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener recomendaciones de empleos personalizadas para el estudiante
    
    Parámetros:
    - limit: Número máximo de recomendaciones (default: 10)
    
    Retorna:
    - Lista de empleos recomendados ordenados por score de compatibilidad
    - Score de matching incluido en cada recomendación
    """
    try:
        # Verificar que es estudiante
        if current_user.role != "student":
            raise HTTPException(
                status_code=403,
                detail="Solo estudiantes pueden obtener recomendaciones"
            )
        
        # Buscar estudiante
        student = (await session.execute(
            select(Student).where(Student.email_hash == hashlib.sha256(current_user.email.encode()).hexdigest())
        )).scalars().first()
        
        if not student:
            raise HTTPException(status_code=404, detail="Perfil de estudiante no encontrado")
        
        # Obtener habilidades del estudiante
        student_skills = json.loads(student.skills or "[]")
        
        # Buscar empleos activos
        from app.models import JobPosition
        all_jobs = (await session.execute(
            select(JobPosition).where(JobPosition.is_active == True)
        )).scalars().all()
        
        # Calcular scores de compatibilidad y ordenar
        scored_jobs = []
        for job in all_jobs:
            job_skills = json.loads(job.skills or "[]") if job.skills else []
            
            # Calcular score basado en coincidencia de skills
            matches = sum(1 for skill in student_skills if any(skill.lower() in js.lower() or js.lower() in skill.lower() for js in job_skills))
            score = (matches / len(job_skills)) * 100 if job_skills else 50
            
            scored_jobs.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description[:200] + "..." if len(job.description) > 200 else job.description,
                "match_score": round(score, 2),
                "job_type": job.job_type,
                "publication_date": job.publication_date
            })
        
        # Ordenar por score descendente
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Limitar resultados
        recommendations = scored_jobs[:limit]
        
        await _log_audit_action(
            session, "GET_RECOMMENDATIONS", f"student_id:{student.id}",
            current_user, details=f"Obtenidas {len(recommendations)} recomendaciones"
        )
        
        # Retornar wrapper con recomendaciones
        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "generated_at": datetime.now().isoformat(),
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        await _log_audit_action(
            session, "GET_RECOMMENDATIONS", f"student_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ✅ NUEVO ENDPOINT CRÍTICO: GET /me
# Obtiene el perfil COMPLETO del usuario autenticado desde BD
# Usado por frontend para sincronización de datos
# ============================================================================

@router.get("/me", response_model=StudentProfile)
async def get_my_profile(
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    ✅ ENDPOINT CRÍTICO: Obtener perfil COMPLETO del usuario autenticado
    
    Este es el endpoint que el frontend DEBE usar para obtener datos frescos de BD.
    
    Características:
    - ✅ No requiere parámetro de ID (usa usuario autenticado)
    - ✅ Retorna StudentProfile completo con CV, skills, etc.
    - ✅ Sincronización de datos del usuario
    - ✅ Recuperación de datos si localStorage fue borrado
    
    Retorna: StudentProfile con TODOS los campos:
    {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "program": "Ingeniería en Sistemas",
        "skills": ["Python", "FastAPI"],
        "soft_skills": ["Liderazgo"],
        "projects": ["Proyecto web"],
        "cv_uploaded": true,
        "cv_filename": "cv.pdf",
        "created_at": "2025-11-19T10:30:00",
        "last_active": "2025-11-19T12:00:00",
        "is_active": true
    }
    """
    try:
        # Verificar que es estudiante
        if current_user.role != "student":
            raise HTTPException(
                status_code=403,
                detail="Solo estudiantes pueden acceder a este endpoint"
            )
        
        # Buscar estudiante por su ID
        student = await session.get(Student, current_user.user_id)
        
        if not student:
            await _log_audit_action(
                session, "GET_PROFILE_ME", f"user_id:{current_user.user_id}",
                current_user, success=False, error_message="Estudiante no encontrado"
            )
            raise HTTPException(
                status_code=404,
                detail="Estudiante no encontrado"
            )
        
        # Actualizar last_active
        student.last_active = datetime.utcnow()
        session.add(student)
        await session.commit()
        
        await _log_audit_action(
            session, "GET_PROFILE_ME", f"student_id:{student.id}",
            current_user, details="Perfil completo del usuario autenticado"
        )
        
        return _convert_to_student_profile(student)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting my profile: {e}")
        await _log_audit_action(
            session, "GET_PROFILE_ME", f"user_id:{current_user.user_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}", response_model=StudentProfile)
async def get_student(
    student_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Obtener perfil de estudiante por ID
    
    Historia de usuario: Como administrador o estudiante, quiero ver los detalles
    completos de un perfil estudiantil para revisar información y hacer seguimiento.
    """
    # Verificar permisos básicos
    if current_user.role not in ["student", "admin", "company"]:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado para ver perfiles de estudiantes"
        )
    student = await session.get(Student, student_id)
    if not student:
        await _log_audit_action(
            session, "GET_STUDENT", f"student_id:{student_id}",
            current_user, success=False, error_message="Estudiante no encontrado"
        )
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar permisos: estudiantes solo pueden ver su propio perfil
    if current_user.role == "student" and current_user.user_id != student_id:
        await _log_audit_action(
            session, "GET_STUDENT", f"student_id:{student_id}",
            current_user, success=False, error_message="Acceso denegado"
        )
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para ver este perfil"
        )
    
    await _log_audit_action(
        session, "GET_STUDENT", f"student_id:{student_id}",
        current_user, details=f"Consulta de perfil de {student.name}"
    )
    
    return _convert_to_student_profile(student)


@router.get("/email/{email}", response_model=StudentProfile)
async def get_student_by_email(
    email: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Obtener estudiante por email
    
    Historia de usuario: Como administrador, quiero buscar estudiantes por email
    para resolver consultas de soporte o verificar registros.
    """
    # Solo administradores pueden buscar por email
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden buscar por email"
        )
    
    student = (await session.execute(
        select(Student).where(Student.email == email)
    )).scalars().first()
    
    if not student:
        await _log_audit_action(
            session, "GET_STUDENT_BY_EMAIL", f"email:{email}",
            current_user, success=False, error_message="Estudiante no encontrado"
        )
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    await _log_audit_action(
        session, "GET_STUDENT_BY_EMAIL", f"email:{email}",
        current_user, details=f"Búsqueda por email de {student.name}"
    )
    
    return _convert_to_student_profile(student)


# === ACTUALIZAR ESTUDIANTES ===

@router.put("/{student_id}", response_model=StudentProfile)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Actualizar datos básicos de estudiante
    
    Historia de usuario: Como estudiante, quiero poder actualizar mi información
    personal como nombre y programa académico para mantener mi perfil actualizado.
    """
    student = await session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar permisos: estudiantes solo pueden editar su propio perfil
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para editar este perfil"
        )
    
    # Registrar valores anteriores para auditoría
    old_values = {
        "name": student.name,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "phone": student.phone,
        "bio": student.bio,
        "program": student.program,
        "career": student.career,
        "semester": student.semester
    }
    
    # Actualizar campos proporcionados
    updated_fields = []
    if student_update.name is not None:
        student.name = student_update.name
        updated_fields.append("name")
    if student_update.first_name is not None:
        student.first_name = student_update.first_name
        updated_fields.append("first_name")
    if student_update.last_name is not None:
        student.last_name = student_update.last_name
        updated_fields.append("last_name")
    if student_update.phone is not None:
        student.set_phone(student_update.phone)
        updated_fields.append("phone")
    if student_update.bio is not None:
        student.bio = student_update.bio
        updated_fields.append("bio")
    if student_update.program is not None:
        student.program = student_update.program
        updated_fields.append("program")
    if student_update.career is not None:
        student.career = student_update.career
        updated_fields.append("career")
    if student_update.semester is not None:
        student.semester = student_update.semester
        updated_fields.append("semester")
    
    # ✅ Actualizar campos Harvard CV (NEW)
    if student_update.objective is not None:
        student.objective = student_update.objective
        updated_fields.append("objective")
    if student_update.education is not None:
        student.education = json.dumps(student_update.education)
        updated_fields.append("education")
    if student_update.experience is not None:
        student.experience = json.dumps(student_update.experience)
        updated_fields.append("experience")
    if student_update.certifications is not None:
        student.certifications = json.dumps(student_update.certifications)
        updated_fields.append("certifications")
    if student_update.languages is not None:
        student.languages = json.dumps(student_update.languages)
        updated_fields.append("languages")
    
    student.updated_at = datetime.utcnow()
    
    try:
        session.add(student)
        await session.commit()
        await session.refresh(student)
        
        await _log_audit_action(
            session, "UPDATE_STUDENT", f"student_id:{student_id}",
            current_user, 
            details=f"Campos actualizados: {', '.join(updated_fields)}. Valores anteriores: {old_values}"
        )
        
        return _convert_to_student_profile(student)
        
    except Exception as e:
        session.rollback()
        await _log_audit_action(
            session, "UPDATE_STUDENT", f"student_id:{student_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando estudiante: {str(e)}"
        )


@router.patch("/{student_id}/skills", response_model=StudentProfile)
async def update_student_skills(
    student_id: int,
    skills_data: StudentSkillsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Actualizar habilidades de estudiante manualmente
    
    Historia de usuario: Como estudiante, quiero poder agregar o quitar habilidades
    de mi perfil para reflejar mejor mi experiencia actual.
    
    Formato esperado (esquema StudentSkillsUpdate):
    {
        "skills": ["Python", "JavaScript"],
        "soft_skills": ["Trabajo en equipo", "Liderazgo"],
        "projects": ["Proyecto web", "App móvil"]
    }
    """
    student = await session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar permisos
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para editar este perfil"
        )
    
    # Validar y actualizar habilidades
    try:
        if skills_data.skills is not None:
            student.skills = json.dumps(skills_data.skills)
            
        if skills_data.soft_skills is not None:
            student.soft_skills = json.dumps(skills_data.soft_skills)
            
        if skills_data.projects is not None:
            student.projects = json.dumps(skills_data.projects)
        
        student.updated_at = datetime.utcnow()
        
        session.add(student)
        await session.commit()
        await session.refresh(student)
        
        await _log_audit_action(
            session, "UPDATE_SKILLS", f"student_id:{student_id}",
            current_user, details=f"Habilidades actualizadas manualmente"
        )
        
        return _convert_to_student_profile(student)
        
    except Exception as e:
        session.rollback()
        await _log_audit_action(
            session, "UPDATE_SKILLS", f"student_id:{student_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=400,
            detail=f"Error actualizando habilidades: {str(e)}"
        )


@router.patch("/{student_id}/activate", response_model=BaseResponse)
async def activate_student(
    student_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Reactivar estudiante (deshacer soft delete)
    
    Historia de usuario: Como administrador, quiero poder reactivar estudiantes
    que fueron marcados como inactivos por error.
    """
    # Solo administradores pueden reactivar
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden reactivar estudiantes"
        )
    
    student = await session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    if student.is_active:
        return BaseResponse(
            success=True,
            message="El estudiante ya está activo"
        )
    
    student.is_active = True
    student.updated_at = datetime.utcnow()
    
    session.add(student)
    await session.commit()
    
    await _log_audit_action(
        session, "ACTIVATE_STUDENT", f"student_id:{student_id}",
        current_user, details=f"Estudiante {student.name} reactivado"
    )
    
    return BaseResponse(
        success=True,
        message="Estudiante reactivado exitosamente"
    )


# === ELIMINAR ESTUDIANTES ===

@router.delete("/{student_id}", response_model=BaseResponse)
async def delete_student(
    student_id: int,
    permanent: bool = Query(False, description="Eliminación permanente (solo admin)"),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Eliminar estudiante (soft delete por defecto)
    
    Historia de usuario: Como administrador, quiero poder desactivar estudiantes
    que ya no están en la universidad, pero mantener sus datos para auditoría.
    En casos excepcionales, quiero poder eliminar permanentemente.
    """
    student = await session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Solo administradores pueden hacer eliminación permanente
    if permanent and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden eliminar permanentemente"
        )
    
    if permanent:
        # Eliminación permanente - solo admin
        try:
            await session.delete(student)
            await session.commit()
            
            await _log_audit_action(
                session, "DELETE_STUDENT_PERMANENT", f"student_id:{student_id}",
                current_user, details=f"Eliminación permanente de {student.name}"
            )
            
            return BaseResponse(
                success=True,
                message="Estudiante eliminado permanentemente"
            )
            
        except Exception as e:
            session.rollback()
            await _log_audit_action(
                session, "DELETE_STUDENT_PERMANENT", f"student_id:{student_id}",
                current_user, success=False, error_message=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error eliminando estudiante: {str(e)}"
            )
    else:
        # Soft delete: marcar como inactivo
        student.is_active = False
        student.updated_at = datetime.utcnow()
        
        session.add(student)
        await session.commit()
        
        await _log_audit_action(
            session, "DELETE_STUDENT_SOFT", f"student_id:{student_id}",
            current_user, details=f"Desactivación de {student.name}"
        )
        
        return BaseResponse(
            success=True,
            message="Estudiante desactivado exitosamente"
        )


# === OPERACIONES ESPECIALES ===

@router.post("/{student_id}/reanalyze", response_model=ResumeAnalysisResponse)
async def reanalyze_student_profile(
    student_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Re-analizar perfil de estudiante con NLP actualizado
    
    Historia de usuario: Como administrador, quiero poder re-procesar los currículums
    cuando el sistema de NLP mejore para actualizar automáticamente las habilidades.
    """
    student = await session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    if not student.profile_text:
        raise HTTPException(
            status_code=400,
            detail="No hay texto de currículum para re-analizar"
        )
    
    # Re-análisis NLP
    try:
        analysis = _extract_resume_analysis(student.profile_text)
    except Exception as e:
        await _log_audit_action(
            session, "REANALYZE_STUDENT", f"student_id:{student_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error en re-análisis: {str(e)}"
        )
    
    # Actualizar estudiante
    student.skills = json.dumps(analysis["skills"])
    student.soft_skills = json.dumps(analysis["soft_skills"])
    student.projects = json.dumps(analysis["projects"])
    student.updated_at = datetime.utcnow()
    
    session.add(student)
    await session.commit()
    await session.refresh(student)
    
    await _log_audit_action(
        session, "REANALYZE_STUDENT", f"student_id:{student_id}",
        current_user, details=f"Re-análisis NLP completado para {student.name}"
    )
    
    # Preparar respuesta
    student_profile = _convert_to_student_profile(student)
    
    return ResumeAnalysisResponse(
        student=student_profile,
        extracted_skills=analysis["skills"],
        extracted_soft_skills=analysis["soft_skills"],
        extracted_projects=analysis["projects"],
        analysis_confidence=analysis["confidence"]
    )


@router.post("/bulk-reanalyze", response_model=BaseResponse)
async def bulk_reanalyze_students(
    student_ids: List[int],
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Re-analizar múltiples estudiantes en lote
    
    Historia de usuario: Como administrador, quiero poder re-procesar múltiples
    currículums al mismo tiempo para optimizar el tiempo de actualización.
    """
    # Solo administradores pueden hacer operaciones en lote
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden realizar operaciones en lote"
        )
    
    if len(student_ids) > 50:
        raise HTTPException(
            status_code=400,
            detail="Máximo 50 estudiantes por operación en lote"
        )
    
    processed = 0
    errors = []
    
    for student_id in student_ids:
        try:
            student = await session.get(Student, student_id)
            if not student or not student.profile_text:
                errors.append(f"Estudiante {student_id}: sin texto de currículum")
                continue
            
            analysis = _extract_resume_analysis(student.profile_text)
            
            student.skills = json.dumps(analysis["skills"])
            student.soft_skills = json.dumps(analysis["soft_skills"])
            student.projects = json.dumps(analysis["projects"])
            student.updated_at = datetime.utcnow()
            
            session.add(student)
            processed += 1
            
        except Exception as e:
            errors.append(f"Estudiante {student_id}: {str(e)}")
    
    await session.commit()
    
    await _log_audit_action(
        session, "BULK_REANALYZE", f"count:{len(student_ids)}",
        current_user, 
        details=f"Procesados: {processed}, Errores: {len(errors)}"
    )
    
    message = f"Re-análisis completado. Procesados: {processed}"
    if errors:
        message += f", Errores: {len(errors)}"
    
    return BaseResponse(
        success=True,
        message=message
    )


# ============================================================================
# ✅ NUEVOS ENDPOINTS PARA GESTIÓN DE CV
# Descargar y eliminar contenido del CV del estudiante
# ============================================================================

@router.get("/{student_id}/resume", response_model=dict)
async def get_student_resume(
    student_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    📥 Descargar/Obtener contenido del CV del estudiante
    
    Retorna el texto extraído del CV almacenado en BD.
    
    Respuesta exitosa (200):
    {
        "student_id": 1,
        "cv_filename": "john_doe_cv.pdf",
        "cv_upload_date": "2025-11-15T10:00:00",
        "content": "Texto del CV extraído (máximo 20k caracteres)...",
        "content_size": 12345
    }
    
    Errores:
    - 404: Estudiante no existe o no tiene CV
    - 403: No tiene permisos para descargar
    
    Permisos:
    - Propietario del perfil (puede descargar su propio CV)
    - Administradores (pueden descargar cualquier CV)
    """
    try:
        # Buscar estudiante
        student = await session.get(Student, student_id)
        if not student:
            await _log_audit_action(
                session, "DOWNLOAD_RESUME", f"student_id:{student_id}",
                current_user, success=False, error_message="Estudiante no encontrado"
            )
            raise HTTPException(
                status_code=404,
                detail="Estudiante no encontrado"
            )
        
        # Verificar que tenga CV
        if not student.cv_uploaded or not student.profile_text:
            await _log_audit_action(
                session, "DOWNLOAD_RESUME", f"student_id:{student_id}",
                current_user, success=False, error_message="CV no disponible"
            )
            raise HTTPException(
                status_code=404,
                detail="Este estudiante no tiene CV disponible"
            )
        
        # Verificar permisos (solo propietario o admin)
        if current_user.role == "student" and current_user.user_id != student_id:
            await _log_audit_action(
                session, "DOWNLOAD_RESUME", f"student_id:{student_id}",
                current_user, success=False, error_message="Acceso denegado"
            )
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para descargar este CV"
            )
        
        # Registrar descarga en auditoría
        await _log_audit_action(
            session, "DOWNLOAD_RESUME", f"student_id:{student_id}",
            current_user, details=f"CV {student.cv_filename} descargado"
        )
        
        return {
            "student_id": student.id,
            "cv_filename": student.cv_filename,
            "cv_upload_date": student.cv_upload_date.isoformat() if student.cv_upload_date else None,
            "content": student.profile_text,
            "content_size": len(student.profile_text) if student.profile_text else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading resume: {e}")
        await _log_audit_action(
            session, "DOWNLOAD_RESUME", f"student_id:{student_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{student_id}/resume", response_model=BaseResponse)
async def delete_student_resume(
    student_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    🗑️ Eliminar/Limpiar el CV del estudiante
    
    Borra todos los datos relacionados con el CV:
    - cv_uploaded = False
    - cv_filename = None
    - profile_text = None (texto extraído)
    - skills = [] (habilidades extraídas)
    - soft_skills = [] (habilidades blandas extraídas)
    - projects = [] (proyectos extraídos)
    
    Respuesta exitosa (200):
    {
        "success": true,
        "message": "CV eliminado exitosamente"
    }
    
    Errores:
    - 404: Estudiante no existe
    - 400: Estudiante no tiene CV para eliminar
    - 403: No tiene permisos para eliminar
    
    Permisos:
    - Propietario del perfil (puede eliminar su propio CV)
    - Administradores (pueden eliminar cualquier CV)
    """
    try:
        # Buscar estudiante
        student = await session.get(Student, student_id)
        if not student:
            await _log_audit_action(
                session, "DELETE_RESUME", f"student_id:{student_id}",
                current_user, success=False, error_message="Estudiante no encontrado"
            )
            raise HTTPException(
                status_code=404,
                detail="Estudiante no encontrado"
            )
        
        # Verificar permisos
        if current_user.role == "student" and current_user.user_id != student_id:
            await _log_audit_action(
                session, "DELETE_RESUME", f"student_id:{student_id}",
                current_user, success=False, error_message="Acceso denegado"
            )
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para eliminar este CV"
            )
        
        # Verificar que tenga CV
        if not student.cv_uploaded:
            await _log_audit_action(
                session, "DELETE_RESUME", f"student_id:{student_id}",
                current_user, details="Intento de eliminar CV inexistente"
            )
            raise HTTPException(
                status_code=400,
                detail="Este estudiante no tiene CV para eliminar"
            )
        
        # Guardar nombre de archivo para auditoría
        old_filename = student.cv_filename
        
        # Limpiar TODOS los datos de CV
        student.cv_uploaded = False
        student.cv_filename = None
        student.cv_upload_date = None
        student.profile_text = None
        student.skills = json.dumps([])
        student.soft_skills = json.dumps([])
        student.projects = json.dumps([])
        student.updated_at = datetime.utcnow()
        
        session.add(student)
        await session.commit()
        await session.refresh(student)
        
        # Registrar en auditoría
        await _log_audit_action(
            session, "DELETE_RESUME", f"student_id:{student_id}",
            current_user, details=f"CV {old_filename} eliminado"
        )
        
        return BaseResponse(
            success=True,
            message="CV eliminado exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"Error deleting resume: {e}")
        await _log_audit_action(
            session, "DELETE_RESUME", f"student_id:{student_id}",
            current_user, success=False, error_message=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando CV"
        )


@router.get("/{student_id}/public", response_model=StudentPublic)
async def get_student_public_profile(
    student_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Obtener perfil público de estudiante (sin autenticación)
    
    Historia de usuario: Como empresa, quiero poder ver perfiles públicos
    de estudiantes para evaluar candidatos potenciales sin necesidad de
    autenticación completa.
    """
    student = await session.get(Student, student_id)
    if not student or not student.is_active:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    return StudentPublic(
        id=student.id,
        name=student.name,
        program=student.program,
        skills=json.loads(student.skills or "[]"),
        soft_skills=json.loads(student.soft_skills or "[]"),
        projects=json.loads(student.projects or "[]"),
        # ✅ ACTUALIZADO: Agregar CV metadata y timestamps
        cv_uploaded=student.cv_uploaded or False,
        cv_filename=student.cv_filename,
        created_at=student.created_at,
        last_active=student.last_active
    )


@router.post("/{student_id}/update-activity", response_model=BaseResponse)
async def update_student_activity(
    student_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Actualizar última actividad del estudiante
    
    Historia de usuario: Como sistema, quiero registrar cuando un estudiante
    está activo para mostrar información relevante a las empresas.
    """
    # Verificar permisos: estudiantes solo pueden actualizar su propia actividad
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=403,
            detail="Solo puede actualizar su propia actividad"
        )
    
    student = await session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    student.last_active = datetime.utcnow()
    session.add(student)
    await session.commit()
    
    return BaseResponse(
        success=True,
        message="Actividad actualizada"
    )


@router.get("/search/skills", response_model=List[StudentPublic])
async def search_students_by_skills(
    skills: List[str] = Query(..., description="Lista de habilidades a buscar"),
    min_matches: int = Query(1, ge=1, description="Mínimo de habilidades que deben coincidir"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: UserContext = Depends(AuthService.get_current_user)
):
    """
    Buscar estudiantes por habilidades específicas (búsqueda integrada de matching)
    
    Historia de usuario: Como empresa, quiero buscar estudiantes que tengan
    habilidades específicas que necesito para mis proyectos.
    
    🔒 Autorización:
    - Solo empresas verificadas y administradores
    - Los estudiantes no pueden usar este endpoint
    
    📊 Respuesta:
    - Lista de estudiantes públicos ordenados por número de coincidencias
    - Cada estudiante incluye habilidades, proyectos y programa
    
    💡 Algoritmo:
    - Búsqueda case-insensitive en habilidades técnicas y blandas
    - Ordenamiento por relevancia (más coincidencias primero)
    - Paginación mediante limit
    """
    # Autorización: solo empresas verificadas y admins
    if current_user.role not in ["company", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo empresas verificadas pueden buscar por habilidades"
        )
    
    # Si es empresa, verificar que está verificada
    if current_user.role == "company":
        company = await session.get(Company, current_user.user_id)
        if not company or not company.is_verified:
            raise HTTPException(
                status_code=403,
                detail="La empresa debe estar verificada para buscar candidatos"
            )
    
    students = (await session.execute(
        select(Student).where(Student.is_active == True)
    )).scalars().all()
    
    matching_students = []
    
    for student in students:
        student_skills = json.loads(student.skills or "[]")
        student_soft_skills = json.loads(student.soft_skills or "[]")
        all_student_skills = student_skills + student_soft_skills
        
        # Contar coincidencias (case-insensitive)
        matches = 0
        for skill in skills:
            if any(skill.lower() in s.lower() or s.lower() in skill.lower() 
                   for s in all_student_skills):
                matches += 1
        
        if matches >= min_matches:
            student_public = StudentPublic(
                id=student.id,
                name=student.name,
                program=student.program,
                skills=student_skills,
                soft_skills=student_soft_skills,
                projects=json.loads(student.projects or "[]"),
                # ✅ ACTUALIZADO: Agregar CV metadata y timestamps
                cv_uploaded=student.cv_uploaded or False,
                cv_filename=student.cv_filename,
                created_at=student.created_at,
                last_active=student.last_active
            )
            matching_students.append((student_public, matches))
    
    # Ordenar por número de coincidencias (mayor a menor)
    matching_students.sort(key=lambda x: x[1], reverse=True)
    
    # Limitar resultados
    result = [student for student, _ in matching_students[:limit]]
    
    await _log_audit_action(
        session, "SEARCH_BY_SKILLS", f"skills:{','.join(skills)}",
        current_user, details=f"Encontrados {len(result)} estudiantes"
    )
    
    return result

# ============================================================================
# END OF STUDENTS ENDPOINTS
# ============================================================================
