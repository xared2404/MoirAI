/**
 * Charts Initialization and Management
 * Handles all chart visualizations in the admin dashboard
 */

// Chart.js library check
if (typeof Chart === 'undefined') {
    console.warn('Chart.js library not loaded. Charts will not render.');
}

/**
 * Visits Histogram Chart Configuration
 */
const VisitsChart = {
    instance: null,
    ctx: null,

    /**
     * Initialize visits histogram chart
     */
    init() {
        const canvasElement = document.getElementById('visitsHistogram');
        if (!canvasElement) {
            console.warn('Visits histogram canvas not found');
            return;
        }

        this.ctx = canvasElement.getContext('2d');

        // Get data based on timeframe
        const timeframe = document.getElementById('visitsTimeframe')?.value || 'week';
        const data = this.getChartData(timeframe);

        this.instance = new Chart(this.ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(115, 15, 51, 0.8)',
                        padding: 12,
                        borderRadius: 4,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 12
                        },
                        callbacks: {
                            label: function (context) {
                                return 'Visitas: ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: this.getMaxValue(data),
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString();
                            },
                            color: '#6b7280',
                            font: {
                                size: 12
                            }
                        },
                        grid: {
                            color: '#e5e7eb',
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: '#6b7280',
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        // Add timeframe change listener
        const timeframeSelect = document.getElementById('visitsTimeframe');
        if (timeframeSelect) {
            timeframeSelect.addEventListener('change', (e) => {
                this.updateChart(e.target.value);
            });
        }
    },

    /**
     * Get chart data based on timeframe
     */
    getChartData(timeframe) {
        let labels, values;

        if (timeframe === 'day') {
            // Hourly data for today
            labels = Array.from({ length: 24 }, (_, i) => i + ':00');
            values = [45, 52, 38, 31, 28, 42, 58, 72, 95, 112, 145, 168,
                182, 175, 158, 142, 128, 135, 148, 156, 142, 125, 98, 65];
        } else if (timeframe === 'week') {
            // Daily data for current week
            labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sab', 'Dom'];
            values = [1450, 1680, 1820, 1950, 2150, 1620, 1147];
        } else if (timeframe === 'month') {
            // Daily data for current month
            labels = Array.from({ length: 30 }, (_, i) => (i + 1) + ' de ' + this.getCurrentMonth());
            values = [
                1050, 1200, 980, 1450, 1680, 1820, 1950, 2150, 1620, 1447,
                1650, 1750, 1920, 2050, 2280, 1950, 1820, 1450, 1280, 1680,
                1850, 2050, 2180, 1920, 1650, 1450, 1280, 950, 1200, 1450
            ];
        }

        return {
            labels: labels,
            datasets: [{
                label: 'Visitas',
                data: values,
                backgroundColor: this.getBarColors(values),
                borderRadius: 4,
                borderSkipped: false,
                hoverBackgroundColor: '#5a0a27'
            }]
        };
    },

    /**
     * Get gradient colors for bars based on values
     */
    getBarColors(values) {
        const maxValue = Math.max(...values);
        return values.map(value => {
            const percentage = value / maxValue;
            if (percentage > 0.8) {
                return 'rgba(115, 15, 51, 0.9)'; // Dark burgundy
            } else if (percentage > 0.6) {
                return 'rgba(115, 15, 51, 0.7)'; // Medium burgundy
            } else if (percentage > 0.4) {
                return 'rgba(188, 147, 91, 0.7)'; // Gold
            } else {
                return 'rgba(188, 147, 91, 0.5)'; // Light gold
            }
        });
    },

    /**
     * Get max value for chart scale
     */
    getMaxValue(data) {
        const max = Math.max(...data.datasets[0].data);
        return Math.ceil(max * 1.1);
    },

    /**
     * Get current month name
     */
    getCurrentMonth() {
        const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
        return months[new Date().getMonth()];
    },

    /**
     * Update chart with new timeframe data
     */
    updateChart(timeframe) {
        const newData = this.getChartData(timeframe);
        this.instance.data = newData;
        this.instance.options.scales.y.max = this.getMaxValue(newData);
        this.instance.update();
    }
};

/**
 * Registers Chart Configuration
 */
const RegistersChart = {
    instance: null,
    ctx: null,

    init() {
        const canvasElement = document.getElementById('registersChart');
        if (!canvasElement) return;

        this.ctx = canvasElement.getContext('2d');

        const data = {
            labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sab', 'Dom'],
            datasets: [{
                label: 'Nuevos Registros',
                data: [12, 19, 8, 15, 22, 9, 5],
                backgroundColor: 'rgba(115, 15, 51, 0.1)',
                borderColor: '#730f33',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        };

        this.instance = new Chart(this.ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#e5e7eb'
                        }
                    }
                }
            }
        });
    }
};

/**
 * Users Distribution Chart Configuration
 */
const UsersChart = {
    instance: null,
    ctx: null,

    init() {
        const canvasElement = document.getElementById('usersChart');
        if (!canvasElement) return;

        this.ctx = canvasElement.getContext('2d');

        const data = {
            labels: ['Estudiantes', 'Empresas', 'Administradores', 'Invitados'],
            datasets: [{
                data: [62, 28, 5, 5],
                backgroundColor: [
                    'rgba(115, 15, 51, 0.8)',
                    'rgba(188, 147, 91, 0.8)',
                    'rgba(26, 70, 57, 0.8)',
                    'rgba(107, 114, 128, 0.8)'
                ],
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        };

        this.instance = new Chart(this.ctx, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
};

/**
 * Initialize all charts when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function () {
    // Check if Chart.js is loaded
    if (typeof Chart !== 'undefined') {
        VisitsChart.init();
        RegistersChart.init();
        UsersChart.init();
    } else {
        console.warn('Chart.js library not found. Ensure it is loaded before charts.js');
    }
});

/**
 * Utility function to update all charts
 */
function refreshAllCharts() {
    if (typeof Chart !== 'undefined') {
        if (VisitsChart.instance) VisitsChart.instance.update();
        if (RegistersChart.instance) RegistersChart.instance.update();
        if (UsersChart.instance) UsersChart.instance.update();
    }
}

/**
 * Utility function to destroy all charts
 */
function destroyAllCharts() {
    if (VisitsChart.instance) VisitsChart.instance.destroy();
    if (RegistersChart.instance) RegistersChart.instance.destroy();
    if (UsersChart.instance) UsersChart.instance.destroy();
}
