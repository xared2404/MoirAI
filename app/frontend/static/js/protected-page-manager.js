/**
 * MoirAI - Protected Page Manager
 * Gestión mejorada de protección de rutas y autenticación
 * Previene race conditions y redirecciones inesperadas
 */

class ProtectedPageManager {
    constructor() {
        this.authCheckInProgress = false;
        this.timeoutMs = 3000;
    }

    /**
     * Verificar autenticación de forma robusta
     * Espera a que authManager esté completamente inicializado
     */
    async ensureAuthenticated(redirectUrl = '/login?redirect=/dashboard') {
        console.log('🔐 ProtectedPageManager: Verificando autenticación...');

        // Verificación primaria: token en API client (más confiable)
        if (!apiClient.isAuthenticated()) {
            console.error('❌ ProtectedPageManager: No autenticado (sin token)');
            window.location.href = redirectUrl;
            return false;
        }

        // Si ya tiene currentUser, usar eso
        if (authManager.currentUser) {
            console.log('✅ ProtectedPageManager: Usuario ya cargado en authManager');
            return true;
        }

        // Si no, intentar cargar usuario
        console.log('⏳ ProtectedPageManager: Cargando usuario...');
        try {
            await this.waitForAuthReady(this.timeoutMs);
            console.log('✅ ProtectedPageManager: Usuario cargado correctamente');
            return true;
        } catch (error) {
            console.warn('⚠️ ProtectedPageManager: Timeout esperando usuario, pero tenemos token. Continuando...');
            // Aunque no tengamos currentUser, si tenemos token podemos continuar
            return true;
        }
    }

    /**
     * Esperar a que authManager cargue el usuario
     */
    async waitForAuthReady(timeoutMs = 3000) {
        return new Promise((resolve, reject) => {
            if (authManager.currentUser) {
                resolve();
                return;
            }

            const startTime = Date.now();
            const checkInterval = setInterval(() => {
                if (authManager.currentUser) {
                    clearInterval(checkInterval);
                    resolve();
                } else if (Date.now() - startTime > timeoutMs) {
                    clearInterval(checkInterval);
                    reject(new Error('Timeout waiting for auth'));
                }
            }, 50);
        });
    }

    /**
     * Verificar rol específico
     */
    async ensureRole(requiredRoles, redirectUrl = '/dashboard') {
        // Asegurar autenticación primero
        await this.ensureAuthenticated();

        let userRole;
        if (typeof storageManager !== 'undefined') {
            userRole = storageManager.getUserRole();
        } else {
            userRole = authManager.getUserRole() || localStorage.getItem('user_role');
        }
        
        if (typeof requiredRoles === 'string') {
            requiredRoles = [requiredRoles];
        }

        if (!requiredRoles.includes(userRole)) {
            console.error(`❌ ProtectedPageManager: Rol no permitido. Se requiere: ${requiredRoles.join(', ')}, actual: ${userRole}`);
            notificationManager.error('No tienes permiso para acceder a esta página');
            setTimeout(() => {
                window.location.href = redirectUrl;
            }, 2000);
            return false;
        }

        console.log(`✅ ProtectedPageManager: Rol ${userRole} verificado`);
        return true;
    }

    /**
     * Inicializar página protegida
     */
    async initProtectedPage(config = {}) {
        const {
            requiredRoles = null,
            redirectOnUnauth = '/login?redirect=/dashboard',
            redirectOnUnauthorized = '/dashboard',
            loadingMessage = 'Cargando...',
            onInit = null
        } = config;

        try {
            // Mostrar loading
            notificationManager.loading(loadingMessage);

            // Verificar autenticación
            await this.ensureAuthenticated(redirectOnUnauth);

            // Verificar rol si es necesario
            if (requiredRoles) {
                await this.ensureRole(requiredRoles, redirectOnUnauthorized);
            }

            // Ejecutar callback de inicialización
            if (onInit && typeof onInit === 'function') {
                await onInit();
            }

            notificationManager.hideLoading();
            console.log('✅ ProtectedPageManager: Página inicializada correctamente');

        } catch (error) {
            notificationManager.hideLoading();
            console.error('❌ ProtectedPageManager: Error inicializando página:', error);
            notificationManager.error(error.message || 'Error al cargar la página');
        }
    }
}

// Instancia global
const protectedPageManager = new ProtectedPageManager();
