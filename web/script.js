// Global variables
const API_BASE_URL = 'http://localhost:5000/api';
let priceChart, exportPieChart, climateChart, trendsChart, exportPerformanceChart, forecastChart;

console.log('🚀 Script.js loaded at:', new Date().toLocaleTimeString());

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded at:', new Date().toLocaleTimeString());
    initializeApp();
});

// Initialize Application
async function initializeApp() {
    console.log('🎯 initializeApp() called');
    setupNavigation();
    setupScrollAnimations();
    setupCounterAnimations();
    console.log('📊 About to initialize charts...');
    await initializeCharts();
    await updateHeroMetrics(); // Load hero section data from API
    setupMarketMeta();
    setupCommodityHighlighting();
    setupTrendButtons();
    setupExportPerformanceToggles();
    setupFormHandling();
    setupSmoothScrolling();
    setupSidebarNavigation();
    enableScrollSnap();
    startRealTimeUpdates();
    console.log('✅ initializeApp() complete - All async operations finished');
}

// Sidebar Navigation Active State
function setupSidebarNavigation() {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    if (!sidebarLinks.length) return;

    const setActive = () => {
        let current = '';
        const sections = document.querySelectorAll('section');
        const scrollPos = window.scrollY + window.innerHeight / 3;
        sections.forEach(section => {
            if (scrollPos >= section.offsetTop) {
                current = section.id;
            }
        });
        sidebarLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    };
    window.addEventListener('scroll', setActive, { passive: true });
    setActive();
}


// Enable Scroll Snap (optional toggleable)
function enableScrollSnap() {
    // For now always enable; could be toggled via user setting later
    document.body.classList.add('enable-snap');
}

// Navigation Setup - Simplified for desktop only
function setupNavigation() {
    const navLinks = document.querySelectorAll('.sidebar-link');

    // Active link highlighting on scroll
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });
    });
}

// Scroll Animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('loaded');
            }
        });
    }, observerOptions);

    // Observe all sections and cards
    const animatedElements = document.querySelectorAll('section, .price-card, .news-card, .insight-card, .country-item');
    animatedElements.forEach(el => {
        el.classList.add('loading');
        observer.observe(el);
    });
}

// Counter Animations
function setupCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number');
    
    const animateCounter = (counter) => {
        const target = parseInt(counter.getAttribute('data-target'));
        const increment = target / 200;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        updateCounter();
    };

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    });

    counters.forEach(counter => {
        counterObserver.observe(counter);
    });
}

// Update Hero Section Metrics with Latest Data
async function updateHeroMetrics() {
    try {
        // Fetch latest production data
        const productionResponse = await fetch(`${API_BASE_URL}/production`);
        const productionResult = await productionResponse.json();
        
        if (productionResult.success && productionResult.data.length > 0) {
            const latestProduction = productionResult.data[productionResult.data.length - 1];
            
            // Update Production (convert to M tons with 1 decimal)
            const productionMT = (latestProduction.output_million_tons).toFixed(1);
            document.getElementById('hero-production').textContent = `${productionMT}M t`;
            
            // Update Area (convert to K ha)
            const areaKHa = Math.round(latestProduction.area_thousand_ha);
            document.getElementById('hero-area').textContent = `${areaKHa}K ha`;
            
            // Update Yield (2 decimals)
            const yieldValue = latestProduction.yield_tons_per_ha.toFixed(1);
            document.getElementById('hero-yield').textContent = `${yieldValue} t/ha`;
        }
        
        // Fetch export data for value and prices
        const exportResponse = await fetch(`${API_BASE_URL}/export`);
        const exportResult = await exportResponse.json();
        
        if (exportResult.success && exportResult.data.length > 0) {
            const latestExport = exportResult.data[exportResult.data.length - 1];
            
            // Update Export Value (convert to billions with 1 decimal)
            const exportValueB = (latestExport.export_value_million_usd / 1000).toFixed(1);
            document.getElementById('hero-value').textContent = `$${exportValueB}B`;
            
            // Update Domestic Price (VN price per ton)
            if (latestExport.price_vn_usd_per_ton) {
                document.getElementById('hero-price').textContent = `$${Math.round(latestExport.price_vn_usd_per_ton).toLocaleString()}`;
            }
        }
        
        console.log('✅ Hero metrics updated with latest data');
    } catch (error) {
        console.error('Error updating hero metrics:', error);
    }
}

// Chart Initialization
async function initializeCharts() {
    console.log('📈 initializeCharts() called');
    initializePriceChart();
    initializeExportPieChart();
    initializeWeatherDualChart();
    initializeTrendsChart();
    initializeExportPerformanceChart();
    initializeForecastChart();
    // Load production data from API
    console.log('🔄 Loading production data...');
    await loadProductionData();
    // Load export/price data from API
    await loadMarketPrices();
    // Load export performance data
    await loadExportPerformanceData();
    console.log('✅ initializeCharts() complete - Production data loaded');
}

// Load and update Market Overview prices
async function loadMarketPrices() {
    try {
        const response = await fetch(`${API_BASE_URL}/export`);
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            // Get latest year with actual data from metadata
            const latestActualYear = result.metadata?.latest_actual_year;
            
            // Filter data to find the records with actual data
            let latestExport, previousExport;
            
            if (latestActualYear) {
                // Find the record for latest actual year
                latestExport = result.data.find(d => d.year === latestActualYear);
                
                // Find the previous year with actual data
                const previousActualData = result.data
                    .filter(d => d.year < latestActualYear && 
                           (d.export_value_million_usd !== null || 
                            d.price_world_usd_per_ton !== null || 
                            d.price_vn_usd_per_ton !== null))
                    .sort((a, b) => b.year - a.year);
                
                previousExport = previousActualData.length > 0 ? previousActualData[0] : latestExport;
            } else {
                // Fallback to last record if metadata not available
                latestExport = result.data[result.data.length - 1];
                previousExport = result.data.length > 1 ? result.data[result.data.length - 2] : latestExport;
            }
            
            console.log(`📊 Using data from year ${latestExport.year} (latest actual year: ${latestActualYear})`);
            
            // Update Export Value card - ONLY in Market Overview section
            const exportValueCard = document.querySelector('#market [data-commodity="export-value"], .market-section [data-commodity="export-value"]');
            if (exportValueCard && latestExport.export_value_million_usd) {
                const valueEl = exportValueCard.querySelector('.price-value');
                if (valueEl) {
                    valueEl.textContent = `$${Math.round(latestExport.export_value_million_usd).toLocaleString()} M`;
                }
                
                // Update year display
                const yearSpan = exportValueCard.querySelector('.meta-item span:last-child');
                if (yearSpan) {
                    yearSpan.textContent = `${latestExport.year} Total`;
                }
                
                // Calculate change
                if (previousExport.export_value_million_usd) {
                    const change = ((latestExport.export_value_million_usd - previousExport.export_value_million_usd) / previousExport.export_value_million_usd * 100).toFixed(1);
                    const changeEl = exportValueCard.querySelector('.price-change');
                    if (changeEl) {
                        const spanEl = changeEl.querySelector('span');
                        const iconEl = changeEl.querySelector('i');
                        if (spanEl) spanEl.textContent = `${change >= 0 ? '↑' : '↓'}${Math.abs(change)}%`;
                        changeEl.classList.toggle('positive', change >= 0);
                        changeEl.classList.toggle('negative', change < 0);
                        if (iconEl) iconEl.className = change >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
                    }
                }
            }
            
            // Update World Price card - ONLY in Market Overview section
            const worldPriceCard = document.querySelector('#market [data-commodity="world-price"], .market-section [data-commodity="world-price"]');
            if (worldPriceCard && latestExport.price_world_usd_per_ton) {
                const valueEl = worldPriceCard.querySelector('.price-value');
                if (valueEl) {
                    valueEl.textContent = `$${Math.round(latestExport.price_world_usd_per_ton).toLocaleString()}`;
                }
                
                // Update date display
                const dateSpan = worldPriceCard.querySelector('.dynamic-date');
                if (dateSpan) {
                    const date = new Date(latestExport.year, 11, 31); // Dec 31 of the year
                    dateSpan.textContent = date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
                }
                
                if (previousExport.price_world_usd_per_ton) {
                    const change = ((latestExport.price_world_usd_per_ton - previousExport.price_world_usd_per_ton) / previousExport.price_world_usd_per_ton * 100).toFixed(1);
                    const changeEl = worldPriceCard.querySelector('.price-change');
                    if (changeEl) {
                        const spanEl = changeEl.querySelector('span');
                        const iconEl = changeEl.querySelector('i');
                        if (spanEl) spanEl.textContent = `${change >= 0 ? '↑' : '↓'}${Math.abs(change)}%`;
                        changeEl.classList.toggle('positive', change >= 0);
                        changeEl.classList.toggle('negative', change < 0);
                        if (iconEl) iconEl.className = change >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
                    }
                }
            }
            
            // Update VN Price card - ONLY in Market Overview section
            const vnPriceCard = document.querySelector('#market [data-commodity="vn-price"], .market-section [data-commodity="vn-price"]');
            if (vnPriceCard && latestExport.price_vn_usd_per_ton) {
                const valueEl = vnPriceCard.querySelector('.price-value');
                if (valueEl) {
                    valueEl.textContent = `$${Math.round(latestExport.price_vn_usd_per_ton).toLocaleString()}`;
                }
                
                // Update date display
                const dateSpan = vnPriceCard.querySelector('.dynamic-date');
                if (dateSpan) {
                    const date = new Date(latestExport.year, 11, 31);
                    dateSpan.textContent = date.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
                }
                
                if (previousExport.price_vn_usd_per_ton) {
                    const change = ((latestExport.price_vn_usd_per_ton - previousExport.price_vn_usd_per_ton) / previousExport.price_vn_usd_per_ton * 100).toFixed(1);
                    const changeEl = vnPriceCard.querySelector('.price-change');
                    if (changeEl) {
                        const spanEl = changeEl.querySelector('span');
                        const iconEl = changeEl.querySelector('i');
                        if (spanEl) spanEl.textContent = `${change >= 0 ? '↑' : '↓'}${Math.abs(change)}%`;
                        changeEl.classList.toggle('positive', change >= 0);
                        changeEl.classList.toggle('negative', change < 0);
                        if (iconEl) iconEl.className = change >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
                    }
                }
                
                // Update VN vs World comparison
                const volumeSpan = vnPriceCard.querySelector('.meta-item.volume span:last-child');
                if (volumeSpan && latestExport.price_world_usd_per_ton) {
                    const ratio = (latestExport.price_vn_usd_per_ton / latestExport.price_world_usd_per_ton * 100).toFixed(1);
                    volumeSpan.textContent = `${ratio}% vs World`;
                }
            }
            
            console.log(`✅ Market prices updated with data from year ${latestExport.year}`);
        }
    } catch (error) {
        console.error('Error loading market prices:', error);
    }
}

// Price Chart - Now loads real data from database
function initializePriceChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--text-secondary') || '#514338';
    const gridColor = styles.getPropertyValue('--border-color') || '#e6d9cc';

    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(218, 165, 32, 0.3)');
    gradient.addColorStop(1, 'rgba(218, 165, 32, 0.05)');

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],  // Will be filled with years from API
            datasets: [
                {
                    label: 'Export Volume (Tons)',
                    data: [],  // Will be filled from API
                    borderColor: '#DAA520',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#DAA520',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y-volume'
                },
                {
                    label: 'World Price (USD/ton)',
                    data: [],  // Will be filled from API
                    borderColor: '#CD853F',
                    backgroundColor: 'rgba(205, 133, 63, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#CD853F',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y-price'
                },
                {
                    label: 'VN Price (USD/ton)',
                    data: [],  // Will be filled from API
                    borderColor: '#8B4513',
                    backgroundColor: 'rgba(139, 69, 19, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#8B4513',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y-price'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: {
                        color: textColor.trim(),
                        font: { family: 'Inter', size: 11 }
                    }
                },
                tooltip: {
                    backgroundColor: '#ffffff',
                    titleColor: textColor.trim(),
                    bodyColor: textColor.trim(),
                    borderColor: gridColor.trim(),
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            // Format based on dataset
                            if (context.datasetIndex === 0) {
                                // Export Volume - in tons
                                label += Math.round(context.parsed.y).toLocaleString() + ' tons';
                            } else {
                                // Prices - per ton
                                label += '$' + Math.round(context.parsed.y).toLocaleString() + '/ton';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: textColor.trim() },
                    grid: { color: gridColor.trim() }
                },
                'y-volume': {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Export Volume (Tons)',
                        color: textColor.trim(),
                        font: { size: 11 }
                    },
                    ticks: { 
                        color: textColor.trim(),
                        callback: function(value) {
                            return value.toLocaleString() + ' tons';
                        }
                    },
                    grid: { color: gridColor.trim() }
                },
                'y-price': {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Price (USD/ton)',
                        color: textColor.trim(),
                        font: { size: 11 }
                    },
                    ticks: { 
                        color: textColor.trim(),
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    // Load real data from API
    loadPriceChartData();
}

// Load real price data from database (2005-2024)
async function loadPriceChartData() {
    console.log('🔄 Loading price chart data...');
    try {
        // Fetch production data for export volume (tons)
        const productionResponse = await fetch(`${API_BASE_URL}/production`);
        console.log('📡 Production API response status:', productionResponse.status);
        
        const productionResult = await productionResponse.json();
        console.log('📊 Production API result:', productionResult);
        
        // Fetch export/price data
        const exportResponse = await fetch(`${API_BASE_URL}/export`);
        const exportResult = await exportResponse.json();
        
        if (productionResult.success && exportResult.success && productionResult.data.length > 0 && exportResult.data.length > 0) {
            // Get years from production data
            const years = productionResult.data.map(item => item.year);
            
            // Get export volume in TONS (not million tons)
            const exportVolumes = productionResult.data.map(item => Math.round(item.export_tons || 0));
            
            // Get prices from export data
            const worldPrices = exportResult.data.map(item => item.price_world_usd_per_ton || 0);
            const vnPrices = exportResult.data.map(item => item.price_vn_usd_per_ton || 0);
            
            console.log('📅 Years:', years);
            console.log('� Export Volumes (tons):', exportVolumes);
            console.log('🌍 World Prices:', worldPrices);
            console.log('🇻🇳 VN Prices:', vnPrices);
            
            // Check if chart exists
            if (!priceChart) {
                console.error('❌ priceChart is not initialized!');
                return;
            }
            
            // Update chart data
            priceChart.data.labels = years;
            priceChart.data.datasets[0].data = exportVolumes;
            priceChart.data.datasets[1].data = worldPrices;
            priceChart.data.datasets[2].data = vnPrices;
            
            console.log('📊 Chart data updated, calling update()...');
            
            // Update chart
            priceChart.update();
            
            console.log('✅ Price chart updated with real data from database (2005-2024)');
            console.log(`Export volumes range: ${Math.min(...exportVolumes).toLocaleString()} - ${Math.max(...exportVolumes).toLocaleString()} tons`);
            console.log(`World prices range: $${Math.min(...worldPrices).toLocaleString()} - $${Math.max(...worldPrices).toLocaleString()}/ton`);
            console.log(`VN prices range: $${Math.min(...vnPrices).toLocaleString()} - $${Math.max(...vnPrices).toLocaleString()}/ton`);
        } else {
            console.error('❌ No data returned from API or API failed');
        }
    } catch (error) {
        console.error('❌ Error loading price chart data:', error);
    }
}

// Populate dynamic date for Market Overview cards
function setupMarketMeta() {
    const dateSpans = document.querySelectorAll('.price-card .dynamic-date');
    if (!dateSpans.length) return;
    const now = new Date();
    const formatted = now.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
    dateSpans.forEach(span => span.textContent = formatted);
}

// Commodity highlighting interaction - ONLY for Market Overview section
function setupCommodityHighlighting() {
    // Only select price cards in Market Overview section, not Weather cards
    const marketSection = document.querySelector('#market, .market-section');
    if (!marketSection) return;
    
    const cards = marketSection.querySelectorAll('.price-card');
    if (!cards.length || !priceChart) return;

    cards.forEach(card => {
        card.addEventListener('click', () => {
            const commodity = card.getAttribute('data-commodity');
            activateCommodity(commodity);
        });
        card.style.cursor = 'pointer';
    });
    
    // Default active first card - only if it exists in Market Overview
    const firstCard = cards[0];
    if (firstCard) {
        const firstCommodity = firstCard.getAttribute('data-commodity');
        activateCommodity(firstCommodity);
    }
}

function activateCommodity(commodity) {
    const cards = document.querySelectorAll('.price-card');
    cards.forEach(c => {
        if (c.getAttribute('data-commodity') === commodity) {
            c.classList.add('active');
            c.classList.remove('dimmed');
        } else {
            c.classList.remove('active');
            c.classList.add('dimmed');
        }
    });

    if (!priceChart) return;
    // Adjust dataset opacities
    priceChart.data.datasets.forEach(ds => {
        const isMatch = ds.label.toLowerCase() === commodity;
        ds.borderWidth = isMatch ? 3 : 2;
        ds.borderColor = adjustAlpha(ds.borderColor, isMatch ? 1 : 0.5);
        ds.backgroundColor = adjustFillAlpha(ds.backgroundColor, isMatch ? 0.35 : 0.1);
        ds.pointRadius = isMatch ? 5 : 3;
        ds.pointBackgroundColor = adjustAlpha(ds.pointBackgroundColor, isMatch ? 1 : 0.45);
    });
    priceChart.update();
}

// Utility: adjust rgba/hex alpha
function adjustAlpha(color, alpha) {
    // If already rgba
    if (color.startsWith('rgba')) {
        return color.replace(/rgba\(([^,]+),([^,]+),([^,]+),[^)]+\)/, (m, r, g, b) => `rgba(${r},${g},${b},${alpha})`);
    }
    // Hex to rgba
    if (color.startsWith('#')) {
        const bigint = parseInt(color.slice(1), 16);
        let r, g, b;
        if (color.length === 7) {
            r = (bigint >> 16) & 255;
            g = (bigint >> 8) & 255;
            b = bigint & 255;
        } else {
            // shorthand #abc
            r = parseInt(color[1] + color[1], 16);
            g = parseInt(color[2] + color[2], 16);
            b = parseInt(color[3] + color[3], 16);
        }
        return `rgba(${r},${g},${b},${alpha})`;
    }
    return color; // fallback
}

function adjustFillAlpha(color, alpha) {
    // For gradient keep original; simple rgba replacement otherwise
    if (typeof color === 'object') return color;
    return adjustAlpha(color, alpha);
}

// Export Pie Chart
function initializeExportPieChart() {
    const ctx = document.getElementById('exportPieChart');
    if (!ctx) return;
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--text-secondary') || '#514338';
    const gridColor = styles.getPropertyValue('--border-color') || '#e6d9cc';

    exportPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['United States', 'Germany', 'Japan', 'Italy', 'France', 'Others'],
            datasets: [{
                data: [22.5, 18.3, 15.7, 12.1, 9.8, 21.6],
                backgroundColor: [
                    '#d29a52', // US
                    '#b77b40', // Germany
                    '#9c6644', // Japan
                    '#c69253', // Italy
                    '#e3b17a', // France
                    '#d8c2a6'  // Others
                ],
                borderColor: '#fff',
                borderWidth: 2,
                hoverOffset: 14
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display:false },
                tooltip: {
                    backgroundColor: '#ffffff',
                    titleColor: textColor.trim(),
                    bodyColor: textColor.trim(),
                    borderColor: gridColor.trim(),
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                duration: 2000
            },
            onHover: (evt, elements) => {
                document.body.style.cursor = elements.length ? 'pointer' : 'default';
            }
        }
    });

    buildDonutLegend();
}

function buildDonutLegend(){
    const legendContainer = document.getElementById('donutLegend');
    if(!legendContainer || !exportPieChart) return;
    legendContainer.innerHTML = '';
    const { labels, datasets } = exportPieChart.data;
    const colors = datasets[0].backgroundColor;
    labels.forEach((label, idx) => {
        const entry = document.createElement('div');
        entry.className = 'legend-entry';
        entry.innerHTML = `<span class="color-box" style="background:${colors[idx]}"></span><span>${label}</span><strong>${datasets[0].data[idx]}%</strong>`;
        entry.addEventListener('click', () => toggleSlice(idx));
        legendContainer.appendChild(entry);
    });
}

function toggleSlice(index){
    if(!exportPieChart) return;
    const meta = exportPieChart.getDatasetMeta(0);
    const slice = meta.data[index];
    slice.outerRadius = slice.outerRadius === slice.options.radius + 20 ? slice.options.radius + 10 : slice.options.radius + 20;
    exportPieChart.draw();
}

// Weather Dual Axis Chart
function initializeWeatherDualChart(){
    const ctx = document.getElementById('weatherDualChart');
    if(!ctx) return;
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--text-secondary') || '#4b2e05';
    const gridColor = '#f4e9dd';
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    const rainfallData = [15, 20, 45, 120, 180, 220, 250, 280, 200, 150, 80, 25];
    const tempData = [22, 24, 26, 28, 27, 25, 24, 24, 25, 26, 24, 22];

    const gradientLine = ctx.getContext('2d').createLinearGradient(0,0,0,300);
    gradientLine.addColorStop(0,'rgba(216,156,58,0.5)');
    gradientLine.addColorStop(1,'rgba(216,156,58,0.05)');

    climateChart = new Chart(ctx, {
        type:'bar',
        data:{
            labels: months,
            datasets:[
                {
                    label:'Rainfall (mm)',
                    data: rainfallData,
                    backgroundColor:'rgba(132,170,242,0.65)',
                    borderColor:'#84aaf2',
                    borderWidth:1,
                    yAxisID:'y'
                },
                {
                    label:'Temperature (°C)',
                    data: tempData,
                    type:'line',
                    borderColor:'#d89c3a',
                    backgroundColor:gradientLine,
                    tension:0.35,
                    yAxisID:'y1',
                    pointBackgroundColor:'#d89c3a',
                    pointBorderColor:'#fff',
                    pointBorderWidth:2,
                    fill:true
                }
            ]
        },
        options:{
            responsive:true,
            maintainAspectRatio:false,
            plugins:{
                legend:{ 
                    labels:{ 
                        color:textColor.trim(), 
                        font:{ family:'Inter', size: 13 },
                        padding: 15
                    },
                    position: 'top'
                },
                tooltip:{
                    mode:'index',
                    intersect:false,
                    backgroundColor:'#ffffff',
                    titleColor:textColor.trim(),
                    bodyColor:textColor.trim(),
                    borderColor:'#e5c9aa',
                    borderWidth:1
                }
            },
            scales:{
                x:{
                    ticks:{ color:textColor.trim(), font: { size: 12 } },
                    grid:{ color:gridColor }
                },
                y:{
                    position:'left',
                    title: {
                        display: true,
                        text: 'Rainfall (mm)',
                        color: textColor.trim()
                    },
                    ticks:{ color:textColor.trim(), font: { size: 12 } },
                    grid:{ color:gridColor }
                },
                y1:{
                    position:'right',
                    title: {
                        display: true,
                        text: 'Temperature (°C)',
                        color: textColor.trim()
                    },
                    ticks:{ color:textColor.trim(), font: { size: 12 } },
                    grid:{ drawOnChartArea:false }
                }
            },
            animation:{ duration:1200, easing:'easeOutQuart' }
        }
    });
}

// Trends Chart
function initializeTrendsChart(){
    const ctx = document.getElementById('trendsChart');
    if(!ctx) return;
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--text-secondary') || '#4b2e05';
    const gridColor = '#e9d6c3';
    const years = Array.from({length:20},(_,i)=> (2005+i).toString());

    const gProd = ctx.getContext('2d').createLinearGradient(0,0,0,300);
    gProd.addColorStop(0,'rgba(196,127,78,0.4)');
    gProd.addColorStop(1,'rgba(196,127,78,0.05)');
    const gArea = ctx.getContext('2d').createLinearGradient(0,0,0,300);
    gArea.addColorStop(0,'rgba(166,94,46,0.35)');
    gArea.addColorStop(1,'rgba(166,94,46,0.05)');
    const gYield = ctx.getContext('2d').createLinearGradient(0,0,0,300);
    gYield.addColorStop(0,'rgba(227,177,122,0.45)');
    gYield.addColorStop(1,'rgba(227,177,122,0.06)');

    trendsChart = new Chart(ctx, {
        type:'line',
        data:{
            labels: years,
            datasets:[
                {
                    label:'Production (Tons)',
                    data: generateTrendData(1.5, 2.5, years.length),
                    borderColor:'#c47f4e',
                    backgroundColor:gProd,
                    fill:true,
                    tension:0.35,
                    pointBackgroundColor:'#c47f4e',
                    pointBorderColor:'#fff',
                    pointBorderWidth:2
                },
                {
                    label:'Area (ha)',
                    data: generateTrendData(450, 650, years.length),
                    borderColor:'#a65e2e',
                    backgroundColor:gArea,
                    fill:true,
                    tension:0.35,
                    pointBackgroundColor:'#a65e2e',
                    pointBorderColor:'#fff',
                    pointBorderWidth:2
                },
                {
                    label:'Yield (t/ha)',
                    data: generateTrendData(2.2, 3.2, years.length).map(v=> (v/years.length)+(2.2 + Math.random()*1)),
                    borderColor:'#e3b17a',
                    backgroundColor:gYield,
                    fill:true,
                    tension:0.35,
                    pointBackgroundColor:'#e3b17a',
                    pointBorderColor:'#fff',
                    pointBorderWidth:2
                }
            ]
        },
        options:{
            responsive:true,
            maintainAspectRatio:false,
            plugins:{ 
                legend:{ labels:{ color:textColor.trim(), font:{ family:'Inter' } } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                // Format large numbers with thousand separators
                                label += context.parsed.y.toLocaleString();
                            }
                            return label;
                        }
                    }
                }
            },
            scales:{
                x:{ ticks:{ color:textColor.trim() }, grid:{ color:gridColor } },
                y:{ 
                    ticks:{ 
                        color:textColor.trim(),
                        callback: function(value) {
                            // Format Y-axis with thousand separators
                            return value.toLocaleString();
                        }
                    }, 
                    grid:{ color:gridColor } 
                }
            },
            animation:{ duration:1400, easing:'easeOutQuart' }
        }
    });
    setupProductionToggles();
}

function setupProductionToggles(){
    const buttons = document.querySelectorAll('.prod-toggle-btn');
    if(!buttons.length || !trendsChart) return;
    buttons.forEach((btn,idx)=>{
        btn.addEventListener('click',()=>{
            buttons.forEach(b=>b.classList.remove('active'));
            btn.classList.add('active');
            const focus = btn.getAttribute('data-focus');
            trendsChart.data.datasets.forEach(ds => {
                const match = ds.label.toLowerCase().includes(focus);
                ds.borderWidth = match?3:2;
                ds.borderColor = adjustAlpha(ds.borderColor, match?1:0.5);
                ds.pointRadius = match?5:3;
                ds.backgroundColor = ds.backgroundColor; // keep gradient
                ds.hidden = false;
                ds.opacity = match?1:0.5;
            });
            trendsChart.update();
        });
    });
}

// ============================================================================
// EXPORT PERFORMANCE CHART (3 columns from coffee_export table)
// ============================================================================

// Initialize Export Performance Chart
function initializeExportPerformanceChart() {
    const ctx = document.getElementById('exportPerformanceChart');
    if (!ctx) return;
    
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--text-secondary') || '#514338';
    const gridColor = styles.getPropertyValue('--border-color') || '#e6d9cc';
    
    exportPerformanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Export Value (Million USD)',
                    data: [],
                    borderColor: '#2ecc71',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y-value',
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'World Price (USD/ton)',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    yAxisID: 'y-price',
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'VN Price (USD/ton)',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    yAxisID: 'y-price',
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: textColor,
                        font: { size: 12, weight: '500' },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#333',
                    bodyColor: '#666',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.datasetIndex === 0) {
                                    // Export value
                                    label += '$' + context.parsed.y.toLocaleString() + ' M';
                                } else {
                                    // Prices
                                    label += '$' + context.parsed.y.toLocaleString();
                                }
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: gridColor,
                        display: true
                    },
                    ticks: {
                        color: textColor,
                        font: { size: 11 }
                    }
                },
                'y-value': {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Export Value (Million USD)',
                        color: '#2ecc71',
                        font: { size: 12, weight: 'bold' }
                    },
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                'y-price': {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Price (USD per ton)',
                        color: '#3498db',
                        font: { size: 12, weight: 'bold' }
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: textColor,
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Load Export Performance Data from API
async function loadExportPerformanceData() {
    try {
        const response = await fetch(`${API_BASE_URL}/export`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ Export performance data loaded:', result);
        
        // Update chart
        updateExportPerformanceChart(result.data);
        
        // Update cards
        updateExportPerformanceCards(result.data);
        
    } catch (error) {
        console.error('❌ Error loading export performance data:', error);
    }
}

// Update Export Performance Chart with data
function updateExportPerformanceChart(data) {
    if (!exportPerformanceChart || !data || data.length === 0) return;
    
    const years = data.map(d => d.year);
    const exportValues = data.map(d => d.export_value_million_usd);
    const worldPrices = data.map(d => d.price_world_usd_per_ton);
    const vnPrices = data.map(d => d.price_vn_usd_per_ton);
    
    exportPerformanceChart.data.labels = years;
    exportPerformanceChart.data.datasets[0].data = exportValues;
    exportPerformanceChart.data.datasets[1].data = worldPrices;
    exportPerformanceChart.data.datasets[2].data = vnPrices;
    
    exportPerformanceChart.update();
    
    console.log('📊 Export performance chart updated with', data.length, 'years');
}

// Update Export Performance Cards
function updateExportPerformanceCards(data) {
    if (!data || data.length === 0) return;
    
    const latest = data[data.length - 1];
    const previous = data[data.length - 2];
    
    // Update Export Value card
    const exportValueCard = document.querySelector('[data-commodity="export-value"]');
    if (exportValueCard) {
        const valueEl = exportValueCard.querySelector('.price-value');
        const changeEl = exportValueCard.querySelector('.price-change span');
        const changeContainer = exportValueCard.querySelector('.price-change');
        
        const billions = (latest.export_value_million_usd / 1000).toFixed(1);
        if (valueEl) valueEl.textContent = `$${billions} B`;
        
        if (previous && changeEl) {
            const pctChange = ((latest.export_value_million_usd - previous.export_value_million_usd) / previous.export_value_million_usd * 100);
            changeEl.textContent = `${pctChange > 0 ? '↑' : '↓'}${Math.abs(pctChange).toFixed(1)}%`;
            changeContainer.classList.toggle('positive', pctChange >= 0);
            changeContainer.classList.toggle('negative', pctChange < 0);
            changeContainer.querySelector('i').className = pctChange >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        }
    }
    
    // Update World Price card
    const worldPriceCard = document.querySelector('[data-commodity="world-price"]');
    if (worldPriceCard) {
        const valueEl = worldPriceCard.querySelector('.price-value');
        const changeEl = worldPriceCard.querySelector('.price-change span');
        const changeContainer = worldPriceCard.querySelector('.price-change');
        
        if (valueEl) valueEl.textContent = `$${Math.round(latest.price_world_usd_per_ton).toLocaleString()}`;
        
        if (previous && changeEl) {
            const pctChange = ((latest.price_world_usd_per_ton - previous.price_world_usd_per_ton) / previous.price_world_usd_per_ton * 100);
            changeEl.textContent = `${pctChange > 0 ? '↑' : '↓'}${Math.abs(pctChange).toFixed(1)}%`;
            changeContainer.classList.toggle('positive', pctChange >= 0);
            changeContainer.classList.toggle('negative', pctChange < 0);
            changeContainer.querySelector('i').className = pctChange >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        }
    }
    
    // Update VN Price card
    const vnPriceCard = document.querySelector('[data-commodity="vn-price"]');
    if (vnPriceCard) {
        const valueEl = vnPriceCard.querySelector('.price-value');
        const changeEl = vnPriceCard.querySelector('.price-change span');
        const changeContainer = vnPriceCard.querySelector('.price-change');
        
        if (valueEl) valueEl.textContent = `$${Math.round(latest.price_vn_usd_per_ton).toLocaleString()}`;
        
        if (previous && changeEl) {
            const pctChange = ((latest.price_vn_usd_per_ton - previous.price_vn_usd_per_ton) / previous.price_vn_usd_per_ton * 100);
            changeEl.textContent = `${pctChange > 0 ? '↑' : '↓'}${Math.abs(pctChange).toFixed(1)}%`;
            changeContainer.classList.toggle('positive', pctChange >= 0);
            changeContainer.classList.toggle('negative', pctChange < 0);
            changeContainer.querySelector('i').className = pctChange >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        }
        
        // Update comparison with world price
        const volumeSpan = vnPriceCard.querySelector('.meta-item.volume span:last-child');
        if (volumeSpan) {
            const ratio = (latest.price_vn_usd_per_ton / latest.price_world_usd_per_ton * 100).toFixed(1);
            volumeSpan.textContent = `vs World: ${ratio}%`;
        }
    }
    
    console.log('💳 Export performance cards updated');
}

// Setup Export Performance Toggle Buttons
function setupExportPerformanceToggles() {
    const toggleButtons = document.querySelectorAll('.export-toggle-btn');
    
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const focus = this.getAttribute('data-focus');
            
            // Update active state
            toggleButtons.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-pressed', 'false');
            });
            this.classList.add('active');
            this.setAttribute('aria-pressed', 'true');
            
            // Update chart visibility
            updateExportPerformanceChartFocus(focus);
        });
    });
}

// Update chart focus based on selected toggle
function updateExportPerformanceChartFocus(focus) {
    if (!exportPerformanceChart) return;
    
    const datasets = exportPerformanceChart.data.datasets;
    
    switch(focus) {
        case 'value':
            datasets[0].hidden = false; // Export Value
            datasets[1].hidden = true;  // World Price
            datasets[2].hidden = true;  // VN Price
            break;
        case 'world-price':
            datasets[0].hidden = true;
            datasets[1].hidden = false;
            datasets[2].hidden = true;
            break;
        case 'vn-price':
            datasets[0].hidden = true;
            datasets[1].hidden = true;
            datasets[2].hidden = false;
            break;
        case 'all':
        default:
            datasets[0].hidden = false;
            datasets[1].hidden = false;
            datasets[2].hidden = false;
    }
    
    exportPerformanceChart.update();
}

// Forecast Chart
function initializeForecastChart() {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--text-secondary') || '#514338';
    const gridColor = styles.getPropertyValue('--border-color') || '#e6d9cc';

    const months = ['Oct 2025', 'Nov 2025', 'Dec 2025', 'Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026'];

    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [
                {
                    label: 'Historical Price',
                    data: [2850, 2890, 2920, null, null, null, null, null],
                    borderColor: '#CD853F',
                    backgroundColor: 'rgba(205, 133, 63, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#CD853F'
                },
                {
                    label: 'Predicted Price',
                    data: [null, null, 2920, 3100, 3250, 3180, 3300, 3420],
                    borderColor: '#DAA520',
                    backgroundColor: 'rgba(218, 165, 32, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderDash: [5, 5],
                    pointBackgroundColor: '#DAA520'
                },
                {
                    label: 'Confidence Interval',
                    data: [null, null, 2920, 3200, 3400, 3300, 3450, 3600],
                    borderColor: 'rgba(218, 165, 32, 0.3)',
                    backgroundColor: 'rgba(218, 165, 32, 0.05)',
                    fill: '+1',
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: textColor.trim(),
                        font: { family: 'Inter' }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: textColor.trim() },
                    grid: { color: gridColor.trim() }
                },
                y: {
                    ticks: { 
                        color: textColor.trim(),
                        callback: function(value) {
                            return '$' + value;
                        }
                    },
                    grid: { color: gridColor.trim() }
                }
            }
        }
    });
}

// Trend Button Setup
function setupTrendButtons() {
    const trendButtons = document.querySelectorAll('.trend-btn');
    
    trendButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            trendButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            button.classList.add('active');
            
            // Update chart based on selection
            const chartType = button.getAttribute('data-chart');
            updateTrendsChart(chartType);
        });
    });
}

// Load Production Data from API
let productionData = null;
let selectedProductionProvince = 'national';

async function loadProductionData() {
    try {
        const response = await fetch(`${API_BASE_URL}/production`);
        const result = await response.json();
        
        if (result.success) {
            productionData = result.data;
            console.log('Production data loaded:', productionData.length, 'years');
            
            // Update chart with real data
            updateTrendsChartWithData();
            
            // Update production cards
            updateProductionCards(productionData);
        } else {
            console.error('Failed to load production data:', result.error);
        }
    } catch (error) {
        console.error('Error loading production data:', error);
    }
}

function updateTrendsChartWithData() {
    if (!trendsChart || !productionData) return;
    
    const years = productionData.map(d => d.year.toString());
    // Convert from millions to tons and thousands to hectares
    const production = productionData.map(d => d.output_million_tons * 1000000);
    const area = productionData.map(d => d.area_thousand_ha * 1000);
    const yieldData = productionData.map(d => d.yield_tons_per_ha);
    
    // Update chart labels and datasets
    trendsChart.data.labels = years;
    trendsChart.data.datasets[0].data = production;
    trendsChart.data.datasets[1].data = area;
    trendsChart.data.datasets[2].data = yieldData;
    
    trendsChart.update();
}

function updateProductionCards(data) {
    if (!data || data.length === 0) return;
    
    // Get latest year data
    const latest = data[data.length - 1];
    const previous = data[data.length - 2];
    
    // Calculate changes
    const prodChange = ((latest.output_million_tons - previous.output_million_tons) / previous.output_million_tons * 100).toFixed(1);
    const areaChange = ((latest.area_thousand_ha - previous.area_thousand_ha) / previous.area_thousand_ha * 100).toFixed(1);
    const yieldChange = ((latest.yield_tons_per_ha - previous.yield_tons_per_ha) / previous.yield_tons_per_ha * 100).toFixed(1);
    
    // Update Production card
    const prodCard = document.querySelector('[data-commodity="production"]');
    if (prodCard) {
        const outputTons = Math.round(latest.output_million_tons * 1000000);
        prodCard.querySelector('.price-value').textContent = outputTons.toLocaleString() + ' t';
        const changeEl = prodCard.querySelector('.price-change');
        changeEl.querySelector('span').textContent = `${prodChange > 0 ? '+' : ''}${prodChange}%`;
        changeEl.classList.toggle('positive', prodChange >= 0);
        changeEl.classList.toggle('negative', prodChange < 0);
        changeEl.querySelector('i').className = prodChange >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
        prodCard.querySelector('.price-label').textContent = `${latest.year} total`;
    }
    
    // Update Area card
    const areaCard = document.querySelector('[data-commodity="area"]');
    if (areaCard) {
        const areaHa = Math.round(latest.area_thousand_ha * 1000);
        areaCard.querySelector('.price-value').textContent = areaHa.toLocaleString() + ' ha';
        const changeEl = areaCard.querySelector('.price-change');
        changeEl.querySelector('span').textContent = `${areaChange > 0 ? '+' : ''}${areaChange}%`;
        changeEl.classList.toggle('positive', areaChange >= 0);
        changeEl.classList.toggle('negative', areaChange < 0);
        changeEl.querySelector('i').className = areaChange >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
    }
    
    // Update Yield card
    const yieldCard = document.querySelector('[data-commodity="yield"]');
    if (yieldCard) {
        const yieldValue = parseFloat(latest.yield_tons_per_ha).toFixed(2);
        yieldCard.querySelector('.price-value').textContent = `${yieldValue} t/ha`;
        const changeEl = yieldCard.querySelector('.price-change');
        changeEl.querySelector('span').textContent = `${yieldChange > 0 ? '+' : ''}${yieldChange}%`;
        changeEl.classList.toggle('positive', yieldChange >= 0);
        changeEl.classList.toggle('negative', yieldChange < 0);
        changeEl.querySelector('i').className = yieldChange >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
    }
    
    // Update summary text
    const summaryEl = document.querySelector('.production-summary');
    if (summaryEl) {
        const maxProd = Math.max(...data.map(d => d.output_million_tons));
        const maxYear = data.find(d => d.output_million_tons === maxProd).year;
        const maxProdTons = Math.round(maxProd * 1000000).toLocaleString();
        summaryEl.innerHTML = `Vietnam's coffee production has grown steadily, peaking at <strong>${maxProdTons} tons</strong> in ${maxYear}.`;
    }
}

// Update Trends Chart
function updateTrendsChart(type) {
    if (!trendsChart) return;
    
    let data, label, color;
    
    switch(type) {
        case 'production':
            data = generateTrendData(1.5, 2.5, 20);
            label = 'Production (Million Tons)';
            color = '#DAA520';
            break;
        case 'area':
            data = generateTrendData(500, 650, 20);
            label = 'Area (Thousand Hectares)';
            color = '#CD853F';
            break;
        case 'yield':
            data = generateTrendData(2.8, 3.8, 20);
            label = 'Yield (Tons/Hectare)';
            color = '#8B4513';
            break;
    }
    
    trendsChart.data.datasets[0].data = data;
    trendsChart.data.datasets[0].label = label;
    trendsChart.data.datasets[0].borderColor = color;
    trendsChart.data.datasets[0].backgroundColor = color.replace(')', ', 0.1)');
    trendsChart.data.datasets[0].pointBackgroundColor = color;
    
    trendsChart.update('active');
}


// Form Handling
function setupFormHandling() {
    const contactForm = document.querySelector('.contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(contactForm);
            const name = formData.get('name');
            const email = formData.get('email');
            const message = formData.get('message');
            
            // Simulate form submission
            const submitBtn = contactForm.querySelector('.submit-btn');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            submitBtn.disabled = true;
            
            setTimeout(() => {
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Message Sent!';
                submitBtn.style.background = 'linear-gradient(45deg, #4CAF50, #45a049)';
                
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    submitBtn.style.background = '';
                    contactForm.reset();
                }, 3000);
            }, 2000);
        });
    }
}

// Smooth Scrolling
function setupSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Utility Functions
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const offsetTop = section.offsetTop - 80;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

function generateDateLabels(days) {
    const labels = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    return labels;
}

function generatePriceData(basePrice, days) {
    const data = [];
    let currentPrice = basePrice;
    
    for (let i = 0; i < days; i++) {
        const change = (Math.random() - 0.5) * 100;
        currentPrice += change;
        currentPrice = Math.max(currentPrice, basePrice * 0.8);
        currentPrice = Math.min(currentPrice, basePrice * 1.2);
        data.push(Math.round(currentPrice));
    }
    
    return data;
}

function generateTrendData(min, max, years) {
    const data = [];
    let currentValue = min;
    const increment = (max - min) / years;
    
    for (let i = 0; i < years; i++) {
        const variation = (Math.random() - 0.5) * 0.2;
        currentValue += increment + variation;
        data.push(Number(currentValue.toFixed(2)));
    }
    
    return data;
}

// Real-time Data Updates (Simulated)
function startRealTimeUpdates() {
    setInterval(() => {
        updatePriceCards();
        updateWeatherData();
    }, 30000); // Update every 30 seconds
}

function updatePriceCards() {
    const priceCards = document.querySelectorAll('.price-card');
    
    priceCards.forEach(card => {
        const priceValue = card.querySelector('.price-value');
        const priceChange = card.querySelector('.price-change span');
        const changeIcon = card.querySelector('.price-change i');
        
        if (priceValue) {
            const currentPrice = parseInt(priceValue.textContent.replace(/[^0-9]/g, ''));
            const change = (Math.random() - 0.5) * 100;
            const newPrice = Math.round(currentPrice + change);
            const percentage = ((change / currentPrice) * 100).toFixed(1);
            
            priceValue.textContent = '$' + newPrice.toLocaleString();
            priceChange.textContent = (percentage > 0 ? '+' : '') + percentage + '%';
            
            if (percentage > 0) {
                priceChange.parentElement.className = 'price-change positive';
                changeIcon.className = 'fas fa-arrow-up';
            } else {
                priceChange.parentElement.className = 'price-change negative';
                changeIcon.className = 'fas fa-arrow-down';
            }
        }
    });
}

function updateWeatherData() {
    const temperature = document.querySelector('.temperature');
    const humiditySpan = document.querySelector('.weather-details .weather-item:nth-child(1) span');
    const rainfallSpan = document.querySelector('.weather-details .weather-item:nth-child(2) span');
    
    if (temperature) {
        const temp = 20 + Math.random() * 10;
        temperature.textContent = Math.round(temp) + '°C';
    }
    
    if (humiditySpan) {
        const hum = 60 + Math.random() * 30;
        humiditySpan.textContent = 'Humidity: ' + Math.round(hum) + '%';
    }
    
    if (rainfallSpan) {
        const rain = Math.random() * 100;
        rainfallSpan.textContent = 'Rainfall: ' + Math.round(rain) + 'mm';
    }
}



// News Card Interactions
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('read-more-btn')) {
        e.preventDefault();
        const newsCard = e.target.closest('.news-card');
        const title = newsCard.querySelector('h3').textContent;
        
        // Simulate opening full article
        alert(`Opening full article: "${title}"\n\nThis would normally navigate to the full article page.`);
    }
});

// Parallax Effect for Hero Section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const heroBackground = document.querySelector('.hero-background');
    
    if (heroBackground) {
        const rate = scrolled * -0.5;
        heroBackground.style.transform = `translateY(${rate}px)`;
    }
});

// Loading Screen Effect
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
    
    // Animate elements in sequence
    const elementsToAnimate = document.querySelectorAll('.price-card, .news-card, .insight-card');
    elementsToAnimate.forEach((element, index) => {
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Performance Optimization
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Debounced scroll handler
const debouncedScrollHandler = debounce(() => {
    // Handle scroll-heavy operations here if needed
}, 16); // ~60fps

window.addEventListener('scroll', debouncedScrollHandler);

// Initialize real-time updates when page loads
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(startRealTimeUpdates, 5000); // Start updates after 5 seconds
});

// Intersection reveal animations for redesigned sections
const revealObserver = new IntersectionObserver((entries)=>{
    entries.forEach(entry => {
        if(entry.isIntersecting){
            entry.target.classList.add('in-view');
            revealObserver.unobserve(entry.target);
        }
    });
},{ threshold:0.15 });

document.querySelectorAll('.reveal').forEach(el=> revealObserver.observe(el));

// Sync aria-pressed state for toggle buttons (weather & production)
function syncPressed(buttons){
    buttons.forEach(btn => {
        btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    });
}

// Observe activation changes
const mutationConfig = { attributes:true, attributeFilter:['class'] };
document.querySelectorAll('.wx-toggle-btn, .prod-toggle-btn').forEach(btn => {
    new MutationObserver(()=>{
        const groupButtons = btn.closest('[role="group"]').querySelectorAll('button');
        syncPressed(groupButtons);
    }).observe(btn, mutationConfig);
});

// ========================================
// Year Selector for Export Data
// ========================================

// Country flags mapping
const countryFlags = {
    'United States': '🇺🇸',
    'Germany': '🇩🇪',
    'Japan': '🇯🇵',
    'Italy': '🇮🇹',
    'France': '🇫🇷',
    'China': '🇨🇳',
    'Belgium': '🇧🇪',
    'Spain': '🇪🇸',
    'United Kingdom': '🇬🇧',
    'Netherlands': '🇳🇱',
    'Others': '🌍'
};

// Initialize year dropdown (2005 to current year - 1)
function initializeYearDropdown() {
    const currentYear = new Date().getFullYear();
    const yearSelect = document.getElementById('exportYear');
    if (!yearSelect) return;

    // Generate all years from current-1 down to 2005
    for (let year = currentYear - 1; year >= 2005; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }

    // Set default to latest year (current - 1)
    yearSelect.value = currentYear - 1;

    // Add event listener for year change
    yearSelect.addEventListener('change', function() {
        const selectedYear = this.value;
        loadExportDataForYear(selectedYear);
    });
}

// Function to load export data for selected year
async function loadExportDataForYear(year) {
    console.log(`Loading export data for year: ${year}`);
    
    // Update year display
    const yearDisplay = document.getElementById('selectedYearDisplay');
    if (yearDisplay) {
        yearDisplay.textContent = year;
    }

    try {
        // Call API to get real data from database
        const data = await fetchExportDataFromDatabase(year);
        
        // Update the chart and country list
        updateExportVisualization(data);
    } catch (error) {
        console.error('Error loading export data:', error);
        // Show error message to user
        showErrorMessage('Failed to load export data for ' + year);
    }
}

// Fetch export data from API
async function fetchExportDataFromDatabase(year) {
    try {
        const response = await fetch(`${API_BASE_URL}/exports/top-countries?year=${year}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Show forecast indicator if data is forecasted
        updateForecastIndicator(result.is_forecast);
        
        // Transform API response to match expected format
        return {
            countries: result.countries || [],
            others: result.others?.percentage || 0,
            is_forecast: result.is_forecast || false
        };
    } catch (error) {
        console.error('API Error:', error);
        // Return empty data on error
        return {
            countries: [],
            others: 0,
            is_forecast: false
        };
    }
}

// Update forecast indicator
function updateForecastIndicator(isForecast) {
    const yearDisplay = document.getElementById('selectedYearDisplay');
    if (!yearDisplay) return;
    
    if (isForecast) {
        yearDisplay.innerHTML = `${yearDisplay.textContent} <span style="font-size: 0.8em; color: #f39c12;">(Forecast)</span>`;
    }
}

// Update chart and country list with new data
function updateExportVisualization(data) {
    if (!data || !data.countries) return;

    // Update country list
    updateCountryList(data.countries, data.others);
    
    // Update pie chart
    updatePieChart(data.countries, data.others);
}

// Update country list display
function updateCountryList(countries, othersPercentage) {
    const countryListContainer = document.getElementById('countryList');
    if (!countryListContainer) return;

    // Clear existing list
    countryListContainer.innerHTML = '';

    // Add top 9 countries (removed flag icons, added volume in tons)
    countries.forEach(country => {
        const row = document.createElement('div');
        row.className = 'country-row-large';
        const volumeInTons = Math.round(country.volume).toLocaleString();
        row.innerHTML = `
            <span class="country-name-large">${country.name}</span>
            <span class="country-volume-large">${volumeInTons} tons</span>
            <span class="country-percentage-large">${country.percentage}%</span>
        `;
        countryListContainer.appendChild(row);
    });

    // Update total
    const total = countries.reduce((sum, c) => sum + c.percentage, 0);
    const exportTotal = document.getElementById('exportTotal');
    if (exportTotal) {
        exportTotal.innerHTML = `Total exports represented: <strong>${total.toFixed(1)}%</strong> of global volume`;
    }
}

// Update pie chart with new data
function updatePieChart(countries, othersData) {
    if (!exportPieChart) return;

    const labels = [...countries.map(c => c.name), 'Others'];
    const dataValues = [...countries.map(c => c.percentage), othersData.percentage || othersData];
    const volumeData = [...countries.map(c => c.volume), othersData.volume || 0];

    // Store volume data for tooltip
    exportPieChart.data.datasets[0].volumeData = volumeData;
    
    // Update chart data
    exportPieChart.data.labels = labels;
    exportPieChart.data.datasets[0].data = dataValues;
    
    // Update tooltip to show volume in tons
    exportPieChart.options.plugins.tooltip.callbacks.label = function(context) {
        const volume = volumeData[context.dataIndex];
        const volumeInThousandTons = (volume / 1000).toFixed(1);
        return context.label + ': ' + context.parsed + '% (' + volumeInThousandTons + 'K tons)';
    };
    
    // Animate the update
    exportPieChart.update('active');

    // Rebuild legend
    buildDonutLegend();
}

// Show error message
function showErrorMessage(message) {
    const countryListContainer = document.getElementById('countryList');
    if (countryListContainer) {
        countryListContainer.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #c0392b;">
                <i class="fas fa-exclamation-circle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize year dropdown when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeYearDropdown();
    initializeProvinceSelector();
    
    // Load initial export data for default year
    const currentYear = new Date().getFullYear();
    loadExportDataForYear(currentYear - 1);  // Load data for 2024
});

// ============================================================================
// PROVINCE SELECTOR FOR WEATHER DATA
// ============================================================================

// API_BASE_URL already defined at top of file
let currentProvince = 'DakLak'; // Default province

// Initialize province selector
function initializeProvinceSelector() {
    const provinceSelect = document.getElementById('provinceSelect');
    if (!provinceSelect) return;

    // Load initial data
    loadWeatherData(currentProvince);

    // Handle province change
    provinceSelect.addEventListener('change', function() {
        currentProvince = this.value;
        loadWeatherData(currentProvince);
    });
}

// Load weather data from API
async function loadWeatherData(province) {
    try {
        // Get last 12 months data
        const response = await fetch(`${API_BASE_URL}/weather/province/${province}?aggregate=recent12`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Update chart with real data
        updateWeatherChart(result.data);
        
        // Update weather cards with stats
        updateWeatherCards(result.stats);
        
    } catch (error) {
        console.error('Error loading weather data:', error);
        // Keep using placeholder data on error
        console.log('Using placeholder data due to API error');
    }
}

// Update weather chart with real data
function updateWeatherChart(data) {
    if (!climateChart || !data || data.length === 0) return;

    // Map month numbers to names
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // For last 12 months, show actual year/month labels and data
    const labels = data.map(record => monthNames[record.month - 1]);
    const rainfallData = data.map(record => record.precipitation_sum || 0);
    const tempData = data.map(record => record.temperature_mean || 0);

    // Update chart labels and datasets
    climateChart.data.labels = labels;
    climateChart.data.datasets[0].data = rainfallData;
    climateChart.data.datasets[1].data = tempData;
    
    // Animate update
    climateChart.update('active');
}

// Update weather cards with statistics
function updateWeatherCards(stats) {
    if (!stats) return;

    // Update Rainfall card
    const rainfallCard = document.querySelector('[data-commodity="rainfall"]');
    if (rainfallCard && stats.precipitation) {
        const value = rainfallCard.querySelector('.price-value');
        const change = rainfallCard.querySelector('.price-change span');
        const changeIcon = rainfallCard.querySelector('.price-change i');
        const changeContainer = rainfallCard.querySelector('.price-change');
        
        if (value) value.textContent = `${Math.round(stats.precipitation.avg)} mm`;
        if (change) change.textContent = `${stats.precipitation.change_pct > 0 ? '↑' : '↓'}${Math.abs(stats.precipitation.change_pct).toFixed(1)}%`;
        
        // Update change direction
        if (changeContainer) {
            if (stats.precipitation.change_pct > 0) {
                changeContainer.classList.remove('negative');
                changeContainer.classList.add('positive');
                if (changeIcon) changeIcon.className = 'fas fa-arrow-up';
            } else {
                changeContainer.classList.remove('positive');
                changeContainer.classList.add('negative');
                if (changeIcon) changeIcon.className = 'fas fa-arrow-down';
            }
        }
        
        // Update range info
        const volumeSpan = rainfallCard.querySelector('.meta-item.volume span:last-child');
        if (volumeSpan) {
            const peakMonths = ['Jul', 'Aug']; // Could be calculated from data
            volumeSpan.textContent = `Peak: ${peakMonths.join('-')}`;
        }
    }

    // Update Temperature card
    const tempCard = document.querySelector('[data-commodity="temperature"]');
    if (tempCard && stats.temperature) {
        const value = tempCard.querySelector('.price-value');
        const change = tempCard.querySelector('.price-change span');
        const changeIcon = tempCard.querySelector('.price-change i');
        const changeContainer = tempCard.querySelector('.price-change');
        
        if (value) value.textContent = `${stats.temperature.avg.toFixed(1)}°C`;
        if (change) change.textContent = `${stats.temperature.change_pct > 0 ? '↑' : '↓'}${Math.abs(stats.temperature.change_pct).toFixed(1)}%`;
        
        // Update change direction
        if (changeContainer) {
            if (stats.temperature.change_pct > 0) {
                changeContainer.classList.remove('negative');
                changeContainer.classList.add('positive');
                if (changeIcon) changeIcon.className = 'fas fa-arrow-up';
            } else {
                changeContainer.classList.remove('positive');
                changeContainer.classList.add('negative');
                if (changeIcon) changeIcon.className = 'fas fa-arrow-down';
            }
        }
        
        // Update range info
        const volumeSpan = tempCard.querySelector('.meta-item.volume span:last-child');
        if (volumeSpan) {
            volumeSpan.textContent = `Range: ${stats.temperature.min.toFixed(1)}-${stats.temperature.max.toFixed(1)}°C`;
        }
    }

    // Update Humidity card
    const humidityCard = document.querySelector('[data-commodity="humidity"]');
    if (humidityCard && stats.humidity) {
        const value = humidityCard.querySelector('.price-value');
        const change = humidityCard.querySelector('.price-change span');
        const changeIcon = humidityCard.querySelector('.price-change i');
        const changeContainer = humidityCard.querySelector('.price-change');
        
        if (value) value.textContent = `${Math.round(stats.humidity.avg)}%`;
        if (change) change.textContent = `${stats.humidity.change_pct > 0 ? '↑' : '↓'}${Math.abs(stats.humidity.change_pct).toFixed(1)}%`;
        
        // Update change direction
        if (changeContainer) {
            if (stats.humidity.change_pct > 0) {
                changeContainer.classList.remove('negative');
                changeContainer.classList.add('positive');
                if (changeIcon) changeIcon.className = 'fas fa-arrow-up';
            } else {
                changeContainer.classList.remove('positive');
                changeContainer.classList.add('negative');
                if (changeIcon) changeIcon.className = 'fas fa-arrow-down';
            }
        }
        
        // Update optimal range
        const volumeSpan = humidityCard.querySelector('.meta-item.volume span:last-child');
        if (volumeSpan) {
            volumeSpan.textContent = `Optimal: 60-80%`;
        }
    }
}