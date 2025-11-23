/**
 * MoirAI - Comprehensive Logout Testing Suite
 * Tests registration, login, and logout for all roles
 * Captures console errors and network issues
 * 
 * Usage: Load this in browser console and run:
 * await runFullLogoutTest()
 */

// ===== CONFIGURATION =====
const API_BASE = window.API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
const TEST_CONFIG = {
    student: {
        email: `student-${Date.now()}@test.com`,
        password: 'TestPassword123!',
        name: 'Test Student',
        program: 'Computer Science',
        role: 'student'
    },
    company: {
        email: `company-${Date.now()}@test.com`,
        password: 'TestPassword123!',
        name: 'Test Company Inc',
        industry: 'Technology',
        company_size: '50-100',
        location: 'Mexico City',
        role: 'company'
    },
    admin: {
        // Using existing admin from .env
        // Admin was created in table admin with email/password (homologated authentication)
        email: 'henryadmin@hotmail.com',
        password: 'Henryadmin369',
        name: 'Henry Admin',
        role: 'admin'
        // No need to skipRegister - admin now uses email/password like others
    }
};

// ===== LOG CAPTURE SYSTEM =====
class LogCapture {
    constructor() {
        this.logs = {
            console: [],
            network: [],
            errors: [],
            warnings: []
        };
        this.originalConsole = {
            log: console.log,
            error: console.error,
            warn: console.warn,
            info: console.info
        };
    }

    start() {
        console.log('🎬 Starting Log Capture...');
        
        // Capture console.log
        console.log = (...args) => {
            this.logs.console.push({
                timestamp: new Date().toISOString(),
                message: args.map(a => typeof a === 'string' ? a : JSON.stringify(a)).join(' ')
            });
            this.originalConsole.log(...args);
        };

        // Capture console.error
        console.error = (...args) => {
            const errorMsg = args.map(a => typeof a === 'string' ? a : JSON.stringify(a)).join(' ');
            this.logs.errors.push({
                timestamp: new Date().toISOString(),
                message: errorMsg,
                stack: new Error().stack
            });
            this.originalConsole.error(...args);
        };

        // Capture console.warn
        console.warn = (...args) => {
            const warnMsg = args.map(a => typeof a === 'string' ? a : JSON.stringify(a)).join(' ');
            this.logs.warnings.push({
                timestamp: new Date().toISOString(),
                message: warnMsg
            });
            this.originalConsole.warn(...args);
        };

        // Capture unhandled errors
        window.addEventListener('error', (event) => {
            this.logs.errors.push({
                timestamp: new Date().toISOString(),
                message: `Uncaught Error: ${event.message}`,
                source: event.filename,
                line: event.lineno,
                stack: event.error?.stack
            });
        });

        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logs.errors.push({
                timestamp: new Date().toISOString(),
                message: `Unhandled Promise Rejection: ${event.reason}`,
                stack: event.reason?.stack
            });
        });
    }

    stop() {
        console.log = this.originalConsole.log;
        console.error = this.originalConsole.error;
        console.warn = this.originalConsole.warn;
        console.info = this.originalConsole.info;
    }

    getLogs() {
        return this.logs;
    }

    printReport() {
        console.log('\n' + '='.repeat(80));
        console.log('📊 LOG CAPTURE REPORT');
        console.log('='.repeat(80) + '\n');

        console.log('📝 CONSOLE LOGS:', this.logs.console.length);
        this.logs.console.forEach(log => {
            console.log(`  [${log.timestamp}] ${log.message}`);
        });

        console.log('\n⚠️  WARNINGS:', this.logs.warnings.length);
        this.logs.warnings.forEach(warn => {
            console.log(`  [${warn.timestamp}] ${warn.message}`);
        });

        console.log('\n❌ ERRORS:', this.logs.errors.length);
        this.logs.errors.forEach(err => {
            console.log(`  [${err.timestamp}] ${err.message}`);
            if (err.source) console.log(`    Source: ${err.source}:${err.line}`);
            if (err.stack) console.log(`    Stack: ${err.stack.split('\n').slice(0, 3).join('\n    ')}`);
        });

        console.log('\n' + '='.repeat(80));
    }
}

// ===== API CLIENT =====
class TestAPIClient {
    constructor() {
        this.apiKey = null;
        this.userId = null;
        this.userRole = null;
    }

    async register(userData) {
        console.log(`📝 Registering ${userData.role}:`, userData.email);
        try {
            const response = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`Register failed: ${error.detail || response.statusText}`);
            }

            const data = await response.json();
            console.log(`✅ Registration successful for ${userData.role}`);
            return data;
        } catch (error) {
            console.error(`❌ Registration error for ${userData.role}:`, error.message);
            throw error;
        }
    }

    async login(email, password, role) {
        console.log(`🔐 Logging in ${role}:`, email);
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`Login failed: ${error.detail || response.statusText}`);
            }

            const data = await response.json();
            this.token = data.api_key || data.access_token;  // Try both field names
            this.userId = data.user_id;
            this.userRole = role;

            // Store in localStorage
            localStorage.setItem('api_key', this.token);
            localStorage.setItem('user_id', this.userId);
            localStorage.setItem('user_role', role);
            localStorage.setItem('user_email', email);

            console.log(`✅ Login successful for ${role}. Token: ${this.token.substring(0, 20)}...`);
            return data;
        } catch (error) {
            console.error(`❌ Login error for ${role}:`, error.message);
            throw error;
        }
    }

    async logout() {
        console.log(`🚪 Logging out ${this.userRole}...`);
        try {
            if (!this.token) {
                throw new Error('No API key found');
            }

            const response = await fetch(`${API_BASE}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.token
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`Logout failed: ${error.detail || response.statusText}`);
            }

            const data = await response.json();

            // Clear localStorage
            localStorage.removeItem('api_key');
            localStorage.removeItem('user_id');
            localStorage.removeItem('user_role');
            localStorage.removeItem('user_email');

            this.apiKey = null;
            this.userId = null;
            this.userRole = null;

            console.log(`✅ Logout successful`);
            return data;
        } catch (error) {
            console.error(`❌ Logout error:`, error.message);
            throw error;
        }
    }

    async getMe() {
        console.log(`👤 Getting user info...`);
        try {
            if (!this.token) {
                throw new Error('No API key found');
            }

            const response = await fetch(`${API_BASE}/auth/me`, {
                method: 'GET',
                headers: {
                    'X-API-Key': this.token
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(`Get user failed: ${error.detail || response.statusText}`);
            }

            const data = await response.json();
            console.log(`✅ User info retrieved:`, data);
            return data;
        } catch (error) {
            console.error(`❌ Get user error:`, error.message);
            throw error;
        }
    }

    clearStorage() {
        localStorage.removeItem('api_key');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_email');
        this.token = null;
        this.userId = null;
        this.userRole = null;
    }
}

// ===== TEST RUNNER =====
class LogoutTestRunner {
    constructor() {
        this.logCapture = new LogCapture();
        this.apiClient = new TestAPIClient();
        this.results = {
            student: {},
            company: {},
            admin: {}
        };
    }

    async testRoleFlow(role) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`🧪 Testing ${role.toUpperCase()} Flow`);
        console.log('='.repeat(80));

        const config = TEST_CONFIG[role];
        const result = {
            role: role,
            register: null,
            login: null,
            getMe: null,
            logout: null,
            errors: []
        };

        try {
            // 1. Register (or skip for admin - now uses email/password like others)
            console.log('\n📝 STEP 1: Register');
            if (role === 'admin') {
                // Admin already exists in database, created from .env with email/password
                // Skip registration and go directly to login
                console.log('⏭️  Skipping registration (admin pre-created with email/password)');
                result.register = true;
                console.log('✅ Register step skipped (using existing admin)');
            } else {
                try {
                    result.register = await this.apiClient.register(config);
                    console.log('✅ Register step passed');
                } catch (error) {
                    result.errors.push(`Register failed: ${error.message}`);
                    console.error('❌ Register step failed');
                    return result;
                }
            }

            // 2. Login
            console.log('\n🔐 STEP 2: Login');
            try {
                result.login = await this.apiClient.login(config.email, config.password, role);
                console.log('✅ Login step passed');
            } catch (error) {
                result.errors.push(`Login failed: ${error.message}`);
                console.error('❌ Login step failed');
                return result;
            }

            // 3. Get user info
            console.log('\n👤 STEP 3: Get User Info');
            try {
                result.getMe = await this.apiClient.getMe();
                console.log('✅ Get user info step passed');
            } catch (error) {
                result.errors.push(`Get user info failed: ${error.message}`);
                console.warn('⚠️  Get user info step failed (non-critical)');
            }

            // 4. Logout
            console.log('\n🚪 STEP 4: Logout');
            try {
                result.logout = await this.apiClient.logout();
                console.log('✅ Logout step passed');
            } catch (error) {
                result.errors.push(`Logout failed: ${error.message}`);
                console.error('❌ Logout step failed');
            }

            // Verify localStorage is cleared
            const apiKey = localStorage.getItem('api_key');
            if (apiKey) {
                result.errors.push(`localStorage not cleared: api_key still present`);
                console.error('❌ localStorage not cleared after logout');
            } else {
                console.log('✅ localStorage properly cleared');
            }

        } catch (error) {
            result.errors.push(`Unexpected error: ${error.message}`);
            console.error('❌ Unexpected error during test:', error);
        } finally {
            // Always cleanup
            this.apiClient.clearStorage();
        }

        this.results[role] = result;
        return result;
    }

    async runAllTests() {
        this.logCapture.start();

        console.log('🎬 Starting Complete Logout Test Suite');
        console.log(`Timestamp: ${new Date().toISOString()}\n`);

        for (const role of ['student', 'company', 'admin']) {
            try {
                await this.testRoleFlow(role);
                // Add delay between tests
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error(`Fatal error testing ${role}:`, error);
            }
        }

        this.logCapture.stop();
        this.printResults();

        return {
            results: this.results,
            logs: this.logCapture.getLogs(),
            timestamp: new Date().toISOString()
        };
    }

    printResults() {
        console.log('\n' + '='.repeat(80));
        console.log('📊 TEST RESULTS SUMMARY');
        console.log('='.repeat(80) + '\n');

        for (const role of ['student', 'company', 'admin']) {
            const result = this.results[role];
            console.log(`\n🔹 ${role.toUpperCase()}:`);
            console.log(`   Register: ${result.register ? '✅' : '❌'}`);
            console.log(`   Login: ${result.login ? '✅' : '❌'}`);
            console.log(`   Get User: ${result.getMe ? '✅' : '❌'}`);
            console.log(`   Logout: ${result.logout ? '✅' : '❌'}`);
            
            if (result.errors.length > 0) {
                console.log(`   Errors:`);
                result.errors.forEach(err => console.log(`     ❌ ${err}`));
            }
        }

        console.log('\n' + '='.repeat(80));
        console.log('📋 CONSOLE LOG REPORT');
        console.log('='.repeat(80));
        this.logCapture.printReport();

        console.log('\n' + '='.repeat(80));
        console.log('💾 SAVING TEST REPORT TO LOCALSTORAGE');
        console.log('='.repeat(80));

        const testReport = {
            timestamp: new Date().toISOString(),
            results: this.results,
            logs: this.logCapture.getLogs()
        };

        localStorage.setItem('logoutTestReport', JSON.stringify(testReport));
        console.log('✅ Test report saved to localStorage["logoutTestReport"]');
        console.log('📌 Retrieve with: JSON.parse(localStorage.getItem("logoutTestReport"))');
    }
}

// ===== MAIN EXPORT =====
async function runFullLogoutTest() {
    const runner = new LogoutTestRunner();
    const results = await runner.runAllTests();
    
    console.log('\n\n📌 TEST COMPLETE!');
    console.log('='.repeat(80));
    console.log('To view the full report, run:');
    console.log('  JSON.parse(localStorage.getItem("logoutTestReport"))');
    console.log('='.repeat(80));
    
    return results;
}

// Auto-run if this script is loaded directly
if (typeof window !== 'undefined') {
    window.runFullLogoutTest = runFullLogoutTest;
    window.logoutTestRunner = LogoutTestRunner;
    console.log('✅ Logout Test Suite loaded');
    console.log('📌 Run tests with: await runFullLogoutTest()');
}
