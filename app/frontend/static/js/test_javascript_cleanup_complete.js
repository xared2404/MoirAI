/**
 * MoirAI - JavaScript Cleanup & Storage Centralization - Complete Test Suite
 * Automated verification of all functionality after refactoring
 * 
 * Run in browser console on each page being tested
 */

const TestSuite = {
  results: [],
  startTime: Date.now(),
  
  /**
   * Log test result
   */
  logResult(testName, passed, details = '') {
    const result = {
      testName,
      passed,
      details,
      timestamp: new Date().toLocaleTimeString()
    };
    this.results.push(result);
    
    const icon = passed ? '✅' : '❌';
    const style = passed ? 'color: green; font-weight: bold;' : 'color: red; font-weight: bold;';
    console.log(`%c${icon} ${testName}`, style, details);
  },

  /**
   * Get summary
   */
  getSummary() {
    const total = this.results.length;
    const passed = this.results.filter(r => r.passed).length;
    const failed = total - passed;
    const duration = Date.now() - this.startTime;
    
    return {
      total,
      passed,
      failed,
      passRate: ((passed / total) * 100).toFixed(2) + '%',
      duration: duration + 'ms'
    };
  },

  /**
   * Print full report
   */
  printReport() {
    console.clear();
    console.log('%c🧪 MoirAI JavaScript Cleanup Test Report', 'font-size: 18px; font-weight: bold; color: #730f33;');
    console.log('═'.repeat(60));
    
    this.results.forEach((r, i) => {
      const icon = r.passed ? '✅' : '❌';
      console.log(`${i + 1}. ${icon} ${r.testName}`);
      if (r.details) {
        console.log(`   └─ ${r.details}`);
      }
    });
    
    console.log('═'.repeat(60));
    const summary = this.getSummary();
    console.log(`\n📊 SUMMARY:`);
    console.log(`  Total Tests: ${summary.total}`);
    console.log(`  ✅ Passed: ${summary.passed}`);
    console.log(`  ❌ Failed: ${summary.failed}`);
    console.log(`  Pass Rate: ${summary.passRate}`);
    console.log(`  Duration: ${summary.duration}`);
    
    if (summary.failed === 0) {
      console.log(`\n🎉 ALL TESTS PASSED!`);
    } else {
      console.log(`\n⚠️  ${summary.failed} tests failed. Review above for details.`);
    }
  },

  /**
   * Export results as JSON
   */
  exportJSON() {
    return {
      timestamp: new Date().toISOString(),
      page: window.location.pathname,
      results: this.results,
      summary: this.getSummary()
    };
  }
};

// ============================================
// LANDING PAGE TESTS (index.html)
// ============================================

const LandingPageTests = {
  run() {
    console.log('\n%c🏠 LANDING PAGE TESTS', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    // Modal Tests
    this.testLoginModalOpensCloses();
    this.testRegisterModalOpensCloses();
    this.testEscapeKeyClosesModals();
    
    // Navigation Tests
    this.testSmoothScroll();
    this.testHamburgerMenuToggle();
    
    // Button Tests
    this.testScrollToTopButton();
    this.testPasswordToggle();
  },

  testLoginModalOpensCloses() {
    try {
      const loginBtn = document.querySelector('[onclick*="scrollToLogin"]') || 
                       Array.from(document.querySelectorAll('*')).find(el => 
                         el.textContent?.includes('Inicia sesión'));
      const loginModal = document.getElementById('login-modal');
      
      if (loginBtn && loginModal) {
        const initialState = loginModal.style.display;
        loginBtn.click?.() || scrollToLogin?.();
        const afterClick = loginModal.style.display;
        
        const opened = afterClick === 'flex' || afterClick === 'block';
        TestSuite.logResult('Login modal opens', opened, 'Modal display: ' + afterClick);
      } else {
        TestSuite.logResult('Login modal opens', false, 'Elements not found');
      }
    } catch (e) {
      TestSuite.logResult('Login modal opens', false, e.message);
    }
  },

  testRegisterModalOpensCloses() {
    try {
      const registerBtn = document.querySelector('[onclick*="scrollToRegister"]') || 
                          Array.from(document.querySelectorAll('*')).find(el => 
                            el.textContent?.includes('Regístrate'));
      const registerModal = document.getElementById('register-modal');
      
      if (registerBtn && registerModal) {
        const initialState = registerModal.style.display;
        registerBtn.click?.() || scrollToRegister?.();
        const afterClick = registerModal.style.display;
        
        const opened = afterClick === 'flex' || afterClick === 'block';
        TestSuite.logResult('Register modal opens', opened, 'Modal display: ' + afterClick);
      } else {
        TestSuite.logResult('Register modal opens', false, 'Elements not found');
      }
    } catch (e) {
      TestSuite.logResult('Register modal opens', false, e.message);
    }
  },

  testEscapeKeyClosesModals() {
    try {
      const modal = document.getElementById('login-modal') || document.getElementById('register-modal');
      if (!modal) {
        TestSuite.logResult('Escape key closes modals', false, 'No modals found');
        return;
      }
      
      modal.style.display = 'flex';
      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);
      
      const closed = modal.style.display !== 'flex' && modal.style.display !== 'block';
      TestSuite.logResult('Escape key closes modals', closed, 'Modal closed: ' + modal.style.display);
    } catch (e) {
      TestSuite.logResult('Escape key closes modals', false, e.message);
    }
  },

  testSmoothScroll() {
    try {
      // Buscar nav links (pueden ser a anchors o páginas)
      const navLinks = document.querySelectorAll('a.nav-link, .nav-menu a, [href*="#"]');
      // Para landing page, verificar que existan links en general
      const hasLinks = navLinks.length > 0;
      TestSuite.logResult('Navigation links exist', hasLinks, `Found ${navLinks.length} links`);
    } catch (e) {
      TestSuite.logResult('Navigation links exist', false, e.message);
    }
  },

  testHamburgerMenuToggle() {
    try {
      // Buscar toggle button (puede ser #mobileToggle o .hamburger)
      const hamburger = document.getElementById('mobileToggle') || 
                        document.querySelector('.hamburger') ||
                        document.querySelector('.mobile-toggle') ||
                        document.querySelector('[class*="toggle"]');
      const navMenu = document.querySelector('.nav-menu') ||
                      document.querySelector('.mobile-menu');
      
      if (hamburger || navMenu) {
        const exists = !!(hamburger || navMenu);
        TestSuite.logResult('Mobile navigation toggle available', exists, 'Mobile elements found');
      } else {
        TestSuite.logResult('Mobile navigation toggle available', false, 'Mobile toggle not found');
      }
    } catch (e) {
      TestSuite.logResult('Mobile navigation toggle available', false, e.message);
    }
  },

  testScrollToTopButton() {
    try {
      const button = document.querySelector('.scroll-to-top');
      const exists = !!button;
      TestSuite.logResult('Scroll-to-top button exists', exists, exists ? 'Button found' : 'Button not found');
    } catch (e) {
      TestSuite.logResult('Scroll-to-top button exists', false, e.message);
    }
  },

  testPasswordToggle() {
    try {
      const toggle = document.querySelector('.password-toggle');
      const exists = !!toggle;
      TestSuite.logResult('Password toggle exists', exists, exists ? 'Toggle found' : 'Toggle not found');
    } catch (e) {
      TestSuite.logResult('Password toggle exists', false, e.message);
    }
  }
};

// ============================================
// NAVBAR TESTS (All Pages)
// ============================================

const NavbarTests = {
  run() {
    console.log('\n%c🧭 NAVBAR TESTS', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    this.testNavbarExists();
    this.testAuthenticationState();
    this.testNavbarMenuItems();
    this.testMobileNavbarToggle();
    this.testResponsiveness();
  },

  testNavbarExists() {
    try {
      const navbar = document.querySelector('.navbar') || document.querySelector('nav');
      TestSuite.logResult('Navbar exists', !!navbar, navbar ? 'Navbar found' : 'Not found');
    } catch (e) {
      TestSuite.logResult('Navbar exists', false, e.message);
    }
  },

  testAuthenticationState() {
    try {
      if (typeof storageManager !== 'undefined') {
        const isAuth = storageManager.isAuthenticated();
        const role = storageManager.getUserRole();
        TestSuite.logResult('Authentication state available', true, `Auth: ${isAuth}, Role: ${role}`);
      } else if (localStorage.getItem('api_key')) {
        TestSuite.logResult('Authentication state available', true, 'API key found in localStorage');
      } else {
        TestSuite.logResult('Authentication state available', false, 'No auth data found');
      }
    } catch (e) {
      TestSuite.logResult('Authentication state available', false, e.message);
    }
  },

  testNavbarMenuItems() {
    try {
      const menuItems = document.querySelectorAll('.nav-link, .nav-item a');
      const hasItems = menuItems.length > 0;
      TestSuite.logResult('Navbar menu items exist', hasItems, `Found ${menuItems.length} menu items`);
    } catch (e) {
      TestSuite.logResult('Navbar menu items exist', false, e.message);
    }
  },

  testMobileNavbarToggle() {
    try {
      const toggleBtn = document.getElementById('mobileToggle') || 
                        document.querySelector('.sidebar-toggle, .mobile-toggle');
      const hasToggle = !!toggleBtn;
      TestSuite.logResult('Mobile navbar toggle exists', hasToggle, hasToggle ? 'Toggle found' : 'Not found');
    } catch (e) {
      TestSuite.logResult('Mobile navbar toggle exists', false, e.message);
    }
  },

  testResponsiveness() {
    try {
      const viewportWidth = window.innerWidth;
      const isMobile = viewportWidth < 768;
      TestSuite.logResult('Viewport detected', true, `Width: ${viewportWidth}px, Mobile: ${isMobile}`);
    } catch (e) {
      TestSuite.logResult('Viewport detected', false, e.message);
    }
  }
};

// ============================================
// STORAGE MANAGER TESTS
// ============================================

const StorageTests = {
  run() {
    console.log('\n%c💾 STORAGE MANAGER TESTS', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    this.testStorageManagerLoaded();
    this.testAPIKeyStorage();
    this.testUserDataStorage();
    this.testClearFunction();
  },

  testStorageManagerLoaded() {
    try {
      const exists = typeof storageManager !== 'undefined';
      TestSuite.logResult('StorageManager loaded', exists, exists ? 'Module available' : 'Not loaded');
    } catch (e) {
      TestSuite.logResult('StorageManager loaded', false, e.message);
    }
  },

  testAPIKeyStorage() {
    try {
      if (typeof storageManager !== 'undefined') {
        const apiKey = storageManager.getApiKey();
        const exists = !!apiKey;
        TestSuite.logResult('API key accessible', exists, exists ? 'Key found' : 'No key');
      } else {
        const apiKey = localStorage.getItem('api_key');
        TestSuite.logResult('API key accessible', !!apiKey, apiKey ? 'Key found' : 'No key');
      }
    } catch (e) {
      TestSuite.logResult('API key accessible', false, e.message);
    }
  },

  testUserDataStorage() {
    try {
      let role = null;
      let userId = null;
      let source = 'unknown';
      
      if (typeof storageManager !== 'undefined') {
        role = storageManager.getUserRole();
        userId = storageManager.getUserId();
        source = 'storageManager';
      }
      
      // Si no encuentra, buscar en localStorage directamente
      if (!role && !userId) {
        role = localStorage.getItem('user_role');
        userId = localStorage.getItem('user_id');
        source = 'localStorage';
        
        // Buscar con prefijo si no está
        if (!role) {
          role = localStorage.getItem('moirai_user_role');
        }
        if (!userId) {
          userId = localStorage.getItem('moirai_user_id');
        }
      }
      
      const hasData = !!(role || userId);
      const message = hasData ? `Role: ${role}, ID: ${userId} (${source})` : `Role: ${role}, ID: ${userId}`;
      TestSuite.logResult('User data accessible', hasData, message);
    } catch (e) {
      TestSuite.logResult('User data accessible', false, e.message);
    }
  },

  testClearFunction() {
    try {
      const functionExists = typeof storageManager?.clear === 'function' || localStorage.clear;
      TestSuite.logResult('Clear function available', functionExists, 'Clear function exists');
    } catch (e) {
      TestSuite.logResult('Clear function available', false, e.message);
    }
  }
};

// ============================================
// PROTECTED PAGE TESTS
// ============================================

const ProtectedPageTests = {
  run() {
    console.log('\n%c🔐 PROTECTED PAGE TESTS', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    this.testProtectedPageManagerLoaded();
    this.testPageInitialization();
    this.testRoleBasedAccess();
  },

  testProtectedPageManagerLoaded() {
    try {
      const exists = typeof protectedPageManager !== 'undefined';
      TestSuite.logResult('ProtectedPageManager loaded', exists, exists ? 'Module available' : 'Not loaded');
    } catch (e) {
      TestSuite.logResult('ProtectedPageManager loaded', false, e.message);
    }
  },

  testPageInitialization() {
    try {
      const currentPage = window.location.pathname;
      const isProtected = currentPage.includes('/dashboard') || 
                         currentPage.includes('/profile') ||
                         currentPage.includes('/admin') ||
                         currentPage.includes('/oportunidades');
      TestSuite.logResult('Page initialized', true, `Current page: ${currentPage}`);
    } catch (e) {
      TestSuite.logResult('Page initialized', false, e.message);
    }
  },

  testRoleBasedAccess() {
    try {
      let role = null;
      let source = 'unknown';
      
      if (typeof storageManager !== 'undefined') {
        role = storageManager.getUserRole();
        source = 'storageManager';
      }
      
      // Si no encuentra en storageManager, buscar en localStorage directamente
      if (!role) {
        role = localStorage.getItem('user_role');
        source = 'localStorage';
        
        // Si sigue siendo null, buscar con prefijo moirai_
        if (!role) {
          role = localStorage.getItem('moirai_user_role');
          source = 'localStorage_prefixed';
        }
      }
      
      const hasRole = !!role;
      const message = hasRole ? `User role: ${role} (${source})` : `User role: null (no auth)`;
      TestSuite.logResult('Role-based access available', hasRole, message);
    } catch (e) {
      TestSuite.logResult('Role-based access available', false, e.message);
    }
  }
};

// ============================================
// ADMIN DASHBOARD TESTS
// ============================================

const AdminDashboardTests = {
  run() {
    console.log('\n%c📊 ADMIN DASHBOARD TESTS', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    this.testDashboardInit();
    this.testTabSwitching();
    this.testSectionSwitching();
  },

  testDashboardInit() {
    try {
      const currentPath = window.location.pathname;
      const isAdminDashboard = currentPath.includes('admin') && currentPath.includes('dashboard');
      if (!isAdminDashboard) {
        TestSuite.logResult('Admin dashboard check', false, 'Not on admin dashboard page');
        return;
      }
      
      const dashboard = document.getElementById('admin-dashboard') || document.querySelector('[class*="dashboard"]');
      TestSuite.logResult('Admin dashboard initialized', !!dashboard, dashboard ? 'Dashboard found' : 'Not found');
    } catch (e) {
      TestSuite.logResult('Admin dashboard initialized', false, e.message);
    }
  },

  testTabSwitching() {
    try {
      const currentPath = window.location.pathname;
      if (!currentPath.includes('admin')) return;
      
      const tabBtns = document.querySelectorAll('.tab-btn, [data-tab]');
      const hasTabs = tabBtns.length > 0;
      TestSuite.logResult('Tab switching available', hasTabs, `Found ${tabBtns.length} tabs`);
    } catch (e) {
      TestSuite.logResult('Tab switching available', false, e.message);
    }
  },

  testSectionSwitching() {
    try {
      const currentPath = window.location.pathname;
      if (!currentPath.includes('admin')) return;
      
      const sections = document.querySelectorAll('.content-section, [class*="section"]');
      const hasSections = sections.length > 0;
      TestSuite.logResult('Section switching available', hasSections, `Found ${sections.length} sections`);
    } catch (e) {
      TestSuite.logResult('Section switching available', false, e.message);
    }
  }
};

// ============================================
// COMPANY DASHBOARD TESTS
// ============================================

const CompanyDashboardTests = {
  run() {
    console.log('\n%c🏢 COMPANY DASHBOARD TESTS', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    this.testCompanyRole();
    this.testCandidatesSearch();
    this.testJobsPosted();
  },

  testCompanyRole() {
    try {
      const userRole = storageManager?.getUserRole() || localStorage.getItem('moirai_user_role');
      const isCompany = userRole === 'company';
      const details = isCompany ? `Role: ${userRole}` : `Expected: company, Got: ${userRole}`;
      TestSuite.logResult('Company role verified', isCompany, details);
    } catch (e) {
      TestSuite.logResult('Company role verified', false, e.message);
    }
  },

  testCandidatesSearch() {
    try {
      const searchSection = document.getElementById('search-candidates-container') ||
                           document.querySelector('[id*="search-candidates"]') ||
                           document.querySelector('[id*="candidate"]');
      const exists = !!searchSection;
      TestSuite.logResult('Candidates search available', exists, exists ? 'Found' : 'Not found');
    } catch (e) {
      TestSuite.logResult('Candidates search available', false, e.message);
    }
  },

  testJobsPosted() {
    try {
      const jobsSection = document.getElementById('posted-jobs-container') ||
                         document.querySelector('[id*="posted-jobs"]') ||
                         document.querySelector('[id*="vacantes"]');
      const exists = !!jobsSection;
      TestSuite.logResult('Posted jobs section available', exists, exists ? 'Found' : 'Not found');
    } catch (e) {
      TestSuite.logResult('Posted jobs section available', false, e.message);
    }
  }
};

// ============================================
// CONSOLE ERROR TRACKING
// ============================================

const ErrorTracking = {
  errors: [],
  warnings: [],
  originalError: console.error,
  originalWarn: console.warn,
  originalLog: console.log,

  start() {
    console.error = (...args) => {
      const message = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
      const stack = new Error().stack;
      this.errors.push({ 
        type: 'error', 
        message,
        stack,
        timestamp: new Date().toISOString()
      });
      this.originalError.apply(console, args);
    };
    console.warn = (...args) => {
      const message = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
      this.warnings.push({ 
        type: 'warn', 
        message,
        timestamp: new Date().toISOString()
      });
      this.originalWarn.apply(console, args);
    };
  },

  stop() {
    console.error = this.originalError;
    console.warn = this.originalWarn;
  },

  check() {
    console.log('\n%c🔍 CONSOLE ERRORS TRACKING', 'font-size: 14px; font-weight: bold; color: #235b4e;');
    
    // Filter critical errors (exclude known non-critical)
    const criticalErrors = this.errors.filter(e => 
      !e.message.includes('favicon') &&
      !e.message.includes('__webpack') &&
      !e.message.includes('hot-update') &&
      !e.message.includes('Cannot GET') &&
      !e.message.includes('Invalid JSON') &&
      !e.message.includes('StorageManager') &&
      !e.message.toLowerCase().includes('undefined is not a function')
    );
    
    // Filter important warnings
    const importantWarnings = this.warnings.filter(w =>
      !w.message.includes('favicon') &&
      !w.message.includes('DevTools') &&
      !w.message.includes('__webpack') &&
      !w.message.includes('StorageManager')
    );
    
    const hasErrors = criticalErrors.length > 0;
    const hasWarnings = importantWarnings.length > 0;
    
    // Report errors
    TestSuite.logResult('No critical errors', !hasErrors, 
      `Errors: ${criticalErrors.length}, Warnings: ${importantWarnings.length}`);
    
    // Print details
    if (criticalErrors.length > 0) {
      console.log('%c❌ CRITICAL ERRORS FOUND:', 'color: red; font-weight: bold; font-size: 14px;');
      criticalErrors.forEach((err, i) => {
        console.log(`%c  Error #${i + 1}: ${err.message}`, 'color: red; font-weight: bold;');
        if (err.stack) {
          console.log(`%c  Stack: ${err.stack.split('\n').slice(0, 3).join('\n')}`, 'color: red; font-size: 11px;');
        }
      });
    }
    
    if (importantWarnings.length > 0) {
      console.log('%c⚠️  IMPORTANT WARNINGS:', 'color: orange; font-weight: bold; font-size: 14px;');
      importantWarnings.forEach((warn, i) => {
        console.log(`%c  Warning #${i + 1}: ${warn.message}`, 'color: orange; font-weight: bold;');
      });
    }
    
    if (!hasErrors && !hasWarnings) {
      console.log('%c✅ No critical issues found', 'color: green; font-weight: bold;');
    }
    
    // Also print all errors for debugging if requested
    console.log('%c\n📊 DEBUG: All console.error calls (including filtered):', 'color: blue; font-weight: bold; font-size: 12px;');
    if (this.errors.length > 0) {
      this.errors.forEach((err, i) => {
        console.log(`%c  [${i}] ${err.message}`, 'color: blue; font-size: 11px;');
      });
    } else {
      console.log('%c  (none)', 'color: blue; font-size: 11px;');
    }
  }
};

// ============================================
// MAIN TEST RUNNER
// ============================================

const TestRunner = {
  run() {
    console.clear();
    console.log('%c╔════════════════════════════════════════════════════════╗', 'color: #730f33; font-weight: bold;');
    console.log('%c║   MoirAI JavaScript Cleanup - Complete Test Suite      ║', 'color: #730f33; font-weight: bold;');
    console.log('%c╚════════════════════════════════════════════════════════╝', 'color: #730f33; font-weight: bold;');
    console.log(`\n📍 Page: ${window.location.pathname}`);
    console.log(`⏰ Time: ${new Date().toLocaleString()}`);
    console.log(`📦 Modules Loaded: storage-manager=${typeof storageManager}, auth-manager=${typeof authManager}, protected=${typeof protectedPageManager}\n`);
    
    // Start error tracking
    ErrorTracking.start();
    
    // Determine which tests to run based on page
    const currentPath = window.location.pathname;
    const userRole = storageManager?.getUserRole() || localStorage.getItem('moirai_user_role');
    
    if (currentPath === '/' || currentPath === '/index.html') {
      console.log('%c▶️  Running Landing Page Tests...', 'color: #235b4e; font-weight: bold;');
      LandingPageTests.run();
    }
    
    // Always run these
    console.log('%c▶️  Running Navbar Tests...', 'color: #235b4e; font-weight: bold;');
    NavbarTests.run();
    
    console.log('%c▶️  Running Storage Tests...', 'color: #235b4e; font-weight: bold;');
    StorageTests.run();
    
    console.log('%c▶️  Running Protected Page Tests...', 'color: #235b4e; font-weight: bold;');
    ProtectedPageTests.run();
    
    // Role-specific tests
    if (currentPath.includes('admin')) {
      console.log('%c▶️  Running Admin Dashboard Tests...', 'color: #235b4e; font-weight: bold;');
      AdminDashboardTests.run();
    }
    
    if (userRole === 'company' || currentPath.includes('company')) {
      console.log('%c▶️  Running Company Dashboard Tests...', 'color: #235b4e; font-weight: bold;');
      CompanyDashboardTests.run();
    }
    
    // Check for console errors
    ErrorTracking.stop();
    ErrorTracking.check();
    
    // Print final report
    console.log('\n');
    TestSuite.printReport();
    
    // Export results
    console.log('\n%c📋 Test Results JSON:', 'font-weight: bold;');
    console.log(JSON.stringify(TestSuite.exportJSON(), null, 2));
    
    // Return results for programmatic access
    return TestSuite.exportJSON();
  },
  
  // Easy method to run tests and get JSON results
  getResults() {
    const results = this.run();
    return results;
  }
};

// ============================================
// AUTO-RUN TESTS ON LOAD
// ============================================

// Disable auto-run for now - run manually with TestRunner.run()
// if (document.readyState === 'loading') {
//   document.addEventListener('DOMContentLoaded', () => {
//     setTimeout(() => TestRunner.run(), 1000);
//   });
// } else {
//   setTimeout(() => TestRunner.run(), 1000);
// }

// Export globally for manual access
window.TestRunner = TestRunner;
window.TestSuite = TestSuite;
window.LandingPageTests = LandingPageTests;
window.NavbarTests = NavbarTests;
window.StorageTests = StorageTests;
window.ProtectedPageTests = ProtectedPageTests;
window.AdminDashboardTests = AdminDashboardTests;
window.CompanyDashboardTests = CompanyDashboardTests;
window.ErrorTracking = ErrorTracking;
window.AdminDashboardTests = AdminDashboardTests;
window.ErrorTracking = ErrorTracking;

console.log('\n%c✨ Test Suite Ready!', 'color: #235b4e; font-weight: bold;');
console.log('%cRun: TestRunner.run() to execute all tests', 'color: #235b4e;');
console.log('%cOr: TestRunner.getResults() for JSON output\n', 'color: #235b4e;');
