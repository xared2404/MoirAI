/**
 * MoirAI - Applications Page JavaScript
 * Gestión de solicitudes de empleo del usuario
 */

let applications = [];
let filteredApplications = [];
let currentPage = 1;
const itemsPerPage = 10;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initApplicationsPage();
});

/**
 * Inicializar página de aplicaciones
 */
async function initApplicationsPage() {
    // Proteger ruta
    await protectedPageManager.initProtectedPage({
        requiredRoles: ['student'],
        redirectOnUnauth: '/login?redirect=/applications',
        redirectOnUnauthorized: '/dashboard',
        loadingMessage: 'Cargando aplicaciones...',
        onInit: async () => {
            await loadApplications();
            setupEventListeners();
        }
    });
}

/**
 * Cargar aplicaciones del usuario
 */
async function loadApplications() {
    try {
        // ✅ CORRECCIÓN: Usar endpoint correcto /students/my-applications en lugar de /applications
        const response = await apiClient.get('/students/my-applications');
        applications = response.applications || response.data || [];

        // Organizar por estado
        applications.forEach(app => {
            // Normalizar fecha
            if (app.created_at) {
                app.created_date = new Date(app.created_at).toLocaleDateString('es-MX');
            }
            if (app.updated_at) {
                app.updated_date = new Date(app.updated_at).toLocaleDateString('es-MX');
            }
        });

        filteredApplications = applications;
        renderApplications();

        // Actualizar estadísticas
        updateStats();

    } catch (error) {
        console.error('Error loading applications:', error);
        throw error;
    }
}

/**
 * Setup de event listeners
 */
function setupEventListeners() {
    // Filtros por estado
    const filterButtons = document.querySelectorAll('.app-filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.dataset.filter;
            filterApplicationsByStatus();
        });
    });

    // Búsqueda
    const searchInput = document.getElementById('searchApplications');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterApplicationsBySearch, 300));
    }

    // Ordenamiento
    const sortSelect = document.getElementById('sortApplications');
    if (sortSelect) {
        sortSelect.addEventListener('change', sortApplications);
    }
}

/**
 * Filtrar aplicaciones por estado
 */
function filterApplicationsByStatus() {
    currentPage = 1;

    if (currentFilter === 'all') {
        filteredApplications = applications;
    } else {
        filteredApplications = applications.filter(app =>
            (app.status || 'pending').toLowerCase() === currentFilter.toLowerCase()
        );
    }

    renderApplications();
}

/**
 * Filtrar por búsqueda
 */
function filterApplicationsBySearch() {
    const searchTerm = document.getElementById('searchApplications')?.value.toLowerCase() || '';
    currentPage = 1;

    if (!searchTerm) {
        filterApplicationsByStatus();
        return;
    }

    const basedApps = currentFilter === 'all' ? applications : applications.filter(app =>
        (app.status || 'pending').toLowerCase() === currentFilter.toLowerCase()
    );

    filteredApplications = basedApps.filter(app =>
        (app.job_title || '').toLowerCase().includes(searchTerm) ||
        (app.company || '').toLowerCase().includes(searchTerm)
    );

    renderApplications();
}

/**
 * Ordenar aplicaciones
 */
function sortApplications() {
    const sortBy = document.getElementById('sortApplications')?.value || 'recent';

    switch (sortBy) {
        case 'recent':
            filteredApplications.sort((a, b) =>
                new Date(b.created_at || 0) - new Date(a.created_at || 0)
            );
            break;
        case 'oldest':
            filteredApplications.sort((a, b) =>
                new Date(a.created_at || 0) - new Date(b.created_at || 0)
            );
            break;
        case 'updated':
            filteredApplications.sort((a, b) =>
                new Date(b.updated_at || 0) - new Date(a.updated_at || 0)
            );
            break;
    }

    currentPage = 1;
    renderApplications();
}

/**
 * Renderizar lista de aplicaciones
 */
function renderApplications() {
    const container = document.getElementById('applicationsContainer');
    if (!container) return;

    // Actualizar contador
    const countElement = document.getElementById('applicationsCount');
    if (countElement) {
        countElement.textContent = filteredApplications.length;
    }

    // Paginación
    const start = (currentPage - 1) * itemsPerPage;
    const paginatedApps = filteredApplications.slice(start, start + itemsPerPage);

    if (paginatedApps.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>Sin aplicaciones</h3>
                <p>Aún no has enviado solicitudes. ${currentFilter !== 'all' ? 'Cambia los filtros para ver más.' : '<a href="/oportunidades">Busca empleos aquí</a>'}</p>
            </div>
        `;
        updatePagination(0);
        return;
    }

    container.innerHTML = paginatedApps.map((app, idx) => {
        const statusConfig = getStatusConfig(app.status || 'pending');
        const isExpired = app.expires_at && new Date(app.expires_at) < new Date();

        return `
            <div class="application-card" data-app-id="${app.id}">
                <div class="app-header">
                    <div class="app-title-section">
                        <h3>${escapeHtml(app.job_title || 'Empleo sin título')}</h3>
                        <p class="app-company">${escapeHtml(app.company || 'Empresa no disponible')}</p>
                    </div>
                    <span class="app-status status-${statusConfig.class}">
                        <i class="${statusConfig.icon}"></i> ${statusConfig.label}
                    </span>
                </div>

                <div class="app-meta">
                    <div class="meta-item">
                        <strong>Solicitado:</strong>
                        <span>${app.created_date || 'N/A'}</span>
                    </div>
                    <div class="meta-item">
                        <strong>Actualizado:</strong>
                        <span>${app.updated_date || app.created_date || 'N/A'}</span>
                    </div>
                    ${app.location ? `
                        <div class="meta-item">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${escapeHtml(app.location)}</span>
                        </div>
                    ` : ''}
                </div>

                ${isExpired ? `
                    <div class="app-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Esta oferta ha expirado</span>
                    </div>
                ` : ''}

                ${app.notes ? `
                    <div class="app-notes">
                        <strong>Notas:</strong>
                        <p>${escapeHtml(app.notes)}</p>
                    </div>
                ` : ''}

                ${app.feedback ? `
                    <div class="app-feedback">
                        <strong>Retroalimentación:</strong>
                        <p>${escapeHtml(app.feedback)}</p>
                    </div>
                ` : ''}

                <div class="app-actions">
                    <button class="btn btn-secondary" onclick="viewApplicationDetail(${app.id})">
                        <i class="fas fa-eye"></i> Ver Detalles
                    </button>
                    ${['pending', 'pending_review'].includes((app.status || 'pending').toLowerCase()) ? `
                        <button class="btn btn-danger" onclick="withdrawApplication(${app.id})">
                            <i class="fas fa-times"></i> Retirar
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');

    updatePagination(filteredApplications.length);
}

/**
 * Ver detalles de una aplicación
 */
async function viewApplicationDetail(appId) {
    try {
        const app = applications.find(a => a.id === appId);
        if (!app) {
            notificationManager.error('Aplicación no encontrada');
            return;
        }

        // Obtener detalles completos del empleo si es necesario
        const statusConfig = getStatusConfig(app.status || 'pending');

        const modal = document.createElement('div');
        modal.className = 'modal modal-app-details';
        modal.id = `appDetailsModal-${appId}`;

        modal.innerHTML = `
            <div class="modal-content">
                <span class="close-modal" onclick="document.getElementById('appDetailsModal-${appId}')?.remove()">&times;</span>

                <div class="modal-header-app">
                    <div>
                        <h1>${escapeHtml(app.job_title || 'Empleo sin título')}</h1>
                        <p class="app-company-modal">${escapeHtml(app.company || 'Empresa')}</p>
                    </div>
                    <span class="app-status status-${statusConfig.class} status-large">
                        ${statusConfig.label}
                    </span>
                </div>

                <div class="modal-body-app">
                    <div class="app-info-grid">
                        <div class="info-section">
                            <h3>Información de la Solicitud</h3>
                            <div class="info-item">
                                <strong>Estado:</strong>
                                <span>${statusConfig.label}</span>
                            </div>
                            <div class="info-item">
                                <strong>Fecha de Solicitud:</strong>
                                <span>${app.created_date || 'N/A'}</span>
                            </div>
                            <div class="info-item">
                                <strong>Última Actualización:</strong>
                                <span>${app.updated_date || app.created_date || 'N/A'}</span>
                            </div>
                            ${app.expires_at ? `
                                <div class="info-item">
                                    <strong>Válida Hasta:</strong>
                                    <span>${new Date(app.expires_at).toLocaleDateString('es-MX')}</span>
                                </div>
                            ` : ''}
                        </div>

                        <div class="info-section">
                            <h3>Información del Empleo</h3>
                            ${app.location ? `
                                <div class="info-item">
                                    <strong>Ubicación:</strong>
                                    <span>${escapeHtml(app.location)}</span>
                                </div>
                            ` : ''}
                            ${app.work_mode ? `
                                <div class="info-item">
                                    <strong>Modalidad:</strong>
                                    <span>${capitalizeFirst(app.work_mode)}</span>
                                </div>
                            ` : ''}
                            ${app.salary_range ? `
                                <div class="info-item">
                                    <strong>Rango Salarial:</strong>
                                    <span>${escapeHtml(app.salary_range)}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    ${app.notes ? `
                        <div class="app-section">
                            <h3>Mis Notas</h3>
                            <p>${escapeHtml(app.notes)}</p>
                            <button class="btn btn-secondary btn-sm" onclick="editApplicationNotes(${appId})">
                                <i class="fas fa-edit"></i> Editar Notas
                            </button>
                        </div>
                    ` : ''}

                    ${app.feedback ? `
                        <div class="app-section feedback">
                            <h3>Retroalimentación de la Empresa</h3>
                            <p>${escapeHtml(app.feedback)}</p>
                        </div>
                    ` : ''}

                    ${app.job_description ? `
                        <div class="app-section">
                            <h3>Descripción del Puesto</h3>
                            <div class="job-desc-text">
                                ${escapeHtml(app.job_description)}
                            </div>
                        </div>
                    ` : ''}
                </div>

                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="document.getElementById('appDetailsModal-${appId}')?.remove()">
                        Cerrar
                    </button>
                    ${['pending', 'pending_review'].includes((app.status || 'pending').toLowerCase()) ? `
                        <button class="btn btn-danger" onclick="withdrawApplication(${appId})">
                            <i class="fas fa-times"></i> Retirar Solicitud
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

    } catch (error) {
        notificationManager.error('Error al cargar detalles');
        console.error(error);
    }
}

/**
 * Editar notas de la aplicación
 */
async function editApplicationNotes(appId) {
    const app = applications.find(a => a.id === appId);
    if (!app) return;

    const newNotes = prompt('Editar notas:', app.notes || '');
    if (newNotes === null) return; // Cancelado

    try {
        notificationManager.loading('Guardando notas...');

        await apiClient.put(`/applications/${appId}`, {
            notes: newNotes
        });

        app.notes = newNotes;
        notificationManager.hideLoading();
        notificationManager.success('Notas actualizadas');

        // Cerrar modal y actualizar
        const modal = document.getElementById(`appDetailsModal-${appId}`);
        if (modal) modal.remove();
        renderApplications();

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al guardar notas');
        console.error(error);
    }
}

/**
 * Retirar una aplicación
 */
async function withdrawApplication(appId) {
    if (!confirm('¿Está seguro de que desea retirar esta solicitud?')) {
        return;
    }

    try {
        notificationManager.loading('Retirando solicitud...');

        await apiClient.delete(`/applications/${appId}`);

        applications = applications.filter(a => a.id !== appId);
        filteredApplications = filteredApplications.filter(a => a.id !== appId);

        notificationManager.hideLoading();
        notificationManager.success('Solicitud retirada');

        // Cerrar modal si está abierto
        const modal = document.getElementById(`appDetailsModal-${appId}`);
        if (modal) modal.remove();

        renderApplications();
        updateStats();

    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al retirar solicitud');
        console.error(error);
    }
}

/**
 * Actualizar estadísticas
 */
function updateStats() {
    const stats = {
        total: applications.length,
        pending: applications.filter(a => ['pending', 'pending_review'].includes((a.status || 'pending').toLowerCase())).length,
        accepted: applications.filter(a => (a.status || '').toLowerCase() === 'accepted').length,
        rejected: applications.filter(a => (a.status || '').toLowerCase() === 'rejected').length
    };

    document.getElementById('totalApplications').textContent = stats.total;
    document.getElementById('pendingApplications').textContent = stats.pending;
    document.getElementById('acceptedApplications').textContent = stats.accepted;
    document.getElementById('rejectedApplications').textContent = stats.rejected;
}

/**
 * Actualizar paginación
 */
function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pageInfo = document.getElementById('pageInfoApp');

    if (pageInfo) {
        if (totalPages === 0) {
            pageInfo.textContent = 'Sin resultados';
        } else {
            pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
        }
    }

    const prevBtn = document.getElementById('prevPageAppBtn');
    const nextBtn = document.getElementById('nextPageAppBtn');

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages || totalPages === 0;
}

/**
 * Página anterior
 */
function previousPageApp() {
    if (currentPage > 1) {
        currentPage--;
        renderApplications();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Página siguiente
 */
function nextPageApp() {
    const totalPages = Math.ceil(filteredApplications.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderApplications();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Obtener configuración del estado
 */
function getStatusConfig(status) {
    const statusMap = {
        'pending': {
            label: 'Pendiente',
            class: 'pending',
            icon: 'fas fa-clock'
        },
        'pending_review': {
            label: 'En Revisión',
            class: 'review',
            icon: 'fas fa-eye'
        },
        'accepted': {
            label: 'Aceptada',
            class: 'accepted',
            icon: 'fas fa-check'
        },
        'rejected': {
            label: 'Rechazada',
            class: 'rejected',
            icon: 'fas fa-times'
        },
        'withdrawn': {
            label: 'Retirada',
            class: 'withdrawn',
            icon: 'fas fa-ban'
        }
    };

    return statusMap[status?.toLowerCase()] || statusMap['pending'];
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
