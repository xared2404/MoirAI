/**
 * Notification Manager - Sistema de notificaciones
 */

class NotificationManager {
  constructor() {
    this.container = null
    this.createContainer()
    this.defaultDuration = 4000
  }

  /**
   * Crear contenedor de notificaciones
   */
  createContainer() {
    if (document.getElementById('notification-container')) {
      this.container = document.getElementById('notification-container')
      return
    }

    this.container = document.createElement('div')
    this.container.id = 'notification-container'
    this.container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 400px;
      pointer-events: none;
    `
    document.body.appendChild(this.container)
  }

  /**
   * Mostrar notificación
   */
  show(message, type = 'info', duration = null) {
    const notification = this.createNotificationElement(message, type)
    this.container.appendChild(notification)
    
    notification.style.pointerEvents = 'auto'
    
    const finalDuration = duration || this.defaultDuration
    
    setTimeout(() => {
      this.removeNotification(notification)
    }, finalDuration)

    // Click para cerrar
    notification.addEventListener('click', () => {
      this.removeNotification(notification)
    })

    return notification
  }

  /**
   * Crear elemento de notificación
   */
  createNotificationElement(message, type) {
    const notification = document.createElement('div')
    
    // Clases y colores según tipo
    const typeConfig = {
      'success': {
        icon: '✓',
        bgColor: '#10b981',
        borderColor: '#059669'
      },
      'error': {
        icon: '✕',
        bgColor: '#ef4444',
        borderColor: '#dc2626'
      },
      'warning': {
        icon: '⚠',
        bgColor: '#f59e0b',
        borderColor: '#d97706'
      },
      'info': {
        icon: 'ℹ',
        bgColor: '#3b82f6',
        borderColor: '#1d4ed8'
      },
      'loading': {
        icon: '⏳',
        bgColor: '#6366f1',
        borderColor: '#4f46e5'
      }
    }

    const config = typeConfig[type] || typeConfig['info']

    notification.className = `notification notification-${type}`
    notification.style.cssText = `
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      background-color: ${config.bgColor};
      border-left: 4px solid ${config.borderColor};
      border-radius: 4px;
      color: white;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      font-size: 14px;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      animation: slideInRight 0.3s ease-out;
      cursor: pointer;
      transition: all 0.3s ease;
      min-width: 250px;
    `

    const icon = document.createElement('span')
    icon.style.cssText = `
      font-size: 18px;
      font-weight: bold;
      min-width: 24px;
      text-align: center;
    `
    icon.textContent = config.icon

    const text = document.createElement('span')
    text.style.cssText = `
      flex: 1;
      word-break: break-word;
    `
    text.textContent = message

    const closeBtn = document.createElement('button')
    closeBtn.style.cssText = `
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 18px;
      padding: 0;
      display: flex;
      align-items: center;
      opacity: 0.7;
      transition: opacity 0.2s;
    `
    closeBtn.innerHTML = '×'
    closeBtn.addEventListener('mouseover', () => closeBtn.style.opacity = '1')
    closeBtn.addEventListener('mouseout', () => closeBtn.style.opacity = '0.7')
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation()
      this.removeNotification(notification)
    })

    notification.appendChild(icon)
    notification.appendChild(text)
    notification.appendChild(closeBtn)

    // Hover effect
    notification.addEventListener('mouseover', () => {
      notification.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)'
      notification.style.transform = 'translateX(-5px)'
    })

    notification.addEventListener('mouseout', () => {
      notification.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)'
      notification.style.transform = 'translateX(0)'
    })

    return notification
  }

  /**
   * Remover notificación
   */
  removeNotification(notification) {
    notification.style.animation = 'slideOutRight 0.3s ease-out'
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 300)
  }

  /**
   * Notificación de éxito
   */
  success(message, duration = null) {
    return this.show(message, 'success', duration)
  }

  /**
   * Notificación de error
   */
  error(message, duration = null) {
    return this.show(message, 'error', duration || 6000)
  }

  /**
   * Notificación de advertencia
   */
  warning(message, duration = null) {
    return this.show(message, 'warning', duration || 5000)
  }

  /**
   * Notificación de información
   */
  info(message, duration = null) {
    return this.show(message, 'info', duration)
  }

  /**
   * Mostrar loading
   * ✅ MEJORADO: Actualiza notificación existente en lugar de crear nuevas
   */
  loading(message = 'Cargando...') {
    // ✅ NUEVO: Buscar si ya existe una notificación de loading
    const existingLoading = this.container.querySelector('[data-is-loading="true"]')
    
    if (existingLoading) {
      // ✅ Actualizar solo el mensaje de la notificación existente
      const messageSpan = existingLoading.querySelector('span:last-child')
      if (messageSpan) {
        messageSpan.textContent = message
      }
      return existingLoading
    }
    
    // ✅ Si no existe, crear una nueva
    const notification = this.createNotificationElement(message, 'loading')
    
    // Agregar spinner animado
    const spinner = document.createElement('div')
    spinner.style.cssText = `
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top: 2px solid white;
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
      margin: -2px 6px 0 -6px;
    `
    
    notification.insertBefore(spinner, notification.querySelector('span:nth-child(2)'))
    this.container.appendChild(notification)
    
    notification.dataset.isLoading = 'true'
    return notification
  }

  /**
   * Ocultar loading
   */
  hideLoading() {
    const loadingNotif = this.container.querySelector('[data-is-loading="true"]')
    if (loadingNotif) {
      this.removeNotification(loadingNotif)
    }
  }

  /**
   * Limpiar todas las notificaciones
   */
  clearAll() {
    while (this.container.firstChild) {
      this.container.removeChild(this.container.firstChild)
    }
  }

  /**
   * Toast - notificación temporal sin close button
   */
  toast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div')
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 10000;
      background-color: rgba(0, 0, 0, 0.9);
      color: white;
      padding: 12px 24px;
      border-radius: 4px;
      font-size: 14px;
      animation: slideInUp 0.3s ease-out;
    `
    toast.textContent = message
    document.body.appendChild(toast)

    setTimeout(() => {
      toast.style.animation = 'slideOutDown 0.3s ease-out'
      setTimeout(() => {
        document.body.removeChild(toast)
      }, 300)
    }, duration)
  }
}

// Crear instancia global
const notificationManager = new NotificationManager()

// Agregar estilos de animaciones si no existen
if (!document.getElementById('notification-animations')) {
  const style = document.createElement('style')
  style.id = 'notification-animations'
  style.textContent = `
    @keyframes slideInRight {
      from {
        opacity: 0;
        transform: translateX(400px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    @keyframes slideOutRight {
      from {
        opacity: 1;
        transform: translateX(0);
      }
      to {
        opacity: 0;
        transform: translateX(400px);
      }
    }

    @keyframes slideInUp {
      from {
        opacity: 0;
        transform: translateY(100px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes slideOutDown {
      from {
        opacity: 1;
        transform: translateY(0);
      }
      to {
        opacity: 0;
        transform: translateY(100px);
      }
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
  `
  document.head.appendChild(style)
}
