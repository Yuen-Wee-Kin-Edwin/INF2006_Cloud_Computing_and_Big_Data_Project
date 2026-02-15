class SalaryChart {
    constructor() {
        this.chart = null;
        this.originalData = [];
        this.filteredData = [];
        this.activeMetric = 'all';
        this.init();
    }

    async init() {
        await this.fetchData();
        // Hide loading indicator
        const loader = document.getElementById('salaryChartLoading');
        if (loader) loader.style.display = 'none';

        if (this.originalData.length) {
            this.populateYearFilter();
            this.setupControls();
            this.renderChart();
            this.setupEventListeners();
        }
    }

    /* ───────── data fetching ───────── */
    async fetchData() {
        try {
            const response = await fetch('/api/salary-trends');
            const json = await response.json();

            if (!json.success || !Array.isArray(json.data)) {
                console.warn('Salary trends API returned no data – falling back to /api/salary-details');
                await this.fetchFallback();
                return;
            }

            this.originalData = json.data
                .filter(d => d.year != null)
                .sort((a, b) => a.year - b.year);

            this.filteredData = [...this.originalData];
        } catch (error) {
            console.error('Error fetching salary trends:', error);
            await this.fetchFallback();
        }
    }

    /** Fallback: fetch raw rows from /api/salary-details and aggregate client-side */
    async fetchFallback() {
        try {
            const response = await fetch('/api/salary-details');
            const json = await response.json();
            const rows = json.success ? json.data : [];

            const yearMap = {};
            rows.forEach(r => {
                const y = r.year;
                if (!y) return;
                if (!yearMap[y]) yearMap[y] = { year: y, mean: [], median: [], p25: [], p75: [] };
                if (r.gross_monthly_mean != null)         yearMap[y].mean.push(r.gross_monthly_mean);
                if (r.gross_monthly_median != null)       yearMap[y].median.push(r.gross_monthly_median);
                if (r.gross_mthly_25_percentile != null)  yearMap[y].p25.push(r.gross_mthly_25_percentile);
                if (r.gross_mthly_75_percentile != null)  yearMap[y].p75.push(r.gross_mthly_75_percentile);
            });

            const avg = arr => arr.length ? +(arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2) : null;

            this.originalData = Object.values(yearMap)
                .sort((a, b) => a.year - b.year)
                .map(g => ({
                    year: g.year,
                    gross_monthly_mean:          avg(g.mean),
                    gross_monthly_median:        avg(g.median),
                    gross_mthly_25_percentile:   avg(g.p25),
                    gross_mthly_75_percentile:   avg(g.p75)
                }));

            this.filteredData = [...this.originalData];
        } catch (err) {
            console.error('Fallback salary fetch failed:', err);
        }
    }

    /* ───────── controls ───────── */
    populateYearFilter() {
        const yearFilter = document.getElementById('yearFilter');
        if (!yearFilter) return;

        const years = this.originalData.map(d => d.year);
        years.forEach(year => {
            const opt = document.createElement('option');
            opt.value = year;
            opt.textContent = year;
            yearFilter.appendChild(opt);
        });
    }

    setupControls() {
        // Metric toggle buttons
        const toggleBtns = document.querySelectorAll('.salary-chart-container .toggle-btn');
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', e => {
                toggleBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.activeMetric = e.target.dataset.metric;
                this.updateChartVisibility(this.activeMetric);
            });
        });

        // Year filter
        const yearFilter = document.getElementById('yearFilter');
        if (yearFilter) {
            yearFilter.addEventListener('change', e => this.filterByYear(e.target.value));
        }
    }

    filterByYear(year) {
        this.filteredData = year === 'all'
            ? [...this.originalData]
            : this.originalData.filter(d => String(d.year) === year);
        this.renderChart();
        // Re-apply metric visibility after re-render
        this.updateChartVisibility(this.activeMetric);
    }

    updateChartVisibility(metric) {
        if (!this.chart) return;

        const map = {
            all:         [true, true, true, true],
            mean:        [true, false, false, false],
            median:      [false, true, false, false],
            percentiles: [false, false, true, true]
        };
        const vis = map[metric] || map.all;

        this.chart.data.datasets.forEach((ds, i) => { ds.hidden = !vis[i]; });
        this.chart.update();
    }

    setupEventListeners() {
        const el = document.getElementById('lastUpdated');
        if (el) el.textContent = new Date().toLocaleDateString();
    }

    /* ───────── chart rendering ───────── */
    renderChart() {
        const canvas = document.getElementById('salaryChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        if (this.chart) this.chart.destroy();

        const labels = this.filteredData.map(d => d.year);
        const fmt = v => v != null ? `$${Number(v).toLocaleString()}` : '—';

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Monthly Mean',
                        data: this.filteredData.map(d => d.gross_monthly_mean),
                        borderColor: '#3a86ff',
                        backgroundColor: 'rgba(58, 134, 255, 0.08)',
                        pointBackgroundColor: '#3a86ff',
                        pointBorderColor: '#fff',
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.35
                    },
                    {
                        label: 'Monthly Median',
                        data: this.filteredData.map(d => d.gross_monthly_median),
                        borderColor: '#ff006e',
                        backgroundColor: 'rgba(255, 0, 110, 0.08)',
                        pointBackgroundColor: '#ff006e',
                        pointBorderColor: '#fff',
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.35
                    },
                    {
                        label: '25th Percentile',
                        data: this.filteredData.map(d => d.gross_mthly_25_percentile),
                        borderColor: '#8338ec',
                        backgroundColor: 'rgba(131, 56, 236, 0.06)',
                        pointBackgroundColor: '#8338ec',
                        pointBorderColor: '#fff',
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        borderWidth: 2,
                        borderDash: [6, 4],
                        fill: false,
                        tension: 0.35
                    },
                    {
                        label: '75th Percentile',
                        data: this.filteredData.map(d => d.gross_mthly_75_percentile),
                        borderColor: '#fb5607',
                        backgroundColor: 'rgba(251, 86, 7, 0.06)',
                        pointBackgroundColor: '#fb5607',
                        pointBorderColor: '#fff',
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        borderWidth: 2,
                        borderDash: [6, 4],
                        fill: false,
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(30,30,30,0.92)',
                        titleFont: { size: 14, weight: '600' },
                        bodyFont: { size: 13 },
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            title: ctx => `Year ${ctx[0].label}`,
                            label: ctx => {
                                const val = ctx.parsed.y;
                                return ` ${ctx.dataset.label}: ${fmt(val)}`;
                            }
                        }
                    },
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'Monthly Gross Salary (SGD)', font: { weight: '600' } },
                        ticks: {
                            callback: v => `$${v.toLocaleString()}`
                        },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        title: { display: true, text: 'Year', font: { weight: '600' } },
                        grid: { display: false }
                    }
                },
                interaction: { intersect: false, mode: 'nearest' },
                onClick: (_event, elements) => {
                    if (elements.length > 0) {
                        const idx = elements[0].index;
                        const year = this.filteredData[idx]?.year;
                        if (year) window.location.href = `/salary-details?year=${year}`;
                    }
                },
                onHover: (event, elements) => {
                    event.chart.canvas.style.cursor = elements.length ? 'pointer' : 'default';
                }
            }
        });
    }
}

// Initialize chart when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SalaryChart();
});