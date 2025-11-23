/**
 * MoirAI - Jobs Search Page JavaScript
 * Búsqueda y filtrado de empleos con matchmaking inteligente
 */

// Estado global
let currentJobs = [];
let allJobsData = [];
let currentPage = 1;
const itemsPerPage = 12;
let totalJobs = 0;
let isSearchInProgress = false;

// Rate limiter para búsquedas
class SearchRateLimiter {
    constructor(maxRequests = 3, windowMs = 5000) {
        this.maxRequests = maxRequests;
        this.windowMs = windowMs;
        this.requests = [];
    }

    isAllowed() {
        const now = Date.now();
        this.requests = this.requests.filter(t => now - t < this.windowMs);

        if (this.requests.length >= this.maxRequests) {
            return false;
        }

        this.requests.push(now);
        return true;
    }
}

const searchLimiter = new SearchRateLimiter(3, 5000);

/**
 * ✨ NUEVO: Normalizar datos de jobs desde diferentes fuentes del API
 * Asegura que los campos están en el formato correcto (arrays, strings, etc)
 */
function normalizeJobData(jobs) {
    if (!Array.isArray(jobs)) return [];

    return jobs.map(job => ({
        ...job,
        // Normalizar skills: asegurar que sea un array
        skills: normalizeSkills(job.skills),
        // Normalizar otros campos
        description: job.description || job.job_description || '',
        title: job.title || job.job_title || '',
        company: job.company || job.company_name || '',
        location: job.location || job.job_location || '',
        salary_min: job.salary_min || job.salary || null,
        salary_max: job.salary_max || null,
        currency: job.currency || 'MXN',
        job_url: job.job_url || job.url || '',
        source: job.source || job.job_source || 'occ'
    }));
}

/**
 * ✨ NUEVO: Normalizar campo de skills
 * Maneja múltiples formatos: array, string JSON, string separado por comas, etc
 */
function normalizeSkills(skills) {
    if (!skills) return [];
    
    // Si ya es un array, retornarlo
    if (Array.isArray(skills)) {
        return skills.filter(s => s).map(s => String(s).trim());
    }
    
    // Si es string, intentar parsear como JSON primero
    if (typeof skills === 'string') {
        try {
            // Intentar parsear como JSON
            const parsed = JSON.parse(skills);
            if (Array.isArray(parsed)) {
                return parsed.filter(s => s).map(s => String(s).trim());
            }
        } catch (e) {
            // No es JSON, continuar
        }
        
        // Si no es JSON, intentar como string separado por comas
        if (skills.includes(',')) {
            return skills.split(',')
                .filter(s => s)
                .map(s => s.trim());
        }
        
        // Si tiene algún contenido, retornarlo como array de un elemento
        if (skills.trim()) {
            return [skills.trim()];
        }
    }
    
    return [];
}

// Inicializar página
document.addEventListener('DOMContentLoaded', () => {
    initJobsSearchPage();
});

/**
 * Inicializar página de búsqueda de empleos
 */
async function initJobsSearchPage() {
    // Proteger ruta - estudiantes y empresas pueden acceder
    await protectedPageManager.initProtectedPage({
        requiredRoles: ['student', 'company'],
        redirectOnUnauth: '/login?redirect=/oportunidades',
        redirectOnUnauthorized: '/dashboard',
        loadingMessage: 'Cargando oportunidades...',
        onInit: async () => {
            setupEventListeners();
            setupBackgroundSearchListeners();
            await loadInitialJobs();
            // Iniciar búsqueda en segundo plano después de cargar inicial
            startBackgroundSearch();
        }
    });
}

/**
 * Setup de event listeners - Refactorizado para modelo JobPosition
 */
function setupEventListeners() {
    // Búsqueda por texto
    const searchInput = document.getElementById('searchJobs');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 500));
    }

    // Filtros - Mapeados a campos del modelo JobPosition
    const filterElements = document.querySelectorAll(
        '.modality-filter, .level-filter, .skill-filter, ' +
        '#locationFilter, #jobTypeFilter, #sortFilter'
    );

    filterElements.forEach(element => {
        element.addEventListener('change', handleFilterChange);
    });

    // Evento adicional para input de ubicación (búsqueda en tiempo real)
    const locationInput = document.getElementById('locationFilter');
    if (locationInput && locationInput.type === 'text') {
        locationInput.addEventListener('input', debounce(handleFilterChange, 300));
    }

    // Botón de limpiar filtros
    const clearFiltersBtn = document.querySelector('.clear-filters-btn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }

    // Cambio de vista
    const viewModeButtons = document.querySelectorAll('.view-mode-btn');
    viewModeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            viewModeButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const mode = e.target.dataset.mode;
            setViewMode(mode);
        });
    });
}

/**
 * Setup de listeners para búsqueda en segundo plano
 */
function setupBackgroundSearchListeners() {
    // Escuchar actualizaciones de empleos en segundo plano
    window.addEventListener('jobsUpdated', (e) => {
        const { keyword, newJobs, totalJobs } = e.detail;
        
        // ✨ NORMALIZAR nuevos empleos antes de agregar
        const normalizedJobs = normalizeJobData(newJobs);
        allJobsData.push(...normalizedJobs);
        
        // Actualizar UI si no hay filtros activos
        const hasActiveFilters = 
            document.getElementById('searchJobs')?.value ||
            document.getElementById('locationFilter')?.value ||
            document.querySelectorAll('.modality-filter:checked').length > 0;
            
        if (!hasActiveFilters) {
            currentJobs = allJobsData;
            currentPage = 1;
            renderJobs();
        }
        
        // Actualizar contador
        updateJobCount(totalJobs);
    });

    // Escuchar cuando se completa la búsqueda en segundo plano
    window.addEventListener('backgroundJobsReady', (e) => {
        const { jobs, count } = e.detail;
        console.log(`🎉 Búsqueda en segundo plano completada: ${count} empleos`);
        notificationManager.success(`Se encontraron ${count} empleos en total`);
    });
}

/**
 * Iniciar búsqueda en segundo plano
 */
function startBackgroundSearch() {
    if (typeof backgroundJobSearch === 'undefined') {
        console.warn('⚠️ backgroundJobSearch no está definido');
        return;
    }
    
    // Solo iniciar si no está corriendo ya
    if (!backgroundJobSearch.isRunning) {
        backgroundJobSearch.start();
    }
}

/**
 * Actualizar contador de empleos
 */
function updateJobCount(count) {
    const countElement = document.getElementById('jobCount');
    if (countElement) {
        countElement.textContent = count;
    }
}

/**
 * Cargar empleos iniciales desde cache persistente (BD)
 * ✨ MEJORADO: Usa parámetros para búsqueda inicial más relevante
 */
async function loadInitialJobs() {
    notificationManager.loading('Cargando empleos disponibles...');

    try {
        // ✨ NUEVO: Intentar cargar del cache persistente (BD) primero
        // GET /job-scraping/cache/list - Mucho más rápido que scraping
        const response = await apiClient.get('/job-scraping/cache/list', {
            params: {
                limit: 100,
                offset: 0
            }
        });

        if (response && response.jobs && response.jobs.length > 0) {
            allJobsData = normalizeJobData(response.jobs);
            currentJobs = allJobsData;
            totalJobs = response.total;
            
            console.log(`✅ Cache cargado: ${allJobsData.length} de ${totalJobs} empleos`);
            notificationManager.hideLoading();
            renderJobs();
            return;
        }

        // Fallback: Si no hay cache, buscar empleos generales con parámetros enriquecidos
        console.log('📦 Cache vacío, buscando empleos iniciales...');
        const searchResponse = await apiClient.post('/job-scraping/search', {
            keyword: 'empleo trabajo oportunidad',  // Múltiples keywords para máxima cobertura
            location: null,
            detailed: true,
            sort_by: 'relevance',  // Ordenar por relevancia
            page: 1,
            category: null,
            experience_level: null,
            work_mode: null,
            job_type: null,
            company_verified: false,
            salary_min: null,
            salary_range: null
        });
        
        allJobsData = normalizeJobData(searchResponse.jobs || []);
        currentJobs = allJobsData;
        totalJobs = searchResponse.total_results || allJobsData.length;

        notificationManager.hideLoading();
        renderJobs();

    } catch (error) {
        notificationManager.hideLoading();
        
        // Si falla todo, mostrar mensaje de error
        console.error('Error al cargar empleos:', error);
        notificationManager.error('Error al cargar empleos. Intenta más tarde.');
    }
}

/**
 * Realizar búsqueda - ✨ MEJORADO: Usa todos los parámetros disponibles del endpoint
 */
async function handleSearch() {
    // Rate limiting
    if (!searchLimiter.isAllowed()) {
        notificationManager.warning('Por favor espera antes de hacer otra búsqueda');
        return;
    }

    if (isSearchInProgress) return;
    isSearchInProgress = true;

    try {
        const keyword = document.getElementById('searchJobs')?.value || '';
        const location = document.getElementById('locationFilter')?.value || '';
        const jobType = document.getElementById('jobTypeFilter')?.value || '';
        
        // Obtener filtros seleccionados
        const workModes = Array.from(
            document.querySelectorAll('.modality-filter:checked')
        ).map(el => el.value).join(',') || null;
        
        const experienceLevels = Array.from(
            document.querySelectorAll('.level-filter:checked')
        ).map(el => el.value).join(',') || null;

        if (!keyword.trim()) {
            notificationManager.warning('Por favor ingresa un término de búsqueda');
            isSearchInProgress = false;
            return;
        }

        notificationManager.loading('Buscando empleos...');

        // ✅ MEJORADO: POST /job-scraping/search con TODOS los parámetros disponibles
        const response = await apiClient.post('/job-scraping/search', {
            keyword: keyword,
            location: location || null,
            job_type: jobType || null,
            work_mode: workModes ? workModes.split(',')[0] : null,  // Primer modo seleccionado
            experience_level: experienceLevels ? experienceLevels.split(',')[0] : null,  // Primer nivel
            sort_by: 'relevance',      // Ordenar por relevancia
            detailed: true,           // Datos básicos (rápido)
            page: 1,
            category: null,            // Categoría (opcional)
            salary_min: null,          // Salario mínimo (opcional)
            salary_range: null,        // Rango salarial (opcional)
            company_verified: false    // Filtrar por empresas verificadas
        });
        
        allJobsData = normalizeJobData(response.jobs || []);
        currentJobs = allJobsData;
        totalJobs = response.total_results || allJobsData.length;
        currentPage = 1;

        notificationManager.hideLoading();

        if (allJobsData.length === 0) {
            notificationManager.info(`No se encontraron empleos para "${keyword}"`);
        } else {
            notificationManager.success(`Se encontraron ${allJobsData.length} empleos`);
        }

        renderJobs();

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error(error.message || 'Error al buscar empleos');
        console.error(error);
    } finally {
        isSearchInProgress = false;
    }
}

/**
 * Manejar cambio de filtro
 */
async function handleFilterChange() {
    currentPage = 1; // Resetear a página 1
    await applyFilters();
}

/**
 * Aplicar filtros basados en el modelo JobPosition
 * Campos disponibles: work_mode, experience_level, skills, category, job_type, location, salary_range
 */
async function applyFilters() {
    try {
        // Obtener valores de filtros del DOM
        const workModes = Array.from(
            document.querySelectorAll('.modality-filter:checked')
        ).map(el => el.value);

        const experienceLevels = Array.from(
            document.querySelectorAll('.level-filter:checked')
        ).map(el => el.value);

        const selectedSkills = Array.from(
            document.querySelectorAll('.skill-filter:checked')
        ).map(el => el.value);

        const location = document.getElementById('locationFilter')?.value || '';
        const jobType = document.getElementById('jobTypeFilter')?.value || '';
        const sortBy = document.getElementById('sortFilter')?.value || 'recent';

        // Filtrar datos basado en modelo JobPosition
        let filtered = [...allJobsData];

        // Filtro por modalidad (work_mode)
        if (workModes.length > 0) {
            filtered = filtered.filter(job => {
                const jobWorkMode = job.work_mode?.toLowerCase() || '';
                return workModes.some(mode => jobWorkMode.includes(mode.toLowerCase()));
            });
        }

        // Filtro por nivel de experiencia (experience_level)
        if (experienceLevels.length > 0) {
            filtered = filtered.filter(job => {
                const jobLevel = job.experience_level?.toLowerCase() || '';
                return experienceLevels.some(level => jobLevel.includes(level.toLowerCase()));
            });
        }

        // Filtro por habilidades (skills - JSON field)
        if (selectedSkills.length > 0) {
            filtered = filtered.filter(job => {
                const jobSkills = Array.isArray(job.skills) 
                    ? job.skills.map(s => s.toLowerCase())
                    : (job.skills || '').toLowerCase().split(',').map(s => s.trim());
                
                return selectedSkills.some(skill =>
                    jobSkills.some(js => js.includes(skill.toLowerCase()))
                );
            });
        }

        // Filtro por ubicación (location field)
        if (location) {
            filtered = filtered.filter(job =>
                job.location?.toLowerCase().includes(location.toLowerCase())
            );
        }

        // Filtro por tipo de trabajo (job_type)
        if (jobType) {
            filtered = filtered.filter(job =>
                job.job_type?.toLowerCase() === jobType.toLowerCase()
            );
        }

        // Ordenar resultados
        switch (sortBy) {
            case 'match':
                // Ordenar por match_score si disponible
                filtered.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
                break;
            case 'salary-high':
                // Ordenar por salary_max de mayor a menor
                filtered.sort((a, b) => {
                    const aSalary = parseFloat(b.salary_max || 0);
                    const bSalary = parseFloat(a.salary_max || 0);
                    return aSalary - bSalary;
                });
                break;
            case 'salary-low':
                // Ordenar por salary_min de menor a mayor
                filtered.sort((a, b) => {
                    const aSalary = parseFloat(a.salary_min || 0);
                    const bSalary = parseFloat(b.salary_min || 0);
                    return aSalary - bSalary;
                });
                break;
            case 'recent':
            default:
                // Ordenar por fecha de publicación más reciente
                filtered.sort((a, b) =>
                    new Date(b.publication_date || b.published_at || 0) - 
                    new Date(a.publication_date || a.published_at || 0)
                );
        }

        currentJobs = filtered;
        currentPage = 1;
        renderJobs();

    } catch (error) {
        notificationManager.error('Error al aplicar filtros');
        console.error(error);
    }
}

/**
 * Renderizar lista de empleos
 */
function renderJobs() {
    const container = document.getElementById('jobsContainer');
    if (!container) {
        console.warn('Container #jobsContainer no encontrado');
        return;
    }

    // Actualizar contador
    const countElement = document.getElementById('resultsCount');
    if (countElement) {
        countElement.textContent = currentJobs.length;
    }

    // Paginación
    const start = (currentPage - 1) * itemsPerPage;
    const paginatedJobs = currentJobs.slice(start, start + itemsPerPage);

    if (paginatedJobs.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem;">
                <i class="fas fa-briefcase" style="font-size: 3rem; color: var(--text-tertiary); margin-bottom: 1rem;"></i>
                <p style="color: var(--text-secondary);">No hay empleos que coincidan con tus filtros</p>
            </div>
        `;
        updatePagination(currentJobs.length);
        return;
    }

    // Renderizar jobs
    container.innerHTML = paginatedJobs.map(job => {
        const matchScore = job.match_score || job.match || 0;
        const matchClass = matchScore >= 75 ? 'high' : matchScore >= 50 ? 'medium' : 'low';

        return `
            <div class="job-card" data-job-id="${job.id || job.job_id}">
                <div class="job-header">
                    <div class="job-info">
                        <h3 class="job-title">${escapeHtml(job.title || 'Sin título')}</h3>
                        <p class="job-company">
                            <i class="fas fa-building"></i>
                            ${escapeHtml(job.company || 'Empresa no disponible')}
                        </p>
                    </div>
                    <span class="job-match match-${matchClass}">
                        ${Math.round(matchScore)}% Match
                    </span>
                </div>

                <div class="job-meta">
                    <div class="job-meta-item">
                        <i class="fas fa-map-marker-alt"></i>
                        ${escapeHtml(job.location || 'Ubicación no especificada')}
                    </div>
                    ${job.work_mode ? `
                        <span class="job-modality ${job.work_mode.toLowerCase()}">
                            ${capitalizeFirst(job.work_mode)}
                        </span>
                    ` : ''}
                    ${job.experience_level ? `
                        <span class="job-level">${capitalizeFirst(job.experience_level)}</span>
                    ` : ''}
                </div>

                ${job.salary_min && job.salary_max ? `
                    <div class="job-salary">
                        <i class="fas fa-money-bill-wave"></i>
                        $${formatNumber(job.salary_min)} - $${formatNumber(job.salary_max)}
                        ${job.currency || 'MXN'}
                    </div>
                ` : ''}

                <p class="job-description">
                    ${escapeHtml((job.description || '').substring(0, 150))}...
                </p>

                ${job.skills && job.skills.length > 0 ? `
                    <div class="job-skills">
                        ${job.skills.slice(0, 3).map(skill => `
                            <span class="skill-tag">${escapeHtml(skill)}</span>
                        `).join('')}
                        ${job.skills.length > 3 ? `
                            <span class="skill-tag">+${job.skills.length - 3} más</span>
                        ` : ''}
                    </div>
                ` : ''}

                <div class="job-actions">
                    <button class="btn btn-secondary" onclick="viewJobDetail('${job.id || job.job_id}')">
                        <i class="fas fa-eye"></i> Ver Detalles
                    </button>
                    <button class="btn btn-primary" onclick="applyForJob('${job.id || job.job_id}')">
                        <i class="fas fa-paper-plane"></i> Aplicar
                    </button>
                </div>
            </div>
        `;
    }).join('');

    updatePagination(currentJobs.length);
}

/**
 * Ver detalles de un empleo
 */
async function viewJobDetail(jobId) {
    try {
        // Buscar en datos locales primero
        let job = allJobsData.find(j => j.id === jobId || j.job_id === jobId);

        if (!job) {
            notificationManager.loading('Cargando detalles del empleo...');

            // Obtener del API si no está en local
            const response = await apiClient.get(`/jobs/${jobId}`);
            job = response.job || response.data;
            
            // ✨ Normalizar job si viene del API
            if (job) {
                const normalized = normalizeJobData([job]);
                job = normalized[0];
            }

            notificationManager.hideLoading();
        }

        // Abrir modal con detalles
        openJobDetailsModal(job);

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al cargar los detalles del empleo');
        console.error(error);
    }
}

/**
 * Abrir modal con detalles del empleo
 */
function openJobDetailsModal(job) {
    const modal = document.createElement('div');
    modal.className = 'modal modal-job-details';
    modal.id = 'jobDetailsModal';

    const matchScore = job.match_score || job.match || 0;
    const matchClass = matchScore >= 75 ? 'high' : matchScore >= 50 ? 'medium' : 'low';

    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-modal" onclick="document.getElementById('jobDetailsModal')?.remove()">&times;</span>

            <div class="modal-header-job">
                <div class="job-title-section">
                    <h1>${escapeHtml(job.title)}</h1>
                    <p class="job-company-modal">
                        <i class="fas fa-building"></i> ${escapeHtml(job.company)}
                    </p>
                </div>
                <span class="job-match-modal match-${matchClass}">
                    ${Math.round(matchScore)}% Match
                </span>
            </div>

            <div class="modal-body-job">
                <div class="job-details-grid">
                    <div class="detail-section">
                        <h3>Información General</h3>
                        <div class="detail-item">
                            <strong>Ubicación:</strong>
                            <span><i class="fas fa-map-marker-alt"></i> ${escapeHtml(job.location)}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Modalidad:</strong>
                            <span class="job-modality ${job.work_mode?.toLowerCase()}">
                                ${capitalizeFirst(job.work_mode)}
                            </span>
                        </div>
                        <div class="detail-item">
                            <strong>Nivel de Experiencia:</strong>
                            <span>${capitalizeFirst(job.experience_level || 'No especificado')}</span>
                        </div>
                        <div class="detail-item">
                            <strong>Tipo de Contrato:</strong>
                            <span>${capitalizeFirst(job.job_type || 'No especificado')}</span>
                        </div>
                    </div>

                    <div class="detail-section">
                        <h3>Compensación</h3>
                        ${job.salary_min && job.salary_max ? `
                            <div class="detail-item">
                                <strong>Rango Salarial:</strong>
                                <span>$${formatNumber(job.salary_min)} - $${formatNumber(job.salary_max)} ${job.currency || 'MXN'}</span>
                            </div>
                        ` : '<p>No especificado</p>'}
                    </div>

                    ${job.benefits && job.benefits.length > 0 ? `
                        <div class="detail-section">
                            <h3>Beneficios</h3>
                            <ul class="benefits-list">
                                ${job.benefits.slice(0, 5).map(benefit => `
                                    <li><i class="fas fa-check"></i> ${escapeHtml(benefit)}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${job.skills && job.skills.length > 0 ? `
                        <div class="detail-section">
                            <h3>Habilidades Requeridas</h3>
                            <div class="skills-grid">
                                ${job.skills.map(skill => `
                                    <span class="skill-tag">${escapeHtml(skill)}</span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>

                <div class="detail-section full-width">
                    <h3>Descripción del Puesto</h3>
                    <div class="job-description-full">
                        ${escapeHtml(job.description || 'No disponible')}
                    </div>
                </div>

                ${job.requirements ? `
                    <div class="detail-section full-width">
                        <h3>Requisitos</h3>
                        <div class="job-requirements">
                            ${escapeHtml(job.requirements)}
                        </div>
                    </div>
                ` : ''}
            </div>

            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="document.getElementById('jobDetailsModal')?.remove()">
                    Cerrar
                </button>
                <button class="btn btn-primary" onclick="applyForJob('${job.id || job.job_id}')">
                    <i class="fas fa-paper-plane"></i> Solicitar Empleo
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

/**
 * Aplicar a un empleo
 */
async function applyForJob(jobId) {
    try {
        // Verificar autenticación
        if (!authManager.isAuthenticated()) {
            window.location.href = '/login?redirect=/oportunidades';
            return;
        }

        const userId = authManager.getUserId();
        if (!userId) {
            notificationManager.error('No se pudo identificar tu usuario');
            return;
        }

        notificationManager.loading('Procesando solicitud...');

        // Crear aplicación
        const response = await apiClient.post('/applications', {
            student_id: userId,
            job_position_id: jobId
        });

        notificationManager.hideLoading();
        notificationManager.success('¡Solicitud enviada exitosamente!');

        // Cerrar modal si está abierto
        const modal = document.getElementById('jobDetailsModal');
        if (modal) modal.remove();

        // Cambiar estado del botón
        const applyBtn = document.querySelector(`button[onclick="applyForJob('${jobId}')"]`);
        if (applyBtn) {
            applyBtn.disabled = true;
            applyBtn.textContent = '✓ Solicitado';
            applyBtn.classList.add('applied');
        }

    } catch (error) {
        notificationManager.hideLoading();

        if (error.status === 409) {
            notificationManager.warning('Ya has solicitado este empleo');
        } else if (error.status === 401) {
            window.location.href = '/login?redirect=/oportunidades';
        } else {
            notificationManager.error(error.message || 'Error al enviar solicitud');
        }

        console.error(error);
    }
}

/**
 * Alternar filtros avanzados
 */
function toggleAdvancedFilters() {
    const filtersSection = document.querySelector('.advanced-filters');
    if (filtersSection) {
        filtersSection.classList.toggle('visible');
    }
}

/**
 * Limpiar todos los filtros - Refactorizado para modelo JobPosition
 */
function clearAllFilters() {
    // Limpiar inputs de texto
    document.getElementById('searchJobs').value = '';
    document.getElementById('locationFilter').value = '';
    
    // Limpiar selects
    document.getElementById('jobTypeFilter').value = '';
    document.getElementById('sortFilter').value = 'recent';

    // Desmarcar todos los checkboxes
    document.querySelectorAll(
        '.modality-filter, .level-filter, .skill-filter'
    ).forEach(checkbox => {
        checkbox.checked = false;
    });

    // Resetear datos
    currentJobs = allJobsData;
    currentPage = 1;

    renderJobs();
    notificationManager.info('Filtros limpios');
}

/**
 * Cambiar modo de vista
 */
function setViewMode(mode) {
    const container = document.getElementById('jobsContainer');
    if (container) {
        container.className = 'jobs-container';
        container.classList.add(`view-${mode}`);
    }
}

/**
 * Actualizar paginación
 */
function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pageInfo = document.getElementById('pageInfo');

    if (pageInfo) {
        if (totalPages === 0) {
            pageInfo.textContent = 'Sin resultados';
        } else {
            pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
        }
    }

    // Botones de navegación
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages || totalPages === 0;
}

/**
 * Página anterior
 */
function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderJobs();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Página siguiente
 */
function nextPage() {
    const totalPages = Math.ceil(currentJobs.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderJobs();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Debounce para búsqueda
 */
function debounce(func, delay) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

/**
 * Utilidades
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function capitalizeFirst(text) {
    if (!text) return '';
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

function formatNumber(num) {
    if (!num) return '0';
    return parseInt(num).toLocaleString('es-MX');
}
