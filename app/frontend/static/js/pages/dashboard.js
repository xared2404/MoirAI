/**
 * MoirAI - Dashboard Page JavaScript
 * Página de inicio de usuarios autenticados
 * Se adapta según el rol: Estudiante, Empresa, Admin
 */

let currentUser = null;
let dashboardData = {
    applications: [],
    recommendations: [],
    posted_jobs: [],
    top_candidates: [],
    stats: {},
    kpis: {},
    monitoring: {}
};

// Flag para prevenir envíos duplicados
let isInitializing = false;

// Rate limiter para acciones
class RateLimiter {
    constructor(maxRequests = 5, windowMs = 10000) {
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

const applicationLimiter = new RateLimiter(3, 5000);

document.addEventListener('DOMContentLoaded', () => {
    // Usar protectedPageManager para mejor sincronización
    protectedPageManager.initProtectedPage({
        redirectOnUnauth: '/login?redirect=/dashboard',
        loadingMessage: 'Cargando dashboard...',
        onInit: async () => {
            // Dar tiempo al role adapter de inicializarse
            await new Promise(resolve => setTimeout(resolve, 150));
            
            // Luego inicializar el dashboard
            initDashboard();
        }
    }).catch(error => {
        console.error('Error en initProtectedPage:', error);
    });
});

/**
 * Inicializar dashboard
 */
async function initDashboard() {
    // Prevenir inicializaciones duplicadas
    if (isInitializing) return;
    isInitializing = true;

    console.log('⏳ Dashboard: Iniciando...');
    console.log('✅ API Client autenticado:', apiClient.isAuthenticated());
    console.log('✅ Auth Manager usuario:', !!authManager.currentUser);

    // Proteger ruta - Verificar autenticación
    if (!apiClient.isAuthenticated()) {
        console.error('❌ Dashboard: No autenticado, redirigiendo a login');
        window.location.href = '/login?redirect=/dashboard';
        return;
    }

    // Si authManager no tiene currentUser, intentar cargar
    if (!authManager.currentUser) {
        console.log('⏳ Dashboard: Cargando usuario desde API...');
        try {
            await authManager.getCurrentUser();
        } catch (error) {
            console.warn('⚠️ Dashboard: Error cargando usuario, pero tenemos token. Continuando...');
        }
    }

    // Cargar datos del usuario
    console.log('⏳ Dashboard: Cargando datos...');

    try {
        // Cargar datos del usuario y datos específicos del rol
        // Usar allSettled para que si una falla, las otras continúen
        const results = await Promise.allSettled([
            loadUserData(),
            loadRoleSpecificData()
        ]);

        // Registrar resultados
        results.forEach((result, index) => {
            if (result.status === 'fulfilled') {
                console.log(`✅ Promesa ${index} resuelta correctamente`);
            } else {
                console.warn(`⚠️ Promesa ${index} rechazada:`, result.reason);
            }
        });

        // Setup de manejadores de eventos
        setupEventHandlers();

        console.log('✅ Dashboard inicializado correctamente');

    } catch (error) {
        // Este catch casi nunca se ejecutará con allSettled, pero es por si acaso
        console.error('❌ Error inesperado en initDashboard:', error);
    } finally {
        isInitializing = false;
    }
}

/**
 * Cargar datos específicos según el rol
 */
async function loadRoleSpecificData() {
    let role;
    if (typeof storageManager !== 'undefined') {
        role = storageManager.getUserRole();
    } else {
        role = authManager.getUserRole() || localStorage.getItem('user_role') || 'student';
    }
    
    console.log(`📊 Cargando datos específicos para rol: ${role}`);
    
    // NO usar throw, solo registrar errores individuales
    try {
        switch (role) {
            case 'student':
                console.log('📚 Iniciando carga de datos de estudiante...');
                await Promise.allSettled([
                    loadApplications(),
                    loadRecommendations(),
                    loadStudentStats()
                ]);
                break;
            
            case 'company':
                console.log('🏢 Iniciando carga de datos de empresa...');
                await Promise.allSettled([
                    loadPostedJobs(),
                    loadTopCandidates(),
                    loadCompanyStats()
                ]);
                break;
            
            case 'admin':
                console.log('👨‍💼 Iniciando carga de datos de admin...');
                await Promise.allSettled([
                    loadKPIs(),
                    loadMonitoring(),
                    loadActivityLog(),
                    loadAdminStats()
                ]);
                break;
            
            default:
                console.log('📚 Iniciando carga de datos por defecto (estudiante)...');
                await Promise.allSettled([
                    loadApplications(),
                    loadRecommendations(),
                    loadStudentStats()
                ]);
        }
        
        console.log('✅ Datos del dashboard cargados exitosamente');
        
    } catch (error) {
        console.error('❌ Error no controlado en carga de datos:', error);
        // NO lanzar el error, solo registrarlo
        // El dashboard seguirá funcionando aunque falten datos
    }
}

/**
 * Manejar token expirado
 */
function handleTokenExpired() {
    authManager.logout();
    notificationManager.error('Tu sesión expiró. Por favor, inicia sesión nuevamente.');
    setTimeout(() => {
        window.location.href = '/login?expired=true';
    }, 2000);
}

/**
 * Cargar datos del usuario actual
 */
async function loadUserData() {
    try {
        // Obtener info del usuario desde el endpoint /auth/me
        const userInfo = await apiClient.get('/auth/me');
        
        if (!userInfo) {
            throw new Error('No se pudo obtener datos del usuario');
        }

        // Usar email como nombre si no hay primer nombre (con storageManager si disponible)
        let userName, userEmail;
        if (typeof storageManager !== 'undefined') {
            userName = storageManager.getUserName() || userInfo.email?.split('@')[0] || 'Usuario';
            userEmail = userInfo.email || storageManager.getUserEmail() || 'Sin email';
        } else {
            userName = localStorage.getItem('user_name') || userInfo.email?.split('@')[0] || 'Usuario';
            userEmail = userInfo.email || localStorage.getItem('user_email') || 'Sin email';
        }

        currentUser = {
            id: userInfo.user_id || (typeof storageManager !== 'undefined' ? storageManager.getUserId() : localStorage.getItem('user_id')),
            email: userEmail,
            first_name: userName,
            role: userInfo.role || localStorage.getItem('user_role')
        };

        // Actualizar elementos del usuario
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');
        const userSubtitleEl = document.getElementById('user-subtitle');

        if (userNameEl) userNameEl.textContent = userName;
        if (userEmailEl) userEmailEl.textContent = userEmail;

        // Actualizar según el rol
        const role = authManager.getUserRole() || userInfo.role;
        if (userSubtitleEl) {
            if (role === 'student') {
                userSubtitleEl.textContent = 'Estudiante de UNRC - Busca tu próxima oportunidad';
            } else if (role === 'company') {
                userSubtitleEl.textContent = 'Empresa Colaboradora - Encuentra el talento que necesitas';
            } else if (role === 'admin') {
                userSubtitleEl.textContent = 'Administrador - Panel de control y monitoreo';
            }
        }

        console.log('✅ Datos del usuario cargados:', { id: currentUser.id, email: currentUser.email, role: currentUser.role });
        return currentUser;

    } catch (error) {
        console.warn('⚠️ Error al cargar datos del usuario desde /auth/me:', error);
        
        // Fallback: usar datos de storage (con storageManager si disponible)
        let fallbackName, fallbackEmail, fallbackRole, fallbackId;
        if (typeof storageManager !== 'undefined') {
            fallbackName = storageManager.getUserName() || 'Usuario';
            fallbackEmail = storageManager.getUserEmail() || 'Sin email';
            fallbackRole = storageManager.getUserRole() || 'student';
            fallbackId = storageManager.getUserId();
        } else {
            fallbackName = localStorage.getItem('user_name') || 'Usuario';
            fallbackEmail = localStorage.getItem('user_email') || 'Sin email';
            fallbackRole = localStorage.getItem('user_role') || 'student';
            fallbackId = localStorage.getItem('user_id');
        }
        
        currentUser = {
            id: fallbackId,
            email: fallbackEmail,
            first_name: fallbackName,
            role: fallbackRole
        };

        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');
        const userSubtitleEl = document.getElementById('user-subtitle');

        if (userNameEl) userNameEl.textContent = fallbackName;
        if (userEmailEl) userEmailEl.textContent = fallbackEmail;
        if (userSubtitleEl) {
            if (fallbackRole === 'student') {
                userSubtitleEl.textContent = 'Estudiante de UNRC - Busca tu próxima oportunidad';
            } else if (fallbackRole === 'company') {
                userSubtitleEl.textContent = 'Empresa Colaboradora - Encuentra el talento que necesitas';
            }
        }

        console.log('✅ Datos del usuario obtenidos de localStorage:', { id: currentUser.id, email: currentUser.email, role: currentUser.role });
        return currentUser;
    }
}

/**
 * Cargar recomendaciones del usuario
 */
async function loadRecommendations() {
    try {
        // ✅ CORRECCIÓN: Usar endpoint correcto /students/recommendations
        const response = await apiClient.get('/students/recommendations');

        dashboardData.recommendations = response.recommendations || [];

        // Renderizar recomendaciones
        renderRecommendations();

    } catch (error) {
        console.warn('No se pudieron cargar las recomendaciones:', error);
        dashboardData.recommendations = [];
        renderRecommendations();
    }
}

/**
 * Cargar aplicaciones del usuario
 */
async function loadApplications() {
    try {
        // ✅ CORRECCIÓN: Usar endpoint correcto /students/my-applications
        const response = await apiClient.get('/students/my-applications');

        dashboardData.applications = response.applications || [];

        // Renderizar tabla
        renderApplicationsTable();

    } catch (error) {
        notificationManager.warning('No se pudieron cargar las aplicaciones');
        console.error(error);
    }
}

/**
 * Cargar vacantes publicadas (Empresa)
 * ⚠️ DESHABILITADO: El endpoint /jobs/company/posted no existe en el backend (MVP)
 * En producción, considerar agregar este endpoint
 */
async function loadPostedJobs() {
    try {
        console.warn('loadPostedJobs() deshabilitado - endpoint /jobs/company/posted no implementado en MVP');
        dashboardData.posted_jobs = [];
        renderPostedJobs();
    } catch (error) {
        notificationManager.warning('No se pudieron cargar las vacantes publicadas');
        console.error(error);
    }
}

/**
 * Cargar candidatos destacados (Empresa)
 * ⚠️ DESHABILITADO: El endpoint /matching/company/top-candidates no existe en el backend (MVP)
 * En producción, considerar agregar este endpoint
 */
async function loadTopCandidates() {
    try {
        console.warn('loadTopCandidates() deshabilitado - endpoint /matching/company/top-candidates no implementado en MVP');
        dashboardData.top_candidates = [];
        renderTopCandidates();
    } catch (error) {
        notificationManager.warning('No se pudieron cargar los candidatos destacados');
        console.error(error);
    }
}

/**
 * Cargar KPIs (Admin)
 */
async function loadKPIs() {
    try {
        // ✅ CORRECCIÓN: Usar endpoint correcto /admin/analytics/kpis
        const response = await apiClient.get('/admin/analytics/kpis');
        dashboardData.kpis = response.kpis || {};
        renderKPIs();
    } catch (error) {
        notificationManager.warning('No se pudieron cargar los KPIs');
        console.error(error);
    }
}

/**
 * Cargar monitoreo de servicios (Admin)
 * ⚠️ DESHABILITADO: El endpoint /admin/monitoring no existe en el backend (MVP)
 * En producción, considerar agregar este endpoint
 */
async function loadMonitoring() {
    try {
        console.warn('loadMonitoring() deshabilitado - endpoint /admin/monitoring no implementado en MVP');
        dashboardData.monitoring = {};
        renderMonitoring();
    } catch (error) {
        notificationManager.warning('No se pudieron cargar los datos de monitoreo');
        console.error(error);
    }
}

/**
 * Cargar registro de actividades (Admin)
 */
async function loadActivityLog() {
    try {
        // ✅ CORRECCIÓN: Usar endpoint correcto /admin/audit-log
        const response = await apiClient.get('/admin/audit-log');
        dashboardData.activityLog = response.logs || [];
        renderActivityLog();
    } catch (error) {
        notificationManager.warning('No se pudieron cargar el registro de actividades');
        console.error(error);
    }
}

/**
 * Cargar estadísticas de Estudiante
 */
async function loadStudentStats() {
    try {
        dashboardData.stats = {
            applications_count: dashboardData.applications.length,
            applications_pending: dashboardData.applications.filter(a => a.status === 'pending').length,
            applications_accepted: dashboardData.applications.filter(a => a.status === 'accepted').length,
            recommendations_count: dashboardData.recommendations.length,
        };

        // Intentar obtener score si existe endpoint
        try {
            const scoreResponse = await apiClient.get(`/matching/student/${currentUser.id}/matching-score`);
            dashboardData.stats.avg_match_score = scoreResponse.avg_score || 0;
        } catch (e) {
            dashboardData.stats.avg_match_score = 0;
        }

        renderStats();
    } catch (error) {
        console.error('Error calculando stats de estudiante:', error);
    }
}

/**
 * Cargar estadísticas de Empresa
 */
async function loadCompanyStats() {
    try {
        // Calcular stats locales de empresa
        dashboardData.stats = {
            posted_jobs_count: dashboardData.posted_jobs.length,
            top_candidates_count: dashboardData.top_candidates.length,
            hires_count: 0, // Se cargaría del backend
            profile_views: 0  // Se cargaría del backend
        };

        // Renderizar stats
        renderStats();
    } catch (error) {
        console.error('Error calculando stats de empresa:', error);
    }
}

/**
 * Cargar estadísticas de Admin
 */
async function loadAdminStats() {
    try {
        dashboardData.stats = {
            total_users: dashboardData.kpis.total_users || 0,
            placement_rate: dashboardData.kpis.placement_rate || 0,
            matches_made: dashboardData.kpis.matches_made || 0,
            system_alerts: dashboardData.monitoring.alerts || 0
        };

        renderStats();
    } catch (error) {
        console.error('Error calculando stats de admin:', error);
    }
}

/**
 * Renderizar tabla de aplicaciones
 */
function renderApplicationsTable() {
    const container = document.getElementById('applications-container');

    if (!container) return;

    if (dashboardData.applications.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>Sin aplicaciones</h3>
                <p>Aún no has aplicado a ningún empleo</p>
                <a href="/oportunidades" class="btn btn-primary">Buscar empleos</a>
            </div>
        `;
        return;
    }

    let html = `
        <table class="applications-table">
            <thead>
                <tr>
                    <th>Empleo</th>
                    <th>Empresa</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;

    dashboardData.applications.forEach(app => {
        const statusColor = {
            'pending': 'pending',
            'accepted': 'success',
            'rejected': 'error',
            'interview': 'warning'
        }[app.status] || 'info';

        const statusLabel = {
            'pending': 'Pendiente',
            'accepted': 'Aceptada',
            'rejected': 'Rechazada',
            'interview': 'Entrevista'
        }[app.status] || app.status;

        const date = new Date(app.applied_at).toLocaleDateString('es-ES');

        html += `
            <tr>
                <td><strong>${app.job?.title || 'Empleo'}</strong></td>
                <td>${app.job?.company || 'Empresa'}</td>
                <td>
                    <span class="status-badge status-${statusColor}">
                        ${statusLabel}
                    </span>
                </td>
                <td>${date}</td>
                <td>
                    <button class="btn-small" onclick="viewJobDetail(${app.job?.id})">
                        <i class="fas fa-eye"></i> Ver
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

/**
 * Renderizar recomendaciones
 */
function renderRecommendations() {
    const container = document.getElementById('recommendations-container');

    if (!container) return;

    if (dashboardData.recommendations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-star"></i>
                <h3>Sin recomendaciones</h3>
                <p>Completá tu perfil para recibir recomendaciones personalizadas</p>
                <a href="/profile" class="btn btn-primary">Completar perfil</a>
            </div>
        `;
        return;
    }

    let html = '<div class="jobs-grid">';

    dashboardData.recommendations.forEach(job => {
        const matchScore = Math.round(job.matching_score * 100);

        html += `
            <div class="job-card-simple">
                <div class="job-card-header">
                    <h4>${job.title}</h4>
                    <span class="match-badge">${matchScore}% Match</span>
                </div>
                <p class="job-company">${job.company}</p>
                <p class="job-location">
                    <i class="fas fa-map-marker-alt"></i> ${job.location || 'Ubicación no especificada'}
                </p>
                <p class="job-modality">
                    <i class="fas fa-briefcase"></i> ${job.work_mode || 'Modalidad no especificada'}
                </p>
                <div class="job-card-footer">
                    <button class="btn-small btn-secondary" onclick="viewJobDetail(${job.id})">
                        <i class="fas fa-eye"></i> Ver
                    </button>
                    <button class="btn-small btn-primary" onclick="applyToJob(${job.id})">
                        <i class="fas fa-check"></i> Aplicar
                    </button>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Renderizar cards de estadísticas
 */
function renderStats() {
    const stats = dashboardData.stats;

    const statsElements = {
        'applications-count': stats.applications_count || 0,
        'match-score': stats.avg_match_score ? Math.round(stats.avg_match_score) + '%' : '0%',
        'recommendations-count': stats.recommendations_count || 0,
        'cv-status': (currentUser && currentUser.cv_uploaded) ? 'Sí ✓' : 'No'
    };

    Object.keys(statsElements).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = statsElements[id];
        }
    });
}

/**
 * Ver detalles de un empleo
 */
async function viewJobDetail(jobId) {
    try {
        const job = await apiClient.get(`/jobs/${jobId}`);

        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content job-modal">
                <span class="close-modal" onclick="this.closest('.modal').remove()">&times;</span>
                <h2>${job.title}</h2>
                <p class="job-company"><strong>${job.company}</strong></p>
                <p class="job-meta">
                    <i class="fas fa-map-marker-alt"></i> ${job.location}
                    | <i class="fas fa-briefcase"></i> ${job.work_mode}
                </p>
                <h4>Descripción</h4>
                <p>${job.description}</p>
                <h4>Salario</h4>
                <p>$${job.salary_min} - $${job.salary_max} ${job.currency}</p>
                <h4>Requisitos</h4>
                <ul>
                    ${job.requirements?.map(req => `<li>${req}</li>`).join('') || '<li>No especificado</li>'}
                </ul>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="applyToJob(${jobId}); this.closest('.modal').remove()">
                        <i class="fas fa-paper-plane"></i> Aplicar Ahora
                    </button>
                    <button class="btn btn-secondary" onclick="closeModal(this)">
                        Cerrar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Fix: Prevenir scroll en background cuando modal está abierto
        document.body.style.overflow = 'hidden';
        
        // Botón close
        const closeBtn = modal.querySelector('.close-modal');
        closeBtn.addEventListener('click', () => {
            closeModalWindow(modal);
        });

        // Cerrar al hacer clic fuera
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModalWindow(modal);
            }
        });
        
        // Cerrar con Escape
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModalWindow(modal);
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

    } catch (error) {
        notificationManager.error('Error al cargar detalles del empleo');
        console.error(error);
    }
}

/**
 * Cerrar modal y restaurar scroll
 */
function closeModalWindow(modal) {
    // Fix: Restaurar scroll cuando se cierra modal
    document.body.style.overflow = 'auto';
    modal.remove();
}

/**
 * Aplicar a un empleo
 */
async function applyToJob(jobId) {
    // Fix: Rate limiting para prevenir envíos duplicados
    if (!applicationLimiter.isAllowed()) {
        notificationManager.warning('Espera un momento antes de enviar otra aplicación');
        return;
    }

    try {
        const userId = currentUser.id;

        notificationManager.loading('Enviando aplicación...');

        const response = await apiClient.post('/applications', {
            student_id: userId,
            job_id: jobId
        });

        notificationManager.hideLoading();
        notificationManager.success('¡Aplicación enviada exitosamente!');

        // Recargar aplicaciones con delay
        setTimeout(() => {
            loadApplications();
        }, 500);

    } catch (error) {
        notificationManager.hideLoading();

        if (error.message?.includes('already applied')) {
            notificationManager.warning('Ya has aplicado a este empleo');
        } else if (error.status === 401) {
            handleTokenExpired();
        } else {
            notificationManager.error('Error al enviar aplicación');
        }

        console.error(error);
    }
}

/**
 * Renderizar vacantes publicadas (Empresa)
 */
function renderPostedJobs() {
    const container = document.getElementById('posted-jobs-container');
    if (!container) return;

    if (dashboardData.posted_jobs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-briefcase"></i>
                <h3>Sin vacantes publicadas</h3>
                <p>Aún no has publicado ninguna vacante</p>
                <a href="/profile" class="btn btn-primary">Publicar vacante</a>
            </div>
        `;
        return;
    }

    let html = '<div class="jobs-grid">';
    dashboardData.posted_jobs.forEach(job => {
        html += `
            <div class="job-card">
                <h4>${job.title}</h4>
                <p class="job-meta">
                    <i class="fas fa-map-marker-alt"></i> ${job.location}
                </p>
                <p>${job.description?.substring(0, 100)}...</p>
                <div class="job-stats">
                    <span><i class="fas fa-eye"></i> ${job.views_count || 0} vistas</span>
                    <span><i class="fas fa-file-alt"></i> ${job.applications_count || 0} aplicaciones</span>
                </div>
                <div class="job-actions">
                    <button class="btn-small" onclick="viewJobDetail(${job.id})">Ver</button>
                    <button class="btn-small btn-secondary" onclick="editJob(${job.id})">Editar</button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Renderizar candidatos destacados (Empresa)
 */
function renderTopCandidates() {
    const container = document.getElementById('top-candidates-container');
    if (!container) return;

    if (dashboardData.top_candidates.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>Sin candidatos</h3>
                <p>No hay candidatos destacados para tus vacantes</p>
                <a href="/buscar-candidatos" class="btn btn-primary">Buscar candidatos</a>
            </div>
        `;
        return;
    }

    let html = '<div class="candidates-grid">';
    dashboardData.top_candidates.forEach(candidate => {
        const matchScore = Math.round((candidate.matching_score || 0) * 100);
        html += `
            <div class="candidate-card">
                <div class="candidate-header">
                    <h4>${candidate.name}</h4>
                    <span class="match-badge">${matchScore}% Match</span>
                </div>
                <p class="candidate-program">${candidate.program}</p>
                <p class="candidate-skills">
                    <i class="fas fa-star"></i> ${(candidate.skills || []).slice(0, 3).join(', ')}
                </p>
                <div class="candidate-actions">
                    <button class="btn-small" onclick="viewCandidateProfile(${candidate.id})">Ver Perfil</button>
                    <button class="btn-small btn-primary" onclick="contactCandidate(${candidate.id})">Contactar</button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Renderizar KPIs (Admin)
 */
function renderKPIs() {
    const container = document.getElementById('kpis-container');
    if (!container) return;

    const kpis = dashboardData.kpis;
    let html = '';

    const kpiData = [
        {
            icon: 'fa-users',
            label: 'Usuarios Totales',
            value: kpis.total_users || 0,
            id: 'total-users'
        },
        {
            icon: 'fa-percentage',
            label: 'Tasa de Colocación',
            value: `${Math.round((kpis.placement_rate || 0) * 100)}%`,
            id: 'placement-rate'
        },
        {
            icon: 'fa-handshake',
            label: 'Coincidencias Realizadas',
            value: kpis.matches_made || 0,
            id: 'matches-made'
        },
        {
            icon: 'fa-chart-line',
            label: 'Tasa de Éxito',
            value: `${Math.round((kpis.success_rate || 0) * 100)}%`,
            id: 'success-rate'
        }
    ];

    kpiData.forEach(kpi => {
        html += `
            <div class="kpi-card">
                <div class="kpi-icon">
                    <i class="fas ${kpi.icon}"></i>
                </div>
                <div class="kpi-content">
                    <h3>${kpi.label}</h3>
                    <p class="kpi-value" id="${kpi.id}">${kpi.value}</p>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

/**
 * Renderizar monitoreo de servicios (Admin)
 */
function renderMonitoring() {
    const container = document.getElementById('monitoring-container');
    if (!container) return;

    const monitoring = dashboardData.monitoring;
    let html = `
        <div class="monitoring-grid">
            <div class="monitoring-item">
                <h4>Estado del Sistema</h4>
                <p class="status ${monitoring.system_status === 'online' ? 'status-online' : 'status-offline'}">
                    <i class="fas fa-circle"></i> ${monitoring.system_status || 'Unknown'}
                </p>
            </div>
            <div class="monitoring-item">
                <h4>Uptime</h4>
                <p class="metric">${monitoring.uptime || '99.9'}%</p>
            </div>
            <div class="monitoring-item">
                <h4>Latencia Promedio</h4>
                <p class="metric">${monitoring.avg_latency || 0}ms</p>
            </div>
            <div class="monitoring-item">
                <h4>Alertas Activas</h4>
                <p class="alert-count">${monitoring.alerts || 0}</p>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Renderizar registro de actividades (Admin)
 */
function renderActivityLog() {
    const container = document.getElementById('activity-log-container');
    if (!container) return;

    if (!dashboardData.activityLog || dashboardData.activityLog.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <p>Sin actividades registradas</p>
            </div>
        `;
        return;
    }

    let html = `<table class="activity-table">
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Usuario</th>
                <th>Acción</th>
                <th>Detalles</th>
            </tr>
        </thead>
        <tbody>`;

    dashboardData.activityLog.slice(0, 20).forEach(log => {
        const timestamp = new Date(log.timestamp).toLocaleString('es-ES');
        html += `
            <tr>
                <td>${timestamp}</td>
                <td>${log.user_name || 'Sistema'}</td>
                <td><span class="action-badge">${log.action}</span></td>
                <td>${log.details || '-'}</td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

/**
 * Ver perfil de candidato (Empresa)
 */
async function viewCandidateProfile(candidateId) {
    // Implementar visualización de perfil
    window.location.href = `/candidate/${candidateId}`;
}

/**
 * Contactar candidato (Empresa)
 */
async function contactCandidate(candidateId) {
    try {
        notificationManager.loading('Enviando mensaje...');
        await apiClient.post(`/messaging/send`, {
            recipient_id: candidateId,
            message: 'Estamos interesados en tu perfil'
        });
        notificationManager.hideLoading();
        notificationManager.success('Mensaje enviado');
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al enviar mensaje');
    }
}

/**
 * Editar vacante (Empresa)
 */
async function editJob(jobId) {
    window.location.href = `/job/${jobId}/edit`;
}

/**
 * Setup de event handlers
 */
function setupEventHandlers() {
    // Botón de logout
    const logoutBtn = document.querySelector('[onclick="logout()"]');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await logout();
        });
    }

    // Event listeners para notificaciones en tiempo real (WebSocket en futuro)
    authManager.onChange((user) => {
        currentUser = user;
        document.getElementById('user-name').textContent = user.first_name || 'Usuario';
    });
}

/**
 * Refrescar dashboard
 */
async function refreshDashboard() {
    notificationManager.loading('Actualizando...');
    try {
        await Promise.all([
            loadApplications(),
            loadRecommendations(),
            loadStats()
        ]);
        notificationManager.hideLoading();
        notificationManager.success('Dashboard actualizado');
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Error al actualizar');
    }
}
