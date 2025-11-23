/**
 * MoirAI - Automated Navigation & Console Capture
 * 
 * Automatiza la navegación por todas las páginas respetando roles
 * y captura todos los logs de consola, errores y warnings
 * 
 * Uso:
 *   // En la consola del navegador
 *   await NavigationCaptureSystem.runFullNavigationTest('student')
 *   await NavigationCaptureSystem.runFullNavigationTest('company')
 *   await NavigationCaptureSystem.runFullNavigationTest('admin')
 */

class NavigationCaptureSystem {
  static config = {
    baseUrl: 'http://localhost:8000',
    waitBetweenPages: 2000, // ms para esperar que la página cargue
    waitForAPI: 3000,       // ms para que las APIs respondan
    captureScreenshots: false,
  };

  static consoleLogs = {
    logs: [],
    errors: [],
    warnings: [],
    apiCalls: [],
  };

  static navigationPaths = {
    student: [
      '/',
      '/dashboard',
      '/oportunidades',
      '/mis-vacantes',
      '/empresas',
      '/profile',
    ],
    company: [
      '/',
      '/dashboard',
      '/mis-vacantes',
      '/buscar-candidatos',
      '/profile',
    ],
    admin: [
      '/',
      '/dashboard',
      '/admin/dashboard',
      '/admin/users',
      '/admin/analytics',
    ],
  };

  /**
   * Inicializar sistema de captura
   */
  static initialize() {
    this.interceptConsole();
    this.interceptFetch();
    this.interceptXHR();
    console.log('%c✅ Navigation Capture System initialized', 'color: green; font-weight: bold;');
  }

  /**
   * Interceptar console methods
   */
  static interceptConsole() {
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;
    const originalDebug = console.debug;

    console.log = (...args) => {
      this.consoleLogs.logs.push({
        timestamp: new Date().toISOString(),
        type: 'log',
        message: args.map(arg => this.stringifyArg(arg)).join(' '),
        args: args,
      });
      return originalLog.apply(console, args);
    };

    console.error = (...args) => {
      this.consoleLogs.errors.push({
        timestamp: new Date().toISOString(),
        type: 'error',
        message: args.map(arg => this.stringifyArg(arg)).join(' '),
        args: args,
        stack: new Error().stack,
      });
      return originalError.apply(console, args);
    };

    console.warn = (...args) => {
      this.consoleLogs.warnings.push({
        timestamp: new Date().toISOString(),
        type: 'warning',
        message: args.map(arg => this.stringifyArg(arg)).join(' '),
        args: args,
      });
      return originalWarn.apply(console, args);
    };

    console.info = (...args) => {
      this.consoleLogs.logs.push({
        timestamp: new Date().toISOString(),
        type: 'info',
        message: args.map(arg => this.stringifyArg(arg)).join(' '),
        args: args,
      });
      return originalInfo.apply(console, args);
    };

    console.debug = (...args) => {
      this.consoleLogs.logs.push({
        timestamp: new Date().toISOString(),
        type: 'debug',
        message: args.map(arg => this.stringifyArg(arg)).join(' '),
        args: args,
      });
      return originalDebug.apply(console, args);
    };
  }

  /**
   * Interceptar llamadas fetch
   */
  static interceptFetch() {
    const originalFetch = window.fetch;

    window.fetch = async (...args) => {
      const url = args[0];
      const options = args[1] || {};
      const startTime = performance.now();

      try {
        const response = await originalFetch.apply(window, args);
        const duration = performance.now() - startTime;

        this.consoleLogs.apiCalls.push({
          timestamp: new Date().toISOString(),
          type: 'fetch',
          method: options.method || 'GET',
          url: url.toString(),
          status: response.status,
          duration: duration.toFixed(2),
          statusText: response.statusText,
        });

        return response;
      } catch (error) {
        const duration = performance.now() - startTime;

        this.consoleLogs.apiCalls.push({
          timestamp: new Date().toISOString(),
          type: 'fetch',
          method: options.method || 'GET',
          url: url.toString(),
          status: 'ERROR',
          duration: duration.toFixed(2),
          error: error.message,
        });

        throw error;
      }
    };
  }

  /**
   * Interceptar XMLHttpRequest
   */
  static interceptXHR() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url) {
      this._requestInfo = { method, url, startTime: performance.now() };
      return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function (data) {
      const self = this;
      const onReadyStateChange = this.onreadystatechange;

      this.onreadystatechange = function () {
        if (self.readyState === 4) {
          const duration = performance.now() - self._requestInfo.startTime;

          NavigationCaptureSystem.consoleLogs.apiCalls.push({
            timestamp: new Date().toISOString(),
            type: 'xhr',
            method: self._requestInfo.method,
            url: self._requestInfo.url,
            status: self.status,
            duration: duration.toFixed(2),
            statusText: self.statusText,
          });
        }

        if (onReadyStateChange) {
          return onReadyStateChange.apply(this, arguments);
        }
      };

      return originalSend.apply(this, arguments);
    };
  }

  /**
   * Convertir argumentos a string
   */
  static stringifyArg(arg) {
    if (typeof arg === 'string') return arg;
    if (typeof arg === 'object') {
      try {
        return JSON.stringify(arg, null, 2);
      } catch (e) {
        return String(arg);
      }
    }
    return String(arg);
  }

  /**
   * Simular login
   */
  static async loginAs(role) {
    console.log(`%c🔐 Logging in as: ${role}`, 'color: blue; font-weight: bold;');

    // Simular credenciales según role
    const credentials = {
      student: {
        email: 'student@unrc.edu.ar',
        password: 'Test@1234',
        role: 'student',
      },
      company: {
        email: 'company@example.com',
        password: 'Test@1234',
        role: 'company',
      },
      admin: {
        email: 'admin@unrc.edu.ar',
        password: 'Test@1234',
        role: 'admin',
      },
    };

    const cred = credentials[role];
    if (!cred) {
      throw new Error(`Unknown role: ${role}`);
    }

    try {
      // Intentar login
      const response = await fetch(`${this.config.baseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: cred.email,
          password: cred.password,
        }),
      });

      if (!response.ok) {
        console.warn(`⚠️  Login failed with status ${response.status}`);
        // Simular login guardando datos en localStorage
        if (typeof storageManager !== 'undefined') {
          storageManager.setUserRole(role);
          storageManager.setAPIKey(`test-api-key-${role}`);
          storageManager.setUserEmail(cred.email);
        } else {
          localStorage.setItem('user_role', role);
          localStorage.setItem('api_key', `test-api-key-${role}`);
          localStorage.setItem('user_email', cred.email);
        }
      } else {
        const data = await response.json();
        if (typeof storageManager !== 'undefined') {
          storageManager.setUserRole(data.role || role);
          storageManager.setAPIKey(data.api_key);
          storageManager.setUserEmail(data.email);
        } else {
          localStorage.setItem('user_role', data.role || role);
          localStorage.setItem('api_key', data.api_key);
          localStorage.setItem('user_email', data.email);
        }
      }

      console.log(`%c✅ Logged in as ${role}`, 'color: green;');
    } catch (error) {
      console.error(`❌ Login error: ${error.message}`);
      // Continuar de todas formas para testing
    }

    // Esperar a que las cookies se procesen
    await this.wait(500);
  }

  /**
   * Esperar tiempo
   */
  static wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Navegar a una página
   */
  static async navigateToPage(path) {
    console.log(`\n%c📍 Navigating to: ${path}`, 'color: #235b4e; font-weight: bold;');

    try {
      // Limpiar logs anteriores pero guardar histórico
      const previousLogs = {
        logs: [...this.consoleLogs.logs],
        errors: [...this.consoleLogs.errors],
        warnings: [...this.consoleLogs.warnings],
        apiCalls: [...this.consoleLogs.apiCalls],
      };

      // Navegar
      window.location.href = `${this.config.baseUrl}${path}`;

      // Esperar a que la página cargue
      await this.wait(this.config.waitBetweenPages);

      // Esperar más para las APIs
      await this.wait(this.config.waitForAPI);

      return previousLogs;
    } catch (error) {
      console.error(`❌ Navigation error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Navegar a una página sin cambiar location (usa iframe o similar)
   */
  static async navigateToPageWithoutReload(path) {
    console.log(`\n%c📍 Navigating to (no reload): ${path}`, 'color: #235b4e; font-weight: bold;');

    try {
      // Usar fetch para cargar la página
      const response = await fetch(`${this.config.baseUrl}${path}`);
      const html = await response.text();

      // Simular que la página se cargó
      document.body.innerHTML = html;

      // Re-ejecutar scripts
      const scripts = document.querySelectorAll('script');
      scripts.forEach(script => {
        const newScript = document.createElement('script');
        newScript.src = script.src;
        newScript.innerHTML = script.innerHTML;
        document.body.appendChild(newScript);
      });

      // Esperar a que se ejecuten
      await this.wait(this.config.waitForAPI);
    } catch (error) {
      console.error(`❌ Navigation error: ${error.message}`);
    }
  }

  /**
   * Capturar los logs de una página
   */
  static capturePageLogs(page, role) {
    return {
      page,
      role,
      timestamp: new Date().toISOString(),
      logs: [...this.consoleLogs.logs],
      errors: [...this.consoleLogs.errors],
      warnings: [...this.consoleLogs.warnings],
      apiCalls: [...this.consoleLogs.apiCalls],
    };
  }

  /**
   * Limpiar logs
   */
  static clearLogs() {
    this.consoleLogs = {
      logs: [],
      errors: [],
      warnings: [],
      apiCalls: [],
    };
  }

  /**
   * Ejecutar navegación completa para un rol
   */
  static async runFullNavigationTest(role) {
    console.clear();
    console.log('%c╔════════════════════════════════════════════════════════╗', 'color: #730f33; font-weight: bold;');
    console.log('%c║  MoirAI - Automated Navigation & Console Capture      ║', 'color: #730f33; font-weight: bold;');
    console.log('%c║  Role: ' + role.toUpperCase().padEnd(47) + '║', 'color: #730f33; font-weight: bold;');
    console.log('%c╚════════════════════════════════════════════════════════╝', 'color: #730f33; font-weight: bold;');

    const startTime = Date.now();
    const navigationResults = [];

    this.initialize();

    try {
      // Step 1: Login
      await this.loginAs(role);

      // Step 2: Navegar por cada página del rol
      const paths = this.navigationPaths[role] || this.navigationPaths.student;

      for (const path of paths) {
        this.clearLogs();

        console.log(`\n%c⏳ Visiting: ${path}`, 'color: #235b4e; font-size: 12px;');

        try {
          // Para la primera página, usar navegación normal
          if (path === '/' && navigationResults.length === 0) {
            window.location.href = `${this.config.baseUrl}${path}`;
            await this.wait(this.config.waitBetweenPages + this.config.waitForAPI);
          } else {
            // Para las demás, intentar sin recargar
            await this.navigateToPageWithoutReload(path);
          }

          // Capturar logs
          const pageCapture = this.capturePageLogs(path, role);
          navigationResults.push(pageCapture);

          console.log(`%c✅ Page loaded: ${path}`, 'color: green; font-size: 12px;');
        } catch (error) {
          console.error(`%c❌ Error loading ${path}: ${error.message}`, 'color: red;');
          navigationResults.push({
            page: path,
            role,
            timestamp: new Date().toISOString(),
            error: error.message,
          });
        }
      }

      // Step 3: Generar reporte
      const duration = Date.now() - startTime;
      const report = this.generateReport(navigationResults, role, duration);

      return report;
    } catch (error) {
      console.error('%c❌ Navigation test failed', 'color: red; font-weight: bold;', error);
      throw error;
    }
  }

  /**
   * Generar reporte de navegación
   */
  static generateReport(navigationResults, role, duration) {
    console.log('\n%c═══════════════════════════════════════════════════════', 'color: #730f33; font-weight: bold;');
    console.log('%c📊 NAVIGATION REPORT - ' + role.toUpperCase(), 'font-size: 14px; font-weight: bold; color: #730f33;');
    console.log('%c═══════════════════════════════════════════════════════', 'color: #730f33; font-weight: bold;');

    let totalErrors = 0;
    let totalWarnings = 0;
    let totalAPIErrors = 0;

    navigationResults.forEach((result, index) => {
      if (result.error) {
        console.log(`\n%c❌ Page ${index + 1}: ${result.page}`, 'color: red; font-weight: bold;');
        console.log(`   Error: ${result.error}`);
      } else {
        console.log(`\n%c✅ Page ${index + 1}: ${result.page}`, 'color: green; font-weight: bold;');

        const errors = result.errors || [];
        const warnings = result.warnings || [];
        const apiCalls = result.apiCalls || [];
        const apiErrors = apiCalls.filter(call => call.status === 'ERROR' || call.status >= 400);

        totalErrors += errors.length;
        totalWarnings += warnings.length;
        totalAPIErrors += apiErrors.length;

        if (errors.length > 0) {
          console.log(`   %c🔴 Console Errors: ${errors.length}`, 'color: red;');
          errors.slice(0, 3).forEach(err => {
            console.log(`      • ${err.message.substring(0, 100)}`);
          });
          if (errors.length > 3) {
            console.log(`      ... and ${errors.length - 3} more`);
          }
        }

        if (warnings.length > 0) {
          console.log(`   %c🟡 Warnings: ${warnings.length}`, 'color: orange;');
          warnings.slice(0, 3).forEach(warn => {
            console.log(`      • ${warn.message.substring(0, 100)}`);
          });
          if (warnings.length > 3) {
            console.log(`      ... and ${warnings.length - 3} more`);
          }
        }

        if (apiErrors.length > 0) {
          console.log(`   %c🌐 API Errors: ${apiErrors.length}`, 'color: #d9534f;');
          apiErrors.slice(0, 3).forEach(call => {
            console.log(`      • ${call.method} ${call.url} [${call.status}]`);
          });
          if (apiErrors.length > 3) {
            console.log(`      ... and ${apiErrors.length - 3} more`);
          }
        }

        if (errors.length === 0 && warnings.length === 0 && apiErrors.length === 0) {
          console.log(`   %c✨ No issues found!`, 'color: green;');
        }
      }
    });

    console.log('\n%c═══════════════════════════════════════════════════════', 'color: #730f33; font-weight: bold;');
    console.log(`%c📈 SUMMARY`, 'font-size: 13px; font-weight: bold; color: #730f33;');
    console.log(`   Pages visited: ${navigationResults.filter(r => !r.error).length}/${navigationResults.length}`);
    console.log(`   Total console errors: ${totalErrors}`);
    console.log(`   Total warnings: ${totalWarnings}`);
    console.log(`   Total API errors: ${totalAPIErrors}`);
    console.log(`   Duration: ${(duration / 1000).toFixed(2)}s`);
    console.log('%c═══════════════════════════════════════════════════════', 'color: #730f33; font-weight: bold;');

    // Exportar resultados
    const fullReport = {
      role,
      timestamp: new Date().toISOString(),
      duration,
      pages: navigationResults,
      summary: {
        totalPages: navigationResults.length,
        successfulPages: navigationResults.filter(r => !r.error).length,
        totalErrors,
        totalWarnings,
        totalAPIErrors,
      },
    };

    console.log('\n%c💾 EXPORT REPORT AS JSON:', 'font-weight: bold; color: #235b4e;');
    console.log(fullReport);

    return fullReport;
  }

  /**
   * Exportar logs a JSON
   */
  static exportAsJSON() {
    return JSON.stringify(this.consoleLogs, null, 2);
  }

  /**
   * Descargar reporte como archivo
   */
  static downloadReport(report, filename = null) {
    const name = filename || `navigation-report-${report.role}-${new Date().toISOString().split('T')[0]}.json`;
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.click();
    console.log(`✅ Report downloaded: ${name}`);
  }
}

// Export globally
window.NavigationCaptureSystem = NavigationCaptureSystem;

console.log('%c✨ Navigation Capture System loaded!', 'color: #235b4e; font-weight: bold; font-size: 14px;');
console.log('%cUsage:', 'font-weight: bold; color: #235b4e;');
console.log('  await NavigationCaptureSystem.runFullNavigationTest("student")');
console.log('  await NavigationCaptureSystem.runFullNavigationTest("company")');
console.log('  await NavigationCaptureSystem.runFullNavigationTest("admin")\n');
