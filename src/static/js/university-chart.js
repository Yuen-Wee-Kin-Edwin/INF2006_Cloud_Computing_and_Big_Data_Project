class UniversityChart {
    constructor() {
        this.chart = null;
        this.originalData = null;
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
            const response = await fetch('/api/university-salary-data');
            this.originalData = await response.json();
            this.populateUniversityFilter();
        } catch (error) {
            console.error('Error fetching university salary data:', error);
        }
    }

    populateUniversityFilter() {
        const universityFilter = document.getElementById('universityFilter');
        const universities = [...new Set(this.originalData.map(item => item.university))].sort();
        
        universities.forEach(uni => {
            const option = document.createElement('option');
            option.value = uni;
            option.textContent = uni;
            universityFilter.appendChild(option);
        });
    }

    setupControls() {
        document.getElementById('universityFilter').addEventListener('change', (e) => {
            this.renderChart(e.target.value);
        });
    }

    setupEventListeners() {
        // Update last updated date
        document.getElementById('universityLastUpdated').textContent = new Date().toLocaleDateString();
    }

    renderChart(selectedUniversity = 'all') {
        const ctx = document.getElementById('universitySalaryChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        const years = [...new Set(this.originalData.map(item => item.year))].sort();
        let datasets;

        if (selectedUniversity === 'all') {
            const universities = [...new Set(this.originalData.map(item => item.university))].sort();
            const colors = ['#3a86ff', '#ff006e', '#8338ec', '#fb5607', '#ffbe0b', '#2ec4b6'];
            
            datasets = universities.map((uni, index) => {
                const uniData = this.originalData.filter(item => item.university === uni);
                return {
                    label: uni,
                    data: years.map(year => {
                        const yearData = uniData.find(d => d.year === year);
                        return yearData ? yearData.gross_monthly_median : null;
                    }),
                    borderColor: colors[index % colors.length],
                    borderWidth: 3,
                    fill: false,
                    tension: 0.3
                };
            });
        } else {
            const uniData = this.originalData.filter(item => item.university === selectedUniversity);
            datasets = [{
                label: selectedUniversity,
                data: years.map(year => {
                    const yearData = uniData.find(d => d.year === year);
                    return yearData ? yearData.gross_monthly_median : null;
                }),
                borderColor: '#3a86ff',
                borderWidth: 3,
                fill: true,
                backgroundColor: 'rgba(58, 134, 255, 0.1)',
                tension: 0.3
            }];
        }

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: years,
                datasets: datasets
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
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Median Monthly Gross Salary'
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
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].datasetIndex;
                        const label = event.chart.data.datasets[index]?.label;
                        if (label) {
                            window.location.href = `/university-details?university=${encodeURIComponent(label)}`;
                        }
                    }
                },
                onHover: (event, elements) => {
                    event.chart.canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new UniversityChart();
});
