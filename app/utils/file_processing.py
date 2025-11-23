"""
Utilidades para procesamiento de archivos
Extracción de texto de PDFs, DOCX y archivos de texto con soporte multi-encoding

FORMATOS SOPORTADOS:
- PDF: pdfplumber, PyPDF2 o pdfminer
- DOCX/DOC: python-docx
- TXT: Detección automática de encoding (UTF-8, Latin-1, CP1252, ISO-8859-1, UTF-16)

USO:
    from app.utils.file_processing import extract_text_from_upload, CVFileValidator
    
    # Validar
    is_valid, error = CVFileValidator.validate_file(file)
    if not is_valid:
        raise ValueError(error)
    
    # Extraer
    text = await extract_text_from_upload(file)
"""
import io
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

# Importaciones de librerías de procesamiento de archivos (con fallbacks)
try:
    import pdfplumber
    PDF_PLUMBER_AVAILABLE = True
except ImportError:
    PDF_PLUMBER_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDF_MINER_AVAILABLE = True
except ImportError:
    PDF_MINER_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

try:
    import docx2txt
    DOCX2TXT_AVAILABLE = True
except ImportError:
    DOCX2TXT_AVAILABLE = False

# Intenta cargar security_middleware si está disponible
try:
    from app.middleware.auth import security_middleware
    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False

# ============================================================================
# VALIDADOR DE ARCHIVOS CV
# ============================================================================

class CVFileValidator:
    """Validador robusto para archivos de CV"""
    
    # Configuración
    MAX_SIZE_MB = 5
    MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
    ALLOWED_MIMETYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/octet-stream'  # DOCX puede venir como octet-stream
    }
    MIN_TEXT_LENGTH = 50  # Mínimo de caracteres extraídos
    
    @staticmethod
    def validate_file(file_obj) -> Tuple[bool, Optional[str]]:
        """
        Validar archivo de CV
        
        Verifica:
        - Existencia del archivo
        - Extensión permitida
        - Tamaño máximo
        
        Returns:
            (is_valid, error_message)
        """
        # Verificar que el archivo existe
        if not file_obj or not file_obj.filename:
            return False, "Archivo no proporcionado"
        
        # Obtener extensión
        file_ext = Path(file_obj.filename).suffix.lower()
        if file_ext not in CVFileValidator.ALLOWED_EXTENSIONS:
            allowed = ', '.join(CVFileValidator.ALLOWED_EXTENSIONS)
            return False, f"Formato no permitido. Permitidos: {allowed}"
        
        # Validar tamaño si está disponible
        if hasattr(file_obj, 'size') and file_obj.size and file_obj.size > CVFileValidator.MAX_SIZE_BYTES:
            return False, f"Archivo muy grande. Máximo: {CVFileValidator.MAX_SIZE_MB}MB"
        
        return True, None
    
    @staticmethod
    def validate_content_type(content_type: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validar content-type del archivo
        
        Nota: Es una validación auxiliar, no crítica
        """
        if not content_type:
            return True, None  # Si no hay content_type, continuar de todas formas
        
        if content_type not in CVFileValidator.ALLOWED_MIMETYPES:
            # Advertencia pero no error crítico
            logger.warning(f"Content-Type inesperado: {content_type}")
            return True, None
        
        return True, None


# ============================================================================
# EXTRACTORES DE TEXTO POR FORMATO
# ============================================================================

def _extract_text_from_pdf(content: bytes) -> str:
    """
    Extraer texto de archivo PDF
    
    Intenta:
    1. pdfplumber (mejor calidad)
    2. PyPDF2
    3. pdfminer
    """
    # Intento 1: pdfplumber
    if PDF_PLUMBER_AVAILABLE:
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
                logger.info("PDF procesado con pdfplumber")
                return text.strip()
        except Exception as e:
            logger.warning(f"Error con pdfplumber: {e}")
    
    # Intento 2: PyPDF2
    if PYPDF2_AVAILABLE:
        try:
            text = ""
            pdf_reader = PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
                logger.info("PDF procesado con PyPDF2")
                return text.strip()
        except Exception as e:
            logger.warning(f"Error con PyPDF2: {e}")
    
    # Intento 3: pdfminer
    if PDF_MINER_AVAILABLE:
        try:
            text = pdf_extract_text(io.BytesIO(content))
            if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
                logger.info("PDF procesado con pdfminer")
                return text.strip()
        except Exception as e:
            logger.warning(f"Error con pdfminer: {e}")
    
    # Si ninguno está disponible
    raise HTTPException(
        status_code=500,
        detail="Procesamiento de PDF no disponible. Instale: pdfplumber o PyPDF2 o pdfminer.six"
    )


def _extract_text_from_docx(content: bytes) -> str:
    """
    Extraer texto de archivo DOCX/DOC
    
    Intenta:
    1. python-docx
    2. docx2txt
    """
    # Intento 1: python-docx (mejor calidad)
    if PYTHON_DOCX_AVAILABLE:
        try:
            from io import BytesIO
            doc = DocxDocument(BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
                logger.info("DOCX procesado con python-docx")
                return text.strip()
        except Exception as e:
            logger.warning(f"Error con python-docx: {e}")
    
    # Intento 2: docx2txt
    if DOCX2TXT_AVAILABLE:
        try:
            text = docx2txt.process(io.BytesIO(content))
            if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
                logger.info("DOCX procesado con docx2txt")
                return text.strip()
        except Exception as e:
            logger.warning(f"Error con docx2txt: {e}")
    
    # Si ninguno está disponible
    raise HTTPException(
        status_code=500,
        detail="Procesamiento de DOCX no disponible. Instale: python-docx o docx2txt"
    )


def _extract_text_from_txt(content: bytes) -> str:
    """
    Extraer texto de archivo TXT
    
    Soporta múltiples encodings con detección automática:
    - UTF-8, UTF-16
    - Latin-1, CP1252, ISO-8859-1
    - Fallback a latin-1 ignorando errores
    """
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            text = content.decode(encoding)
            if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
                logger.info(f"TXT decodificado con {encoding}")
                return text.strip()
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Fallback: latin-1 ignorando errores
    try:
        logger.warning("TXT: usando latin-1 con errors='ignore'")
        text = content.decode('latin-1', errors='ignore')
        if text and len(text.strip()) >= CVFileValidator.MIN_TEXT_LENGTH:
            return text.strip()
    except Exception as e:
        pass
    
    raise HTTPException(
        status_code=400,
        detail="No se pudo decodificar el archivo TXT. Intente con UTF-8 o Latin-1"
    )


# ============================================================================
# FUNCIÓN PRINCIPAL DE EXTRACCIÓN
# ============================================================================

def extract_text_from_upload(file: UploadFile) -> str:
    """
    Extraer texto de archivo subido (PDF, DOCX o TXT)
    
    FUNCIÓN SINCRÓNICA - para uso inmediato
    
    Args:
        file: Archivo subido a través de FastAPI
        
    Returns:
        str: Texto extraído del archivo
        
    Raises:
        HTTPException: Si hay error en el procesamiento
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
    
    # Leer contenido del archivo
    try:
        content = file.file.read()
        file.file.seek(0)  # Reset para futuras lecturas
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error leyendo archivo: {str(e)}"
        )
    
    # Validar archivo por seguridad si security_middleware está disponible
    if SECURITY_MIDDLEWARE_AVAILABLE:
        try:
            security_middleware.validate_file_upload(content, file.filename)
        except Exception as e:
            logger.warning(f"Error en validación de seguridad: {e}")
            # Continuar de todas formas
    
    # Validar con CVFileValidator
    is_valid, error = CVFileValidator.validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Validar content-type
    if hasattr(file, 'content_type'):
        CVFileValidator.validate_content_type(file.content_type)
    
    # Determinar tipo de archivo y extraer texto
    filename_lower = file.filename.lower()
    
    try:
        if filename_lower.endswith('.pdf'):
            return _extract_text_from_pdf(content)
        elif filename_lower.endswith(('.docx', '.doc')):
            return _extract_text_from_docx(content)
        elif filename_lower.endswith('.txt'):
            return _extract_text_from_txt(content)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado: {file.filename}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando archivo {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando archivo: {str(e)}"
        )


async def extract_text_from_upload_async(file: UploadFile) -> str:
    """
    Extraer texto de archivo subido (versión ASINCRÓNICA)
    
    Para uso en endpoints async
    
    Args:
        file: Archivo subido a través de FastAPI
        
    Returns:
        str: Texto extraído del archivo
    """
    # Crear archivo temporal
    try:
        content = await file.read()
        file_ext = Path(file.filename).suffix.lower()
        
        # Escribir en archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Procesar como si fuera upload synchrono
            class FakeFile:
                def __init__(self, filename, content):
                    self.filename = filename
                    self.file = io.BytesIO(content)
                    self.content_type = file.content_type if hasattr(file, 'content_type') else None
                
                def read(self):
                    return self.file.getvalue()
            
            fake_file = FakeFile(file.filename, content)
            return extract_text_from_upload(fake_file)
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(tmp_path)
            except:
                pass
    except Exception as e:
        logger.error(f"Error en extracción async: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando archivo: {str(e)}"
        )


# ============================================================================
# FUNCIONES UTILIDAD
# ============================================================================

def validate_file_for_processing(file: UploadFile) -> bool:
    """
    Validar que el archivo es apropiado para procesamiento
    
    Args:
        file: Archivo a validar
        
    Returns:
        bool: True si el archivo es válido
        
    Raises:
        HTTPException: Si el archivo no es válido
    """
    is_valid, error = CVFileValidator.validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    return True


def get_file_info(file: UploadFile) -> dict:
    """
    Obtener información del archivo subido
    
    Args:
        file: Archivo subido
        
    Returns:
        dict: Información del archivo con claves:
            - filename: Nombre del archivo
            - content_type: MIME type
            - size_bytes: Tamaño en bytes
            - extension: Extensión del archivo
            - size_mb: Tamaño en MB (redondeado a 2 decimales)
    """
    file_size = None
    try:
        current_pos = file.file.tell()
        file.file.seek(0, 2)  # Ir al final
        file_size = file.file.tell()
        file.file.seek(current_pos)  # Volver a posición original
    except:
        pass
    
    file_ext = Path(file.filename).suffix.lower() if file.filename and '.' in file.filename else ''
    
    return {
        'filename': file.filename,
        'content_type': getattr(file, 'content_type', None),
        'size_bytes': file_size,
        'extension': file_ext,
        'size_mb': round(file_size / (1024 * 1024), 2) if file_size else None
    }
