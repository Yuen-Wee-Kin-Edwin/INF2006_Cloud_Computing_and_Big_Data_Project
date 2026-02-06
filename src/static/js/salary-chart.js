class SalaryChart {
    constructor() {
        this.chart = null;
        this.originalData = null;
        this.filteredData = null;
        this.init();
    }

    async init() {
        await this.fetchData();
        this.setupControls();
        this.renderChart();
        this.setupEventListeners();
    }

    async fetchData() {
        try {
            const response = await fetch('/api/salary-data');
            this.originalData = await response.json();
            this.filteredData = [...this.originalData];
            this.populateYearFilter();
        } catch (error) {
            console.error('Error fetching salary data:', error);
        }
    }

    populateYearFilter() {
        const yearFilter = document.getElementById('yearFilter');
        const years = [...new Set(this.originalData.map(item => item.year))].sort();
        
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearFilter.appendChild(option);
        });
    }

    setupControls() {
        const toggleButtons = document.querySelectorAll('.toggle-btn');
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                toggleButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                this.updateChartVisibility(e.target.dataset.metric);
            });
        });

        document.getElementById('yearFilter').addEventListener('change', (e) => {
            this.filterDataByYear(e.target.value);
        });
    }

    filterDataByYear(year) {
        if (year === 'all') {
            this.filteredData = [...this.originalData];
        } else {
            this.filteredData = this.originalData.filter(item => item.year.toString() === year);
        }
        this.renderChart();
    }

    updateChartVisibility(metric) {
        if (!this.chart) return;

        const datasets = this.chart.data.datasets;
        const visibility = {
            'all': [true, true, true, true],
            'mean': [true, false, false, false],
            'median': [false, true, false, false],
            'percentiles': [false, false, true, true]
        };

        const visState = visibility[metric] || visibility['all'];
        
        datasets.forEach((dataset, index) => {
            dataset.hidden = !visState[index];
        });

        this.chart.update();
    }

    setupEventListeners() {
        // Update last updated date
        document.getElementById('lastUpdated').textContent = new Date().toLocaleDateString();
    }

    renderChart() {
        const ctx = document.getElementById('salaryChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.chart) {
            this.chart.destroy();
        }

        const years = this.filteredData.map(item => item.year);
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: [
                    {
                        label: 'Monthly Mean',
                        data: this.filteredData.map(item => item.gross_monthly_mean),
                        borderColor: '#3a86ff',
                        backgroundColor: 'rgba(58, 134, 255, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Monthly Median',
                        data: this.filteredData.map(item => item.gross_monthly_median),
                        borderColor: '#ff006e',
                        backgroundColor: 'rgba(255, 0, 110, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: '25th Percentile',
                        data: this.filteredData.map(item => item.gross_mthly_25_percentile),
                        borderColor: '#8338ec',
                        backgroundColor: 'rgba(131, 56, 236, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3
                    },
                    {
                        label: '75th Percentile',
                        data: this.filteredData.map(item => item.gross_mthly_75_percentile),
                        borderColor: '#fb5607',
                        backgroundColor: 'rgba(251, 86, 7, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Monthly Gross Salary'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'nearest'
                }
            }
        });
    }
}

// Initialize chart when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SalaryChart();
});