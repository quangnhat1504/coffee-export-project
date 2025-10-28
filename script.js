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
    setupTrendButtons();
    setupFormHandling();
    setupSmoothScrolling();
}

// Navigation Setup
function setupNavigation() {
    const navbar = document.querySelector('.navbar');
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');

    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Mobile menu toggle
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    // Close mobile menu when clicking on links
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });

    // Active link highlighting
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
    initializeClimateChart();
    initializeTrendsChart();
    initializeForecastChart();
}

// Price Chart
function initializePriceChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;

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
                        color: '#E8E8E8',
                        font: { family: 'Inter' }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 35, 41, 0.95)',
                    titleColor: '#E8E8E8',
                    bodyColor: '#B0B0B0',
                    borderColor: '#333840',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    ticks: { color: '#B0B0B0' },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                },
                y: {
                    ticks: { 
                        color: '#B0B0B0',
                        callback: function(value) {
                            return '$' + value;
                        }
                    },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Export Pie Chart
function initializeExportPieChart() {
    const ctx = document.getElementById('exportPieChart');
    if (!ctx) return;

    exportPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['United States', 'Germany', 'Japan', 'Italy', 'France', 'Others'],
            datasets: [{
                data: [22.5, 18.3, 15.7, 12.1, 9.8, 21.6],
                backgroundColor: [
                    '#DAA520',
                    '#CD853F',
                    '#8B4513',
                    '#B8860B',
                    '#DEB887',
                    '#D2691E'
                ],
                borderColor: '#1e2329',
                borderWidth: 3,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#E8E8E8',
                        font: { family: 'Inter' },
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 35, 41, 0.95)',
                    titleColor: '#E8E8E8',
                    bodyColor: '#B0B0B0',
                    borderColor: '#333840',
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
            }
        }
    });
}

// Climate Chart
function initializeClimateChart() {
    const ctx = document.getElementById('climateChart');
    if (!ctx) return;

    climateChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [
                {
                    label: 'Rainfall (mm)',
                    data: [15, 20, 45, 120, 180, 220, 250, 280, 200, 150, 80, 25],
                    backgroundColor: 'rgba(100, 149, 237, 0.7)',
                    borderColor: '#6495ED',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Temperature (°C)',
                    data: [22, 24, 26, 28, 27, 25, 24, 24, 25, 26, 24, 22],
                    type: 'line',
                    borderColor: '#DAA520',
                    backgroundColor: 'rgba(218, 165, 32, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1',
                    pointBackgroundColor: '#DAA520',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#E8E8E8',
                        font: { family: 'Inter' }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#B0B0B0' },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: { color: '#B0B0B0' },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: { color: '#B0B0B0' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// Trends Chart
function initializeTrendsChart() {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;

    const years = [];
    for (let i = 2005; i <= 2024; i++) {
        years.push(i.toString());
    }

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Production (Million Tons)',
                data: generateTrendData(1.5, 2.5, 20),
                borderColor: '#DAA520',
                backgroundColor: 'rgba(218, 165, 32, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#DAA520',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#E8E8E8',
                        font: { family: 'Inter' }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#B0B0B0' },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                },
                y: {
                    ticks: { color: '#B0B0B0' },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Forecast Chart
function initializeForecastChart() {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;

    const months = ['Oct 2024', 'Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025', 'May 2025'];

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
                        color: '#E8E8E8',
                        font: { family: 'Inter' }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#B0B0B0' },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
                },
                y: {
                    ticks: { 
                        color: '#B0B0B0',
                        callback: function(value) {
                            return '$' + value;
                        }
                    },
                    grid: { color: 'rgba(51, 56, 64, 0.5)' }
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
    const humidity = document.querySelector('.weather-item:nth-child(1) span');
    const rainfall = document.querySelector('.weather-item:nth-child(2) span');
    
    if (temperature) {
        const temp = 20 + Math.random() * 10;
        temperature.textContent = Math.round(temp) + '°C';
    }
    
    if (humidity) {
        const hum = 60 + Math.random() * 30;
        humidity.textContent = 'Humidity: ' + Math.round(hum) + '%';
    }
    
    if (rainfall) {
        const rain = Math.random() * 100;
        rainfall.textContent = 'Rainfall: ' + Math.round(rain) + 'mm';
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

// Initialize real-time updates when page loads
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(startRealTimeUpdates, 5000); // Start updates after 5 seconds
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

// Keyboard Navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');
        
        if (navMenu.classList.contains('active')) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        }
    }
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