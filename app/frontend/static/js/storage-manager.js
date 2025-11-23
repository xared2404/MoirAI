/**
 * MoirAI Storage Manager
 * Centralizes all localStorage and sessionStorage access
 * Provides typed, consistent API for data persistence
 * 
 * Benefits:
 * - Single source of truth for storage keys
 * - Easy to audit data access patterns
 * - Type-safe getters/setters
 * - Encryption-ready for future implementation
 * - Easy to migrate to IndexedDB if needed
 */

const storageManager = {
  // Keys - Define all storage keys in one place
  KEYS: {
    // Authentication
    API_KEY: 'api_key',
    USER_ID: 'user_id',
    USER_ROLE: 'user_role',
    USER_EMAIL: 'user_email',
    USER_NAME: 'user_name',
    
    // Legacy/Fallback
    MOIRAI_TOKEN: 'moirai_token',
    
    // Session (temporary)
    SESSION_USER: 'session_user',
    SESSION_TOKEN: 'session_token'
  },

  // ============================================
  // Authentication Data
  // ============================================

  /**
   * Set complete user session data
   */
  setUserSession(userData) {
    if (!userData) {
      console.warn('⚠️ setUserSession called with empty data');
      return;
    }

    if (userData.api_key) {
      localStorage.setItem(this.KEYS.API_KEY, userData.api_key);
    }
    if (userData.user_id) {
      localStorage.setItem(this.KEYS.USER_ID, userData.user_id.toString());
    }
    if (userData.role) {
      localStorage.setItem(this.KEYS.USER_ROLE, userData.role);
    }
    if (userData.email) {
      localStorage.setItem(this.KEYS.USER_EMAIL, userData.email);
    }
    if (userData.name) {
      localStorage.setItem(this.KEYS.USER_NAME, userData.name);
    }

    console.log('✅ User session saved:', {
      userId: userData.user_id,
      role: userData.role,
      email: userData.email
    });
  },

  /**
   * Get complete user session
   */
  getUserSession() {
    return {
      api_key: this.getApiKey(),
      user_id: this.getUserId(),
      role: this.getUserRole(),
      email: this.getUserEmail(),
      name: this.getUserName()
    };
  },

  /**
   * Get API Key
   */
  getApiKey() {
    const apiKey = localStorage.getItem(this.KEYS.API_KEY);
    if (!apiKey) {
      console.warn('⚠️ API Key not found in storage');
    }
    return apiKey;
  },

  /**
   * Set API Key
   */
  setApiKey(apiKey) {
    if (!apiKey) {
      console.warn('⚠️ Trying to set empty API key');
      return;
    }
    localStorage.setItem(this.KEYS.API_KEY, apiKey);
    console.log('✅ API Key set');
  },

  /**
   * Check if API Key exists
   */
  hasApiKey() {
    return !!localStorage.getItem(this.KEYS.API_KEY);
  },

  /**
   * Get User ID
   */
  getUserId() {
    return localStorage.getItem(this.KEYS.USER_ID);
  },

  /**
   * Set User ID
   */
  setUserId(userId) {
    localStorage.setItem(this.KEYS.USER_ID, userId.toString());
  },

  /**
   * Get User Role
   */
  getUserRole() {
    return localStorage.getItem(this.KEYS.USER_ROLE) || 'student';
  },

  /**
   * Set User Role
   */
  setUserRole(role) {
    localStorage.setItem(this.KEYS.USER_ROLE, role);
  },

  /**
   * Get User Email
   */
  getUserEmail() {
    return localStorage.getItem(this.KEYS.USER_EMAIL);
  },

  /**
   * Set User Email
   */
  setUserEmail(email) {
    localStorage.setItem(this.KEYS.USER_EMAIL, email);
  },

  /**
   * Get User Name
   */
  getUserName() {
    return localStorage.getItem(this.KEYS.USER_NAME);
  },

  /**
   * Set User Name
   */
  setUserName(name) {
    localStorage.setItem(this.KEYS.USER_NAME, name);
  },

  // ============================================
  // Generic Storage Methods
  // ============================================

  /**
   * Generic get from localStorage
   */
  get(key, defaultValue = null) {
    const value = localStorage.getItem(key);
    return value !== null ? value : defaultValue;
  },

  /**
   * Generic set to localStorage
   */
  set(key, value) {
    if (value === null || value === undefined) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, value.toString());
    }
  },

  /**
   * Generic remove from localStorage
   */
  remove(key) {
    localStorage.removeItem(key);
  },

  /**
   * Get from sessionStorage
   */
  getSession(key, defaultValue = null) {
    const value = sessionStorage.getItem(key);
    return value !== null ? value : defaultValue;
  },

  /**
   * Set to sessionStorage
   */
  setSession(key, value) {
    if (value === null || value === undefined) {
      sessionStorage.removeItem(key);
    } else {
      sessionStorage.setItem(key, value.toString());
    }
  },

  /**
   * Remove from sessionStorage
   */
  removeSession(key) {
    sessionStorage.removeItem(key);
  },

  // ============================================
  // Utility Methods
  // ============================================

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return this.hasApiKey();
  },

  /**
   * Clear all storage (logout)
   */
  clear() {
    console.log('🔓 Clearing all storage (logout)');
    
    // Clear localStorage
    Object.values(this.KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    
    // Clear sessionStorage
    sessionStorage.clear();
    
    console.log('✅ Storage cleared');
  },

  /**
   * Get all stored data (for debugging)
   */
  getAll() {
    const data = {};
    
    // Get all known keys
    Object.entries(this.KEYS).forEach(([name, key]) => {
      data[name] = localStorage.getItem(key);
    });
    
    return data;
  },

  /**
   * Validate stored data integrity
   */
  validate() {
    const required = [this.KEYS.API_KEY, this.KEYS.USER_ID, this.KEYS.USER_ROLE];
    const missing = required.filter(key => !localStorage.getItem(key));
    
    if (missing.length > 0) {
      console.warn('⚠️ Missing required keys:', missing);
      return false;
    }
    
    console.log('✅ Storage validation passed');
    return true;
  },

  /**
   * Debug: Log all storage
   */
  debug() {
    console.group('🔍 Storage Manager Debug');
    console.log('localStorage:', this.getAll());
    console.log('sessionStorage:', Object.fromEntries(
      Object.entries(this.KEYS).map(([name, key]) => [
        name,
        sessionStorage.getItem(key)
      ])
    ));
    console.log('Authenticated:', this.isAuthenticated());
    console.log('Valid:', this.validate());
    console.groupEnd();
  },

  // ============================================
  // ✅ NUEVOS: Profile Management (BD Sync)
  // ============================================

  /**
   * ✅ Guardar perfil completo del usuario
   * Maneja arrays y objetos complejos
   */
  setUserProfile(profile) {
    if (!profile) {
      console.warn('⚠️ setUserProfile called with empty data');
      return;
    }

    try {
      // Guardar como JSON para preservar estructura
      localStorage.setItem('currentUserProfile', JSON.stringify(profile));
      
      // Guardar timestamp para detectar caducidad
      localStorage.setItem('currentUserProfile_timestamp', Date.now().toString());

      console.log('✅ User profile saved to cache:', {
        userId: profile.id,
        email: profile.email,
        cvUploaded: profile.cv_uploaded,
        skillsCount: profile.skills?.length || 0
      });
    } catch (error) {
      console.error('❌ Error saving profile to cache:', error);
      localStorage.removeItem('currentUserProfile');
      localStorage.removeItem('currentUserProfile_timestamp');
    }
  },

  /**
   * ✅ Obtener perfil del caché
   */
  getUserProfile() {
    try {
      const cached = localStorage.getItem('currentUserProfile');
      if (!cached) {
        return null;
      }
      
      const profile = JSON.parse(cached);
      return profile;
    } catch (error) {
      console.error('❌ Corrupted profile in cache:', error);
      localStorage.removeItem('currentUserProfile');
      localStorage.removeItem('currentUserProfile_timestamp');
      return null;
    }
  },

  /**
   * ✅ Validar que caché sea válido
   */
  validateUserProfile() {
    const profile = this.getUserProfile();
    if (!profile) {
      return false;
    }

    // Verificar campos críticos
    const required = ['id', 'email', 'name'];
    const valid = required.every(field => !!profile[field]);
    
    if (!valid) {
      console.warn('⚠️ Profile missing required fields');
      this.clearUserProfile();
      return false;
    }

    return true;
  },

  /**
   * ✅ Limpiar perfil del caché
   */
  clearUserProfile() {
    localStorage.removeItem('currentUserProfile');
    localStorage.removeItem('currentUserProfile_timestamp');
    console.log('✅ User profile cleared from cache');
  },

  /**
   * ✅ Verificar si caché está expirado
   */
  isProfileExpired(maxAgeMinutes = 60) {
    const timestamp = localStorage.getItem('currentUserProfile_timestamp');
    if (!timestamp) {
      return true;
    }

    const ageMinutes = (Date.now() - parseInt(timestamp)) / (1000 * 60);
    const expired = ageMinutes > maxAgeMinutes;
    
    if (expired) {
      console.warn(`⚠️ Profile cache expired (${ageMinutes.toFixed(2)} min)`);
    }
    
    return expired;
  }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = storageManager;
}
