/**
 * Navbar Manager - Gestor global de la barra de navegación
 * Se ejecuta en TODAS las páginas y adapta la navbar según:
 * - Si el usuario está autenticado o no
 * - El role del usuario (student/company/admin)
 * - La página actual
 */

class NavbarManager {
    constructor() {
        this.isAuthenticated = false;
        this.userRole = null;
        this.userName = null;
        this.currentPage = null;
        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) {
            console.log('ℹ️ NavbarManager ya inicializado');
            return;
        }
        this.initialized = true;
        
        console.log('🔄 Inicializando NavbarManager...');
        
        try {
            if (typeof storageManager !== 'undefined') {
                this.isAuthenticated = storageManager.isAuthenticated();
                this.userRole = storageManager.getUserRole();
                this.userName = storageManager.getUserName() || storageManager.getUserEmail() || 'Usuario';
            } else {
                this.isAuthenticated = !!localStorage.getItem('api_key');
                this.userRole = localStorage.getItem('user_role') || null;
                this.userName = localStorage.getItem('user_name') || localStorage.getItem('user_email') || 'Usuario';
            }
            
            this.currentPage = this.getCurrentPage();

            console.log(`📌 NavbarManager State:`, {
                isAuthenticated: this.isAuthenticated,
                userRole: this.userRole,
                currentPage: this.currentPage
            });

            if (this.isAuthenticated) {
                this.setupAuthenticatedNavbar();
            } else {
                this.setupPublicNavbar();
            }

        } catch (error) {
            console.error('❌ Error en NavbarManager:', error);
            this.setupPublicNavbar();
        }
    }

    getCurrentPage() {
        const path = window.location.pathname;
        if (path === '/' || path === '') return 'home';
        if (path === '/dashboard') return 'dashboard';
        if (path === '/oportunidades') return 'oportunidades';
        if (path === '/profile') return 'profile';
        if (path === '/applications') return 'applications';
        if (path === '/admin') return 'admin';
        return 'home';
    }

    setupAuthenticatedNavbar() {
        console.log('🔐 Configurando navbar autenticada para:', this.userRole);
        
        const navbarContainer = document.getElementById('navbar-container') || document.querySelector('.navbar');
        if (!navbarContainer) {
            console.warn('⚠️ Navbar container no encontrada');
            return;
        }

        navbarContainer.innerHTML = '';

        const menuItems = this.getMenuItemsByRole().map(item => {
            return `
                <li class="nav-item">
                    <a href="${item.href}" class="nav-link ${this.currentPage === item.page ? 'active' : ''}">
                        <i class="fas ${item.icon}"></i>
                        <span>${item.label}</span>
                    </a>
                </li>
            `;
        }).join('');

        navbarContainer.innerHTML = `
            <div class="nav-container">
                <div class="nav-logo">
                    <a href="/dashboard">
                        <i class="fas fa-brain"></i>
                        <span>MoirAI</span>
                    </a>
                </div>

                <div class="nav-menu" id="nav-menu">
                    <ul class="nav-list">
                        ${menuItems}
                    </ul>
                </div>

                <div class="nav-cta">
                    <div class="user-info" style="display: flex; align-items: center; gap: 15px; margin-right: 20px;">
                        <span class="user-name" style="font-size: 14px; color: #333;">${this.userName}</span>
                        <button class="btn btn-secondary" onclick="logout()" style="cursor: pointer;">
                            <i class="fas fa-sign-out-alt"></i> Salir
                        </button>
                    </div>
                </div>
            </div>
        `;

        console.log('✅ Navbar autenticada configurada para role:', this.userRole);
    }

    setupPublicNavbar() {
        console.log('🌐 Configurando navbar pública...');
        
        const navbarContainer = document.getElementById('navbar-container') || document.querySelector('.navbar');
        if (!navbarContainer) {
            console.warn('⚠️ Navbar container no encontrada');
            return;
        }

        navbarContainer.innerHTML = '';

        navbarContainer.innerHTML = `
            <div class="nav-container">
                <div class="nav-logo">
                    <a href="/">
                        <i class="fas fa-brain"></i>
                        <span>MoirAI</span>
                    </a>
                </div>

                <div class="nav-menu" id="nav-menu">
                    <ul class="nav-list">
                        <li class="nav-item">
                            <a href="/" class="nav-link ${this.currentPage === 'home' ? 'active' : ''}">
                                <i class="fas fa-home"></i>
                                <span>Inicio</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="/oportunidades" class="nav-link ${this.currentPage === 'oportunidades' ? 'active' : ''}">
                                <i class="fas fa-briefcase"></i>
                                <span>Oportunidades</span>
                            </a>
                        </li>
                    </ul>
                </div>

                <div class="nav-cta">
                    <button class="btn btn-primary" onclick="window.location.href='/login'" style="cursor: pointer;">
                        <i class="fas fa-sign-in-alt"></i> Iniciar Sesión
                    </button>
                </div>
            </div>
        `;

        console.log('✅ Navbar pública configurada');
    }

    getMenuItemsByRole() {
        const menus = {
            'student': [
                { href: '/dashboard', icon: 'fa-home', label: 'Dashboard', page: 'dashboard' },
                { href: '/oportunidades', icon: 'fa-briefcase', label: 'Oportunidades', page: 'oportunidades' },
                { href: '/profile', icon: 'fa-user', label: 'Mi Perfil', page: 'profile' },
                { href: '/applications', icon: 'fa-file-alt', label: 'Mis Aplicaciones', page: 'applications' }
            ],
            'company': [
                { href: '/dashboard', icon: 'fa-home', label: 'Dashboard', page: 'dashboard' },
                { href: '/buscar-candidatos', icon: 'fa-search', label: 'Buscar Candidatos', page: 'buscar-candidatos' },
                { href: '/profile', icon: 'fa-building', label: 'Mi Empresa', page: 'profile' },
                { href: '/mis-vacantes', icon: 'fa-briefcase', label: 'Mis Vacantes', page: 'mis-vacantes' }
            ],
            'admin': [
                { href: '/dashboard', icon: 'fa-home', label: 'Dashboard', page: 'dashboard' },
                { href: '/admin/users', icon: 'fa-users', label: 'Usuarios', page: 'admin-users' },
                { href: '/admin/analytics', icon: 'fa-chart-line', label: 'Analítica', page: 'admin-analytics' },
                { href: '/admin/settings', icon: 'fa-cog', label: 'Configuración', page: 'admin-settings' }
            ]
        };

        return menus[this.userRole] || menus['student'];
    }

    requireAuth() {
        if (!this.isAuthenticated) {
            console.log('🔒 No autenticado, redirigiendo a /login...');
            window.location.href = `/login?redirect=${window.location.pathname}`;
            return false;
        }
        return true;
    }

    requirePublic() {
        if (this.isAuthenticated) {
            console.log('✅ Ya autenticado, redirigiendo a /dashboard...');
            window.location.href = '/dashboard';
            return false;
        }
        return true;
    }

    requireRole(allowedRoles) {
        if (!Array.isArray(allowedRoles)) {
            allowedRoles = [allowedRoles];
        }

        if (!allowedRoles.includes(this.userRole)) {
            console.log(`🚫 Rol no permitido. Required: ${allowedRoles}, Got: ${this.userRole}`);
            window.location.href = '/dashboard';
            return false;
        }
        return true;
    }
}

// ✅ CREAR INSTANCIA GLOBAL
const navbarManager = new NavbarManager();
console.log('✅ NavbarManager instance created:', navbarManager);

// ✅ INICIALIZACIÓN ROBUSTA
let navbarInitialized = false;

function initializeNavbar() {
    if (navbarInitialized) {
        console.log('ℹ️ Navbar ya inicializada, previniendo duplicados...');
        return;
    }
    navbarInitialized = true;
    
    console.log('📍 Iniciando navbar (global)...');
    console.log('navbarManager:', navbarManager);
    
    if (!navbarManager) {
        console.error('❌ CRÍTICO: navbarManager no está definido');
        navbarInitialized = false;
        return;
    }
    
    navbarManager.initialize().then(() => {
        console.log('✅ Navbar inicializada exitosamente');
        setupMobileMenu();
        setupScrollEffects();
    }).catch(error => {
        console.error('❌ Error inicializando navbar:', error);
        navbarInitialized = false;
    });
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            initializeNavbar();
        }, 50);
    });
} else {
    setTimeout(() => {
        initializeNavbar();
    }, 50);
}

function setupMobileMenu() {
    const navbar = document.querySelector('.navbar');
    const navContainer = document.querySelector('.nav-container');
    
    if (!navbar || !navContainer) return;

    let mobileToggle = document.getElementById('mobileToggle');
    if (!mobileToggle) {
        mobileToggle = document.createElement('button');
        mobileToggle.className = 'sidebar-toggle';
        mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
        mobileToggle.id = 'mobileToggle';
        navContainer.appendChild(mobileToggle);
    }

    mobileToggle.addEventListener('click', () => {
        navbar.classList.toggle('show');
        mobileToggle.classList.toggle('active');
    });

    const navLinks = navbar.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                navbar.classList.remove('show');
                mobileToggle.classList.remove('active');
            }
        });
    });

    document.addEventListener('click', (event) => {
        if (window.innerWidth <= 768) {
            const isClickInsideNavbar = navbar.contains(event.target);
            const isClickOnToggle = mobileToggle.contains(event.target);

            if (!isClickInsideNavbar && !isClickOnToggle && navbar.classList.contains('show')) {
                navbar.classList.remove('show');
                mobileToggle.classList.remove('active');
            }
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            navbar.classList.remove('show');
            if (mobileToggle) mobileToggle.style.display = 'none';
            if (mobileToggle) mobileToggle.classList.remove('active');
        } else {
            if (mobileToggle) mobileToggle.style.display = 'flex';
        }
    });
}

function setupScrollEffects() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 10) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

function setActiveLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');
        
        if (href === currentPath || (currentPath === '/' && href === '/dashboard')) {
            link.classList.add('active');
        }
    });
}

function smoothScroll(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

/**
 * GLOBAL LOGOUT FUNCTION
 * Consolidated from multiple logout implementations
 * Used by navbar, dashboard, profile, and all pages
 * Available in navbar context (loaded on all pages)
 */
async function logout() {
    try {
        console.log('🚪 Iniciando logout...');
        
        // Call core logout from authManager if available
        if (typeof authManager !== 'undefined' && authManager) {
            try {
                console.log('🔄 Llamando authManager.logout()...');
                await authManager.logout();
                console.log('✅ authManager.logout() completado');
            } catch (authError) {
                console.warn('⚠️ authManager.logout() falló, continuando con fallback:', authError);
            }
        } else {
            console.warn('⚠️ authManager no disponible, usando fallback');
        }
        
        // Fallback: Clear storage directly if authManager isn't available or failed
        try {
            if (typeof storageManager !== 'undefined' && storageManager) {
                console.log('🧹 Limpiando storageManager...');
                if (typeof storageManager.clearUserSession === 'function') {
                    storageManager.clearUserSession();
                    console.log('✅ storageManager.clearUserSession() completado');
                } else {
                    console.warn('⚠️ storageManager.clearUserSession no es una función');
                }
            } else {
                console.log('🧹 storageManager no disponible, limpiando localStorage directamente...');
                localStorage.removeItem('api_key');
                localStorage.removeItem('user_id');
                localStorage.removeItem('user_role');
                localStorage.removeItem('user_email');
                localStorage.removeItem('user_name');
                localStorage.removeItem('moirai_api_key');
                localStorage.removeItem('moirai_token');
            }
        } catch (storageError) {
            console.error('❌ Error limpiando storage:', storageError);
        }
        
        // Show success notification
        try {
            if (typeof notificationManager !== 'undefined' && notificationManager) {
                console.log('📢 Mostrando notificación de logout...');
                notificationManager.success('Hasta luego 👋');
            }
        } catch (notifError) {
            console.warn('⚠️ Error mostrando notificación:', notifError);
        }
        
        // Redirect after notification is shown
        console.log('↪️ Redirigiendo a home en 1 segundo...');
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
        
    } catch (error) {
        console.error('❌ Error general en logout:', error);
        
        // Emergency fallback logout
        try {
            localStorage.clear();
            sessionStorage.clear();
        } catch (e) {
            console.error('❌ Error limpiando todo el storage:', e);
        }
        
        // Force redirect anyway
        console.log('⚠️ Error en logout, forzando redirección...');
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
}

window.megaMenuUtils = {
    setActiveLink,
    smoothScroll
};

