"""
🧠 spaCy NLP Service - Singleton Pattern

Proporciona acceso a modelos spaCy con caching singleton para evitar cargas repetidas.
Implementa NER, tokenización, lemmatización y análisis de entidades.

IMPORTANTE: La carga inicial (~500ms) ocurre solo una vez por sesión.
Las llamadas subsecuentes son <1ms.
"""

import spacy
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Representa una entidad nombrada extraída"""
    text: str
    label: str  # ORG, PERSON, GPE, DATE, LANGUAGE, etc
    start_char: int
    end_char: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "label": self.label,
            "start": self.start_char,
            "end": self.end_char,
        }


@dataclass
class Token:
    """Representa un token analizado"""
    text: str
    lemma: str
    pos: str  # Parte del discurso
    is_stop: bool
    is_alpha: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "lemma": self.lemma,
            "pos": self.pos,
            "is_stop": self.is_stop,
            "is_alpha": self.is_alpha,
        }


class SpacyNLPService:
    """
    Servicio singleton para operaciones NLP con spaCy.
    Soporta múltiples idiomas con fallback automático.
    
    Uso:
    ----
    nlp = SpacyNLPService()  # Auto-detecta y carga ambos modelos
    
    # Extrae entidades
    entities = nlp.extract_entities("Apple is in California")
    
    # Tokeniza y lemmatiza
    tokens = nlp.tokenize("running quickly")
    
    # Análisis completo (automáticamente en el idioma correcto)
    result = nlp.analyze("Trabajé en Google como Senior Engineer")
    """
    
    _instance = None
    _models = {}  # Dict de modelos por idioma
    _primary_model = None
    _primary_lang = None
    
    def __new__(cls, primary_lang: str = "auto"):
        """Singleton pattern: garantiza una sola instancia"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._setup_models(primary_lang)
        return cls._instance
    
    @classmethod
    def _setup_models(cls, primary_lang: str = "auto"):
        """Carga los modelos spaCy para español e inglés"""
        # Mapeo de idiomas a modelos
        MODEL_MAP = {
            "es": "es_core_news_md",
            "en": "en_core_web_md",
        }
        
        # Detecta idioma primario
        if primary_lang == "auto":
            # Intenta cargar español primero (más común en el proyecto)
            primary_lang = "es"
        
        cls._primary_lang = primary_lang
        
        # Carga modelos
        for lang, model_name in MODEL_MAP.items():
            try:
                logger.info(f"Cargando modelo spaCy: {model_name} ({lang})...")
                cls._models[lang] = spacy.load(model_name)
                logger.info(f"✅ Modelo {model_name} cargado")
                
                # Establece modelo primario
                if lang == primary_lang and cls._primary_model is None:
                    cls._primary_model = cls._models[lang]
            except OSError:
                logger.warning(
                    f"⚠️  Modelo {model_name} no disponible.\n"
                    f"Instala con: python -m spacy download {model_name}"
                )
        
        # Fallback: si no hay modelo primario, usa el primero disponible
        if cls._primary_model is None and cls._models:
            cls._primary_model = list(cls._models.values())[0]
            logger.warning(f"Usando modelo de fallback: {cls._primary_model.meta['name']}")
    
    @property
    def model(self):
        """Acceso al modelo spaCy primario"""
        if self._primary_model is None:
            self._setup_models(self._primary_lang or "auto")
        return self._primary_model
    
    def get_model_for_text(self, text: str) -> Any:
        """
        Selecciona el mejor modelo para el texto (detección automática de idioma).
        
        Returns:
            Modelo spaCy más apropiado para el texto
        """
        if not self._models:
            return self.model
        
        # Análisis simple de idioma basado en palabras clave
        text_lower = text.lower()
        
        # Palabras indicadoras de español
        spanish_indicators = {
            "educación", "experiencia", "habilidades", "certificaciones",
            "objetivo", "trabaje", "desarrolle", "lidere", "gestioné",
            "graduado", "licenciatura", "maestría", "doctorado", "universidad",
            "empresa", "empresa", "departamento", "proyecto", "equipo",
        }
        
        # Palabras indicadoras de inglés
        english_indicators = {
            "education", "experience", "skills", "certifications",
            "objective", "worked", "developed", "led", "managed",
            "bachelor", "master", "degree", "university",
            "company", "department", "project", "team",
        }
        
        spanish_score = sum(1 for indicator in spanish_indicators if indicator in text_lower)
        english_score = sum(1 for indicator in english_indicators if indicator in text_lower)
        
        # Selecciona modelo basado en score
        if spanish_score > english_score and "es" in self._models:
            return self._models["es"]
        elif english_score > spanish_score and "en" in self._models:
            return self._models["en"]
        else:
            # Fallback al modelo primario
            return self.model
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extrae entidades nombradas del texto.
        
        Auto-detecta el idioma y usa el modelo más apropiado.
        
        Returns:
            Lista de Entity objects con label (ORG, PERSON, GPE, DATE, etc)
        """
        model = self.get_model_for_text(text)
        doc = model(text)
        entities = [
            Entity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
            )
            for ent in doc.ents
        ]
        return entities
    
    def extract_entities_by_label(
        self, text: str, label: str
    ) -> List[str]:
        """
        Extrae solo entidades de un tipo específico.
        
        Args:
            text: Texto a analizar
            label: Tipo de entidad (ORG, PERSON, GPE, DATE, LANGUAGE, etc)
        
        Returns:
            Lista de textos de entidades
        """
        entities = self.extract_entities(text)
        return [e.text for e in entities if e.label == label]
    
    def tokenize(self, text: str, remove_stop: bool = False) -> List[Token]:
        """
        Tokeniza y lemmatiza el texto.
        
        Auto-detecta el idioma del texto.
        
        Args:
            text: Texto a tokenizar
            remove_stop: Si True, excluye palabras stopwords
        
        Returns:
            Lista de Token objects
        """
        model = self.get_model_for_text(text)
        doc = model(text)
        tokens = [
            Token(
                text=token.text,
                lemma=token.lemma_,
                pos=token.pos_,
                is_stop=token.is_stop,
                is_alpha=token.is_alpha,
            )
            for token in doc
            if not (remove_stop and token.is_stop)
        ]
        return tokens
    
    def extract_technical_terms(
        self, text: str, custom_terms: Optional[List[str]] = None
    ) -> List[str]:
        """
        Extrae términos técnicos del texto (puede ser extendido con custom_terms).
        
        Args:
            text: Texto a analizar
            custom_terms: Lista de términos técnicos personalizados
        
        Returns:
            Lista de términos técnicos encontrados
        """
        # Términos técnicos conocidos
        DEFAULT_TECH_TERMS = {
            # Lenguajes
            "python", "javascript", "typescript", "java", "cpp", "csharp",
            "go", "rust", "ruby", "php", "kotlin", "swift", "scala",
            # Frameworks
            "react", "vue", "angular", "fastapi", "django", "spring boot",
            "express", "next.js", "nuxt", "laravel", "rails",
            # Bases de datos
            "postgresql", "mongodb", "mysql", "redis", "cassandra",
            "elasticsearch", "dynamodb", "firestore",
            # DevOps/Cloud
            "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
            "jenkins", "gitlab", "github", "circleci",
            # ML/AI
            "tensorflow", "pytorch", "scikit-learn", "keras", "nltk",
            "spacy", "huggingface", "transformers",
            # Otros
            "git", "sql", "bash", "linux", "agile", "microservices",
        }
        
        tech_set = DEFAULT_TECH_TERMS.copy()
        if custom_terms:
            tech_set.update(term.lower() for term in custom_terms)
        
        doc = self.model(text.lower())
        found_terms = [
            token.text for token in doc
            if token.text.lower() in tech_set and token.is_alpha
        ]
        return list(set(found_terms))  # Devuelve únicos
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Análisis completo del texto.
        
        Auto-detecta el idioma y aplica el modelo más apropiado.
        
        Returns:
            Diccionario con:
            - entities: Entidades nombradas
            - tokens: Tokens analizados
            - tech_terms: Términos técnicos
            - org_entities: Solo ORG
            - person_entities: Solo PERSON
            - location_entities: Solo GPE/LOC
            - date_entities: Solo DATE
        """
        model = self.get_model_for_text(text)
        doc = model(text)
        
        return {
            "text": text,
            "language": doc.lang_,
            "model_used": model.meta.get("name", "unknown"),
            "entities": [e.to_dict() for e in self.extract_entities(text)],
            "tokens": [t.to_dict() for t in self.tokenize(text, remove_stop=True)],
            "tech_terms": self.extract_technical_terms(text),
            "organizations": self.extract_entities_by_label(text, "ORG"),
            "persons": self.extract_entities_by_label(text, "PERSON"),
            "locations": self.extract_entities_by_label(text, "GPE"),
            "dates": self.extract_entities_by_label(text, "DATE"),
            "languages": self.extract_entities_by_label(text, "LANGUAGE"),
        }
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridad semántica entre dos textos.
        
        Usa embeddings de spaCy y selecciona el modelo más apropiado
        basado en el idioma detectado de ambos textos.
        
        Returns:
            Score 0.0 a 1.0 (1.0 = idénticos)
        """
        # Usa modelo basado en el primer texto
        model = self.get_model_for_text(text1)
        doc1 = model(text1)
        doc2 = model(text2)
        
        if not doc1.has_vector or not doc2.has_vector:
            logger.warning("Uno o ambos documentos no tienen vectores")
            return 0.0
        
        return doc1.similarity(doc2)
    
    @staticmethod
    def get_instance(primary_lang: str = "auto") -> "SpacyNLPService":
        """
        Obtiene la instancia singleton.
        
        Args:
            primary_lang: Idioma primario ("es", "en", o "auto" para auto-detectar)
        """
        return SpacyNLPService(primary_lang)


# Singleton global
def get_nlp_service(primary_lang: str = "auto") -> SpacyNLPService:
    """
    Factory function para obtener la instancia singleton.
    
    Carga automáticamente ambos modelos (español e inglés) y auto-detecta
    el idioma del texto para usar el modelo más apropiado.
    
    Args:
        primary_lang: Idioma preferido ("es", "en", o "auto")
    
    Uso recomendado:
    ----------------
    from app.services.spacy_nlp_service import get_nlp_service
    
    nlp = get_nlp_service()
    
    # Procesa CV en español
    result_es = nlp.analyze("Trabajé en Google como Senior Engineer")
    
    # Procesa CV en inglés
    result_en = nlp.analyze("I worked at Apple as a Software Engineer")
    
    # Automáticamente usa el modelo correcto para cada uno
    """
    return SpacyNLPService(primary_lang)
