// Global variables
let priceChart, exportPieChart, climateChart, trendsChart, forecastChart;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize Application
function initializeApp() {
    setupNavigation();
    setupScrollAnimations();
    setupCounterAnimations();
    initializeCharts();
    setupMarketMeta();
    setupCommodityHighlighting();
    setupTrendButtons();
    setupFormHandling();
    setupSmoothScrolling();
    setupSidebarNavigation();
    enableScrollSnap();
    startRealTimeUpdates();
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

// Chart Initialization
function initializeCharts() {
    initializePriceChart();
    initializeExportPieChart();
    initializeWeatherDualChart();
    initializeTrendsChart();
    initializeForecastChart();
}


// Price Chart
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
            labels: generateDateLabels(30),
            datasets: [
                {
                    label: 'Arabica',
                    data: generatePriceData(4250, 30),
                    borderColor: '#DAA520',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#DAA520',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                },
                {
                    label: 'Robusta',
                    data: generatePriceData(2850, 30),
                    borderColor: '#CD853F',
                    backgroundColor: 'rgba(205, 133, 63, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#CD853F',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                },
                {
                    label: 'Domestic',
                    data: generatePriceData(2650, 30),
                    borderColor: '#8B4513',
                    backgroundColor: 'rgba(139, 69, 19, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#8B4513',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
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
                },
                tooltip: {
                    backgroundColor: '#ffffff',
                    titleColor: textColor.trim(),
                    bodyColor: textColor.trim(),
                    borderColor: gridColor.trim(),
                    borderWidth: 1
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
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Populate dynamic date for Market Overview cards
function setupMarketMeta() {
    const dateSpans = document.querySelectorAll('.price-card .dynamic-date');
    if (!dateSpans.length) return;
    const now = new Date();
    const formatted = now.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
    dateSpans.forEach(span => span.textContent = formatted);
}

// Commodity highlighting interaction
function setupCommodityHighlighting() {
    const cards = document.querySelectorAll('.price-card');
    if (!cards.length || !priceChart) return;

    cards.forEach(card => {
        card.addEventListener('click', () => {
            const commodity = card.getAttribute('data-commodity');
            activateCommodity(commodity);
        });
        card.style.cursor = 'pointer';
    });
    // Default active first card
    activateCommodity('arabica');
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
                    label:'Production (M Tons)',
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
                    label:'Area (K ha)',
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
            plugins:{ legend:{ labels:{ color:textColor.trim(), font:{ family:'Inter' } } } },
            scales:{
                x:{ ticks:{ color:textColor.trim() }, grid:{ color:gridColor } },
                y:{ ticks:{ color:textColor.trim() }, grid:{ color:gridColor } }
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