/**
 * MoirAI - Mis Vacantes (My Jobs) Page JavaScript
 * Gestión de vacantes publicadas por empresas
 */

let jobs = [];
let filteredJobs = [];

document.addEventListener('DOMContentLoaded', () => {
    initMisVacantesPage();
});

/**
 * Inicializar página de mis vacantes
 */
async function initMisVacantesPage() {
    // Proteger ruta - solo empresas pueden publicar vacantes
    await protectedPageManager.initProtectedPage({
        requiredRoles: ['company'],
        redirectOnUnauth: '/login?redirect=/mis-vacantes',
        redirectOnUnauthorized: '/dashboard',
        loadingMessage: 'Cargando mis vacantes...',
        onInit: async () => {
            await loadJobs();
        }
    });
}

/**
 * Cargar vacantes de la empresa
 */
async function loadJobs() {
    try {
        const apiKey = getApiKey();
        if (!apiKey) {
            notificationManager.error('No autenticado');
            return;
        }

        const response = await fetch(`${API_BASE}/company/jobs`, {
            headers: { 'X-API-Key': apiKey }
        });

        if (!response.ok) throw new Error('Error al cargar vacantes');

        const data = await response.json();
        jobs = data.jobs || data.data || [];

        renderJobs(jobs);
        applyFilters();
    } catch (error) {
        console.error('Error:', error);
        showError('Error al cargar vacantes');
    }
}

/**
 * Renderizar vacantes
 */
function renderJobs(jobsToRender) {
    const container = document.getElementById('jobsList');
    if (!container) return;

    if (jobsToRender.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-briefcase"></i>
                <h3>Sin vacantes publicadas</h3>
                <p>Publica tu primera vacante para comenzar</p>
                <a href="/profile" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Publicar Vacante
                </a>
            </div>
        `;
        return;
    }

    container.innerHTML = jobsToRender.map(job => `
        <div class="job-item">
            <div class="job-header">
                <h3>${job.title}</h3>
                <span class="status-badge status-${job.status || 'active'}">
                    ${job.status || 'Activa'}
                </span>
            </div>
            <p class="job-company">${job.company}</p>
            <p class="job-location">
                <i class="fas fa-map-marker-alt"></i> ${job.location || 'No especificada'}
            </p>
            <div class="job-meta">
                <span><i class="fas fa-eye"></i> ${job.views || 0} vistas</span>
                <span><i class="fas fa-file-alt"></i> ${job.applications || 0} aplicaciones</span>
                <span><i class="fas fa-calendar"></i> ${formatDate(job.created_at)}</span>
            </div>
            <div class="job-actions">
                <button class="btn btn-small" onclick="viewJob(${job.id})">
                    <i class="fas fa-eye"></i> Ver
                </button>
                <button class="btn btn-small btn-secondary" onclick="editJob(${job.id})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn btn-small btn-danger" onclick="deleteJob(${job.id})">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Ver detalles de vacante
 */
async function viewJob(jobId) {
    window.location.href = `/job/${jobId}`;
}

/**
 * Editar vacante
 */
async function editJob(jobId) {
    window.location.href = `/job/${jobId}/edit`;
}

/**
 * Eliminar vacante
 */
async function deleteJob(jobId) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta vacante?')) {
        return;
    }

    try {
        const apiKey = getApiKey();
        const response = await fetch(`${API_BASE}/company/jobs/${jobId}`, {
            method: 'DELETE',
            headers: { 'X-API-Key': apiKey }
        });

        if (response.ok) {
            notificationManager.success('Vacante eliminada');
            await loadJobs();
        } else {
            throw new Error('Error al eliminar');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Error al eliminar vacante');
    }
}

/**
 * Aplicar filtros
 */
function applyFilters() {
    const statusFilter = Array.from(
        document.querySelectorAll('.filter-group input[type="checkbox"]:checked')
    ).map(cb => cb.value);

    filteredJobs = statusFilter.length === 0
        ? jobs
        : jobs.filter(job => statusFilter.includes(job.status));

    renderJobs(filteredJobs);
}

/**
 * Resetear filtros
 */
function resetFilters() {
    document.querySelectorAll('.filter-group input[type="checkbox"]').forEach(cb => cb.checked = false);
    applyFilters();
}

/**
 * Obtener API key del storage
 */
function getApiKey() {
    if (typeof storageManager !== 'undefined') {
        return storageManager.getApiKey();
    }
    return localStorage.getItem('api_key');
}

/**
 * Formatear fecha
 */
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('es-ES');
}

/**
 * Mostrar error
 */
function showError(message) {
    notificationManager.error(message);
}

// Setup event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Filtros
    document.querySelectorAll('.filter-group input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });

    // Botón resetear
    const resetBtn = document.querySelector('button[onclick="resetFilters()"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetFilters);
    }
});
