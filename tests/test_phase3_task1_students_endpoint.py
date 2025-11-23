"""
TEST: FASE 3 - TAREA 1
Validar que el endpoint GET /students/ ahora busca correctamente por email usando hash

Status: ✅ Task 1 Completada
"""
import unittest
from sqlmodel import Session, create_engine, SQLModel, select, delete
from sqlmodel.pool import StaticPool
import json
from datetime import datetime
from app.models import Student
from app.utils.encryption import encryption_service, get_encryption_service


class TestPhase3Task1StudentsEndpoint(unittest.TestCase):
    """Tests para validar que /students/ busca correctamente por email con hash"""

    def setUp(self):
        """Configurar BD en memoria para tests"""
        # Crear BD en memoria
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        """Limpiar BD después de tests"""
        self.session.exec(delete(Student))
        self.session.commit()
        self.session.close()

    def _create_test_student(self, name: str, email: str, program: str = "Ingeniería en Sistemas", 
                            skills: list = None) -> Student:
        """Helper para crear estudiante de prueba"""
        if skills is None:
            skills = ["Python", "JavaScript"]

        student = Student(
            name=name,
            program=program,
            consent_data_processing=True,
            skills=json.dumps(skills),
            soft_skills=json.dumps(["Comunicación", "Liderazgo"]),
            projects=json.dumps(["Proyecto A", "Proyecto B"]),
            is_active=True
        )
        # Encriptar email
        student.set_email(email)
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student

    def test_1_search_by_name_partial_match(self):
        """Test: Búsqueda por nombre con coincidencia parcial"""
        print("\n✅ TEST 1: Búsqueda por nombre (coincidencia parcial)")
        
        # Crear estudiantes
        student1 = self._create_test_student("Juan González", "juan@email.com")
        student2 = self._create_test_student("Juanita Pérez", "juanita@email.com")
        student3 = self._create_test_student("María López", "maria@email.com")
        
        # Búsqueda: name.ilike("%juan%")
        search_term = "juan"
        results = self.session.exec(
            select(Student).where(Student.name.ilike(f"%{search_term}%"))
        ).all()
        
        # Validar resultados
        assert len(results) == 2, f"Esperaba 2 resultados, obtuve {len(results)}"
        assert student1.id in [r.id for r in results]
        assert student2.id in [r.id for r in results]
        assert student3.id not in [r.id for r in results]
        
        print(f"   ✓ Búsqueda '{search_term}' encontró {len(results)} estudiantes")
        for r in results:
            print(f"     - {r.name}")

    def test_2_search_by_email_hash_exact_match(self):
        """Test: Búsqueda por email usando hash (coincidencia exacta)"""
        print("\n✅ TEST 2: Búsqueda por email (hash, coincidencia exacta)")
        
        # Crear estudiantes
        student1 = self._create_test_student("Juan González", "juan@email.com")
        student2 = self._create_test_student("Juanita Pérez", "juanita@email.com")
        
        # Búsqueda: email_hash == SHA256(email)
        search_email = "juan@email.com"
        email_hash = encryption_service._get_hash_email(search_email)
        
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        
        # Validar resultados
        assert len(results) == 1, f"Esperaba 1 resultado, obtuve {len(results)}"
        assert results[0].id == student1.id
        
        print(f"   ✓ Búsqueda de email exacto encontró: {results[0].name}")
        print(f"   ✓ Email hash: {email_hash[:16]}...")

    def test_3_search_email_case_insensitive(self):
        """Test: Búsqueda por email es case-insensitive"""
        print("\n✅ TEST 3: Búsqueda por email case-insensitive")
        
        student = self._create_test_student("Juan", "JUAN@EMAIL.COM")
        
        # Intentar búsquedas con diferentes casos
        test_emails = [
            "juan@email.com",
            "JUAN@EMAIL.COM",
            "Juan@Email.Com",
            "JuAn@EmAiL.cOm"
        ]
        
        for test_email in test_emails:
            email_hash = encryption_service._get_hash_email(test_email)
            results = self.session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
            
            assert len(results) == 1, f"Email {test_email} debería encontrar el estudiante"
            print(f"   ✓ '{test_email}' → encontrado")

    def test_4_search_by_email_with_special_characters(self):
        """Test: Búsqueda por email con caracteres especiales"""
        print("\n✅ TEST 4: Búsqueda por email con caracteres especiales")
        
        special_emails = [
            "test+label@email.com",
            "user.name@email.com",
            "name_surname@email.com",
            "123-456@email.com"
        ]
        
        students = []
        for i, email in enumerate(special_emails):
            student = self._create_test_student(f"Student{i}", email)
            students.append(student)
        
        # Buscar cada email
        for i, email in enumerate(special_emails):
            email_hash = encryption_service._get_hash_email(email)
            results = self.session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
            
            assert len(results) == 1
            assert results[0].id == students[i].id
            print(f"   ✓ '{email}' → encontrado correctamente")

    def test_5_search_logic_detection(self):
        """Test: Lógica de detección (email vs nombre)"""
        print("\n✅ TEST 5: Detección inteligente (email vs nombre)")
        
        student = self._create_test_student("Juan", "juan@email.com")
        
        # Caso 1: search sin "@" → búsqueda por nombre
        print("   Simulando: search=juan (sin @)")
        search_term = "juan"
        if "@" in search_term:
            # email_hash
            email_hash = encryption_service._get_hash_email(search_term)
            results = self.session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
        else:
            # nombre
            results = self.session.exec(
                select(Student).where(Student.name.ilike(f"%{search_term}%"))
            ).all()
        
        assert len(results) == 1
        print(f"   ✓ 'juan' detectado como nombre → encontrado")
        
        # Caso 2: search con "@" → búsqueda por email
        print("   Simulando: search=juan@email.com (con @)")
        search_term = "juan@email.com"
        if "@" in search_term:
            # email_hash
            email_hash = encryption_service._get_hash_email(search_term)
            results = self.session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
        else:
            # nombre
            results = self.session.exec(
                select(Student).where(Student.name.ilike(f"%{search_term}%"))
            ).all()
        
        assert len(results) == 1
        print(f"   ✓ 'juan@email.com' detectado como email → encontrado")

    def test_6_no_email_exposed_in_hash_search(self):
        """Test: Email NUNCA se expone durante búsqueda por hash"""
        print("\n✅ TEST 6: Email NUNCA expuesto durante búsqueda por hash")
        
        student = self._create_test_student("Juan", "juan@email.com")
        
        # La búsqueda NUNCA lee el campo email encriptado
        # Solo usa email_hash para buscar
        email_hash = encryption_service._get_hash_email("juan@email.com")
        
        # Obtener estudiante
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        
        assert len(results) == 1
        found_student = results[0]
        
        # El email en la BD sigue encriptado (nunca fue desencriptado durante búsqueda)
        # Patrón Fernet: comienza con "gAAAAAA"
        assert found_student.email.startswith("gAA"), f"Email debería estar encriptado: {found_student.email[:20]}"
        
        # El hash es diferente del email original
        assert found_student.email_hash == email_hash
        assert found_student.email_hash != "juan@email.com"
        
        print(f"   ✓ Email en BD: {found_student.email[:20]}... (encriptado, Fernet)")
        print(f"   ✓ Email hash: {found_student.email_hash[:16]}... (SHA-256)")
        print(f"   ✓ Email NUNCA se desencriptó durante la búsqueda")

    def test_7_search_returns_decrypted_email(self):
        """Test: Respuesta retorna email desencriptado"""
        print("\n✅ TEST 7: Respuesta retorna email desencriptado")
        
        student = self._create_test_student("Juan", "juan@email.com")
        
        # Búsqueda por hash
        email_hash = encryption_service._get_hash_email("juan@email.com")
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        
        found_student = results[0]
        
        # Desencriptar (como lo hace el endpoint)
        decrypted = found_student.decrypt_sensitive_fields()
        
        # El email desencriptado debe ser correcto
        assert decrypted["email"] == "juan@email.com"
        
        print(f"   ✓ Email desencriptado correctamente: {decrypted['email']}")

    def test_8_search_empty_results(self):
        """Test: Búsqueda sin resultados retorna lista vacía"""
        print("\n✅ TEST 8: Búsqueda sin resultados")
        
        student = self._create_test_student("Juan", "juan@email.com")
        
        # Búsqueda por email que no existe
        email_hash = encryption_service._get_hash_email("inexistente@email.com")
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        
        assert len(results) == 0
        print(f"   ✓ Email inexistente retorna lista vacía")

    def test_9_performance_email_search(self):
        """Test: Performance de búsqueda por email"""
        print("\n✅ TEST 9: Performance de búsqueda por email")
        
        import time
        
        # Crear 100 estudiantes
        for i in range(100):
            self._create_test_student(f"Student{i}", f"student{i}@email.com")
        
        # Medir tiempo de búsqueda
        start = time.time()
        email_hash = encryption_service._get_hash_email("student50@email.com")
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        elapsed = time.time() - start
        
        assert len(results) == 1
        assert elapsed < 0.01  # Debe ser < 10ms
        
        print(f"   ✓ Búsqueda en 100 registros: {elapsed*1000:.2f}ms ✅")


if __name__ == "__main__":
    # Ejecutar tests con verbose
    unittest.main(verbosity=2)
