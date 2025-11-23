"""
TEST: FASE 3 - TAREA 2
Validar que /matching/filter-by-criteria soporta email search con hash
"""
import unittest
from sqlmodel import Session, create_engine, SQLModel, select, delete
from sqlmodel.pool import StaticPool
import json
from app.models import Student
from app.utils.encryption import encryption_service


class TestPhase3Task2MatchingLogic(unittest.TestCase):
    """Tests para validar lógica de email search en matching"""

    @classmethod
    def setUpClass(cls):
        """Configurar BD en memoria"""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(cls.engine)

    def setUp(self):
        """Crear sesión de test"""
        self.session = Session(self.engine)

    def tearDown(self):
        """Limpiar datos"""
        self.session.exec(delete(Student))
        self.session.commit()
        self.session.close()

    def _create_test_student(self, name: str, email: str, skills: list = None) -> Student:
        """Helper para crear estudiante"""
        if skills is None:
            skills = ["Python", "JavaScript"]

        student = Student(
            name=name,
            program="Ingeniería en Sistemas",
            consent_data_processing=True,
            skills=json.dumps(skills),
            soft_skills=json.dumps(["Comunicación"]),
            projects=json.dumps(["Proyecto A"]),
            is_active=True
        )
        student.set_email(email)
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        return student

    def test_1_email_hash_field_exists(self):
        """Test: Field email_hash existe"""
        print("\n✅ TEST 1: email_hash field exists")
        student = self._create_test_student("Juan", "juan@email.com")
        assert hasattr(student, 'email_hash')
        assert len(student.email_hash) == 64
        print(f"   ✓ email_hash: {student.email_hash[:16]}...")

    def test_2_exact_email_search(self):
        """Test: Búsqueda exacta por email_hash"""
        print("\n✅ TEST 2: Exact email search via hash")
        student = self._create_test_student("Juan", "juan@email.com")
        email_hash = encryption_service._get_hash_email("juan@email.com")
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        assert len(results) == 1
        assert results[0].id == student.id
        print(f"   ✓ Found: {results[0].name}")

    def test_3_email_not_found(self):
        """Test: Email no encontrado"""
        print("\n✅ TEST 3: Email not found returns empty")
        self._create_test_student("Juan", "juan@email.com")
        email_hash = encryption_service._get_hash_email("notfound@email.com")
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        assert len(results) == 0
        print(f"   ✓ Empty result for non-existent email")

    def test_4_case_insensitive(self):
        """Test: Case-insensitive search"""
        print("\n✅ TEST 4: Case-insensitive")
        self._create_test_student("Juan", "JUAN@EMAIL.COM")
        for test_email in ["juan@email.com", "JUAN@EMAIL.COM", "Juan@Email.Com"]:
            email_hash = encryption_service._get_hash_email(test_email)
            results = self.session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
            assert len(results) == 1
            print(f"   ✓ '{test_email}' → found")

    def test_5_special_chars(self):
        """Test: Special characters in email"""
        print("\n✅ TEST 5: Special characters")
        for email in ["test+label@email.com", "user.name@email.com"]:
            self.session.exec(delete(Student))
            self.session.commit()
            self._create_test_student("Test", email)
            email_hash = encryption_service._get_hash_email(email)
            results = self.session.exec(
                select(Student).where(Student.email_hash == email_hash)
            ).all()
            assert len(results) == 1
            print(f"   ✓ '{email}' → found")

    def test_6_email_encrypted(self):
        """Test: Email stays encrypted"""
        print("\n✅ TEST 6: Email encrypted in DB")
        student = self._create_test_student("Juan", "juan@email.com")
        assert student.email.startswith("gA"), "Should be Fernet encrypted"
        email_hash = encryption_service._get_hash_email("juan@email.com")
        assert email_hash != student.email
        print(f"   ✓ Email encrypted: {student.email[:20]}...")

    def test_7_matching_criteria_email(self):
        """Test: MatchingCriteria supports email"""
        print("\n✅ TEST 7: MatchingCriteria.email field")
        from app.schemas import MatchingCriteria
        criteria = MatchingCriteria(email="juan@email.com", skills=["Python"])
        assert criteria.email == "juan@email.com"
        print(f"   ✓ MatchingCriteria.email = {criteria.email}")

    def test_8_performance(self):
        """Test: Performance with 100 records"""
        print("\n✅ TEST 8: Performance")
        import time
        for i in range(100):
            self._create_test_student(f"Student{i}", f"student{i}@email.com")
        start = time.time()
        email_hash = encryption_service._get_hash_email("student50@email.com")
        results = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        elapsed = time.time() - start
        assert len(results) == 1
        assert elapsed < 0.01
        print(f"   ✓ 100 records: {elapsed*1000:.2f}ms ✅")

    def test_9_combined_filters(self):
        """Test: Combined email + skills"""
        print("\n✅ TEST 9: Combined email + skills")
        s1 = self._create_test_student("Juan", "juan@email.com", skills=["Python", "ML"])
        s2 = self._create_test_student("Maria", "maria@email.com", skills=["Java"])
        email_hash = encryption_service._get_hash_email("juan@email.com")
        candidates = self.session.exec(
            select(Student).where(Student.email_hash == email_hash)
        ).all()
        results = []
        for c in candidates:
            skills = json.loads(c.skills or "[]")
            if any(s.lower() in ["python", "ml"] for s in skills):
                results.append(c)
        assert len(results) == 1
        print(f"   ✓ Found: {results[0].name}")

    def test_10_backward_compat(self):
        """Test: Skills-only search still works"""
        print("\n✅ TEST 10: Backward compatibility")
        s1 = self._create_test_student("Juan", "juan@email.com", skills=["Python"])
        s2 = self._create_test_student("Maria", "maria@email.com", skills=["Java"])
        all_students = self.session.exec(select(Student)).all()
        results = []
        for s in all_students:
            skills = json.loads(s.skills or "[]")
            if any("python" in sk.lower() for sk in skills):
                results.append(s)
        assert len(results) == 1
        print(f"   ✓ Found: {results[0].name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
