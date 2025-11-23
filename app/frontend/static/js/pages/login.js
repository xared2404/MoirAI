/**
 * MoirAI - Login Page JavaScript
 * Manejo de autenticación y login de usuarios
 */

// Flag para prevenir submit duplicado
let loginSubmitInProgress = false;
let registerSubmitInProgress = false;

document.addEventListener('DOMContentLoaded', () => {
    initLoginPage();
});

/**
 * Inicializar página de login
 */
async function initLoginPage() {
    // Verificar si ya está autenticado
    if (authManager.isAuthenticated()) {
        window.location.href = '/dashboard';
        return;
    }

    // Setup form handlers
    setupLoginForm();
    setupRegisterForm();
    setupTabSwitcher();
    setupPasswordToggle();
    setupSocialLogin();
}

/**
 * Setup del formulario de login
 */
function setupLoginForm() {
    const form = document.getElementById('login-form');
    if (!form) return;

    // Validación en tiempo real
    FormValidator.setupRealtimeValidation(form);

    // Manejador del submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Fix: Prevenir envío duplicado
        if (loginSubmitInProgress) {
            return;
        }

        // Validar formulario
        const validation = FormValidator.validateForm(form);
        if (!validation.valid) {
            notificationManager.error('Por favor completa todos los campos correctamente');
            return;
        }

        loginSubmitInProgress = true;

        // Obtener datos
        const email = form.querySelector('[name="email"]').value;
        const password = form.querySelector('[name="password"]').value;
        const rememberMe = form.querySelector('[name="remember"]')?.checked || false;

        // Mostrar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        notificationManager.loading('Iniciando sesión...');

        try {
            // Llamar al API
            const response = await authManager.login(email, password);

            if (rememberMe) {
                StorageManager.set('rememberEmail', email);
            }

            notificationManager.hideLoading();
            notificationManager.success('¡Bienvenido!');

            // Determinar a dónde redirigir
            const urlParams = new URLSearchParams(window.location.search);
            const redirect = urlParams.get('redirect') || '/dashboard';

            setTimeout(() => {
                window.location.href = redirect;
            }, 1000);

        } catch (error) {
            notificationManager.hideLoading();

            if (error.message?.includes('401')) {
                notificationManager.error('Email o contraseña incorrectos');
            } else if (error.message?.includes('429')) {
                notificationManager.error('Demasiados intentos. Intenta más tarde');
            } else {
                notificationManager.error(error.message || 'Error al iniciar sesión');
            }

            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            loginSubmitInProgress = false;
        }
    });

    // Cargar email guardado si existe
    const savedEmail = StorageManager.get('rememberEmail');
    if (savedEmail) {
        form.querySelector('[name="email"]').value = savedEmail;
        form.querySelector('[name="remember"]').checked = true;
    }
}

/**
 * Setup del formulario de registro
 */
function setupRegisterForm() {
    const form = document.getElementById('register-form');
    if (!form) return;

    // Validación en tiempo real
    FormValidator.setupRealtimeValidation(form);

    // ✅ CORRECCIÓN: Mostrar/ocultar campos según rol
    const roleSelect = form.querySelector('[name="role"]');
    if (roleSelect) {
        roleSelect.addEventListener('change', (e) => {
            const role = e.target.value;
            
            // Ocultar todos los campos condicionales
            document.getElementById('student-program').style.display = 'none';
            document.getElementById('company-industry').style.display = 'none';
            document.getElementById('company-size').style.display = 'none';
            document.getElementById('company-location').style.display = 'none';
            
            // Mostrar según rol
            if (role === 'student') {
                document.getElementById('student-program').style.display = 'block';
            } else if (role === 'company') {
                document.getElementById('company-industry').style.display = 'block';
                document.getElementById('company-size').style.display = 'block';
                document.getElementById('company-location').style.display = 'block';
            }
        });
    }

    // Manejador del submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Fix: Prevenir envío duplicado
        if (registerSubmitInProgress) {
            return;
        }

        // Validar formulario
        const validation = FormValidator.validateForm(form);
        if (!validation.valid) {
            notificationManager.error('Por favor completa todos los campos correctamente');
            return;
        }

        registerSubmitInProgress = true;

        // Obtener datos
        const formData = FormValidator.getFormData(form);
        
        // ✅ CORRECCIÓN: Mapear datos correctamente según la estructura esperada por backend
        const userData = {
            name: `${formData.first_name} ${formData.last_name}`.trim(),
            email: formData.email,
            password: formData.password,
            role: formData.role || 'student',
            // Campos según rol
            program: formData.role === 'student' ? formData.program : undefined,
            industry: formData.role === 'company' ? formData.industry : undefined,
            companySize: formData.role === 'company' ? formData.company_size : undefined,
            location: formData.role === 'company' ? formData.location : undefined
        };

        // Mostrar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        notificationManager.loading('Creando cuenta...');

        try {
            // Llamar al API de registro
            const response = await authManager.register(userData);

            notificationManager.hideLoading();
            notificationManager.success('¡Cuenta creada exitosamente!');

            // Limpiar formulario
            FormValidator.clearForm(form);

            // Redirigir al dashboard después de 2 segundos
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 2000);

        } catch (error) {
            notificationManager.hideLoading();

            if (error.message?.includes('already exists')) {
                notificationManager.error('Este email ya está registrado');
            } else if (error.message?.includes('validation')) {
                notificationManager.error('Verifique los datos ingresados');
            } else {
                notificationManager.error(error.message || 'Error al crear la cuenta');
            }

            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            registerSubmitInProgress = false;
        }
    });
}

/**
 * Setup del cambio de tabs (Login/Register)
 */
function setupTabSwitcher() {
    const tabs = document.querySelectorAll('.auth-tab');
    const panels = document.querySelectorAll('.auth-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();

            // Remover clase active de todos
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            // Agregar clase active al actual
            tab.classList.add('active');
            const targetPanel = document.getElementById(tab.dataset.tab);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }

            // Limpiar formularios
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                if (!form.classList.contains('active')) {
                    FormValidator.clearForm(form);
                }
            });
        });
    });
}

/**
 * Setup para mostrar/ocultar contraseña
 */
function setupPasswordToggle() {
    const toggleBtns = document.querySelectorAll('.password-toggle');

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input');
            const icon = btn.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
}

/**
 * Setup para social login (placeholder)
 */
function setupSocialLogin() {
    const googleBtn = document.getElementById('google-login');
    const linkedinBtn = document.getElementById('linkedin-login');

    if (googleBtn) {
        googleBtn.addEventListener('click', async () => {
            notificationManager.warning('Google login: En desarrollo');
            // Implementar OAuth con Google
        });
    }

    if (linkedinBtn) {
        linkedinBtn.addEventListener('click', async () => {
            notificationManager.warning('LinkedIn login: En desarrollo');
            // Implementar OAuth con LinkedIn
        });
    }
}

/**
 * Recuperar contraseña
 */
async function handleForgotPassword() {
    const email = prompt('Ingresa tu email:');
    if (!email) return;

    if (!FormValidator.validate('email', email).valid) {
        notificationManager.error('Email inválido');
        return;
    }

    notificationManager.loading('Enviando instrucciones...');

    try {
        // ⚠️ DESHABILITADO: El endpoint /auth/forgot-password no existe en el backend (MVP)
        // await apiClient.post('/auth/forgot-password', { email });
        // notificationManager.hideLoading();
        // notificationManager.success('Revisa tu email para resetear la contraseña');
        
        throw new Error('Recuperación de contraseña no disponible en esta versión');
    } catch (error) {
        notificationManager.hideLoading();
        notificationManager.error('Funcionalidad no disponible: ' + error.message);
    }
}

/**
 * Cambiar entre tabs programáticamente
 */
function switchToRegister() {
    const registerTab = document.querySelector('[data-tab="register"]');
    if (registerTab) {
        registerTab.click();
    }
}

function switchToLogin() {
    const loginTab = document.querySelector('[data-tab="login"]');
    if (loginTab) {
        loginTab.click();
    }
}
