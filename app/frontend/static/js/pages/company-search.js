/**
 * MoirAI - Company Search Students Page JavaScript
 * Búsqueda y filtrado de candidatos para empresas
 */

// Estado global
let allStudents = [];
let filteredStudents = [];
let currentPage = 1;
const itemsPerPage = 12;
let totalStudents = 0;
let isSearchInProgress = false;

// Rate limiter
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

// Inicializar página
document.addEventListener('DOMContentLoaded', () => {
    initCompanySearchPage();
});

/**
 * Inicializar página con verificación de protectedPageManager
 */
async function initCompanySearchPage() {
    // Verificar que protectedPageManager está definido
    if (typeof protectedPageManager === 'undefined') {
        console.warn('⚠️ ProtectedPageManager no está definido aún, reintentando...');
        setTimeout(initCompanySearchPage, 500);
        return;
    }

    // Proteger ruta - solo empresas y admins
    await protectedPageManager.initProtectedPage({
        requiredRoles: ['company', 'admin'],
        redirectOnUnauth: '/login?redirect=/buscar-candidatos',
        redirectOnUnauthorized: '/dashboard',
        loadingMessage: 'Cargando candidatos...',
        onInit: async () => {
            setupEventListeners();
            await loadInitialStudents();
        }
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Búsqueda
    const searchInput = document.getElementById('searchStudents');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 500));
    }

    // Filtros
    const filterElements = document.querySelectorAll(
        '.skill-filter, .availability-filter, .experience-filter, ' +
        '#universityFilter, #majorFilter, #sortFilter'
    );

    filterElements.forEach(element => {
        element.addEventListener('change', handleFilterChange);
    });

    // Botones de acción
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }

    // View mode
    const viewModeButtons = document.querySelectorAll('.view-mode-btn');
    viewModeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            viewModeButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            setViewMode(e.target.dataset.mode);
        });
    });
}

/**
 * Cargar estudiantes inicialmente
 * ⚠️ ACTUALIZADO: Usar /students/search/skills en lugar de /matching/featured-students
 * ya que el router matching.py no está registrado en el backend MVP
 */
async function loadInitialStudents() {
    notificationManager.loading('Cargando candidatos disponibles...');

    try {
        // ✅ ALTERNATIVA: Usar endpoint de búsqueda por skills (disponible)
        const response = await apiClient.get('/students/search/skills?limit=50');
        allStudents = response.students || response.data || [];
        filteredStudents = allStudents;
        totalStudents = allStudents.length;

        notificationManager.hideLoading();
        renderStudents();

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.warning('No se pudo cargar candidatos destacados');
        console.error(error);
    }
}

/**
 * Realizar búsqueda
 */
async function handleSearch() {
    if (!searchLimiter.isAllowed()) {
        notificationManager.warning('Por favor espera antes de hacer otra búsqueda');
        return;
    }

    if (isSearchInProgress) return;
    isSearchInProgress = true;

    try {
        const searchTerm = document.getElementById('searchStudents')?.value || '';

        if (!searchTerm.trim()) {
            filteredStudents = allStudents;
            renderStudents();
            isSearchInProgress = false;
            return;
        }

        notificationManager.loading('Buscando candidatos...');

        // ✅ CORRECCIÓN: Usar endpoint correcto GET /{company_id}/search-students
        // Obtener company_id del usuario actual (si es empresa)
        const currentUser = authManager.getCurrentUser();
        if (!currentUser || !currentUser.user_id) {
            throw new Error('Usuario no autenticado');
        }

        // El endpoint espera query parameters, no POST body
        const queryParams = new URLSearchParams({
            skills: searchTerm,  // Buscar por skill
            limit: 50
        }).toString();

        const response = await apiClient.get(`/companies/${currentUser.user_id}/search-students?${queryParams}`);

        allStudents = response.students || response.data || [];
        filteredStudents = allStudents;
        totalStudents = allStudents.length;
        currentPage = 1;

        notificationManager.hideLoading();

        if (allStudents.length === 0) {
            notificationManager.info(`No se encontraron candidatos para "${searchTerm}"`);
        } else {
            notificationManager.success(`Se encontraron ${allStudents.length} candidatos`);
        }

        renderStudents();

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error(error.message || 'Error al buscar candidatos');
        console.error(error);
    } finally {
        isSearchInProgress = false;
    }
}

/**
 * Manejar cambio de filtro
 */
async function handleFilterChange() {
    currentPage = 1;
    await applyFilters();
}

/**
 * Aplicar filtros
 */
async function applyFilters() {
    try {
        const skills = Array.from(
            document.querySelectorAll('.skill-filter:checked')
        ).map(el => el.value);

        const availabilities = Array.from(
            document.querySelectorAll('.availability-filter:checked')
        ).map(el => el.value);

        const experience = document.getElementById('experienceFilter')?.value || '';
        const university = document.getElementById('universityFilter')?.value || '';
        const sortBy = document.getElementById('sortFilter')?.value || 'match';

        let filtered = [...allStudents];

        // Filtro por habilidades
        if (skills.length > 0) {
            filtered = filtered.filter(student => {
                const studentSkills = (student.skills || []).map(s => s.toLowerCase());
                return skills.some(skill =>
                    studentSkills.some(ss => ss.includes(skill.toLowerCase()))
                );
            });
        }

        // Filtro por disponibilidad
        if (availabilities.length > 0) {
            filtered = filtered.filter(student =>
                availabilities.includes(student.availability?.toLowerCase())
            );
        }

        // Filtro por experiencia
        if (experience) {
            filtered = filtered.filter(student => {
                const projects = (student.projects_count || 0);
                if (experience === 'sin-experiencia') return projects === 0;
                if (experience === '1-proyecto') return projects === 1;
                if (experience === '2-proyectos') return projects >= 2;
                return true;
            });
        }

        // Filtro por universidad
        if (university) {
            filtered = filtered.filter(student =>
                student.university?.toLowerCase().includes(university.toLowerCase())
            );
        }

        // Ordenar
        switch (sortBy) {
            case 'match':
                filtered.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
                break;
            case 'experience':
                filtered.sort((a, b) => (b.projects_count || 0) - (a.projects_count || 0));
                break;
            case 'recent':
            default:
                filtered.sort((a, b) =>
                    new Date(b.profile_updated || 0) - new Date(a.profile_updated || 0)
                );
        }

        filteredStudents = filtered;
        currentPage = 1;
        renderStudents();

    } catch (error) {
        notificationManager.error('Error al aplicar filtros');
        console.error(error);
    }
}

/**
 * Renderizar estudiantes
 */
function renderStudents() {
    const container = document.getElementById('studentsContainer');
    if (!container) return;

    // Actualizar contador
    const countElement = document.getElementById('resultsCount');
    if (countElement) {
        countElement.textContent = filteredStudents.length;
    }

    // Paginación
    const start = (currentPage - 1) * itemsPerPage;
    const paginatedStudents = filteredStudents.slice(start, start + itemsPerPage);

    if (paginatedStudents.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem;">
                <i class="fas fa-user-graduate" style="font-size: 3rem; color: var(--text-tertiary);"></i>
                <p style="color: var(--text-secondary); margin-top: 1rem;">
                    No hay candidatos que coincidan con tus criterios
                </p>
            </div>
        `;
        updatePagination(filteredStudents.length);
        return;
    }

    container.innerHTML = paginatedStudents.map(student => {
        const matchScore = student.match_score || student.match || 0;
        const matchClass = matchScore >= 75 ? 'high' : matchScore >= 50 ? 'medium' : 'low';

        return `
            <div class="student-card" data-student-id="${student.id}">
                <div class="student-header">
                    <div class="student-avatar">
                        <img src="${student.avatar_url || '/static/images/avatar-default.png'}"
                             alt="${escapeHtml(student.full_name || 'Estudiante')}"
                             onerror="this.src='/static/images/avatar-default.png'">
                    </div>
                    <div class="student-info">
                        <h3 class="student-name">${escapeHtml(student.full_name || 'Estudiante')}</h3>
                        <p class="student-major">
                            ${escapeHtml(student.major || 'Carrera no especificada')}
                        </p>
                        <p class="student-university">
                            <i class="fas fa-university"></i>
                            ${escapeHtml(student.university || 'UNRC')}
                        </p>
                    </div>
                    <span class="match-score match-${matchClass}">
                        ${Math.round(matchScore)}% Match
                    </span>
                </div>

                <div class="student-meta">
                    <div class="meta-item">
                        <i class="fas fa-briefcase"></i>
                        <span>${student.projects_count || 0} Proyectos</span>
                    </div>
                    ${student.availability ? `
                        <div class="meta-item">
                            <i class="fas fa-calendar"></i>
                            <span>${capitalizeFirst(student.availability)}</span>
                        </div>
                    ` : ''}
                    ${student.expected_graduation ? `
                        <div class="meta-item">
                            <i class="fas fa-graduation-cap"></i>
                            <span>Egresa: ${student.expected_graduation}</span>
                        </div>
                    ` : ''}
                </div>

                ${student.skills && student.skills.length > 0 ? `
                    <div class="student-skills">
                        ${student.skills.slice(0, 4).map(skill => `
                            <span class="skill-tag">${escapeHtml(skill)}</span>
                        `).join('')}
                        ${student.skills.length > 4 ? `
                            <span class="skill-tag">+${student.skills.length - 4}</span>
                        ` : ''}
                    </div>
                ` : ''}

                ${student.bio ? `
                    <p class="student-bio">
                        ${escapeHtml(student.bio.substring(0, 100))}...
                    </p>
                ` : ''}

                <div class="student-actions">
                    <button class="btn btn-secondary" onclick="viewStudentProfile(${student.id})">
                        <i class="fas fa-eye"></i> Ver Perfil
                    </button>
                    <button class="btn btn-primary" onclick="sendProposal(${student.id})">
                        <i class="fas fa-envelope"></i> Enviar Propuesta
                    </button>
                </div>
            </div>
        `;
    }).join('');

    updatePagination(filteredStudents.length);
}

/**
 * Ver perfil del estudiante
 */
async function viewStudentProfile(studentId) {
    try {
        notificationManager.loading('Cargando perfil...');

        const response = await apiClient.get(`/students/${studentId}`);
        const student = response.student || response.data;

        notificationManager.hideLoading();
        openStudentProfileModal(student);

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al cargar el perfil');
        console.error(error);
    }
}

/**
 * Abrir modal con perfil del estudiante
 */
function openStudentProfileModal(student) {
    const modal = document.createElement('div');
    modal.className = 'modal modal-student-profile';
    modal.id = `studentModal-${student.id}`;

    const matchScore = student.match_score || 0;
    const matchClass = matchScore >= 75 ? 'high' : matchScore >= 50 ? 'medium' : 'low';

    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-modal" onclick="document.getElementById('studentModal-${student.id}')?.remove()">&times;</span>

            <div class="modal-header-student">
                <div class="header-content">
                    <img src="${student.avatar_url || '/static/images/avatar-default.png'}"
                         alt="${escapeHtml(student.full_name)}" class="profile-avatar"
                         onerror="this.src='/static/images/avatar-default.png'">
                    <div>
                        <h1>${escapeHtml(student.full_name)}</h1>
                        <p>${escapeHtml(student.major || 'Carrera no especificada')}</p>
                        <p><i class="fas fa-university"></i> ${escapeHtml(student.university || 'UNRC')}</p>
                    </div>
                </div>
                <span class="match-score match-${matchClass}">
                    ${Math.round(matchScore)}% Match
                </span>
            </div>

            <div class="modal-body-student">
                <div class="profile-section">
                    <h3>Información General</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Email:</strong>
                            <span>${escapeHtml(student.email || 'N/A')}</span>
                        </div>
                        <div class="info-item">
                            <strong>Disponibilidad:</strong>
                            <span>${capitalizeFirst(student.availability || 'No especificada')}</span>
                        </div>
                        <div class="info-item">
                            <strong>Proyectos Completados:</strong>
                            <span>${student.projects_count || 0}</span>
                        </div>
                        <div class="info-item">
                            <strong>Egreso Esperado:</strong>
                            <span>${student.expected_graduation || 'N/A'}</span>
                        </div>
                    </div>
                </div>

                ${student.bio ? `
                    <div class="profile-section">
                        <h3>Acerca de</h3>
                        <p>${escapeHtml(student.bio)}</p>
                    </div>
                ` : ''}

                ${student.skills && student.skills.length > 0 ? `
                    <div class="profile-section">
                        <h3>Habilidades</h3>
                        <div class="skills-grid">
                            ${student.skills.map(skill => `
                                <span class="skill-tag">${escapeHtml(skill)}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${student.projects && student.projects.length > 0 ? `
                    <div class="profile-section">
                        <h3>Proyectos Destacados</h3>
                        <div class="projects-list">
                            ${student.projects.slice(0, 3).map(project => `
                                <div class="project-item">
                                    <h4>${escapeHtml(project.name || 'Proyecto sin nombre')}</h4>
                                    <p>${escapeHtml(project.description?.substring(0, 100) || '')}</p>
                                    ${project.technologies ? `
                                        <div class="tech-tags">
                                            ${project.technologies.map(tech => `
                                                <span>${escapeHtml(tech)}</span>
                                            `).join('')}
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>

            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="document.getElementById('studentModal-${student.id}')?.remove()">
                    Cerrar
                </button>
                <button class="btn btn-primary" onclick="sendProposal(${student.id})">
                    <i class="fas fa-envelope"></i> Enviar Propuesta
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

/**
 * Enviar propuesta al estudiante
 * ⚠️ DESHABILITADO: El endpoint /companies/send-proposal no existe en el backend (MVP)
 * En producción, considerar agregar este endpoint para comunicación entre empresas y estudiantes
 */
async function sendProposal(studentId) {
    try {
        notificationManager.error('Esta funcionalidad no está disponible en esta versión');
        console.warn('sendProposal() deshabilitado - endpoint /companies/send-proposal no implementado en MVP');
        return;
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error(error.message || 'Error al enviar propuesta');
        console.error(error);
    }
}

/**
 * Limpiar filtros
 */
function clearAllFilters() {
    document.getElementById('searchStudents').value = '';
    document.getElementById('majorFilter').value = '';
    document.getElementById('universityFilter').value = '';
    document.getElementById('sortFilter').value = 'match';

    document.querySelectorAll(
        '.skill-filter, .availability-filter, .experience-filter'
    ).forEach(checkbox => {
        checkbox.checked = false;
    });

    filteredStudents = allStudents;
    currentPage = 1;

    renderStudents();
    notificationManager.info('Filtros limpios');
}

/**
 * Cambiar modo de vista
 */
function setViewMode(mode) {
    const container = document.getElementById('studentsContainer');
    if (container) {
        container.className = 'students-container';
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
        pageInfo.textContent = totalPages === 0 ? 'Sin resultados' : `Página ${currentPage} de ${totalPages}`;
    }

    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages || totalPages === 0;
}

/**
 * Navegación
 */
function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderStudents();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function nextPage() {
    const totalPages = Math.ceil(filteredStudents.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderStudents();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Utilidades
 */
function debounce(func, delay) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

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
