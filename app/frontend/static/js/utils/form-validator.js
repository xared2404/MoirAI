/**
 * MoirAI - Form Validator Utility
 * Validación de formularios en cliente
 * 
 * Uso:
 *   FormValidator.validate('email', 'test@example.com') // true
 *   FormValidator.validateForm(formElement) // { valid: true, errors: {} }
 */

const FormValidator = {
    /**
     * Expresiones regulares
     */
    patterns: {
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
        phone: /^[0-9]{10,}$/,
        url: /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/,
        number: /^\d+$/,
        alphanumeric: /^[a-zA-Z0-9]+$/,
        username: /^[a-zA-Z0-9_]{3,20}$/,
    },

    /**
     * Validar un campo específico
     */
    validate(type, value) {
        if (!value) {
            return { valid: false, error: 'Este campo es requerido' };
        }

        switch (type) {
            case 'email':
                return this.patterns.email.test(value)
                    ? { valid: true }
                    : { valid: false, error: 'Email inválido' };

            case 'password':
                if (value.length < 8) {
                    return { valid: false, error: 'Mínimo 8 caracteres' };
                }
                if (!/[A-Z]/.test(value)) {
                    return { valid: false, error: 'Debe incluir mayúscula' };
                }
                if (!/[a-z]/.test(value)) {
                    return { valid: false, error: 'Debe incluir minúscula' };
                }
                if (!/\d/.test(value)) {
                    return { valid: false, error: 'Debe incluir número' };
                }
                return { valid: true };

            case 'confirm-password':
                return { valid: true }; // Se valida comparando con password

            case 'phone':
                return this.patterns.phone.test(value)
                    ? { valid: true }
                    : { valid: false, error: 'Teléfono inválido' };

            case 'text':
                return value.trim().length > 0
                    ? { valid: true }
                    : { valid: false, error: 'Este campo no puede estar vacío' };

            case 'textarea':
                return value.trim().length > 10
                    ? { valid: true }
                    : { valid: false, error: 'Mínimo 10 caracteres' };

            case 'url':
                return this.patterns.url.test(value)
                    ? { valid: true }
                    : { valid: false, error: 'URL inválida' };

            case 'checkbox':
                return value
                    ? { valid: true }
                    : { valid: false, error: 'Debes aceptar este campo' };

            default:
                return { valid: true };
        }
    },

    /**
     * Validar que dos campos coincidan (ej: password y confirm)
     */
    match(value1, value2, fieldName = 'campos') {
        return value1 === value2
            ? { valid: true }
            : { valid: false, error: `Los ${fieldName} no coinciden` };
    },

    /**
     * Validar un formulario completo
     */
    validateForm(formElement) {
        const errors = {};
        let isValid = true;

        const fields = formElement.querySelectorAll('[data-validate]');

        fields.forEach(field => {
            const type = field.dataset.validate;
            const value = field.value || field.checked;
            const name = field.name;

            const result = this.validate(type, value);

            if (!result.valid) {
                errors[name] = result.error;
                isValid = false;
                this.showError(field, result.error);
            } else {
                this.clearError(field);
            }
        });

        // Validación especial: coincidencia de contraseñas
        const passwordField = formElement.querySelector('[name="password"]');
        const confirmField = formElement.querySelector('[name="confirm-password"]');

        if (passwordField && confirmField) {
            const matchResult = this.match(
                passwordField.value,
                confirmField.value,
                'contraseñas'
            );

            if (!matchResult.valid) {
                errors['confirm-password'] = matchResult.error;
                isValid = false;
                this.showError(confirmField, matchResult.error);
            }
        }

        return { valid: isValid, errors };
    },

    /**
     * Mostrar error en campo
     */
    showError(field, message) {
        field.classList.add('error');
        field.classList.remove('valid');

        // Crear o actualizar elemento de error
        let errorElement = field.nextElementSibling;

        if (!errorElement || !errorElement.classList.contains('error-message')) {
            errorElement = document.createElement('span');
            errorElement.className = 'error-message';
            field.parentNode.insertBefore(errorElement, field.nextSibling);
        }

        errorElement.textContent = message;
    },

    /**
     * Limpiar error en campo
     */
    clearError(field) {
        field.classList.remove('error');
        field.classList.add('valid');

        const errorElement = field.nextElementSibling;
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.remove();
        }
    },

    /**
     * Validar en tiempo real mientras se escribe
     */
    setupRealtimeValidation(formElement) {
        const fields = formElement.querySelectorAll('[data-validate]');

        fields.forEach(field => {
            field.addEventListener('blur', () => {
                const type = field.dataset.validate;
                const value = field.value || field.checked;
                const result = this.validate(type, value);

                if (!result.valid) {
                    this.showError(field, result.error);
                } else {
                    this.clearError(field);
                }
            });

            field.addEventListener('input', () => {
                if (field.classList.contains('error')) {
                    const type = field.dataset.validate;
                    const value = field.value || field.checked;
                    const result = this.validate(type, value);

                    if (result.valid) {
                        this.clearError(field);
                    }
                }
            });
        });
    },

    /**
     * Obtener valores del formulario
     */
    getFormData(formElement) {
        const formData = new FormData(formElement);
        const data = Object.fromEntries(formData);
        return data;
    },

    /**
     * Llenar formulario con datos
     */
    fillForm(formElement, data) {
        Object.keys(data).forEach(key => {
            const field = formElement.elements[key];
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = data[key];
                } else {
                    field.value = data[key];
                }
            }
        });
    },

    /**
     * Limpiar formulario
     */
    clearForm(formElement) {
        formElement.reset();
        const errors = formElement.querySelectorAll('.error-message');
        errors.forEach(error => error.remove());
        const fields = formElement.querySelectorAll('[data-validate]');
        fields.forEach(field => {
            field.classList.remove('error', 'valid');
        });
    },
};

// Exportar para uso global
window.FormValidator = FormValidator;
