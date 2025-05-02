/**
 * Dashboard Main Module
 * Main entry point for the dashboard application
 */

import { createWeightChart, createHeartRateChart, createActivityChart, createSleepChart } from './components/charts.js';
import { updateSummaryCards } from './components/summary.js';
import { loadGoalsAndAchievements } from './components/goals.js';
import { filterDataByDate, calculateAndUpdateSummary } from './utils/data.js';
import { applyThemeColors } from './utils/theme.js';
import { ensureFullDateRange } from './utils/date.js';

// Global variables
let dashboardData = window.dashboardData || null;

/**
 * Update charts and summary cards based on the selected date range.
 * This function now properly recalculates summary data based on the selected days.
 */
function updateDisplayForDateRange(days) {
    if (!dashboardData) {
        console.warn('No data available to update display.');
        document.getElementById('no-data-message').style.display = 'block';
        return;
    }

    console.log(`Updating dashboard for ${days} days with data:`, dashboardData);

    // Create charts with data
    createWeightChart(dashboardData.weight, days);
    createHeartRateChart(dashboardData.heart_rate, days);
    createActivityChart(dashboardData.activity, days);
    createSleepChart(dashboardData.sleep, days);

    // Recalculate summary based on the selected time range
    // This ensures the summary cards show data consistent with the charts
    const calculatedSummary = calculateAndUpdateSummary(dashboardData, days);
    
    // Update summary cards with recalculated data
    updateSummaryCards({ summary: calculatedSummary });
    
    // Hide loading overlays
    document.querySelectorAll('.loading-overlay').forEach(overlay => {
        overlay.style.display = 'none';
    });
}

/**
 * Initialize the dashboard UI
 */
function initializeDashboardUI() {
    const urlParams = new URLSearchParams(window.location.search);
    const daysParam = urlParams.get('days');
    const filterDays = daysParam === '30' ? 30 : 7; // Default to 7 days

    // Calculate actual date range
    const now = new Date();
    const startDate = new Date(now);
    startDate.setDate(startDate.getDate() - filterDays);
    
    // Format dates as yyyy-mm-dd
    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    const startDateStr = formatDate(startDate);
    const endDateStr = formatDate(now);
    
    // Set the active button based on days parameter
    if (filterDays === 30) {
        document.getElementById('range-7d').classList.remove('active');
        document.getElementById('range-30d').classList.add('active');
        document.getElementById('date-range-text').textContent = `Data from ${startDateStr} to ${endDateStr}`;
    } else {
        // Ensure 7d is active by default if no param or param is not 30
        document.getElementById('range-7d').classList.add('active');
        document.getElementById('range-30d').classList.remove('active');
        document.getElementById('date-range-text').textContent = `Data from ${startDateStr} to ${endDateStr}`;
    }
    
    // Ensure date range text is left-aligned
    document.getElementById('data-range').style.textAlign = 'left';
    document.getElementById('data-range').style.display = 'block';
    document.getElementById('data-range').style.width = '100%';

    if (dashboardData) {
        console.log('Original data received:', dashboardData);

        // Standardize data structure immediately
        const summary = dashboardData.summary; // Keep original summary if present
        dashboardData = {
            weight: dashboardData.weights || dashboardData.weight || [],
            heart_rate: dashboardData.heartRates || dashboardData.heart_rate || [],
            activity: dashboardData.activities || dashboardData.activity || [],
            sleep: dashboardData.sleeps || dashboardData.sleep || [],
            summary: summary 
        };
        
        // Debug logging - check data sizes and date ranges
        console.log(`Standardized data (${filterDays} days view):`, {
            weight: {
                count: dashboardData.weight.length,
                firstDate: dashboardData.weight.length > 0 ? dashboardData.weight[0].date : 'none',
                lastDate: dashboardData.weight.length > 0 ? dashboardData.weight[dashboardData.weight.length-1].date : 'none'
            },
            heart_rate: {
                count: dashboardData.heart_rate.length,
                firstDate: dashboardData.heart_rate.length > 0 ? dashboardData.heart_rate[0].date : 'none',
                lastDate: dashboardData.heart_rate.length > 0 ? dashboardData.heart_rate[dashboardData.heart_rate.length-1].date : 'none'
            },
            activity: {
                count: dashboardData.activity.length,
                firstDate: dashboardData.activity.length > 0 ? dashboardData.activity[0].date : 'none',
                lastDate: dashboardData.activity.length > 0 ? dashboardData.activity[dashboardData.activity.length-1].date : 'none'
            },
            sleep: {
                count: dashboardData.sleep.length,
                firstDate: dashboardData.sleep.length > 0 ? dashboardData.sleep[0].date : 'none',
                lastDate: dashboardData.sleep.length > 0 ? dashboardData.sleep[dashboardData.sleep.length-1].date : 'none'
            }
        });
        
        // Debug logging - check current date
        const now = new Date();
        const thirtyDaysAgo = new Date(now);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        console.log('Date range debug:', {
            today: now.toISOString().split('T')[0],
            thirtyDaysAgo: thirtyDaysAgo.toISOString().split('T')[0]
        });

        const hasData = 
            dashboardData.weight.length > 0 || 
            dashboardData.heart_rate.length > 0 || 
            dashboardData.activity.length > 0 || 
            dashboardData.sleep.length > 0;
            
        document.getElementById('no-data-message').style.display = hasData ? 'none' : 'block';
        
        if (hasData) {
            try {
                const isDarkMode = document.body.classList.contains('dark-mode');
                applyThemeColors(isDarkMode);
                
                // Call the centralized function to update charts and summaries with the days parameter
                updateDisplayForDateRange(filterDays); 

            } catch (e) {
                console.error('Error initializing dashboard:', e);
                document.querySelectorAll('.loading-overlay').forEach(overlay => {
                    overlay.style.display = 'none'; // Hide loading on error
                });
            }
        } else {
             document.querySelectorAll('.loading-overlay').forEach(overlay => {
                overlay.style.display = 'none'; // Hide loading if no data
            });
        }

    } else {
        console.warn('No dashboardData available globally.');
        document.getElementById('no-data-message').style.display = 'block';
        document.querySelectorAll('.loading-overlay').forEach(overlay => {
            overlay.style.display = 'none'; // Hide loading if no data object
        });
    }

    loadGoalsAndAchievements();
    setupEventListeners(); // Setup listeners after initial load
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // 使用直接绑定点击事件的方式替代可能被其他库干扰的方式
    const range7dBtn = document.getElementById('range-7d');
    const range30dBtn = document.getElementById('range-30d');
    const refreshBtn = document.getElementById('refresh-dashboard');
    
    if (range7dBtn) {
        range7dBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (this.classList.contains('active')) {
                return; // Already active
            }
            
            // 设置按钮状态
            this.classList.add('active');
            range30dBtn.classList.remove('active');
            
            // 显示加载状态
            const icon = refreshBtn.querySelector('i');
            if (icon) icon.classList.add('fa-spin');
            
            // 跳转到7天视图
            window.location.href = '/dashboard?days=7';
            return false;
        };
    }
    
    if (range30dBtn) {
        range30dBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (this.classList.contains('active')) {
                return; // Already active
            }
            
            // 设置按钮状态
            this.classList.add('active');
            range7dBtn.classList.remove('active');
            
            // 显示加载状态
            const icon = refreshBtn.querySelector('i');
            if (icon) icon.classList.add('fa-spin');
            
            // 跳转到30天视图
            window.location.href = '/dashboard?days=30';
            return false;
        };
    }

    if (refreshBtn) {
        refreshBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            this.classList.add('disabled');
            const icon = this.querySelector('i');
            if (icon) icon.classList.add('fa-spin');
            
            // 获取当前选中的天数
            const days = document.getElementById('range-30d').classList.contains('active') ? 30 : 7;
            
            // 添加refresh参数强制刷新
            window.location.href = `/dashboard?refresh=1&days=${days}`;
            return false;
        };
    }
}

/**
 * Set active range button
 */
function setActiveRangeButton(button) {
    document.querySelectorAll('.toggle-btn-group .toggle-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    button.classList.add('active');
}

/**
 * Update URL parameter without page reload
 */
function updateUrlParameter(key, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url.toString());
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboardUI();
}); 