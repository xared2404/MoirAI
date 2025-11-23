"""
Text Vectorization and NLP Processing Service

Módulo especializado en normalización de texto, construcción de vocabulario
y representación vectorial de texto usando TF-IDF y análisis de tokens.

INDEPENDIENTE de nlp_service.py - puede ser intercambiado en el futuro
sin impactar lógica de matching.

Características:
- Normalización robusta de texto (lowercasing, stemming opcional, manejo unicode)
- Construcción y gestión de vocabulario dinámico
- Vectorización TF-IDF con fallback manual
- Análisis de similitud coseno
- Extracción y ponderación de términos relevantes
- Protección contra DoS (truncado de inputs)

Casos de uso:
1. Normalizar perfiles de estudiantes y descripciones de trabajos
2. Construir vocabulario técnico personalizado por dominio
3. Generar vectores para comparación de similaridad
4. Extraer términos relevantes con scores TF-IDF
5. Análisis comparativo entre documentos
"""

from typing import List, Dict, Tuple, Optional, Set
import re
import unicodedata
import math
import json
from dataclasses import dataclass, field
from collections import Counter
from enum import Enum

from app.core.config import settings


# ============================================================================
# CONSTANTES DE SEGURIDAD Y CONFIGURACIÓN (desde settings)
# ============================================================================

# Límites para protección contra DoS y entradas maliciosas
MAX_TEXT_LEN = settings.NLP_MAX_TEXT_LENGTH       # Máximo de caracteres a procesar
MAX_TOKEN_LEN = settings.NLP_MAX_TOKEN_LENGTH     # Máximo de caracteres por token
MAX_TOKENS = settings.NLP_MAX_VOCAB_SIZE          # Máximo de tokens únicos en vocabulario
MAX_NGRAM_SIZE = settings.NLP_MAX_NGRAM_SIZE      # Máximo n-gramas (1=unigramas, 2=bigramas, etc.)
MIN_TOKEN_LENGTH = settings.NLP_MIN_TOKEN_LENGTH  # Longitud mínima de tokens

# Stopwords técnicos a excluir (en inglés y español)
TECHNICAL_STOPWORDS = {
    # Inglés
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "that", "this", "these", "those", "it", "as", "if", "not", "no", "yes",
    # Español
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "y", "o", "pero", "en", "por", "para", "con", "sin", "al", "a",
    "es", "son", "está", "están", "fue", "fueron", "sea", "sean",
    "este", "ese", "aquel", "esto", "eso", "aquello", "como", "si",
}

# Mapeo de términos técnicos a normalizar
TECHNICAL_NORMALIZATION_MAP = {
    "c++": "cpp",
    "c#": "csharp",
    "node.js": "nodejs",
    ".net": "dotnet",
    "f#": "fsharp",
    "objective-c": "objectivec",
    "visual basic": "visualbasic",
    "front-end": "frontend",
    "back-end": "backend",
    "full-stack": "fullstack",
    "machine-learning": "machinelearning",
    "deep-learning": "deeplearning",
    "natural-language": "naturallanguage",
    "aws": "aws",
    "gcp": "gcp",
    "azure": "azure",
    "ci/cd": "cicd",
}

# Vocabulario técnico conocido (para validación y análisis)
TECHNICAL_VOCAB = {
    # Lenguajes de programación
    "python", "java", "javascript", "typescript", "go", "rust", "kotlin",
    "ruby", "php", "swift", "csharp", "cpp", "c", "scala", "r", "matlab",
    # Frameworks y librerías
    "react", "vue", "angular", "svelte", "fastapi", "django", "flask",
    "spring", "springboot", "dotnet", "nodejs", "express", "nestjs",
    # Bases de datos
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
    "dynamodb", "firestore", "sqlite",
    # Cloud y DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "gitlab", "github", "circleci", "travisci",
    # ML/AI
    "tensorflow", "pytorch", "keras", "sklearn", "scikit-learn", "numpy",
    "pandas", "huggingface", "openai", "langchain",
    # Otros
    "sql", "nosql", "rest", "graphql", "grpc", "websocket", "api",
    "microservices", "linux", "unix", "windows", "macos",
}

# Vocabulario de habilidades blandas (Soft Skills) - Español e Inglés
SOFT_SKILLS_VOCAB = {
    # Comunicación
    "comunicación", "communication", "presentation", "presentación",
    "escritura", "writing", "habla", "speaking", "escucha", "listening",
    
    # Liderazgo y trabajo en equipo
    "liderazgo", "leadership", "trabajo en equipo", "teamwork", "colaboración",
    "collaboration", "coordinación", "coordination", "mentoring", "coaching",
    
    # Pensamiento crítico y resolución
    "problem solving", "resolución de problemas", "análisis", "analysis",
    "pensamiento crítico", "critical thinking", "toma de decisiones",
    "decision making", "juicio crítico", "reasoning",
    
    # Creatividad e innovación
    "creatividad", "creativity", "innovación", "innovation", "pensamiento lateral",
    "lateral thinking", "diseño creativo", "creative design",
    
    # Adaptabilidad y flexibilidad
    "adaptabilidad", "adaptability", "flexibilidad", "flexibility",
    "aprendizaje continuo", "continuous learning", "versatilidad", "versatility",
    
    # Responsabilidad y ética
    "responsabilidad", "responsibility", "ética", "ethics", "integridad", "integrity",
    "confiabilidad", "reliability", "profesionalismo", "professionalism",
    
    # Iniciativa y autonomía
    "iniciativa", "initiative", "autonomía", "autonomy", "proactividad", "proactivity",
    "independencia", "independence", "autodidacta", "self-taught",
    
    # Inteligencia emocional
    "inteligencia emocional", "emotional intelligence", "empatía", "empathy",
    "autoconciencia", "self-awareness", "gestión emocional", "emotional management",
    
    # Gestión y organización
    "gestión del tiempo", "time management", "organización", "organization",
    "planificación", "planning", "priorización", "prioritization",
    
    # Negociación y resolución de conflictos
    "negociación", "negotiation", "resolución de conflictos", "conflict resolution",
    "diplomacia", "diplomacy", "mediación", "mediation",
    
    # Otros
    "paciencia", "patience", "atención al detalle", "attention to detail",
    "meticulosidad", "meticulousness", "precisión", "precision",
    "orientación al cliente", "customer focus", "satisfacción del cliente",
}


# ============================================================================
# ENUMS Y DATACLASSES
# ============================================================================

class NormalizationType(str, Enum):
    """Tipos de normalización disponibles"""
    BASIC = "basic"              # Solo lowercase + unicode
    AGGRESSIVE = "aggressive"    # Basic + stopwords removal
    TECHNICAL = "technical"      # Aggressive + mapeo técnico


@dataclass
class TokenFrequency:
    """Información de frecuencia de un token"""
    token: str
    frequency: int
    document_frequency: int = 0  # En cuántos documentos aparece
    tf_idf_score: float = 0.0
    is_technical: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "token": self.token,
            "frequency": self.frequency,
            "document_frequency": self.document_frequency,
            "tf_idf_score": round(self.tf_idf_score, 6),
            "is_technical": self.is_technical,
        }


@dataclass
class VocabularyStats:
    """Estadísticas de un vocabulario"""
    total_tokens: int = 0
    unique_tokens: int = 0
    technical_tokens: int = 0
    average_token_length: float = 0.0
    coverage_percentage: float = 0.0  # % del texto cubierto
    dominant_terms: List[str] = field(default_factory=list)


# ============================================================================
# FUNCIONES PRINCIPALES DE NORMALIZACIÓN
# ============================================================================

def _normalize_unicode(text: str) -> str:
    """Normalizar caracteres unicode eliminando acentos."""
    if not text:
        return ""
    # NFKD: descompone caracteres (é -> e + ´)
    text = unicodedata.normalize("NFKD", text)
    # Eliminar marcas diacríticas (combining characters)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def _apply_technical_mapping(text: str) -> str:
    """Mapear términos técnicos comunes a formas normalizadas."""
    if not text:
        return ""
    for technical_term, normalized in TECHNICAL_NORMALIZATION_MAP.items():
        # Buscar palabra completa (con límites de palabra)
        pattern = r"\b" + re.escape(technical_term) + r"\b"
        text = re.sub(pattern, normalized, text, flags=re.IGNORECASE)
    return text


def normalize_text(
    text: str,
    normalization_type: NormalizationType = NormalizationType.AGGRESSIVE,
    remove_numbers: bool = False,
    min_token_length: int = None,
) -> str:
    """
    Normalizar texto aplicando transformaciones progresivas.
    
    Args:
        text: Texto a normalizar
        normalization_type: Nivel de normalización
        remove_numbers: Si True, eliminar números
        min_token_length: Longitud mínima de tokens (usa settings si no se especifica)
        
    Returns:
        Texto normalizado
        
    Ejemplo:
        >>> normalize_text("¡Hola MUNDO! C++ & Node.js")
        "hola mundo cpp nodejs"
    """
    if not text:
        return ""
    
    # Usar valor de settings si no se proporciona
    if min_token_length is None:
        min_token_length = MIN_TOKEN_LENGTH
    
    # Truncar para proteger contra DoS
    text = str(text)[:MAX_TEXT_LEN]
    
    # PASO 1: Minúsculas
    text = text.strip().lower()
    
    # PASO 2: Normalización unicode
    text = _normalize_unicode(text)
    
    # PASO 3: Mapeo técnico (antes de eliminar caracteres especiales)
    if normalization_type in (NormalizationType.AGGRESSIVE, NormalizationType.TECHNICAL):
        text = _apply_technical_mapping(text)
    
    # PASO 4: Eliminar caracteres especiales (mantener letras, números, espacios)
    if remove_numbers:
        text = re.sub(r"[^a-z\s]", " ", text)
    else:
        text = re.sub(r"[^a-z0-9\s]", " ", text)
    
    # PASO 5: Eliminar espacios múltiples
    text = re.sub(r"\s+", " ", text).strip()
    
    # PASO 6: Filtrar stopwords si es normalización agresiva
    if normalization_type in (NormalizationType.AGGRESSIVE, NormalizationType.TECHNICAL):
        tokens = text.split()
        tokens = [t for t in tokens if t not in TECHNICAL_STOPWORDS and len(t) >= min_token_length]
        text = " ".join(tokens)
    
    return text


# ============================================================================
# ANÁLISIS DE TOKENS Y VOCABULARIO
# ============================================================================

class VocabularyBuilder:
    """
    Constructor de vocabulario con análisis de frecuencia y relevancia.
    
    Mantiene estadísticas sobre tokens, cálcula TF-IDF y permite
    análisis de vocabulario técnico vs general.
    """
    
    def __init__(self, max_vocab_size: int = MAX_TOKENS):
        self.max_vocab_size = max_vocab_size
        self.token_frequencies: Dict[str, int] = {}
        self.document_frequencies: Dict[str, int] = {}
        self.total_documents = 0
        self.tokens_by_document: List[Set[str]] = []
        self.technical_tokens: Set[str] = set()
    
    def add_document(self, text: str, normalization: NormalizationType = NormalizationType.AGGRESSIVE):
        """
        Añadir un documento al vocabulario.
        
        Args:
            text: Texto del documento
            normalization: Tipo de normalización a aplicar
        """
        normalized = normalize_text(text, normalization)
        tokens = set(normalized.split()) if normalized else set()
        
        # Actualizar frecuencias
        for token in tokens:
            self.token_frequencies[token] = self.token_frequencies.get(token, 0) + 1
            self.document_frequencies[token] = self.document_frequencies.get(token, 0) + 1
            
            # Detectar si es término técnico
            if token in TECHNICAL_VOCAB or any(tech in token for tech in TECHNICAL_VOCAB):
                self.technical_tokens.add(token)
        
        self.tokens_by_document.append(tokens)
        self.total_documents += 1
    
    def get_vocabulary(self, top_n: Optional[int] = None) -> List[str]:
        """Obtener vocabulario ordenado por frecuencia."""
        sorted_tokens = sorted(
            self.token_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        vocab = [token for token, _ in sorted_tokens]
        
        if top_n:
            vocab = vocab[:top_n]
        
        return vocab
    
    def calculate_tfidf(self, token: str) -> float:
        """
        Calcular TF-IDF de un token.
        
        TF-IDF = (frecuencia del token) * ln(documentos totales / documentos con token)
        """
        if token not in self.token_frequencies or self.total_documents == 0:
            return 0.0
        
        tf = self.token_frequencies[token]
        df = self.document_frequencies.get(token, 1)
        idf = math.log(self.total_documents / max(1, df))
        
        return tf * idf
    
    def get_top_terms(self, top_n: int = 20) -> List[TokenFrequency]:
        """Obtener los N términos más relevantes por TF-IDF."""
        terms = []
        for token, freq in self.token_frequencies.items():
            tfidf = self.calculate_tfidf(token)
            terms.append(TokenFrequency(
                token=token,
                frequency=freq,
                document_frequency=self.document_frequencies.get(token, 0),
                tf_idf_score=tfidf,
                is_technical=token in self.technical_tokens,
            ))
        
        # Ordenar por TF-IDF
        terms.sort(key=lambda x: x.tf_idf_score, reverse=True)
        return terms[:top_n]
    
    def get_stats(self) -> VocabularyStats:
        """Obtener estadísticas del vocabulario."""
        if not self.token_frequencies:
            return VocabularyStats()
        
        total_tokens = sum(self.token_frequencies.values())
        unique_tokens = len(self.token_frequencies)
        avg_length = sum(len(t) for t in self.token_frequencies.keys()) / unique_tokens if unique_tokens > 0 else 0
        
        top_terms = self.get_top_terms(5)
        
        return VocabularyStats(
            total_tokens=total_tokens,
            unique_tokens=unique_tokens,
            technical_tokens=len(self.technical_tokens),
            average_token_length=round(avg_length, 2),
            dominant_terms=[t.token for t in top_terms],
        )


# ============================================================================
# VECTORIZACIÓN Y SIMILITUD
# ============================================================================

class TextVectorizer:
    """
    Vectorización de texto usando TF-IDF.
    
    Permite convertir textos a vectores numéricos para cálculo de similitud.
    Usa sklearn si está disponible, con fallback a implementación manual.
    """
    
    def __init__(self, ngram_range: Tuple[int, int] = (1, 2)):
        """
        Args:
            ngram_range: Rango de n-gramas (min, max). Ej: (1,2) = unigramas + bigramas
        """
        self.ngram_range = ngram_range
        self.vocabulary: Dict[str, int] = {}
        self.idf_weights: Dict[str, float] = {}
        self.fitted = False
    
    def _generate_ngrams(self, tokens: List[str], n: int) -> List[str]:
        """Generar n-gramas a partir de tokens."""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = " ".join(tokens[i:i+n])
            ngrams.append(ngram)
        return ngrams
    
    def fit(self, texts: List[str], normalization: NormalizationType = NormalizationType.AGGRESSIVE):
        """
        Entrenar vectorizador con corpus de textos.
        
        Args:
            texts: Lista de documentos
            normalization: Tipo de normalización a aplicar
        """
        # Normalizar y tokenizar
        all_ngrams = []
        doc_ngrams = []
        
        for text in texts:
            normalized = normalize_text(text, normalization)
            tokens = normalized.split() if normalized else []
            
            # Generar n-gramas
            document_ngrams = set()
            for n in range(self.ngram_range[0], min(self.ngram_range[1] + 1, len(tokens) + 1)):
                ngrams = self._generate_ngrams(tokens, n)
                document_ngrams.update(ngrams)
            
            all_ngrams.extend(document_ngrams)
            doc_ngrams.append(document_ngrams)
        
        # Construir vocabulario
        token_freq = Counter(all_ngrams)
        for idx, (token, _) in enumerate(sorted(
            token_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.vocabulary.get("_max_features", MAX_TOKENS)]):
            self.vocabulary[token] = idx
        
        # Calcular IDF
        num_docs = len(texts)
        for token in self.vocabulary:
            doc_count = sum(1 for doc_set in doc_ngrams if token in doc_set)
            if doc_count > 0:
                self.idf_weights[token] = math.log(num_docs / doc_count)
        
        self.fitted = True
    
    def transform_to_vector(self, text: str, normalization: NormalizationType = NormalizationType.AGGRESSIVE) -> Dict[str, float]:
        """
        Transformar texto a vector TF-IDF.
        
        Returns:
            Dict {token: tfidf_score}
        """
        if not self.fitted or not self.vocabulary:
            raise ValueError("Vectorizer not fitted. Call fit() first.")
        
        normalized = normalize_text(text, normalization)
        tokens = normalized.split() if normalized else []
        
        # Generar n-gramas
        ngrams = []
        for n in range(self.ngram_range[0], min(self.ngram_range[1] + 1, len(tokens) + 1)):
            ngrams.extend(self._generate_ngrams(tokens, n))
        
        # Contar frecuencias
        ngram_freq = Counter(ngrams)
        total_ngrams = len(ngrams) if ngrams else 1
        
        # Calcular TF-IDF
        vector = {}
        for ngram, freq in ngram_freq.items():
            if ngram in self.vocabulary:
                tf = freq / total_ngrams
                idf = self.idf_weights.get(ngram, 1.0)
                tfidf = tf * idf
                vector[ngram] = tfidf
        
        return vector
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """
        Calcular similitud coseno entre dos vectores TF-IDF.
        
        Returns:
            Valor entre 0 y 1 (1 = idénticos, 0 = completamente diferentes)
        """
        # Obtener términos comunes
        common_terms = set(vec1.keys()) & set(vec2.keys())
        
        if not common_terms:
            return 0.0
        
        # Producto escalar
        dot_product = sum(vec1[term] * vec2[term] for term in common_terms)
        
        # Magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values())) if vec1 else 0
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values())) if vec2 else 0
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        similarity = dot_product / (mag1 * mag2)
        return max(0.0, min(similarity, 1.0))


# ============================================================================
# ANÁLISIS Y EXTRACCIÓN DE TÉRMINOS
# ============================================================================

class TermExtractor:
    """
    Extrae y analiza términos relevantes de documentos.
    
    Enfocado en:
    - Identificar términos técnicos
    - Extraer frases multipalabra significativas
    - Ponderar términos por relevancia
    """
    
    def __init__(self, min_term_length: int = 2):
        self.min_term_length = min_term_length
        self.extracted_terms: Dict[str, float] = {}
    
    def extract_technical_terms(self, text: str) -> List[Tuple[str, float]]:
        """
        Extraer términos técnicos de un texto.
        
        Returns:
            Lista de (término, relevancia) ordenada por relevancia descendente
        """
        normalized = normalize_text(text, NormalizationType.TECHNICAL)
        tokens = normalized.split()
        
        technical_terms = []
        for token in tokens:
            if token in TECHNICAL_VOCAB or any(tech in token for tech in TECHNICAL_VOCAB):
                relevance = 1.0  # Base
                
                # Aumentar relevancia si aparece múltiples veces
                relevance += tokens.count(token) * 0.1
                
                technical_terms.append((token, relevance))
        
        # Deduplicar y ordenar
        unique_terms = {}
        for term, relevance in technical_terms:
            unique_terms[term] = max(unique_terms.get(term, 0), relevance)
        
        return sorted(unique_terms.items(), key=lambda x: x[1], reverse=True)
    
    def extract_soft_skills(self, text: str) -> List[Tuple[str, float]]:
        """
        Extraer habilidades blandas (soft skills) de un texto.
        
        Usa el mismo algoritmo que extract_technical_terms pero con SOFT_SKILLS_VOCAB.
        
        Returns:
            Lista de (habilidad, relevancia) ordenada por relevancia descendente
        
        Ejemplo:
            Input: "Tengo excelentes habilidades de comunicación y liderazgo..."
            Output: [("comunicación", 1.1), ("liderazgo", 1.0), ...]
        """
        normalized = normalize_text(text, NormalizationType.TECHNICAL)
        tokens = normalized.split()
        
        soft_skills = []
        for token in tokens:
            if token in SOFT_SKILLS_VOCAB or any(skill in token for skill in SOFT_SKILLS_VOCAB):
                relevance = 1.0  # Base
                
                # Aumentar relevancia si aparece múltiples veces
                relevance += tokens.count(token) * 0.1
                
                soft_skills.append((token, relevance))
        
        # Deduplicar y ordenar
        unique_skills = {}
        for skill, relevance in soft_skills:
            unique_skills[skill] = max(unique_skills.get(skill, 0), relevance)
        
        return sorted(unique_skills.items(), key=lambda x: x[1], reverse=True)
    
    def extract_keyphrases(self, text: str, max_phrase_length: int = 3) -> List[Tuple[str, float]]:
        """
        Extraer frases clave (n-gramas significativos).
        
        Args:
            text: Texto a procesar
            max_phrase_length: Máximo de palabras por frase
            
        Returns:
            Lista de (frase, score) ordenada por score descendente
        """
        normalized = normalize_text(text, NormalizationType.AGGRESSIVE)
        tokens = normalized.split()
        
        if len(tokens) < 2:
            return []
        
        phrases = {}
        for n in range(2, min(max_phrase_length + 1, len(tokens) + 1)):
            for i in range(len(tokens) - n + 1):
                phrase = " ".join(tokens[i:i+n])
                if len(phrase) >= self.min_term_length:
                    # Score basado en frecuencia
                    phrases[phrase] = phrases.get(phrase, 0) + 1
        
        # Normalizar scores
        max_freq = max(phrases.values()) if phrases else 1
        return sorted(
            [(phrase, freq / max_freq) for phrase, freq in phrases.items()],
            key=lambda x: x[1],
            reverse=True
        )


# ============================================================================
# SERVICIO PRINCIPAL
# ============================================================================

class TextVectorizationService:
    """
    Servicio integrado de vectorización y análisis NLP.
    
    Orquesta normalización, vocabulario y vectorización para tareas
    como matching entre perfiles y ofertas.
    """
    
    def __init__(self):
        self.vectorizer: Optional[TextVectorizer] = None
        self.vocab_builder: Optional[VocabularyBuilder] = None
        self.term_extractor = TermExtractor()
    
    def prepare_corpus(
        self,
        texts: List[str],
        normalization: NormalizationType = NormalizationType.AGGRESSIVE,
        ngram_range: Tuple[int, int] = (1, 2),
    ) -> VocabularyStats:
        """
        Preparar corpus: normalizar, construir vocabulario y entrenar vectorizador.
        
        Args:
            texts: Documentos a procesar
            normalization: Tipo de normalización
            ngram_range: Rango de n-gramas para vectorización
            
        Returns:
            Estadísticas del vocabulario construido
        """
        self.vocab_builder = VocabularyBuilder()
        self.vectorizer = TextVectorizer(ngram_range=ngram_range)
        
        # Construir vocabulario
        for text in texts:
            self.vocab_builder.add_document(text, normalization)
        
        # Entrenar vectorizador
        self.vectorizer.fit(texts, normalization)
        
        return self.vocab_builder.get_stats()
    
    def get_similarity(
        self,
        text1: str,
        text2: str,
        normalization: NormalizationType = NormalizationType.AGGRESSIVE,
    ) -> float:
        """
        Calcular similitud entre dos textos.
        
        Requiere que corpus haya sido preparado previamente.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            normalization: Tipo de normalización
            
        Returns:
            Similitud [0, 1]
        """
        if not self.vectorizer or not self.vectorizer.fitted:
            # Fallback: usar corpus mínimo
            self.prepare_corpus([text1, text2], normalization)
        
        vec1 = self.vectorizer.transform_to_vector(text1, normalization)
        vec2 = self.vectorizer.transform_to_vector(text2, normalization)
        
        return self.vectorizer.cosine_similarity(vec1, vec2)
    
    def analyze_document(self, text: str) -> Dict:
        """
        Análisis completo de un documento (Genérico: CV, oferta de trabajo, etc).
        
        Returns:
            Dict con:
            - normalized_text: Texto normalizado
            - token_count: Número de tokens
            - unique_tokens: Tokens únicos
            - tokens: Lista de tokens (primeros 50)
            - technical_terms: Términos técnicos encontrados (Tuple[term, relevance])
            - soft_skills: Habilidades blandas encontradas (Tuple[skill, relevance])
            - keyphrases: Frases clave (Tuple[phrase, score])
            - text_length: Largo original del texto
            - normalized_length: Largo del texto normalizado
        """
        normalized = normalize_text(text, NormalizationType.TECHNICAL)
        tokens = normalized.split() if normalized else []
        
        technical_terms = self.term_extractor.extract_technical_terms(text)
        soft_skills = self.term_extractor.extract_soft_skills(text)
        keyphrases = self.term_extractor.extract_keyphrases(text)
        
        return {
            "normalized_text": normalized,
            "token_count": len(tokens),
            "unique_tokens": len(set(tokens)),
            "tokens": tokens[:50],  # Primeros 50 para preview
            "technical_terms": technical_terms[:10],
            "soft_skills": soft_skills[:10],
            "keyphrases": keyphrases[:10],
            "text_length": len(text),
            "normalized_length": len(normalized),
        }
    
    # ❌ ELIMINADO: calculate_match_score()
    # 
    # RAZÓN: Contiene lógica de NEGOCIO (pesos, heurísticas)
    # que no pertenece a TextVectorizationService (que debe ser puro).
    # 
    # NUEVA UBICACIÓN: matching_service.py
    # Allí se usa get_similarity() (función matemática pura) con lógica de negocio.
    #
    # Esto mantiene la separación de responsabilidades:
    # - text_vectorization_service = análisis y similitud (math puro)
    # - matching_service = lógica de matching (reglas de negocio)


# Instancia compartida del servicio
text_vectorization_service = TextVectorizationService()
