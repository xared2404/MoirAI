/**
 * MoirAI - Dashboard Role Adapter
 * Adaptador de dashboard según el rol del usuario
 * Controla qué secciones se muestran para Estudiante, Empresa y Admin
 */

class DashboardRoleAdapter {
    constructor() {
        this.role = null;
        this.user = null;
    }

    /**
     * Inicializar adaptador según role
     */
    async initialize() {
        try {
            // Obtener role de storage o del usuario actual (con storageManager si disponible)
            if (typeof storageManager !== 'undefined') {
                this.role = storageManager.getUserRole();
            } else {
                this.role = localStorage.getItem('user_role') || 'student';
            }
            
            // ✅ Solo renderizar la interfaz de contenido, NO la navbar
            // La navbar es responsabilidad EXCLUSIVA de navbar-manager.js
            this.setupRoleInterface();
            
        } catch (error) {
            console.error('Error inicializando role adapter:', error);
            throw error;
        }
    }

    /**
     * Configurar la interfaz según el rol
     */
    setupRoleInterface() {
        // Ocultar todos los contenidos
        document.getElementById('student-content').style.display = 'none';
        document.getElementById('company-content').style.display = 'none';
        document.getElementById('admin-content').style.display = 'none';

        // Mostrar contenido según role
        switch (this.role) {
            case 'student':
                document.getElementById('student-content').style.display = 'block';
                this.setupStudentStats();
                break;
            
            case 'company':
                document.getElementById('company-content').style.display = 'block';
                this.setupCompanyStats();
                break;
            
            case 'admin':
                document.getElementById('admin-content').style.display = 'block';
                this.setupAdminStats();
                break;
            
            default:
                // Por defecto mostrar interfaz de estudiante
                document.getElementById('student-content').style.display = 'block';
                this.setupStudentStats();
        }
    }

    /**
     * Configurar stats para Estudiante
     */
    setupStudentStats() {
        const statsContainer = document.getElementById('stats-container');
        if (!statsContainer) return;

        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-briefcase"></i>
                </div>
                <div class="stat-content">
                    <h3>Aplicaciones</h3>
                    <p class="stat-number" id="applications-count">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-star"></i>
                </div>
                <div class="stat-content">
                    <h3>Score Match</h3>
                    <p class="stat-number" id="match-score">0%</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-lightbulb"></i>
                </div>
                <div class="stat-content">
                    <h3>Recomendaciones</h3>
                    <p class="stat-number" id="recommendations-count">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-file-pdf"></i>
                </div>
                <div class="stat-content">
                    <h3>CV Actualizado</h3>
                    <p class="stat-text" id="cv-status">No</p>
                </div>
            </div>
        `;
    }

    /**
     * Configurar stats para Empresa
     */
    setupCompanyStats() {
        const statsContainer = document.getElementById('stats-container');
        if (!statsContainer) return;

        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-briefcase"></i>
                </div>
                <div class="stat-content">
                    <h3>Vacantes Publicadas</h3>
                    <p class="stat-number" id="posted-jobs-count">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-user-check"></i>
                </div>
                <div class="stat-content">
                    <h3>Candidatos Revisados</h3>
                    <p class="stat-number" id="candidates-reviewed-count">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-handshake"></i>
                </div>
                <div class="stat-content">
                    <h3>Contrataciones</h3>
                    <p class="stat-number" id="hires-count">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-eye"></i>
                </div>
                <div class="stat-content">
                    <h3>Perfil Visto</h3>
                    <p class="stat-number" id="profile-views-count">0</p>
                </div>
            </div>
        `;
    }

    /**
     * Configurar stats para Admin
     */
    setupAdminStats() {
        const statsContainer = document.getElementById('stats-container');
        if (!statsContainer) return;

        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-content">
                    <h3>Usuarios Totales</h3>
                    <p class="stat-number" id="total-users">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-percentage"></i>
                </div>
                <div class="stat-content">
                    <h3>Tasa de Colocación</h3>
                    <p class="stat-number" id="placement-rate">0%</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-content">
                    <h3>Coincidencias Realizadas</h3>
                    <p class="stat-number" id="matches-made">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-alert-triangle"></i>
                </div>
                <div class="stat-content">
                    <h3>Alertas del Sistema</h3>
                    <p class="stat-number" id="system-alerts">0</p>
                </div>
            </div>
        `;
    }

    /**
     * Obtener el role del usuario
     */
    getRole() {
        return this.role;
    }

    /**
     * Verificar si el usuario tiene un role específico
     */
    hasRole(role) {
        return this.role === role;
    }

    /**
     * Obtener plantilla de contenido según role
     */
    getContentTemplate(role) {
        const templates = {
            'student': 'student-content',
            'company': 'company-content',
            'admin': 'admin-content'
        };
        return templates[role] || 'student-content';
    }
}

// Instancia global del adaptador
const dashboardRoleAdapter = new DashboardRoleAdapter();

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Esperar a que authManager esté completamente cargado
        setTimeout(() => {
            dashboardRoleAdapter.initialize().catch(error => {
                console.error('Error inicializando dashboard role adapter:', error);
            });
        }, 150);
    });
} else {
    // Esperar a que authManager esté completamente cargado
    setTimeout(() => {
        dashboardRoleAdapter.initialize().catch(error => {
            console.error('Error inicializando dashboard role adapter:', error);
        });
    }, 150);
}
