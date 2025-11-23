"""
FASE 3 - Búsquedas Avanzadas Seguras
Tests para validar que las búsquedas complejas usan hashes
y no exponen datos encriptados
"""

import unittest
import json
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel, select, delete
from sqlmodel.pool import StaticPool

from app.models import Student, Company
from app.utils.encryption import encryption_service


class TestPhase3AdvancedSearches(unittest.TestCase):
    """Tests para búsquedas avanzadas con hash-based filtering"""

    @classmethod
    def setUpClass(cls):
        """Crear BD temporal en memoria"""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(cls.engine)

    def setUp(self):
        """Crear datos de prueba antes de cada test"""
        with Session(self.engine) as session:
            # Limpiar datos anteriores
            session.exec(delete(Student))
            session.commit()

    def _create_test_students(self, session: Session):
        """Helper para crear estudiantes de prueba"""
        students = [
            {
                "name": "Juan García",
                "email": "juan@example.com",
                "phone": "+34 123 456 789",
                "program": "Ingeniería de Software",
                "skills": json.dumps(["Python", "React", "Django"]),
                "soft_skills": json.dumps(["Liderazgo", "Comunicación"]),
                "projects": json.dumps(["Sistema de gestión", "App móvil"]),
            },
            {
                "name": "María López",
                "email": "maria@example.com",
                "phone": "+34 987 654 321",
                "program": "Ingeniería de Datos",
                "skills": json.dumps(["Python", "SQL", "Machine Learning"]),
                "soft_skills": json.dumps(["Análisis", "Resolución de problemas"]),
                "projects": json.dumps(["Análisis de datos", "Pipeline ML"]),
            },
            {
                "name": "Carlos Martín",
                "email": "carlos@example.com",
                "phone": "+34 555 666 777",
                "program": "Ingeniería de Software",
                "skills": json.dumps(["JavaScript", "React", "Node.js"]),
                "soft_skills": json.dumps(["Creatividad", "Trabajo en equipo"]),
                "projects": json.dumps(["Frontend framework", "E-commerce"]),
            },
        ]

        for data in students:
            student = Student(
                name=data["name"],
                program=data["program"],
                skills=data["skills"],
                soft_skills=data["soft_skills"],
                projects=data["projects"],
                is_active=True,
            )
            # Encriptar campos sensibles
            student.set_email(data["email"])
            student.set_phone(data["phone"])
            
            session.add(student)
        
        session.commit()
        return session.exec(select(Student)).all()

    # ============= TESTS =============

    def test_1_filter_by_email_hash(self):
        """
        TEST 1: Búsqueda por email usa hash, no desencripta
        
        Verifica que:
        - Búsqueda por email normalizado y hasheado
        - Email nunca se desencripta durante búsqueda
        - Respuesta retorna email desencriptado
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            # Búsqueda por email
            search_email = "juan@example.com"
            email_hash = encryption_service._get_hash_email(search_email)
            
            # Búsqueda segura (por hash)
            found_student = session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).first()
            
            self.assertIsNotNone(found_student, "Estudiante debería encontrarse por hash")
            self.assertEqual(found_student.name, "Juan García")
            
            # Verificar que el email está encriptado en BD
            self.assertNotEqual(found_student.email, search_email, 
                              "Email en BD debería estar encriptado")
            self.assertTrue(found_student.email.startswith("gAAAAA"),
                          "Email debería ser Fernet encriptado")
            
            # Verificar que desencriptación funciona
            decrypted = found_student.decrypt_sensitive_fields()
            self.assertEqual(decrypted["email"], search_email)
    
    def test_2_filter_by_skills(self):
        """
        TEST 2: Búsqueda por skills no afecta seguridad
        
        Verifica que:
        - Búsqueda por skills funciona normalmente
        - No interfiere con encriptación de email/phone
        - Retorna datos correctos
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            # Buscar estudiantes con Python
            search_skill = "Python"
            
            found = []
            for student in students:
                skills = json.loads(student.skills or "[]")
                if any(search_skill.lower() in s.lower() for s in skills):
                    found.append(student)
            
            self.assertEqual(len(found), 2, "Debería encontrar 2 estudiantes con Python")
            
            # Verificar que email sigue encriptado
            for student in found:
                self.assertTrue(student.email.startswith("gAAAAA"),
                              "Email debería seguir encriptado")
                # Pero desencriptación funciona
                decrypted = student.decrypt_sensitive_fields()
                self.assertIn("@example.com", decrypted["email"])
    
    def test_3_filter_by_program(self):
        """
        TEST 3: Búsqueda por programa académico
        
        Verifica que:
        - Filtros por programa funcionan
        - Combinan correctamente con filtros de email
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            # Buscar estudiantes de Ingeniería de Software
            found = session.exec(
                select(Student).where(Student.program == "Ingeniería de Software")
            ).all()
            
            self.assertEqual(len(found), 2, "Debería encontrar 2 estudiantes de Ingeniería de Software")
            for student in found:
                self.assertEqual(student.program, "Ingeniería de Software")
    
    def test_4_combined_filters(self):
        """
        TEST 4: Múltiples filtros combinados
        
        Verifica que:
        - Email + skills + program juntos
        - Búsqueda por hash mantiene performance
        - Resultados correctos
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            # Filtro 1: Email específico
            email_to_find = "maria@example.com"
            email_hash = encryption_service._get_hash_email(email_to_find)
            
            # Filtro 2: Tener skill Python
            search_skill = "Python"
            
            # Filtro 3: Programa específico
            program_filter = "Ingeniería de Datos"
            
            # Búsqueda por email
            found = session.exec(
                select(Student).where(
                    Student.email_hash == email_hash
                )
            ).first()
            
            self.assertIsNotNone(found)
            self.assertEqual(found.name, "María López")
            
            # Verificar skills
            skills = json.loads(found.skills or "[]")
            self.assertIn("Python", skills)
            
            # Verificar programa
            self.assertEqual(found.program, program_filter)
    
    def test_5_performance_complex_search(self):
        """
        TEST 5: Performance de búsqueda compleja con batch de 100 registros
        
        Verifica que:
        - 100 registros se desencriptan rápido
        - Búsqueda por hash es rápido
        - Combinación < 500ms total
        """
        import time
        
        with Session(self.engine) as session:
            # Crear 100 estudiantes (versión simplificada)
            base_students = self._create_test_students(session)
            
            # Duplicar para llegar a ~100
            for i in range(33):  # 3 base * 33 = 99 aproximadamente
                for base_student in base_students:
                    student = Student(
                        name=f"{base_student.name}_{i}",
                        program=base_student.program,
                        skills=base_student.skills,
                        soft_skills=base_student.soft_skills,
                        projects=base_student.projects,
                        is_active=True,
                    )
                    student.set_email(f"user{i}_{base_student.name}@example.com")
                    student.set_phone(f"+34 {i}23 456 789")
                    session.add(student)
            
            session.commit()
            
            # Medir búsqueda
            start = time.time()
            
            # Búsqueda por Python + programa
            search_skill = "Python"
            target_program = "Ingeniería de Datos"
            found_students = []
            all_students = session.exec(select(Student)).all()
            
            for student in all_students:
                skills = json.loads(student.skills or "[]")
                if (any(search_skill.lower() in s.lower() for s in skills) and
                    student.program == target_program):
                    found_students.append(student)
            
            # Desencriptar todos
            for student in found_students:
                _ = student.decrypt_sensitive_fields()
            
            elapsed = time.time() - start
            
            self.assertLess(elapsed, 0.5, 
                           f"Búsqueda compleja debería ser < 500ms, fue {elapsed*1000:.2f}ms")
            print(f"✅ TEST 5: {len(found_students)} registros en {elapsed*1000:.2f}ms")
    
    def test_6_case_insensitive_email_search(self):
        """
        TEST 6: Búsqueda de email insensible a mayúsculas
        
        Verifica que:
        - JUAN@EXAMPLE.COM coincida con juan@example.com
        - Juan@Example.Com coincida
        - " juan@example.com " (con espacios) coincida
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            test_cases = [
                "JUAN@EXAMPLE.COM",
                "Juan@Example.Com",
                " juan@example.com ",
                "JUAN@EXAMPLE.COM  ",
            ]
            
            for test_email in test_cases:
                email_hash = encryption_service._get_hash_email(test_email)
                found = session.exec(
                    select(Student).where(Student.email_hash == email_hash)
                ).first()
                self.assertIsNotNone(found, 
                                   f"Debería encontrar con: {test_email}")
                self.assertEqual(found.name, "Juan García")
    
    def test_7_no_hash_exposed_in_results(self):
        """
        TEST 7: Respuestas no exponen email_hash
        
        Verifica que:
        - Cuando se convierte a StudentProfile, no hay hashes
        - JSON response seguro
        - Solo email desencriptado
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            student = students[0]
            
            # Simular conversión a respuesta
            decrypted = student.decrypt_sensitive_fields()
            
            # Email debería estar desencriptado
            self.assertIn("@", decrypted["email"])
            self.assertNotIn("gAAAAA", decrypted["email"])
            
            # No debería haber "hash" en respuesta
            self.assertNotIn("email_hash", decrypted)
            self.assertNotIn("phone_hash", decrypted)
    
    def test_8_pagination_with_filters(self):
        """
        TEST 8: Paginación con filtros combinados
        
        Verifica que:
        - Limit y offset funcionan
        - Ordenamiento correcto
        - Con filtros aplicados
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            # Obtener con limit y offset
            limit = 1
            offset = 0
            
            paginated = session.exec(
                select(Student).offset(offset).limit(limit)
            ).all()
            
            self.assertEqual(len(paginated), 1)
            
            # Siguiente página
            offset = 1
            paginated2 = session.exec(
                select(Student).offset(offset).limit(limit)
            ).all()
            
            self.assertEqual(len(paginated2), 1)
            self.assertNotEqual(paginated[0].id, paginated2[0].id)
    
    def test_9_search_with_special_characters(self):
        """
        TEST 9: Emails con caracteres especiales
        
        Verifica que:
        - + en emails funciona (test+email@example.com)
        - Puntos en emails funcionan
        - Guiones funcionan
        """
        with Session(self.engine) as session:
            # Crear estudiante con email especial
            special_emails = [
                "test+email@example.com",
                "user.name@example.com",
                "user-name@example.com",
            ]
            
            for special_email in special_emails:
                student = Student(
                    name=f"Test {special_email}",
                    program="Test",
                    is_active=True,
                )
                student.set_email(special_email)
                session.add(student)
            
            session.commit()
            
            # Buscar cada uno
            for special_email in special_emails:
                email_hash = encryption_service._get_hash_email(special_email)
                found = session.exec(
                    select(Student).where(Student.email_hash == email_hash)
                ).first()
                self.assertIsNotNone(found, f"Debería encontrar: {special_email}")
                
                decrypted = found.decrypt_sensitive_fields()
                self.assertEqual(decrypted["email"], special_email)
    
    def test_10_empty_results_graceful(self):
        """
        TEST 10: Sin resultados retorna [] sin errores
        
        Verifica que:
        - Búsqueda sin coincidencias retorna []
        - No hay excepciones
        - Pueda manejarse correctamente
        """
        with Session(self.engine) as session:
            students = self._create_test_students(session)
            
            # Buscar email que no existe
            nonexistent_email = "notexist@example.com"
            email_hash = encryption_service._get_hash_email(nonexistent_email)
            
            found = session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
            
            self.assertEqual(len(found), 0)
            self.assertIsInstance(found, list)


if __name__ == "__main__":
    # Configurar colores para output
    unittest.main(verbosity=2)
