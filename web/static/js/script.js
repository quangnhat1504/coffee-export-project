// Global variables
const API_BASE_URL = 'http://localhost:5000/api';
let priceChart, exportPieChart, climateChart, trendsChart, exportPerformanceChart, forecastChart;
let apiAvailable = false;

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds
const apiCache = new Map();

console.log('🚀 Script.js loaded at:', new Date().toLocaleTimeString());
console.log('🔗 API Base URL:', API_BASE_URL);

// ============================================================================
// CACHE HELPER FUNCTIONS
// ============================================================================

/**
 * Get cached data if available and not expired
 * @param {string} key - Cache key
 * @returns {object|null} - Cached data or null
 */
function getCachedData(key) {
    const cached = apiCache.get(key);
    if (!cached) return null;
    
    const now = Date.now();
    if (now - cached.timestamp > CACHE_DURATION) {
        apiCache.delete(key);
        return null;
    }
    
    console.log(`✅ Cache hit: ${key}`);
    return cached.data;
}

/**
 * Store data in cache
 * @param {string} key - Cache key
 * @param {object} data - Data to cache
 */
function setCachedData(key, data) {
    apiCache.set(key, {
        data: data,
        timestamp: Date.now()
    });
    console.log(`💾 Cached: ${key}`);
}

// ============================================================================
// API HELPER FUNCTIONS WITH RETRY LOGIC AND CACHING
// ============================================================================

/**
 * Fetch data from API with caching, retry logic and error handling
 * @param {string} url - API endpoint URL
 * @param {boolean} useCache - Whether to use cache
 * @param {number} maxRetries - Maximum number of retry attempts
 * @param {number} retryDelay - Delay between retries in ms
 * @returns {Promise<object>} - API response data
 */
async function fetchWithRetry(url, useCache = true, maxRetries = 3, retryDelay = 1000) {
    // Check cache first
    if (useCache) {
        const cached = getCachedData(url);
        if (cached) return cached;
    }
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            console.log(`📡 Fetching (attempt ${attempt}/${maxRetries}): ${url}`);
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                mode: 'cors',
                cache: 'default'  // Use browser cache
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
            }
            
            const data = await response.json();
            console.log(`✅ Fetch successful: ${url}`);
            
            // Cache the result
            if (useCache) {
                setCachedData(url, data);
            }
            
            return data;
            
        } catch (error) {
            console.warn(`⚠️  Attempt ${attempt} failed: ${error.message}`);
            
            if (attempt === maxRetries) {
                console.error(`❌ All ${maxRetries} attempts failed for: ${url}`);
                throw error;
            }
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
    }
}

// Helper function to check API connection
async function checkAPIConnection() {
    try {
        const data = await fetchWithRetry(`${API_BASE_URL}/health`, 2, 500);
        
        if (data.status === 'healthy' || data.status === 'degraded') {
            console.log('✅ API Connection successful:', data);
            apiAvailable = true;
            return true;
        } else {
            throw new Error('API is not healthy');
        }
    } catch (error) {
        console.error('❌ API Connection failed:', error.message);
        console.error('   Make sure the Flask API is running on http://localhost:5000');
        console.error('   Run: npm run start-api');
        apiAvailable = false;
        showAPIErrorNotification();
        return false;
    }
}

// Show API error notification to user
function showAPIErrorNotification() {
    // Remove existing notification if any
    const existing = document.getElementById('api-error-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.id = 'api-error-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f44336;
        color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 400px;
        font-family: Arial, sans-serif;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `
        <strong style="font-size: 18px;">⚠️ API Connection Error</strong>
        <p style="margin: 10px 0;">Cannot connect to the API server.</p>
        <p style="margin: 10px 0; font-size: 14px;">
            Please make sure the Flask API is running:<br>
            <code style="background: rgba(0,0,0,0.2); padding: 5px; border-radius: 3px; display: inline-block; margin-top: 5px;">
                npm run start-api
            </code>
        </p>
        <button onclick="this.parentElement.remove()" style="
            background: white;
            color: #f44336;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
        ">Close</button>
        <button onclick="location.reload()" style="
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid white;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
            margin-left: 10px;
        ">Retry</button>
    `;
    document.body.appendChild(notification);
    
    // Auto-remove after 15 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 15000);
}

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded at:', new Date().toLocaleTimeString());
    initializeApp();
});
// ================================================================
// 📢 Load Coffee News from Flask API (/api/news)
// ================================================================
async function loadCoffeeNews() {
    const container = document.querySelector(".news-list");
    if (!container) return;
    container.innerHTML = "<p>🔄 Đang tải tin tức mới nhất từ nhiều nguồn...</p>";

    // Fallback images array
    const fallbackImages = [
        "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400&h=300&fit=crop&q=80",
        "https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=300&fit=crop&q=80",
    ];

    // Function to get random fallback image
    function getRandomFallbackImage() {
        return fallbackImages[Math.floor(Math.random() * fallbackImages.length)];
    }

    // Function to validate and fix image URL
    function validateImageUrl(url) {
        if (!url) return getRandomFallbackImage();
        
        // Check if it's a valid URL
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            return getRandomFallbackImage();
        }
        
        // Check if it's a data URL or placeholder
        if (url.startsWith('data:') || url.includes('placeholder')) {
            return getRandomFallbackImage();
        }
        
        return url;
    }

    // Function to get category CSS class based on source
    function getCategoryClass(source) {
        const sourceMap = {
            'VOV': 'vov',
            'Báo Mới': 'baomoi',
            'VnExpress': 'vnexpress',
            'CafeControl': 'cafecontrol',
            'Thanh Niên': 'thanhnien',
            'Tuổi Trẻ': 'tuoitre'
        };
        return sourceMap[source] || 'default';
    }

    try {
        const res = await fetch(`${API_BASE_URL}/news`);
        const data = await res.json();

        if (!data.success || !data.data.length) {
            container.innerHTML = "<p>⚠️ Không có tin tức mới.</p>";
            return;
        }

        container.innerHTML = "";
        data.data.forEach((item, index) => {
            // Validate and ensure image URL is proper
            const imageUrl = validateImageUrl(item.image);
            const categoryClass = getCategoryClass(item.source);
            
            const newsElement = document.createElement('article');
            newsElement.className = 'news-item';
            newsElement.innerHTML = `
                <div class="news-thumbnail">
                    <img src="${imageUrl}" 
                         alt="${item.title}" 
                         onerror="this.onerror=null; this.src='${getRandomFallbackImage()}';"
                         loading="lazy">
                    <div class="news-category ${categoryClass}">${item.source}</div>
                </div>
                <div class="news-item-content">
                    <h3 class="news-item-title">
                        <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
                    </h3>
                    <p class="news-item-desc">
                        <i class="fas fa-newspaper"></i> ${item.source} • 
                        <i class="fas fa-clock"></i> ${item.time}
                    </p>
                </div>
            `;
            container.appendChild(newsElement);
        });
        
        console.log(`✅ Loaded ${data.data.length} news items from multiple sources`);
    } catch (err) {
        console.error('❌ Error loading news:', err);
        container.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #dc3545;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">Lỗi khi tải tin tức</p>
                <p style="font-size: 0.9rem; opacity: 0.8;">${err.message}</p>
            </div>
        `;
    }
}

// Gọi hàm khi DOM sẵn sàng
document.addEventListener("DOMContentLoaded", loadCoffeeNews);

// Initialize Application
async function initializeApp() {
    console.log('🎯 initializeApp() called');
    
    // Check API connection first
    console.log('🔍 Checking API connection...');
    const apiConnected = await checkAPIConnection();
    if (!apiConnected) {
        console.warn('⚠️ Continuing without API connection - some features may not work');
    }
    
    setupNavigation();
    setupScrollAnimations();
    setupCounterAnimations();
    console.log('📊 About to initialize charts...');
    await initializeCharts();
    await updateHeroMetrics(); // Load hero section data from API
    setupMarketMeta();
    setupCommodityHighlighting();
    setupMarketChartToggles(); // NEW: Setup toggle buttons for market chart
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
    if (!apiAvailable) {
        console.warn('⚠️  Skipping hero metrics update - API not available');
        return;
    }
    
    try {
        console.log('📊 Fetching hero metrics from API...');
        
        // Fetch latest production data
        const productionResult = await fetchWithRetry(`${API_BASE_URL}/production`);
        
        if (productionResult.success && productionResult.data.length > 0) {
            const latestProduction = productionResult.data[productionResult.data.length - 1];
            
            // Update Production (convert to M tons with 1 decimal)
            const productionMT = (latestProduction.output_million_tons).toFixed(1);
            const heroProduction = document.getElementById('hero-production');
            if (heroProduction) heroProduction.textContent = `${productionMT}M t`;
            
            // Update Area (convert to K ha)
            const areaKHa = Math.round(latestProduction.area_thousand_ha);
            const heroArea = document.getElementById('hero-area');
            if (heroArea) heroArea.textContent = `${areaKHa}K ha`;
            
            // Update Yield (2 decimals)
            const yieldValue = latestProduction.yield_tons_per_ha.toFixed(1);
            const heroYield = document.getElementById('hero-yield');
            if (heroYield) heroYield.textContent = `${yieldValue} t/ha`;
        }
        
        // Fetch export data for value and prices
        const exportResult = await fetchWithRetry(`${API_BASE_URL}/export`);
        
        if (exportResult.success && exportResult.data.length > 0) {
            const latestExport = exportResult.data[exportResult.data.length - 1];
            
            // Update Export Value (convert to billions with 1 decimal)
            const exportValueB = (latestExport.export_value_million_usd / 1000).toFixed(1);
            const heroValue = document.getElementById('hero-value');
            if (heroValue) heroValue.textContent = `$${exportValueB}B`;
            
            // Update Domestic Price (VN price per ton)
            if (latestExport.price_vn_usd_per_ton) {
                const heroPrice = document.getElementById('hero-price');
                if (heroPrice) heroPrice.textContent = `$${Math.round(latestExport.price_vn_usd_per_ton).toLocaleString()}`;
            }
        }
        
        console.log('✅ Hero metrics updated with latest data');
    } catch (error) {
        console.error('❌ Error updating hero metrics:', error);
        console.error('   Some metrics may not display correctly');
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
                                // Export Volume - convert to million tons
                                const millionTons = (context.parsed.y / 1000000).toFixed(2);
                                label += millionTons + ' million tons';
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
                        text: 'Export Volume (Million Tons)',
                        color: textColor.trim(),
                        font: { size: 11 }
                    },
                    ticks: { 
                        color: textColor.trim(),
                        callback: function(value) {
                            // Convert tons to million tons for display
                            return (value / 1000000).toFixed(1) + 'M';
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

// Setup Market Chart Toggle Buttons
function setupMarketChartToggles() {
    const checkboxes = document.querySelectorAll('.market-checkbox');
    
    if (!checkboxes.length) {
        console.warn('No checkboxes found for market chart');
        return;
    }
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const dataset = this.getAttribute('data-dataset');
            const isChecked = this.checked;
            
            console.log(`Market checkbox changed: ${dataset} = ${isChecked}`);
            
            // Update chart visibility
            togglePriceChartSeries(dataset, isChecked);
        });
    });
    
    console.log('✅ Market chart toggles initialized -', checkboxes.length, 'checkboxes found');
}

// Toggle series visibility in price chart
function togglePriceChartSeries(dataset, visible) {
    if (!priceChart) {
        console.warn('Price chart not initialized');
        return;
    }
    
    let datasetIndex = -1;
    
    // Map dataset name to dataset index
    switch(dataset) {
        case 'volume':
            datasetIndex = 0; // Export Volume
            break;
        case 'worldPrice':
            datasetIndex = 1; // World Price
            break;
        case 'vnPrice':
            datasetIndex = 2; // VN Price
            break;
    }
    
    if (datasetIndex !== -1) {
        // Set visibility: checked = show, unchecked = hide
        const meta = priceChart.getDatasetMeta(datasetIndex);
        meta.hidden = !visible; // hidden=false means show, hidden=true means hide
        
        // Update Y-axes visibility based on which datasets are visible
        updatePriceChartAxes();
        
        // Update chart
        priceChart.update();
        
        console.log(`${visible ? 'Showing' : 'Hiding'} ${dataset} in market chart`);
    }
}

// Update Y-axes visibility based on visible datasets
function updatePriceChartAxes() {
    if (!priceChart) return;
    
    // Check if Export Volume (dataset 0) is visible
    const volumeMeta = priceChart.getDatasetMeta(0);
    const isVolumeVisible = !volumeMeta.hidden;
    
    // Check if any price dataset (1 or 2) is visible
    const worldPriceMeta = priceChart.getDatasetMeta(1);
    const vnPriceMeta = priceChart.getDatasetMeta(2);
    const isPriceVisible = !worldPriceMeta.hidden || !vnPriceMeta.hidden;
    
    // Show/hide Y-axes accordingly
    priceChart.options.scales['y-volume'].display = isVolumeVisible;
    priceChart.options.scales['y-price'].display = isPriceVisible;
    
    // If only price axis is visible, position it on the left for better readability
    if (isPriceVisible && !isVolumeVisible) {
        priceChart.options.scales['y-price'].position = 'left';
    } else {
        priceChart.options.scales['y-price'].position = 'right';
    }
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
            labels: ['Germany', 'Italy', 'United States', 'Japan', 'Russian Federation', 'Belgium', 'Spain', 'Algeria', 'Thailand', 'Others'],
            datasets: [{
                data: [18.3, 10.7, 9.2, 7.6, 6.5, 6.1, 5.9, 4.7, 2.5, 28.5],
                backgroundColor: [
                    '#8B4513',  // Germany - SaddleBrown (nâu đậm)
                    '#A0522D',  // Italy - Sienna (nâu đỏ)
                    '#D2691E',  // US - Chocolate đậm
                    '#CD853F',  // Japan - Peru (vàng nâu sáng)
                    '#B8860B',  // Russian Federation - DarkGoldenrod (vàng đậm)
                    '#8B7355',  // Belgium - Burlywood4 (nâu xám)
                    '#DEB887',  // Spain - Burlywood (be vàng nhạt)
                    '#D2B48C',  // Algeria - Tan (be sáng)
                    '#F4A460',  // Thailand - SandyBrown (cam nâu)
                    '#BC8F8F'   // Others - RosyBrown (nâu hồng)
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
    const checkboxes = document.querySelectorAll('.prod-checkbox');
    if(!checkboxes.length || !trendsChart) return;
    
    checkboxes.forEach((checkbox)=>{
        checkbox.addEventListener('change',()=>{
            updateProductionChart();
        });
    });
}

function updateProductionChart() {
    const checkboxes = document.querySelectorAll('.prod-checkbox');
    const checkedDatasets = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('data-dataset'));
    
    trendsChart.data.datasets.forEach(ds => {
        const datasetName = ds.label.toLowerCase();
        let isVisible = false;
        
        if (checkedDatasets.includes('production') && datasetName.includes('production')) {
            isVisible = true;
        }
        if (checkedDatasets.includes('area') && datasetName.includes('area')) {
            isVisible = true;
        }
        if (checkedDatasets.includes('yield') && datasetName.includes('yield')) {
            isVisible = true;
        }
        
        ds.hidden = !isVisible;
    });
    
    trendsChart.update();
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
    
    // Update NEW Export Stats Cards (3 cards below title)
    updateExportStatsCards(data);
    
    console.log('💳 Export performance cards updated');
}

/**
 * Update Export Stats Cards (2024 Data Summary Cards)
 */
function updateExportStatsCards(data) {
    if (!data || data.length === 0) return;
    
    console.log('💳 Updating export stats cards...');
    
    const latest = data[data.length - 1];  // 2024 data
    const previous = data[data.length - 2]; // 2023 data
    
    // 1. Update Export Value Card
    const valueElement = document.getElementById('value-export');
    const changeExportElement = document.getElementById('change-export');
    
    if (valueElement && latest.export_value_million_usd) {
        const valueInBillions = (latest.export_value_million_usd / 1000).toFixed(2);
        valueElement.innerHTML = `$${valueInBillions}B`;
        
        // Calculate year-over-year change
        if (changeExportElement && previous) {
            const change = latest.export_value_million_usd - previous.export_value_million_usd;
            const changePct = ((change / previous.export_value_million_usd) * 100).toFixed(1);
            const isPositive = change >= 0;
            
            changeExportElement.classList.remove('positive', 'negative', 'neutral');
            changeExportElement.classList.add(isPositive ? 'positive' : 'negative');
            
            changeExportElement.innerHTML = `
                <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
                <span>${isPositive ? '+' : ''}${changePct}% </span>
            `;
        }
    }
    
    // 2. Update World Price Card
    const worldPriceElement = document.getElementById('value-world-price');
    const changeWorldPriceElement = document.getElementById('change-world-price');
    
    if (worldPriceElement && latest.price_world_usd_per_ton) {
        const formattedPrice = Math.round(latest.price_world_usd_per_ton).toLocaleString('en-US');
        worldPriceElement.innerHTML = `$${formattedPrice}`;
        
        // Calculate year-over-year change
        if (changeWorldPriceElement && previous) {
            const change = latest.price_world_usd_per_ton - previous.price_world_usd_per_ton;
            const changePct = ((change / previous.price_world_usd_per_ton) * 100).toFixed(1);
            const isPositive = change >= 0;
            
            changeWorldPriceElement.classList.remove('positive', 'negative', 'neutral');
            changeWorldPriceElement.classList.add(isPositive ? 'positive' : 'negative');
            
            changeWorldPriceElement.innerHTML = `
                <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
                <span>${isPositive ? '+' : ''}${changePct}% </span>
            `;
        }
    }
    
    // 3. Update VN Price Card
    const vnPriceElement = document.getElementById('value-vn-price');
    const changeVnPriceElement = document.getElementById('change-vn-price');
    
    if (vnPriceElement && latest.price_vn_usd_per_ton) {
        const formattedPrice = Math.round(latest.price_vn_usd_per_ton).toLocaleString('en-US');
        vnPriceElement.innerHTML = `$${formattedPrice}`;
        
        // Calculate year-over-year change
        if (changeVnPriceElement && previous) {
            const change = latest.price_vn_usd_per_ton - previous.price_vn_usd_per_ton;
            const changePct = ((change / previous.price_vn_usd_per_ton) * 100).toFixed(1);
            const isPositive = change >= 0;
            
            changeVnPriceElement.classList.remove('positive', 'negative', 'neutral');
            changeVnPriceElement.classList.add(isPositive ? 'positive' : 'negative');
            
            changeVnPriceElement.innerHTML = `
                <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
                <span>${isPositive ? '+' : ''}${changePct}% </span>
            `;
        }
    }
    
    console.log('✅ Export stats cards updated:', {
        exportValue: `$${(latest.export_value_million_usd / 1000).toFixed(2)}B`,
        worldPrice: `$${Math.round(latest.price_world_usd_per_ton)}`,
        vnPrice: `$${Math.round(latest.price_vn_usd_per_ton)}`
    });
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
        console.log('🔄 Fetching production data from:', `${API_BASE_URL}/production`);
        const response = await fetch(`${API_BASE_URL}/production`);
        const result = await response.json();
        
        console.log('📦 Production API response:', result);
        
        if (result.success && result.data && result.data.length > 0) {
            productionData = result.data;
            console.log('✅ Production data loaded:', productionData.length, 'years');
            console.log('📊 Sample data:', productionData[0]);
            
            // Update chart with real data
            updateTrendsChartWithData();
            
            // Update production cards
            updateProductionCards(productionData);
        } else {
            console.error('❌ Failed to load production data:', result.error || 'No data');
            console.log('Using fallback generated data');
        }
    } catch (error) {
        console.error('❌ Error loading production data:', error);
        console.log('Using fallback generated data');
    }
}

function updateTrendsChartWithData() {
    if (!trendsChart) {
        console.warn('⚠️ trendsChart not initialized');
        return;
    }
    if (!productionData) {
        console.warn('⚠️ productionData not available');
        return;
    }
    
    console.log('📈 Updating trends chart with real data...');
    
    const years = productionData.map(d => d.year.toString());
    // Convert from millions to tons and thousands to hectares
    const production = productionData.map(d => d.output_million_tons * 1000000);
    const area = productionData.map(d => d.area_thousand_ha * 1000);
    const yieldData = productionData.map(d => d.yield_tons_per_ha);
    
    console.log('Years:', years);
    console.log('Production sample:', production.slice(0, 3));
    console.log('Area sample:', area.slice(0, 3));
    console.log('Yield sample:', yieldData.slice(0, 3));
    
    // Update chart labels and datasets
    trendsChart.data.labels = years;
    trendsChart.data.datasets[0].data = production;
    trendsChart.data.datasets[1].data = area;
    trendsChart.data.datasets[2].data = yieldData;
    
    trendsChart.update();
    console.log('✅ Trends chart updated successfully');
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

// Sync aria-pressed state for toggle buttons (weather only now)
function syncPressed(buttons){
    buttons.forEach(btn => {
        btn.setAttribute('aria-pressed', btn.classList.contains('active') ? 'true' : 'false');
    });
}

// Observe activation changes for weather buttons only
const mutationConfig = { attributes:true, attributeFilter:['class'] };
document.querySelectorAll('.wx-toggle-btn').forEach(btn => {
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

    // Define color palette for countries (10 distinct colors)
    const colorPalette = [
        '#8B4513',  // 1st - SaddleBrown (nâu đậm)
        '#A0522D',  // 2nd - Sienna (nâu đỏ)
        '#D2691E',  // 3rd - Chocolate đậm
        '#CD853F',  // 4th - Peru (vàng nâu sáng)
        '#B8860B',  // 5th - DarkGoldenrod (vàng đậm)
        '#8B7355',  // 6th - Burlywood4 (nâu xám)
        '#DEB887',  // 7th - Burlywood (be vàng nhạt)
        '#D2B48C',  // 8th - Tan (be sáng)
        '#F4A460',  // 9th - SandyBrown (cam nâu)
        '#BC8F8F'   // Others - RosyBrown (nâu hồng)
    ];

    // Generate colors based on number of countries
    const colors = countries.map((_, index) => colorPalette[index % colorPalette.length]);
    colors.push(colorPalette[colorPalette.length - 1]); // Others color

    // Store volume data for tooltip
    exportPieChart.data.datasets[0].volumeData = volumeData;
    
    // Update chart data
    exportPieChart.data.labels = labels;
    exportPieChart.data.datasets[0].data = dataValues;
    exportPieChart.data.datasets[0].backgroundColor = colors;
    
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

// ==========================================================
// ☕ PROVINCE COFFEE PRICES CHART (Last 7 Days) - Multi-line Chart
// ==========================================================

let provincePricesChart = null;

/**
 * Fetch recent coffee prices by province from API
 */
async function fetchProvincePrices(days = 7) {
    console.log('🔵 fetchProvincePrices called - v5.0');
    try {
        const url = `${API_BASE_URL}/coffee-prices/recent?days=${days}`;
        console.log('🔵 Fetching from:', url);
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('🔵 API Response:', data);
        
        if (data.success && data.provinces) {
            console.log('🔵 Initializing chart with', data.provinces.length, 'provinces');
            
            // Update info cards first
            updateProvincePriceCards(data.provinces);
            
            // Then initialize chart
            initializeProvincePricesChart(data.provinces);
        } else {
            console.error('❌ Failed to load province prices:', data.error);
        }
    } catch (error) {
        console.error('❌ Error fetching province prices:', error);
    }
}

/**
 * Update province price info cards with latest data
 */
function updateProvincePriceCards(provinces) {
    console.log('💳 Updating province price cards:', provinces);
    
    const provinceMapping = {
        'DakLak': 'daklak',
        'DakNong': 'daknong',
        'GiaLai': 'gialai',
        'LamDong': 'lamdong'
    };
    
    provinces.forEach(province => {
        const cardId = provinceMapping[province.name];
        if (!cardId) return;
        
        // Get DOM elements
        const priceElement = document.getElementById(`price-${cardId}`);
        const changeElement = document.getElementById(`change-${cardId}`);
        const dateElement = document.getElementById(`date-${cardId}`);
        
        if (!priceElement || !changeElement || !dateElement) {
            console.warn(`⚠️ Card elements not found for ${cardId}`);
            return;
        }
        
        // Update price
        const currentPrice = province.current_price || 0;
        const formattedPrice = new Intl.NumberFormat('vi-VN').format(Math.round(currentPrice));
        priceElement.innerHTML = `₫${formattedPrice}`;
        
        // Update change percentage
        const changePercent = province.price_change_percent || 0;
        const changeValue = province.price_change || 0;
        const isPositive = changePercent > 0;
        const isNegative = changePercent < 0;
        const isNeutral = changePercent === 0;
        
        // Remove all classes
        changeElement.classList.remove('positive', 'negative', 'neutral');
        
        // Add appropriate class
        if (isPositive) {
            changeElement.classList.add('positive');
            changeElement.innerHTML = `<i class="fas fa-arrow-up"></i><span>+${changePercent.toFixed(2)}%</span>`;
        } else if (isNegative) {
            changeElement.classList.add('negative');
            changeElement.innerHTML = `<i class="fas fa-arrow-down"></i><span>${changePercent.toFixed(2)}%</span>`;
        } else {
            changeElement.classList.add('neutral');
            changeElement.innerHTML = `<i class="fas fa-minus"></i><span>0.0%</span>`;
        }
        
        // Update date (get most recent date from prices)
        if (province.prices && province.prices.length > 0) {
            const mostRecentDate = province.prices[0].date; // Already sorted DESC
            const dateObj = new Date(mostRecentDate);
            const formattedDate = dateObj.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                year: 'numeric' 
            });
            dateElement.textContent = formattedDate;
        }
        
        console.log(`✅ Updated card for ${province.name}:`, {
            price: formattedPrice,
            change: changePercent,
            date: dateElement.textContent
        });
    });
}

/**
 * Initialize province prices line chart (4 lines, 1 per province)
 */
function initializeProvincePricesChart(provinces) {
    console.log('🟢 initializeProvincePricesChart called with:', provinces);
    
    // Color palette for provinces
    const provinceColors = {
        'DakLak': { border: '#8B4513', bg: 'rgba(139, 69, 19, 0.1)' },
        'DakNong': { border: '#D2691E', bg: 'rgba(210, 105, 30, 0.1)' },
        'GiaLai': { border: '#CD853F', bg: 'rgba(205, 133, 63, 0.1)' },
        'LamDong': { border: '#A0522D', bg: 'rgba(160, 82, 45, 0.1)' }
    };
    
    // Get all unique dates and sort them
    const allDates = new Set();
    provinces.forEach(province => {
        province.prices.forEach(p => allDates.add(p.date));
    });
    const sortedDates = Array.from(allDates).sort();
    
    console.log('🟢 All unique dates:', sortedDates);
    console.log('🟢 Provinces data:', provinces.map(p => ({
        name: p.name,
        priceCount: p.prices.length,
        dates: p.prices.map(x => x.date)
    })));
    
    // Format labels (MM/DD)
    const labels = sortedDates.map(dateStr => {
        const date = new Date(dateStr);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });
    
    // Create datasets (one line per province)
    const datasets = provinces.map(province => {
        // Create price array matching sorted dates (sortedDates is ASC)
        // Need to map each date in sortedDates to corresponding price from province.prices
        const priceData = sortedDates.map(date => {
            // Find price object for this specific date
            const priceObj = province.prices.find(p => p.date === date);
            if (!priceObj) {
                console.warn(`⚠️ ${province.name}: No price found for date ${date}`);
                return null;
            }
            return priceObj.price;
        });
        
        // DEBUG: Detailed log for LamDong
        if (province.name === 'LamDong') {
            console.log('🔴 LAMDONG DEBUG:');
            console.log('  - Total dates in sortedDates:', sortedDates.length);
            console.log('  - SortedDates:', JSON.stringify(sortedDates));
            console.log('  - Province.prices length:', province.prices.length);
            console.log('  - Province.prices:', JSON.stringify(province.prices));
            console.log('  - Mapping check:');
            sortedDates.forEach((date, idx) => {
                const found = province.prices.find(p => p.date === date);
                console.log(`    ${date} → ${found ? found.price : 'NULL'} (index ${idx})`);
            });
            console.log('  - Final PriceData array:', JSON.stringify(priceData));
            console.log('  - Non-null count:', priceData.filter(p => p !== null).length);
        }
        
        console.log(`🟢 ${province.name} price data:`, priceData);
        
        const color = provinceColors[province.name] || { 
            border: '#666', 
            bg: 'rgba(102, 102, 102, 0.1)' 
        };
        
        return {
            label: province.name,
            data: priceData,
            borderColor: color.border,
            backgroundColor: color.bg,
            borderWidth: 3,
            fill: false,  // Changed from true - disable fill to avoid overlap issues
            tension: 0.4,
            spanGaps: true,  // Draw line even when there are null values
            pointRadius: 5,  // Increased from 4
            pointHoverRadius: 7,  // Increased from 6
            pointBackgroundColor: color.border,
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: color.border,
            pointHoverBorderWidth: 3
        };
    });
    
    // Calculate min/max for Y-axis with expanded range (to flatten the curves)
    let allPrices = [];
    datasets.forEach(dataset => {
        const validPrices = dataset.data.filter(v => v !== null && v !== undefined);
        allPrices = allPrices.concat(validPrices);
    });
    
    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const priceRange = maxPrice - minPrice;
    
    // Expand range by 50% on each side to make curves appear flatter
    const expandedMin = Math.floor(minPrice - (priceRange * 0.5));
    const expandedMax = Math.ceil(maxPrice + (priceRange * 0.5));
    
    console.log('📊 Y-axis range adjustment:', {
        dataMin: minPrice,
        dataMax: maxPrice,
        range: priceRange,
        chartMin: expandedMin,
        chartMax: expandedMax
    });
    
    // Chart configuration
    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 13,
                            weight: '600',
                            family: "'Inter', sans-serif"
                        },
                        color: '#2c3e50',
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    padding: 12,
                    displayColors: true,
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            return `${label}: ${formatNumber(value)} ₫/kg`;
                        }
                    }
                },
                title: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: "'Inter', sans-serif"
                        },
                        color: '#666',
                        maxRotation: 0,
                        autoSkip: false
                    },
                    title: {
                        display: true,
                        text: 'Date',
                        font: {
                            size: 13,
                            weight: '600'
                        },
                        color: '#2c3e50'
                    }
                },
                y: {
                    min: expandedMin,
                    max: expandedMax,
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: "'Inter', sans-serif"
                        },
                        color: '#666',
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    },
                    title: {
                        display: true,
                        text: 'Price (₫/kg)',
                        font: {
                            size: 13,
                            weight: '600'
                        },
                        color: '#2c3e50'
                    }
                }
            }
        }
    };
    
    // Initialize chart (Market Overview section only)
    const canvas1 = document.getElementById('provincePricesChart');
    
    console.log('🟢 Canvas element:', { canvas1: !!canvas1 });
    
    if (canvas1) {
        console.log('🟢 Creating province prices chart');
        if (provincePricesChart) provincePricesChart.destroy();
        const ctx1 = canvas1.getContext('2d');
        provincePricesChart = new Chart(ctx1, config);
        console.log('✅ Chart created successfully');
    } else {
        console.error('❌ Canvas provincePricesChart not found!');
    }
}

/**
 * Format number with thousand separators
 */
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return Math.round(num).toLocaleString('en-US');
}

// Initialize province prices chart on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🟡 DOM loaded - calling fetchProvincePrices (v5.0)');
    fetchProvincePrices(7);
});