/**
 * Auth Manager - Gestión de autenticación y sesión de usuario
 */

class AuthManager {
  constructor(apiClient) {
    this.api = apiClient
    this.currentUser = null
    this.listeners = []
  }

  /**
   * Registrar un callback que se ejecute cuando cambie el estado de autenticación
   */
  onChange(callback) {
    this.listeners.push(callback)
  }

  /**
   * Notificar cambios a todos los listeners
   */
  notifyListeners() {
    this.listeners.forEach(callback => callback(this.currentUser))
  }

  /**
   * Registro de nuevo usuario
   * ✅ CORRECCIÓN: Mapea correctamente api_key de la respuesta
   */
  async register(userData) {
    try {
      const response = await this.api.post('/auth/register', {
        // ✅ Backend espera estructura correcta
        name: userData.name || `${userData.firstName} ${userData.lastName}`.trim(),
        email: userData.email,
        password: userData.password,
        role: userData.role || userData.userType || 'student',
        program: userData.program,              // Para estudiantes
        industry: userData.industry,            // Para empresas
        company_size: userData.companySize,     // Para empresas
        location: userData.location             // Para empresas
      })

      // ✅ CORRECCIÓN: Mapear api_key correctamente (no token)
      if (response.api_key) {
        this.api.setToken(response.api_key)
      }

      this.currentUser = {
        user_id: response.user_id,
        email: userData.email,
        name: userData.name || `${userData.firstName} ${userData.lastName}`.trim(),
        role: response.role || userData.role || 'student'
      }

      this.notifyListeners()
      return response

    } catch (error) {
      console.error('Error en registro:', error)
      throw {
        message: error.message || 'Error al registrar usuario',
        code: error.status
      }
    }
  }

  /**
   * Login con email y contraseña
   * ✅ CORRECCIÓN: Mapea correctamente api_key de la respuesta
   * ✅ Si no viene api_key, usa la guardada del registro
   */
  async login(email, password) {
    try {
      console.log('📍 Iniciando login...');
      
      const response = await this.api.post('/auth/login', {
        email,
        password
      })

      console.log('📍 Respuesta del login:', {
        user_id: response.user_id,
        email: response.email,
        role: response.role,
        api_key_presente: !!response.api_key,
        api_key_vacio: response.api_key === '',
        api_key_length: response.api_key?.length || 0
      });

            // ✅ CORRECCIÓN: Verificar api_key o usar la guardada del registro
      let apiKey = response.api_key;
      
      // Si no viene api_key en la respuesta, usar la guardada del registro
      if (!apiKey || apiKey === '' || apiKey === undefined) {
        console.log('⚠️ api_key vacío o no presente, buscando en storage...');
        apiKey = storageManager?.getApiKey();
        
        console.log('📍 Storage api_key:', {
          presente: !!apiKey,
          length: apiKey?.length || 0
        });
        
        // Si tampoco está en storage, error
        if (!apiKey) {
          console.error('❌ No se encontró API key en respuesta ni en storage');
          throw new Error('No se recibió API key de autenticación. Por favor, vuelve a registrarte.')
        }
      }

      console.log('✅ API key obtenida, usando para autenticación');

      // ✅ CORRECCIÓN: Usar api_key en lugar de token
      this.api.setToken(apiKey)
      
      this.currentUser = {
        user_id: response.user_id,
        email: response.email,
        name: response.name,
        role: response.role
      }

      // ✅ ACTUALIZACIÓN: Guardar usando storageManager
      if (storageManager) {
        storageManager.setUserSession({
          api_key: apiKey,
          user_id: response.user_id,
          role: response.role,
          email: response.email,
          name: response.name
        });
      } else {
        // Fallback si storageManager no está disponible
        localStorage.setItem('api_key', apiKey)
        localStorage.setItem('user_id', response.user_id.toString())
        localStorage.setItem('user_role', response.role)
        localStorage.setItem('user_email', response.email)
      }

      console.log('✅ Datos guardados');

      this.notifyListeners()
      return response

    } catch (error) {
      console.error('❌ Error en login:', error)
      throw {
        message: error.message || 'Error al iniciar sesión',
        code: error.status,
        isAuthError: error.status === 401
      }
    }
  }

  /**
   * Logout
   */
  async logout() {
    try {
      if (this.api.isAuthenticated()) {
        await this.api.post('/auth/logout')
      }
    } catch (error) {
      console.warn('Error en logout:', error)
    }

    // ✅ CORRECCIÓN: Limpiar completamente la sesión
    this.api.clearToken()
    this.currentUser = null
    
    // Limpiar datos de storage
    if (storageManager) {
      storageManager.clearUserSession()
    } else {
      // Fallback si storageManager no disponible
      localStorage.removeItem('moirai_api_key')
      localStorage.removeItem('moirai_user_id')
      localStorage.removeItem('moirai_user_role')
      localStorage.removeItem('moirai_user_email')
      localStorage.removeItem('moirai_user_name')
      // También limpiar sin prefijo por compatibilidad
      localStorage.removeItem('api_key')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_role')
      localStorage.removeItem('user_email')
    }
    
    this.notifyListeners()
  }

  /**
   * Obtener usuario actual
   */
  /**
   * ✅ UNIFIED: Obtener usuario COMPLETO de BD usando /auth/me
   * 
   * Usa SIEMPRE GET /auth/me (endpoint unificado para todos los roles)
   * Retorna StudentProfile, CompanyProfile o AdminContext según el rol
   */
  async getCurrentUser() {
    try {
      if (!this.api.isAuthenticated()) {
        return null
      }

      // ✅ UNIFIED: Usar SIEMPRE el mismo endpoint para todos los roles
      const endpoint = '/auth/me'
      
      console.log(`📍 getCurrentUser: Usando endpoint unificado ${endpoint}`)
      
      const response = await this.api.get(endpoint)
      
      this.currentUser = response.user || response

      // ✅ Guardar el rol de la respuesta en localStorage (siempre desde BD)
      if (this.currentUser && this.currentUser.role) {
        localStorage.setItem('user_role', this.currentUser.role)
        console.log(`✅ Rol actualizado en localStorage: ${this.currentUser.role}`)
      }

      // ✅ Sincronizar con localStorage como caché
      try {
        localStorage.setItem('currentUserProfile', JSON.stringify(this.currentUser))
        localStorage.setItem('currentUserProfile_timestamp', Date.now().toString())
        console.log('✅ User profile cached:', { 
          userId: this.currentUser.id,
          role: this.currentUser.role
        })
      } catch (storageError) {
        console.warn('⚠️ localStorage no disponible:', storageError)
      }

      this.notifyListeners()
      return this.currentUser

    } catch (error) {
      console.error('❌ Error obtener usuario actual:', error)
      
      // ✅ Fallback a localStorage si falla
      try {
        const cached = localStorage.getItem('currentUserProfile')
        if (cached) {
          const profile = JSON.parse(cached)
          if (profile && profile.id) {
            console.warn('⚠️ BD no disponible, usando caché:', profile)
            this.currentUser = profile
            this.notifyListeners()
            return this.currentUser
          }
        }
      } catch (e) {
        console.error('❌ Caché corrupto, limpiando')
        try {
          localStorage.removeItem('currentUserProfile')
          localStorage.removeItem('currentUserProfile_timestamp')
        } catch (clearError) {
          console.error('Error limpiando localStorage:', clearError)
        }
      }
      
      // Si es error 401, limpiar sesión
      if (error.status === 401) {
        this.api.clearToken()
        this.currentUser = null
      }
      
      return null
    }
  }

  /**
   * Verificar si el usuario está autenticado
   */
  isAuthenticated() {
    return this.api.isAuthenticated() && !!this.currentUser
  }

  /**
   * Renovar token si es necesario
   * ⚠️ DESHABILITADO: El endpoint /auth/refresh no existe en el backend (MVP)
   * En producción, considerar agregar JWT refresh token mechanism
   */
  async refreshToken() {
    console.warn('refreshToken() deshabilitado - endpoint /auth/refresh no implementado en MVP')
    return false
    // try {
    //   const response = await this.api.post('/auth/refresh')
    //   if (response.token) {
    //     this.api.setToken(response.token)
    //     return true
    //   }
    //   return false
    // } catch (error) {
    //   console.error('Error renovando token:', error)
    //   return false
    // }
  }

  /**
   * Cambiar contraseña
   * ⚠️ DESHABILITADO: El endpoint /auth/change-password no existe en el backend (MVP)
   * En producción, considerar agregar este endpoint de seguridad
   */
  async changePassword(currentPassword, newPassword) {
    console.warn('changePassword() deshabilitado - endpoint /auth/change-password no implementado en MVP')
    throw {
      message: 'Cambio de contraseña no disponible en esta versión',
      code: 'NOT_AVAILABLE'
    }
    // try {
    //   const response = await this.api.post('/auth/change-password', {
    //     current_password: currentPassword,
    //     new_password: newPassword
    //   })
    //   return response
    // } catch (error) {
    //   console.error('Error cambiando contraseña:', error)
    //   throw {
    //     message: error.message || 'Error al cambiar contraseña',
    //     code: error.status
    //   }
    // }
  }

  /**
   * Solicitar reset de contraseña
   * ⚠️ DESHABILITADO: El endpoint /auth/forgot-password no existe en el backend (MVP)
   * En producción, considerar agregar este endpoint de recuperación
   */
  async requestPasswordReset(email) {
    console.warn('requestPasswordReset() deshabilitado - endpoint /auth/forgot-password no implementado en MVP')
    throw {
      message: 'Recuperación de contraseña no disponible en esta versión',
      code: 'NOT_AVAILABLE'
    }
    // try {
    //   const response = await this.api.post('/auth/forgot-password', { email })
    //   return response
    // } catch (error) {
    //   console.error('Error solicitando reset:', error)
    //   throw {
    //     message: error.message || 'Error al solicitar reset de contraseña',
    //     code: error.status
    //   }
    // }
  }

  /**
   * Confirmar reset de contraseña
   * ⚠️ DESHABILITADO: El endpoint /auth/reset-password no existe en el backend (MVP)
   * En producción, considerar agregar este endpoint de recuperación
   */
  async resetPassword(token, newPassword) {
    console.warn('resetPassword() deshabilitado - endpoint /auth/reset-password no implementado en MVP')
    throw {
      message: 'Confirmación de reset no disponible en esta versión',
      code: 'NOT_AVAILABLE'
    }
    // try {
    //   const response = await this.api.post('/auth/reset-password', {
    //     token,
    //     new_password: newPassword
    //   })
    //   return response
    // } catch (error) {
    //   console.error('Error confirmando reset:', error)
    //   throw {
    //     message: error.message || 'Error al confirmar reset de contraseña',
    //     code: error.status
    //   }
    // }
  }

  /**
   * Obtener rol del usuario actual
   */
  getUserRole() {
    if (!this.currentUser) return null
    return this.currentUser.user_type || this.currentUser.role
  }

  /**
   * Verificar si es estudiante
   */
  isStudent() {
    return this.getUserRole() === 'student'
  }

  /**
   * Verificar si es empresa
   */
  isCompany() {
    return this.getUserRole() === 'company'
  }

  /**
   * Verificar si es administrador
   */
  isAdmin() {
    return this.getUserRole() === 'admin'
  }

  /**
   * Obtener información del usuario actual
   */
  getUserInfo() {
    return this.currentUser
  }

  /**
   * Obtener ID del usuario actual
   */
  getUserId() {
    return this.currentUser?.id
  }

  /**
   * Obtener email del usuario actual
   */
  getUserEmail() {
    return this.currentUser?.email
  }
}

// Crear instancia global del AuthManager
const authManager = new AuthManager(apiClient)

// Auto-cargar usuario actual al iniciar
document.addEventListener('DOMContentLoaded', async () => {
  console.log('⏳ Auth-manager: Verificando autenticación...');
  if (apiClient.isAuthenticated()) {
    console.log('✅ Auth-manager: Token encontrado, cargando usuario...');
    try {
      const user = await authManager.getCurrentUser();
      console.log('✅ Auth-manager: Usuario cargado:', user);
    } catch (error) {
      console.warn('⚠️ Auth-manager: Error cargando usuario:', error);
    }
  } else {
    console.log('⚠️ Auth-manager: No hay token en localStorage');
  }
})

// Event listener global para unauthorized
window.addEventListener('unauthorized', () => {
  console.log('🔐 Auth-manager: Sesión no autorizada, limpiando datos');
  authManager.currentUser = null
  authManager.notifyListeners()
})
