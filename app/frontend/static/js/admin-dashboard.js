/**
 * MoirAI Admin Dashboard - Core Navigation & Tabs
 * Lightweight version: only handles tab/section switching and analytics integration
 * Charts, notifications, and utilities moved to separate modules
 */

let dashboardAnalytics = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeEventListeners();
});

/**
 * Navigate between sections (Overview, Students, Companies, Analytics, Settings)
 */
function initializeNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.getAttribute('data-section');
            if (section) switchSection(section);
        });
    });
}

/**
 * Switch main section content
 */
function switchSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));

    const section = document.getElementById(sectionId);
    if (section) section.classList.add('active');

    const navItem = document.querySelector(`[data-section="${sectionId}"]`);
    if (navItem) navItem.classList.add('active');

    // Load analytics if switching to that section
    if (sectionId === 'analytics') initializeAnalytics();
}

/**
 * Initialize analytics module on first load
 */
function initializeAnalytics() {
    if (!dashboardAnalytics) {
        dashboardAnalytics = new AdminAnalyticsPage('#analytics');
        dashboardAnalytics.initialize(true).catch(err => {
            console.error('📊 Analytics init error:', err);
            notificationManager?.show('Error al cargar analítica', 'error');
        });
    } else if (dashboardAnalytics.initialized) {
        dashboardAnalytics.loadAnalytics(true).catch(err => {
            console.error('📊 Analytics reload error:', err);
        });
    }
}

/**
 * Tab switching (for tables/content within sections)
 */
function initializeEventListeners() {
    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
    });

    // Sidebar toggle
    const toggleBtn = document.getElementById('toggleSidebar');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            document.querySelector('.sidebar')?.classList.toggle('collapsed');
        });
    }

    // Action buttons (view/edit/delete)
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            handleActionButton(btn);
        });
    });
}

/**
 * Switch between tabs within a section
 */
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    const tabElement = document.getElementById(`${tabId}-tab`);
    if (tabElement) tabElement.classList.add('active');

    const tabBtn = document.querySelector(`[data-tab="${tabId}"]`);
    if (tabBtn) tabBtn.classList.add('active');
}

/**
 * Handle action button clicks (view, edit, delete)
 */
function handleActionButton(btn) {
    const action = btn.classList.contains('view') ? 'view' :
                   btn.classList.contains('edit') ? 'edit' : 'delete';

    if (action === 'delete' && !confirm('¿Eliminar elemento?')) return;
    
    const message = action === 'delete' ? 'Eliminado' : `Acción: ${action}`;
    notificationManager?.show(message, 'info');
}
