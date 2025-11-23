/**
 * MoirAI Landing Page - Main JavaScript
 * Core: Navigation, modals, smooth scroll, scroll-to-top
 * Auth logic separated to login.js
 */

document.addEventListener('DOMContentLoaded', () => {
    initializeModals();
    initializeNavigation();
    initializePasswordToggles();
    createScrollToTopButton();
    addAnimationStyles();
});

/**
 * Modal Management (for landing page only)
 */
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');

    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.modal').style.display = 'none';
        });
    });

    modals.forEach(modal => {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) modal.style.display = 'none';
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            modals.forEach(modal => modal.style.display = 'none');
        }
    });
}

/**
 * Open login/register modals
 */
function scrollToLogin() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.style.display = 'flex';
}

function scrollToRegister() {
    const modal = document.getElementById('register-modal');
    if (modal) modal.style.display = 'flex';
}

/**
 * Navigation: Smooth scroll and hamburger menu
 */
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                    if (navMenu?.style.display === 'flex') {
                        navMenu.style.display = 'none';
                    }
                }
            }
        });
    });

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navMenu.style.display = navMenu?.style.display === 'flex' ? 'none' : 'flex';
        });
    }

    document.addEventListener('click', (event) => {
        if (navMenu?.style.display === 'flex') {
            if (!event.target.closest('.nav-container')) {
                navMenu.style.display = 'none';
            }
        }
    });
}

/**
 * Password toggle (show/hide)
 */
function initializePasswordToggles() {
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            const input = toggle.closest('.password-input-group')?.querySelector('input');
            const icon = toggle.querySelector('i');
            
            if (input?.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    });
}

/**
 * Scroll to top button
 */
function createScrollToTopButton() {
    const button = document.createElement('button');
    button.innerHTML = '<i class="fas fa-arrow-up"></i>';
    button.className = 'scroll-to-top';
    
    Object.assign(button.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        width: '50px',
        height: '50px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #730f33, #e2bb84)',
        color: 'white',
        border: 'none',
        cursor: 'pointer',
        display: 'none',
        zIndex: '999',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
    });

    button.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', () => {
        button.style.display = window.scrollY > 300 ? 'flex' : 'none';
        button.style.alignItems = 'center';
        button.style.justifyContent = 'center';
    });

    document.body.appendChild(button);
}

/**
 * Add animation styles
 */
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100px);
                opacity: 0;
            }
        }

        .scroll-to-top:hover {
            transform: translateY(-3px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15);
        }
    `;
    document.head.appendChild(style);
}

/**
 * Analytics event tracking
 */
function trackEvent(eventName, eventData = {}) {
    console.log('📊 Event:', eventName, eventData);
}

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn')) {
        trackEvent('button_click', { button_text: e.target.textContent });
    }
});
