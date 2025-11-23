/**
 * MoirAI - Profile Page JavaScript
 * Gestión del perfil de usuario y upload de CV
 */

let currentUser = null;
let uploadInProgress = false;

document.addEventListener('DOMContentLoaded', () => {
    initProfilePage();
});

/**
 * Inicializar página de perfil
 */
async function initProfilePage() {
    // Proteger ruta - todos los roles autenticados pueden acceder
    await protectedPageManager.initProtectedPage({
        redirectOnUnauth: '/login?redirect=/profile',
        loadingMessage: 'Cargando perfil...',
        onInit: async () => {
            await loadUserProfile();
            setupFormHandlers();
            setupCVUpload();
        }
    });
}

/**
 * ✅ Cargar perfil del usuario desde BD (NO localStorage)
 * Funciona para estudiantes y empresas
 * Si falla, usa localStorage como fallback
 */
async function loadUserProfile() {
    try {
        console.log('📥 Cargando perfil del usuario desde BD...');
        
        // ✅ Obtener perfil COMPLETO de BD
        currentUser = await authManager.getCurrentUser();

        if (!currentUser) {
            throw new Error('No se pudo obtener datos del usuario');
        }

        const isStudent = authManager.isStudent();
        const isCompany = authManager.isCompany();

        console.log('✅ Perfil cargado exitosamente:', {
            id: currentUser.id,
            email: currentUser.email,
            role: isStudent ? 'student' : isCompany ? 'company' : 'unknown',
            cvUploaded: currentUser.cv_uploaded,
            skillsCount: currentUser.skills?.length || 0
        });

        // Llenar formulario con datos existentes (de BD)
        const form = document.getElementById('profile-form');
        if (form) {
            // ✅ Campos comunes a ambos roles (con validación defensiva)
            const firstNameField = form.querySelector('[name="first_name"]');
            if (firstNameField) firstNameField.value = currentUser.first_name || '';
            
            const lastNameField = form.querySelector('[name="last_name"]');
            if (lastNameField) lastNameField.value = currentUser.last_name || '';
            
            const emailField = form.querySelector('[name="email"]');
            if (emailField) emailField.value = currentUser.email || '';
            
            const phoneField = form.querySelector('[name="phone"]');
            if (phoneField) phoneField.value = currentUser.phone || '';
            
            const bioField = form.querySelector('[name="bio"]');
            if (bioField) bioField.value = currentUser.bio || '';

            // ✅ Campos específicos de estudiante
            if (isStudent) {
                const studentForm = document.getElementById('student-fields');
                if (studentForm) {
                    studentForm.style.display = 'block';
                    const careerField = studentForm.querySelector('[name="career"]');
                    if (careerField) careerField.value = currentUser.career || '';
                    
                    const semesterField = studentForm.querySelector('[name="semester"]');
                    if (semesterField) semesterField.value = currentUser.semester || '';
                    
                    const programField = studentForm.querySelector('[name="program"]');
                    if (programField) programField.value = currentUser.program || '';
                }
            } else if (isCompany) {
                // Ocultar campos específicos de estudiante si es empresa
                const studentForm = document.getElementById('student-fields');
                if (studentForm) {
                    studentForm.style.display = 'none';
                }
            }
        }

        // ✅ Mostrar CV solo para estudiantes
        if (isStudent) {
            // Mostrar container Harvard CV
            const harvardContainer = document.getElementById('harvard-cv-container');
            if (harvardContainer) {
                harvardContainer.style.display = 'block';
            }
            
            // Ocultar fallback
            const fallbackCard = document.getElementById('skills-card-fallback');
            if (fallbackCard) {
                fallbackCard.style.display = 'none';
            }

            if (currentUser.cv_uploaded && currentUser.cv_filename) {
                console.log('📄 CV encontrado:', currentUser.cv_filename);
                showCVStatus(true, currentUser.cv_filename, currentUser.cv_upload_date);
            } else {
                console.log('⚪ Sin CV');
                showCVStatus(false);
            }

            // ✅ Mostrar habilidades de BD (solo para estudiantes)
            const allSkills = [];
            
            if (currentUser.skills && Array.isArray(currentUser.skills)) {
                allSkills.push(...currentUser.skills);
                console.log(`📚 ${currentUser.skills.length} habilidades técnicas`);
            }
            
            if (currentUser.soft_skills && Array.isArray(currentUser.soft_skills)) {
                allSkills.push(...currentUser.soft_skills);
                console.log(`💬 ${currentUser.soft_skills.length} habilidades blandas`);
            }
            
            if (allSkills.length > 0) {
                displayInferredSkills(allSkills);
            }

            // ✨ Cargar secciones Harvard CV
            loadCVHarvardSections(currentUser);

        } else if (isCompany) {
            // Ocultar container Harvard CV
            const harvardContainer = document.getElementById('harvard-cv-container');
            if (harvardContainer) {
                harvardContainer.style.display = 'none';
            }
            
            // Mostrar fallback de skills
            const fallbackCard = document.getElementById('skills-card-fallback');
            if (fallbackCard) {
                fallbackCard.style.display = 'block';
            }
            
            // Ocultar secciones de CV para empresas
            const cvCard = document.querySelector('.profile-card:has(#cv-upload-area)');
            if (cvCard) cvCard.style.display = 'none';
        }

        return currentUser;

    } catch (error) {
        console.error('❌ Error cargando perfil:', error);
        notificationManager.error('Error al cargar perfil');
        throw error;
    }
}

/**
 * ✨ NUEVA FUNCIÓN: Limpiar todos los datos de CV anteriores
 * Se llama al reuploaded para no mantener datos viejos
 */
function clearCVData() {
    console.log('🧹 Borrando todos los campos Harvard CV...');
    
    // Limpiar objetivo
    const objectiveField = document.getElementById('objective');
    if (objectiveField) objectiveField.value = '';
    
    // Limpiar educación
    const educationList = document.getElementById('education-list');
    if (educationList) educationList.innerHTML = '';
    
    // Limpiar experiencia
    const experienceList = document.getElementById('experience-list');
    if (experienceList) experienceList.innerHTML = '';
    
    // Limpiar certificaciones
    const certificationsList = document.getElementById('certifications-list');
    if (certificationsList) certificationsList.innerHTML = '';
    
    // Limpiar idiomas
    const languagesList = document.getElementById('languages-list');
    if (languagesList) languagesList.innerHTML = '';
    
    console.log('✅ Todos los campos Harvard CV han sido limpiados');
}

/**
 * ✨ NUEVA FUNCIÓN: Guardar cambios de CV en BD inmediatamente
 * Se llama después de cada eliminación para persistir cambios
 */
async function persistCVChanges(cvData) {
    try {
        notificationManager.loading('Guardando cambios en CV...');
        
        // Fusionar cvData con datos actuales del usuario
        const updatedUser = {
            ...currentUser,
            ...cvData
        };
        
        // Enviar PUT a BD
        const response = await apiClient.put(`/students/${currentUser.id}`, updatedUser);
        
        // Actualizar currentUser localmente
        currentUser = { ...currentUser, ...response };
        
        // Actualizar localStorage
        StorageManager.set('currentUser', currentUser);
        
        notificationManager.hideLoading();
        notificationManager.success('Cambios guardados en BD');
        
        console.log('✅ Cambios de CV persistidos:', cvData);
        
        return response;
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al guardar cambios: ' + (error.message || 'Error desconocido'));
        console.error('❌ Error guardando cambios de CV:', error);
    }
}

/**
 * Setup de manejadores de formulario
 */
function setupFormHandlers() {
    const form = document.getElementById('profile-form');
    if (!form) return;

    // Validación en tiempo real
    FormValidator.setupRealtimeValidation(form);

    // Manejador del submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validar formulario
        const validation = FormValidator.validateForm(form);
        if (!validation.valid) {
            notificationManager.error('Por favor completa todos los campos correctamente');
            return;
        }

        // Obtener datos
        const formData = FormValidator.getFormData(form);

        // ✨ Serializar datos Harvard CV
        const harvardData = serializeCVHarvardData();
        Object.assign(formData, harvardData);

        // Mostrar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        notificationManager.loading('Actualizando perfil...');

        try {
            // Enviar datos al API
            const response = await apiClient.put(`/students/${currentUser.id}`, formData);

            // Actualizar datos locales
            currentUser = { ...currentUser, ...response };

            // Guardar en localStorage
            StorageManager.set('currentUser', currentUser);

            notificationManager.hideLoading();
            notificationManager.success('Perfil actualizado exitosamente');

            submitBtn.disabled = false;
            submitBtn.textContent = originalText;

        } catch (error) {
            notificationManager.hideLoading();
            notificationManager.error(error.message || 'Error al actualizar perfil');

            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}

/**
 * Setup del upload de CV
 */
function setupCVUpload() {
    const uploadArea = document.getElementById('cv-upload-area');
    const fileInput = document.getElementById('cv-file-input');
    const uploadBtn = document.getElementById('cv-upload-btn');

    if (!uploadArea || !fileInput) return;

    // Click en área para abrir file picker
    uploadArea.addEventListener('click', () => fileInput.click());

    // Cambio en input de archivo
    fileInput.addEventListener('change', (e) => handleCVUpload(e.target.files[0]));

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleCVUpload(e.dataTransfer.files[0]);
    });
}

/**
 * ✅ Manejar upload de CV
 * Sincroniza correctamente con BD y localStorage
 */
async function handleCVUpload(file) {
    if (!file) return;

    // Validar tipo de archivo
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.txt')) {
        notificationManager.error('Solo se permiten archivos PDF, DOCX o TXT');
        return;
    }

    // Validar tamaño (máximo 5MB)
    if (file.size > 5 * 1024 * 1024) {
        notificationManager.error('El archivo no debe superar 5MB');
        return;
    }

    // Fix: Prevenir uploads duplicados
    if (uploadInProgress) {
        notificationManager.warning('Ya hay un upload en proceso');
        return;
    }

    uploadInProgress = true;
    notificationManager.loading(`Subiendo CV...`);

    try {
        // Preparar metadatos JSON para el endpoint
        const metadata = {
            name: currentUser.name || `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim(),
            email: currentUser.email,
            program: currentUser.career || currentUser.program || ''
        };
        
        // ✨ DEBUG: Loguear metadatos antes de enviar
        console.log('📤 Enviando metadatos de CV:', metadata);
        console.log('📄 Archivo:', { name: file.name, size: file.size, type: file.type });

        // Usar XMLHttpRequest para obtener progress con FormData
        const response = await uploadFileWithProgress(
            `/students/upload_resume`,
            file,
            metadata,
            (percentComplete) => {
                // Solo actualizar si no estamos cerca del 100%
                if (percentComplete < 100) {
                    notificationManager.loading(`Subiendo CV... ${Math.round(percentComplete)}%`);
                }
            }
        );

        // ✅ Procesar respuesta: ResumeAnalysisResponse contiene student y skills extraídas
        if (response.student) {
            // ✅ IMPORTANTE: Limpiar datos anteriores antes de cargar nuevos
            console.log('🧹 Limpiando datos de CV anterior...');
            clearCVData();
            
            // ✅ CAMBIO: Usar respuesta de BD, NO localStorage solo
            // Actualizar currentUser con datos de la respuesta (de BD)
            currentUser = { ...currentUser, ...response.student };
            
            // ✅ Guardar en localStorage como caché (robusto, sin dependencias)
            try {
                localStorage.setItem('currentUserProfile', JSON.stringify(currentUser));
                localStorage.setItem('currentUserProfile_timestamp', Date.now().toString());
                console.log('✅ CV profile cached:', {
                    fileName: response.student.cv_filename,
                    skillsCount: response.extracted_skills?.length || 0
                });
            } catch (storageError) {
                console.warn('⚠️ localStorage no disponible:', storageError);
            }

            // ✅ IMPORTANTE: Cerrar notificación de carga ANTES de mostrar éxito
            notificationManager.hideLoading();
            notificationManager.success('CV subido y analizado exitosamente');

            // Mostrar estado del CV
            showCVStatus(true, response.student.cv_filename || response.student.name, response.student.cv_upload_date);

            // ✅ Mostrar habilidades extraídas
            if (response.extracted_skills || response.extracted_soft_skills) {
                const allSkills = [
                    ...(response.extracted_skills || []),
                    ...(response.extracted_soft_skills || [])
                ];
                displayInferredSkills(allSkills);
                notificationManager.success(`¡${allSkills.length} habilidades analizadas!`);
            }

            // ✅ NUEVO: Recargar TODAS las secciones Harvard CV con datos extraídos
            console.log('🔄 Cargando nuevas secciones Harvard CV...');
            loadCVHarvardSections(currentUser);
            
            // Scroll suave al container Harvard CV para mostrar los nuevos datos
            setTimeout(() => {
                const harvardContainer = document.getElementById('harvard-cv-container');
                if (harvardContainer) {
                    harvardContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 500);
        } else {
            throw new Error('Respuesta inesperada del servidor');
        }

        uploadInProgress = false;

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error(error.message || 'Error al subir CV');
        uploadInProgress = false;
    }
}

/**
 * Upload de archivo con progress
 * 
 * Utiliza FormData para enviar:
 * - meta: JSON string con metadatos del estudiante
 * - file: archivo de CV
 */
function uploadFileWithProgress(url, file, metadata, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        // ✅ Usar localStorage directamente sin dependencias condicionales
        const apiKey = localStorage.getItem('api_key') || localStorage.getItem('authToken');

        // Setup xhr
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                onProgress(percentComplete);
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (e) {
                    reject(new Error('Invalid response format'));
                }
            } else {
                try {
                    const error = JSON.parse(xhr.responseText);
                    console.error('❌ Upload error response:', error);
                    reject(new Error(error.detail || error.message || 'Upload failed'));
                } catch (e) {
                    // Si no puede parsear JSON, loguear la respuesta como texto
                    console.error('❌ Upload error (non-JSON):', xhr.responseText);
                    reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.responseText}`));
                }
            }
        });

        xhr.addEventListener('error', () => {
            reject(new Error('Network error during upload'));
        });

        xhr.addEventListener('abort', () => {
            reject(new Error('Upload cancelled'));
        });

        // Preparar FormData con meta como JSON string y file
        const formData = new FormData();
        formData.append('meta', JSON.stringify(metadata));
        formData.append('file', file);

        xhr.open('POST', `${window.API_BASE_URL}${url}`, true);
        if (apiKey) {
            xhr.setRequestHeader('X-API-Key', apiKey);
        }
        xhr.send(formData);
    });
}

/**
 * ✨ NUEVA FUNCIÓN: Guardar solo el Objetivo Profesional
 * Función específica para guardar cambios del textarea de objetivo
 */
async function saveObjective() {
    try {
        const objectiveField = document.getElementById('objective');
        if (!objectiveField) {
            notificationManager.error('Campo de objetivo no encontrado');
            return;
        }
        
        const objective = objectiveField.value.trim();
        
        // Validación opcional: al menos 5 caracteres
        if (objective && objective.length < 5) {
            notificationManager.warning('El objetivo debe tener al menos 5 caracteres');
            return;
        }
        
        notificationManager.loading('Guardando objetivo...');
        
        // Actualizar solo el campo objective
        const updatedUser = {
            ...currentUser,
            objective: objective
        };
        
        // Enviar PUT a BD
        const response = await apiClient.put(`/students/${currentUser.id}`, updatedUser);
        
        // Actualizar currentUser
        currentUser = { ...currentUser, ...response };
        
        // Guardar en localStorage
        StorageManager.set('currentUser', currentUser);
        
        notificationManager.hideLoading();
        notificationManager.success('Objetivo profesional guardado ✅');
        
        console.log('✅ Objetivo profesional guardado:', objective.substring(0, 50) + '...');
        
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error(error.message || 'Error al guardar objetivo');
        console.error('❌ Error guardando objetivo:', error);
    }
}

/**
 * Mostrar estado del CV
 */
function showCVStatus(uploaded, fileName) {
    const statusElement = document.getElementById('cv-status');
    const downloadBtn = document.getElementById('cv-download-btn');
    const deleteBtn = document.getElementById('cv-delete-btn');

    if (!statusElement) return;

    if (uploaded) {
        statusElement.innerHTML = `
            <div class="cv-status-success">
                <i class="fas fa-check-circle"></i>
                <p>CV cargado: <strong>${fileName}</strong></p>
                <p class="upload-date">Última actualización: ${new Date().toLocaleDateString('es-ES')}</p>
            </div>
        `;

        if (downloadBtn) {
            downloadBtn.style.display = 'block';
            downloadBtn.href = `/api/v1/students/${currentUser.id}/download-resume`;
        }

        if (deleteBtn) {
            deleteBtn.style.display = 'block';
            deleteBtn.addEventListener('click', deleteCVFile);
        }
    } else {
        statusElement.innerHTML = `
            <div class="cv-status-empty">
                <i class="fas fa-file-pdf"></i>
                <p>No hay CV cargado</p>
            </div>
        `;

        if (downloadBtn) downloadBtn.style.display = 'none';
        if (deleteBtn) deleteBtn.style.display = 'none';
    }
}

/**
 * Eliminar archivo CV
 */
async function deleteCVFile() {
    if (!confirm('¿Estás seguro de que deseas eliminar tu CV?')) {
        return;
    }

    notificationManager.loading('Eliminando CV...');

    try {
        await apiClient.delete(`/students/${currentUser.id}/resume`);

        currentUser.cv_file = null;
        currentUser.cv_uploaded = false;

        StorageManager.set('currentUser', currentUser);

        notificationManager.hideLoading();
        notificationManager.success('CV eliminado');

        showCVStatus(false);

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al eliminar CV');
    }
}

/**
 * Mostrar habilidades inferidas
 */
function displayInferredSkills(skills) {
    // Intentar llenar ambos contenedores (para compatibilidad)
    const mainContainer = document.getElementById('inferred-skills');
    const fallbackContainer = document.getElementById('inferred-skills-fallback');

    if (!skills || skills.length === 0) {
        // Empty state
        const emptyHtml = `
            <div class="empty-state">
                <i class="fas fa-brain"></i>
                <p>Sube tu CV para que analicemos tus habilidades</p>
            </div>
        `;
        
        if (mainContainer) mainContainer.innerHTML = emptyHtml;
        if (fallbackContainer) fallbackContainer.innerHTML = emptyHtml;
        return;
    }

    let html = '<div class="cv-skills-grid">';

    skills.forEach((skill, index) => {
        // Mostrar solo el texto tal como viene
        const skillName = typeof skill === 'string' ? skill : (skill.name || 'Desconocida');

        html += `
            <div class="skill-item skill-badge-tech">
                <span class="skill-name">${skillName}</span>
                <button class="skill-remove" onclick="removeSkill('${index}')" title="Remover">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    });

    html += '</div>';
    
    // Llenar ambos contenedores
    if (mainContainer) mainContainer.innerHTML = html;
    if (fallbackContainer) fallbackContainer.innerHTML = html;
}

/**
 * Remover habilidad
 */
async function removeSkill(skillId) {
    try {
        // Si es índice numérico (string skills)
        if (!isNaN(skillId)) {
            const index = parseInt(skillId);
            if (currentUser.inferred_skills) {
                currentUser.inferred_skills = currentUser.inferred_skills.filter((_, i) => i !== index);
            }
        } else {
            // Si es ID de objeto
            if (currentUser.inferred_skills) {
                currentUser.inferred_skills = currentUser.inferred_skills.filter(s => 
                    typeof s === 'string' ? true : s.id !== skillId
                );
            }
        }
        
        displayInferredSkills(currentUser.inferred_skills);
        notificationManager.success('Habilidad removida');
    } catch (error) {
        notificationManager.error('Error al remover habilidad');
    }
}

/**
 * Cambiar contraseña
 */
async function handlePasswordChange() {
    const currentPassword = prompt('Ingresa tu contraseña actual:');
    if (!currentPassword) return;

    const newPassword = prompt('Ingresa tu nueva contraseña:');
    if (!newPassword) return;

    const confirmPassword = prompt('Confirma tu nueva contraseña:');
    if (confirmPassword !== newPassword) {
        notificationManager.error('Las contraseñas no coinciden');
        return;
    }

    // Validar nueva contraseña
    const validation = FormValidator.validate('password', newPassword);
    if (!validation.valid) {
        notificationManager.error(validation.error);
        return;
    }

    notificationManager.loading('Cambiando contraseña...');

    try {
        await authManager.changePassword(currentPassword, newPassword);
        notificationManager.hideLoading();
        notificationManager.success('Contraseña cambiada exitosamente');
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error(error.message || 'Error al cambiar contraseña');
    }
}

/**
 * ✨ NUEVA FUNCIÓN: Cargar secciones CV Harvard
 * Llena los campos existentes en el HTML con datos del usuario
 */
function loadCVHarvardSections(user) {
    console.log('📝 Llenando secciones Harvard CV con datos:', user);
    
    if (!user) {
        console.warn('⚠️ No hay datos de usuario para llenar Harvard CV');
        return;
    }

    try {
        // 1️⃣ Objetivo Profesional (textarea)
        const objectiveField = document.getElementById('objective');
        if (objectiveField && user.objective) {
            objectiveField.value = user.objective;
            console.log('✅ Objetivo cargado:', user.objective.substring(0, 50) + '...');
        }

        // 2️⃣ Educación (nested list)
        const educationValue = user.education 
            ? (typeof user.education === 'string' ? JSON.parse(user.education) : user.education) 
            : [];
        if (Array.isArray(educationValue) && educationValue.length > 0) {
            renderNestedItems('education', educationValue, ['institution', 'degree', 'field_of_study', 'graduation_year']);
            console.log('✅ Educación cargada:', educationValue.length, 'items');
        }

        // 3️⃣ Experiencia Profesional (nested list)
        const experienceValue = user.experience 
            ? (typeof user.experience === 'string' ? JSON.parse(user.experience) : user.experience) 
            : [];
        if (Array.isArray(experienceValue) && experienceValue.length > 0) {
            renderNestedItems('experience', experienceValue, ['position', 'company', 'start_date', 'end_date', 'description']);
            console.log('✅ Experiencia cargada:', experienceValue.length, 'items');
        }

        // 4️⃣ Certificaciones (simple list)
        const certificationsValue = user.certifications 
            ? (typeof user.certifications === 'string' ? JSON.parse(user.certifications) : user.certifications) 
            : [];
        if (Array.isArray(certificationsValue) && certificationsValue.length > 0) {
            renderSimpleItems('certifications', certificationsValue);
            console.log('✅ Certificaciones cargadas:', certificationsValue.length, 'items');
        }

        // 5️⃣ Idiomas (simple list)
        const languagesValue = user.languages 
            ? (typeof user.languages === 'string' ? JSON.parse(user.languages) : user.languages) 
            : [];
        if (Array.isArray(languagesValue) && languagesValue.length > 0) {
            renderSimpleItems('languages', languagesValue);
            console.log('✅ Idiomas cargados:', languagesValue.length, 'items');
        }

        console.log('✨ Todas las secciones Harvard CV han sido cargadas exitosamente');

    } catch (error) {
        console.error('❌ Error cargando secciones Harvard CV:', error);
    }
}

/**
 * ✨ NUEVA FUNCIÓN: Renderizar items anidados (educación, experiencia)
 */
function renderNestedItems(sectionId, items, fields) {
    const container = document.getElementById(`${sectionId}-list`);
    if (!container) return;

    container.innerHTML = '';

    if (!Array.isArray(items) || items.length === 0) return;

    items.forEach((item, index) => {
        const itemEl = document.createElement('div');
        itemEl.className = 'form-nested';
        itemEl.id = `${sectionId}-item-${index}`;

        let formFields = '';
        fields.forEach(field => {
            const value = item[field] || '';
            const label = field.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

            formFields += `
                <div class="form-group" style="margin-bottom: 0.75rem;">
                    <label>${label}</label>
                    <input 
                        type="text" 
                        name="${sectionId}[${index}][${field}]"
                        value="${value}"
                        placeholder="${label}"
                    />
                </div>
            `;
        });

        itemEl.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--primary-color); font-size: 0.9rem;">#${index + 1}</h4>
                <button type="button" class="form-nested-remove-btn" onclick="removeNestedItem('${sectionId}', ${index})">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
            ${formFields}
        `;

        container.appendChild(itemEl);
    });
}

/**
 * ✨ NUEVA FUNCIÓN: Renderizar items simples (certificaciones, idiomas)
 */
function renderSimpleItems(sectionId, items) {
    const container = document.getElementById(`${sectionId}-list`);
    if (!container) return;

    container.innerHTML = '';

    if (!Array.isArray(items) || items.length === 0) return;

    items.forEach((item, index) => {
        const itemEl = document.createElement('div');
        itemEl.className = 'items-list-item';
        
        itemEl.innerHTML = `
            <input 
                type="text" 
                name="${sectionId}[${index}]"
                value="${item}"
                placeholder="Ingresa ${sectionId === 'certifications' ? 'certificación' : 'idioma'}..."
            />
            <button type="button" class="items-list-item-remove" onclick="removeSimpleItem('${sectionId}', ${index})" title="Eliminar">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(itemEl);
    });
}

/**
 * ✨ NUEVA FUNCIÓN: Agregar item anidado (educación, experiencia)
 */
function addNestedItem(sectionId, fields) {
    const container = document.getElementById(`${sectionId}-list`);
    if (!container) return;

    const index = container.querySelectorAll('.form-nested').length;

    const itemEl = document.createElement('div');
    itemEl.className = 'form-nested';
    itemEl.id = `${sectionId}-item-${index}`;

    let formFields = '';
    fields.forEach(field => {
        const label = field.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

        formFields += `
            <div class="form-group" style="margin-bottom: 0.75rem;">
                <label>${label}</label>
                <input 
                    type="text" 
                    name="${sectionId}[${index}][${field}]"
                    placeholder="${label}"
                />
            </div>
        `;
    });

    itemEl.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: var(--primary-color); font-size: 0.9rem;">#${index + 1}</h4>
            <button type="button" class="form-nested-remove-btn" onclick="removeNestedItem('${sectionId}', ${index})">
                <i class="fas fa-trash"></i> Eliminar
            </button>
        </div>
        ${formFields}
    `;

    container.appendChild(itemEl);
}

/**
 * ✨ NUEVA FUNCIÓN: Remover item anidado
 * Marca como eliminado y persiste en BD
 */
function removeNestedItem(sectionId, index) {
    if (!confirm('¿Estás seguro de que deseas eliminar este item?')) return;
    
    const itemEl = document.getElementById(`${sectionId}-item-${index}`);
    if (itemEl) {
        // Marcar como eliminado (no remover del DOM todavía)
        itemEl.setAttribute('data-removed', 'true');
        itemEl.style.opacity = '0.5';
        itemEl.style.pointerEvents = 'none';
        itemEl.style.background = 'rgba(255,0,0,0.05)';
        
        // Mostrar notificación de pendiente guardado
        notificationManager.info('Item marcado para eliminar. Guarda los cambios.');
        
        // Serializar datos ACTUALES y guardar en BD
        const cvData = serializeCVHarvardData();
        persistCVChanges(cvData);
    }
}

/**
 * ✨ NUEVA FUNCIÓN: Agregar item simple (certificación, idioma)
 */
function addSimpleItem(sectionId) {
    const container = document.getElementById(`${sectionId}-list`);
    if (!container) return;

    const index = container.querySelectorAll('.items-list-item').length;
    const itemEl = document.createElement('div');
    itemEl.className = 'items-list-item';

    itemEl.innerHTML = `
        <input 
            type="text" 
            name="${sectionId}[${index}]"
            placeholder="Ingresa ${sectionId === 'certifications' ? 'certificación' : 'idioma'}..."
        />
        <button type="button" class="items-list-item-remove" onclick="removeSimpleItem('${sectionId}', ${index})" title="Eliminar">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(itemEl);
}

/**
 * ✨ NUEVA FUNCIÓN: Remover item simple
 * Marca como eliminado y persiste en BD
 */
function removeSimpleItem(sectionId, index) {
    const container = document.getElementById(`${sectionId}-list`);
    if (!container) return;

    const items = Array.from(container.querySelectorAll('.items-list-item'));
    if (index < items.length) {
        const itemEl = items[index];
        
        // Marcar como eliminado (no remover del DOM todavía)
        itemEl.setAttribute('data-removed', 'true');
        itemEl.style.opacity = '0.5';
        itemEl.style.pointerEvents = 'none';
        itemEl.style.background = 'rgba(255,0,0,0.05)';
        
        // Mostrar notificación de pendiente guardado
        notificationManager.info('Item marcado para eliminar. Guarda los cambios.');
        
        // Serializar datos ACTUALES y guardar en BD
        const cvData = serializeCVHarvardData();
        persistCVChanges(cvData);
    }
}

/**
 * ✨ NUEVA FUNCIÓN: Serializar datos Harvard para envío
 * Convierte los formularios anidados a JSON para el API
 * ⚠️ Excluye items marcados como eliminados (data-removed="true")
 */
function serializeCVHarvardData() {
    const data = {};
    
    // Objetivo (simple textarea)
    const objectiveField = document.getElementById('objective');
    if (objectiveField) {
        data.objective = objectiveField.value.trim();
    }

    // Educación (array de objetos)
    const educationList = document.getElementById('education-list');
    if (educationList) {
        data.education = [];
        document.querySelectorAll('#education-list .form-nested').forEach((item) => {
            // ⚠️ Saltar items marcados como eliminados
            if (item.getAttribute('data-removed') === 'true') {
                return;
            }
            
            const inputs = item.querySelectorAll('input[type="text"]');
            const fieldNames = ['institution', 'degree', 'field_of_study', 'graduation_year'];
            const obj = {};
            inputs.forEach((inp, i) => {
                if (i < fieldNames.length) {
                    obj[fieldNames[i]] = inp.value;
                }
            });
            if (Object.keys(obj).length > 0) {
                data.education.push(obj);
            }
        });
    }

    // Experiencia (array de objetos)
    const experienceList = document.getElementById('experience-list');
    if (experienceList) {
        data.experience = [];
        document.querySelectorAll('#experience-list .form-nested').forEach((item) => {
            // ⚠️ Saltar items marcados como eliminados
            if (item.getAttribute('data-removed') === 'true') {
                return;
            }
            
            const inputs = item.querySelectorAll('input[type="text"]');
            const fieldNames = ['position', 'company', 'start_date', 'end_date', 'description'];
            const obj = {};
            inputs.forEach((inp, i) => {
                if (i < fieldNames.length) {
                    obj[fieldNames[i]] = inp.value;
                }
            });
            if (Object.keys(obj).length > 0) {
                data.experience.push(obj);
            }
        });
    }

    // Certificaciones (array de strings)
    const certificationsList = document.getElementById('certifications-list');
    if (certificationsList) {
        data.certifications = Array.from(
            document.querySelectorAll('#certifications-list .items-list-item:not([data-removed="true"]) input[type="text"]')
        ).map(inp => inp.value.trim()).filter(v => v.length > 0);
    }

    // Idiomas (array de strings)
    const languagesList = document.getElementById('languages-list');
    if (languagesList) {
        data.languages = Array.from(
            document.querySelectorAll('#languages-list .items-list-item:not([data-removed="true"]) input[type="text"]')
        ).map(inp => inp.value.trim()).filter(v => v.length > 0);
    }

    console.log('✨ Datos Harvard serializados (excluyendo eliminados):', data);
    return data;
}
