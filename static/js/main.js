/**
 * Factryl Infometrics - Main JavaScript
 * Handles all interactive features and animations
 */

// Global variables
let isLoading = false;
let currentQuery = '';

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    setupNavigation();
    setupScrollEffects();
    setupLoadingOverlay();
    
    // Add smooth scrolling to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Setup navigation functionality
 */
function setupNavigation() {
    const navbar = document.querySelector('.navbar');
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.boxShadow = 'none';
        }
    });
    
    // Mobile menu toggle
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }
}

/**
 * Setup scroll-based animations
 */
function setupScrollEffects() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .demo-step, .stat-item').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

/**
 * Setup loading overlay functionality
 */
function setupLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const loadingText = document.getElementById('loading-text');
    
    window.showLoading = function(query = '') {
        if (isLoading) return;
        
        isLoading = true;
        currentQuery = query;
        
        overlay.classList.remove('hidden');
        progressFill.style.width = '0%';
        progressText.textContent = '0%';
        
        // Simulate progress
        simulateProgress();
    };
    
    window.hideLoading = function() {
        isLoading = false;
        overlay.classList.add('hidden');
    };
    
    function simulateProgress() {
        const steps = [
            { progress: 15, text: 'Initializing scrapers...', delay: 500 },
            { progress: 35, text: 'Fetching data from news sources...', delay: 800 },
            { progress: 55, text: 'Analyzing social media content...', delay: 700 },
            { progress: 75, text: 'Processing credibility scores...', delay: 600 },
            { progress: 90, text: 'Generating visualizations...', delay: 500 },
            { progress: 100, text: 'Complete!', delay: 300 }
        ];
        
        let currentStep = 0;
        
        function nextStep() {
            if (!isLoading || currentStep >= steps.length) return;
            
            const step = steps[currentStep];
            
            // Update progress bar
            progressFill.style.width = step.progress + '%';
            progressText.textContent = step.progress + '%';
            loadingText.textContent = step.text;
            
            currentStep++;
            
            if (currentStep < steps.length) {
                setTimeout(nextStep, step.delay);
            }
        }
        
        nextStep();
    }
}

/**
 * Search functionality
 */
window.performSearch = async function(query, options = {}) {
    if (!query || query.trim().length < 2) {
        showNotification('Please enter a search query of at least 2 characters', 'warning');
        return;
    }
    
    console.log('Starting search for:', query);
    showLoading(query);
    
    try {
        const requestBody = {
            query: query.trim(),
            sources: options.sources,
            max_results: options.max_results || 50
        };
        
        console.log('Sending request:', requestBody);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            // Display results
            displayResults(data.result);
            showNotification('Report generated successfully!', 'success');
        } else {
            throw new Error(data.error || 'Search failed');
        }
        
    } catch (error) {
        console.error('Search error:', error);
        showNotification('Search failed: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
};

/**
 * Display search results
 */
function displayResults(result) {
    console.log('Displaying results:', result);
    
    // Create comprehensive results display
    const statistics = result.statistics || {};
    const metadata = result.metadata || {};
    const analysis = result.analysis || {};
    
    const resultsHtml = `
        <div class="results-summary">
            <h2>Infometric Report for "${result.query}"</h2>
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number">${result.results ? result.results.length : 0}</div>
                    <div class="stat-label">Total Items Found</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${statistics.sources ? Object.keys(statistics.sources).length : 0}</div>
                    <div class="stat-label">Data Sources</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${metadata.processing_time_seconds ? metadata.processing_time_seconds.toFixed(2) : 'N/A'}s</div>
                    <div class="stat-label">Processing Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${analysis.overall_credibility_score ? (analysis.overall_credibility_score * 100).toFixed(1) + '%' : 'N/A'}</div>
                    <div class="stat-label">Credibility Score</div>
                </div>
            </div>
            
            ${result.results && result.results.length > 0 ? `
            <div class="results-details">
                <h3>Latest Articles</h3>
                <div class="articles-list">
                    ${result.results.slice(0, 5).map(item => `
                        <div class="article-item">
                            <h4>${item.title || 'Untitled'}</h4>
                            <p class="article-source">Source: ${item.source || 'Unknown'}</p>
                            <p class="article-snippet">${item.content ? item.content.substring(0, 200) + '...' : 'No content available'}</p>
                            ${item.url ? `<a href="${item.url}" target="_blank" class="article-link">Read more</a>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : '<p>No detailed results available, but analysis was performed.</p>'}
            
            ${analysis.sentiment_analysis ? `
            <div class="analysis-section">
                <h3>Sentiment Analysis</h3>
                <div class="sentiment-bar">
                    <div class="sentiment-positive" style="width: ${(analysis.sentiment_analysis.positive * 100)}%"></div>
                    <div class="sentiment-neutral" style="width: ${(analysis.sentiment_analysis.neutral * 100)}%"></div>
                    <div class="sentiment-negative" style="width: ${(analysis.sentiment_analysis.negative * 100)}%"></div>
                </div>
                <div class="sentiment-labels">
                    <span>Positive: ${(analysis.sentiment_analysis.positive * 100).toFixed(1)}%</span>
                    <span>Neutral: ${(analysis.sentiment_analysis.neutral * 100).toFixed(1)}%</span>
                    <span>Negative: ${(analysis.sentiment_analysis.negative * 100).toFixed(1)}%</span>
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    // Create a modal or redirect to results page
    showResultsModal(resultsHtml, result);
}

/**
 * Show results in a modal
 */
function showResultsModal(html, data) {
    const modal = document.createElement('div');
    modal.className = 'results-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Search Results</h3>
                <button class="modal-close" onclick="this.closest('.results-modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                ${html}
                <div class="results-actions">
                    <button class="btn btn-primary" onclick="downloadResults()">
                        <i class="fas fa-download"></i>
                        Download Report
                    </button>
                    <button class="btn btn-secondary" onclick="this.closest('.results-modal').remove()">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Store results data for download
    window.currentResults = data;
}

/**
 * Download results as JSON
 */
window.downloadResults = function() {
    if (!window.currentResults) return;
    
    const dataStr = JSON.stringify(window.currentResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `factryl-report-${window.currentResults.query.replace(/\s+/g, '-')}.json`;
    link.click();
};

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.closest('.notification').remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'info-circle',
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'error': 'exclamation-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Utility functions
 */
window.utils = {
    // Format numbers with commas
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },
    
    // Format dates
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    // Truncate text
    truncateText: function(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Add some CSS for notifications and modals
const additionalStyles = `
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    min-width: 300px;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
}

.notification-info { border-left: 4px solid #3182ce; }
.notification-success { border-left: 4px solid #38a169; }
.notification-warning { border-left: 4px solid #d69e2e; }
.notification-error { border-left: 4px solid #e53e3e; }

.notification-close {
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0.6;
    margin-left: auto;
}

.results-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
}

.modal-content {
    background: white;
    border-radius: 12px;
    max-width: 800px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #e2e8f0;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    opacity: 0.6;
}

.modal-body {
    padding: 20px;
}

.results-actions {
    display: flex;
    gap: 12px;
    margin-top: 20px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-secondary {
    background: #e2e8f0;
    color: #4a5568;
}

.summary-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.stat-card {
    background: #f7fafc;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #e2e8f0;
}

.stat-number {
    font-size: 1.5rem;
    font-weight: bold;
    color: #667eea;
    margin-bottom: 5px;
}

.stat-label {
    font-size: 0.9rem;
    color: #718096;
}

.results-details {
    margin-top: 25px;
}

.articles-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-top: 15px;
}

.article-item {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.article-item h4 {
    margin: 0 0 8px 0;
    color: #2d3748;
    font-size: 1rem;
}

.article-source {
    font-size: 0.85rem;
    color: #667eea;
    font-weight: 500;
    margin: 0 0 8px 0;
}

.article-snippet {
    color: #4a5568;
    margin: 0 0 10px 0;
    line-height: 1.4;
}

.article-link {
    color: #667eea;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
}

.article-link:hover {
    text-decoration: underline;
}

.analysis-section {
    margin-top: 25px;
    padding-top: 20px;
    border-top: 1px solid #e2e8f0;
}

.sentiment-bar {
    height: 20px;
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    margin: 10px 0;
    border: 1px solid #e2e8f0;
}

.sentiment-positive {
    background: #48bb78;
}

.sentiment-neutral {
    background: #ed8936;
}

.sentiment-negative {
    background: #f56565;
}

.sentiment-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.9rem;
}

.sentiment-labels span {
    padding: 5px 10px;
    border-radius: 4px;
    background: #f7fafc;
}
</style>
`;

// Inject additional styles
document.head.insertAdjacentHTML('beforeend', additionalStyles); 