/**
 * Dashboard Charts Module
 * Handles the creation and management of all dashboard charts
 */

import { addAlphaToColor } from '../utils/theme.js';
import { generateDateRange, createDataWithFullDateRange, ensureFullDateRange } from '../utils/date.js';
import { displayError } from './errors.js';

// Global chart instances
let weightChart, heartRateChart, activityChart, sleepChart;

/**
 * Display a message when no data is available
 */
function displayNoDataMessage(ctx, message) {
    // Clear the canvas
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Create temporary chart to show axes even with no data
    const tempData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        datasets: [{
            label: 'No Data',
            data: [],
            borderColor: 'rgba(0,0,0,0)',
            backgroundColor: 'rgba(0,0,0,0)'
        }]
    };
    
    const tempChart = new Chart(ctx, {
        type: 'line',
        data: tempData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    display: true,
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 7
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true
                }
            }
        }
    });
    
    // Display the message
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '16px Arial';
    ctx.fillStyle = 'var(--text-secondary)';
    ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    ctx.restore();
}

/**
 * Create weight chart
 */
function createWeightChart(weightData, days = null) {
    const ctx = document.getElementById('weight-chart').getContext('2d');
    
    if (weightChart) {
        weightChart.destroy();
    }
    
    if (!weightData || weightData.length === 0) {
        displayNoDataMessage(ctx, 'No weight data available');
        return;
    }
    
    try {
        const cleanData = weightData.filter(w => w && w.date && w.value !== undefined);
        
        if (cleanData.length === 0) {
            displayNoDataMessage(ctx, 'No valid weight data available');
            return;
        }
        
        const unit = cleanData[0].unit || 'kg';
        // Use provided days parameter if available, otherwise check DOM
        const daysToShow = days || (document.getElementById('range-30d').classList.contains('active') ? 30 : 7);
        
        console.log(`Creating weight chart with ${cleanData.length} data points for ${daysToShow} days`);
        
        // Force complete date range from today back daysToShow days
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const startDate = new Date(today);
        startDate.setDate(startDate.getDate() - daysToShow + 1);
        console.log(`Weight chart date range: ${startDate.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
        
        // Ensure we have complete date coverage using the new helper function
        const completeDataArray = ensureFullDateRange(cleanData, daysToShow);
        const dateLabels = [];
        const values = [];
        
        // Generate the date labels
        const currentDate = new Date(startDate);
        while (currentDate <= today) {
            dateLabels.push(currentDate.toISOString().split('T')[0]);
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        // Extract values from the complete data array
        completeDataArray.forEach(item => {
            values.push(item ? parseFloat(item.value) : null);
        });
        
        console.log(`Weight chart has ${dateLabels.length} date labels and ${values.filter(v => v !== null).length} values`);
        
        const style = getComputedStyle(document.documentElement);
        const weightColor = style.getPropertyValue('--chart-5').trim() || '#5AC8FA';
        const gridColor = style.getPropertyValue('--color-chart-grid').trim() || 'rgba(0, 0, 0, 0.05)';
        const textColor = style.getPropertyValue('--color-chart-text').trim() || '#666666';
        
        weightChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dateLabels,
                datasets: [{
                    label: `Weight (${unit})`,
                    data: values,
                    borderColor: weightColor,
                    backgroundColor: addAlphaToColor(weightColor, 0.3),
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: weightColor,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.raw === null) return 'No data';
                                return `Weight: ${context.raw} ${unit}`;
                            }
                        }
                    },
                    legend: {
                        labels: {
                            color: textColor
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 7,
                            color: textColor
                        },
                        grid: {
                            display: true,
                            color: gridColor
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: unit,
                            color: textColor
                        },
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            display: true,
                            color: gridColor
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating weight chart:', error);
        displayNoDataMessage(ctx, 'Error creating chart');
    }
}

/**
 * Create heart rate chart
 */
function createHeartRateChart(heartRateData, days = null) {
    const ctx = document.getElementById('heart-rate-chart').getContext('2d');
    
    if (heartRateChart) {
        heartRateChart.destroy();
    }
    
    if (!heartRateData || heartRateData.length === 0) {
        displayNoDataMessage(ctx, 'No heart rate data available');
        return;
    }
    
    try {
        const cleanData = heartRateData.filter(hr => hr && hr.date);
        
        if (cleanData.length === 0) {
            displayNoDataMessage(ctx, 'No valid heart rate data available');
            return;
        }
        
        const unit = 'bpm';
        // Use provided days parameter if available, otherwise check DOM
        const daysToShow = days || (document.getElementById('range-30d').classList.contains('active') ? 30 : 7);
        
        console.log(`Creating heart rate chart with ${cleanData.length} data points for ${daysToShow} days`);
        
        // Force complete date range from today back daysToShow days
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const startDate = new Date(today);
        startDate.setDate(startDate.getDate() - daysToShow + 1);
        console.log(`Heart rate chart date range: ${startDate.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
        
        // Ensure we have complete date coverage
        const completeDataArray = ensureFullDateRange(cleanData, daysToShow);
        
        // Generate the date labels
        const dateLabels = [];
        const currentDate = new Date(startDate);
        while (currentDate <= today) {
            dateLabels.push(currentDate.toISOString().split('T')[0]);
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        // Extract values from the complete data array
        const avgValues = [];
        const minValues = [];
        const maxValues = [];
        
        completeDataArray.forEach(item => {
            if (item) {
                let avg = null;
                if (item.avg !== undefined) avg = parseFloat(item.avg);
                else if (item.value !== undefined) avg = parseFloat(item.value);
                
                let min = item.min !== undefined ? parseFloat(item.min) : null;
                let max = item.max !== undefined ? parseFloat(item.max) : null;
                
                avgValues.push(avg);
                minValues.push(min);
                maxValues.push(max);
            } else {
                avgValues.push(null);
                minValues.push(null);
                maxValues.push(null);
            }
        });
        
        const hasMinMaxData = minValues.some(v => v !== null) && maxValues.some(v => v !== null);
        
        console.log(`Heart rate chart has ${dateLabels.length} date labels and ${avgValues.filter(v => v !== null).length} values`);
        
        const style = getComputedStyle(document.documentElement);
        const hrColor = style.getPropertyValue('--chart-3').trim() || '#FF2D55';
        const hrMinColor = style.getPropertyValue('--chart-7').trim() || '#FFCC00';
        const hrMaxColor = style.getPropertyValue('--chart-6').trim() || '#FF4081';
        const gridColor = style.getPropertyValue('--color-chart-grid').trim() || 'rgba(0, 0, 0, 0.05)';
        const textColor = style.getPropertyValue('--color-chart-text').trim() || '#666666';
        
        const datasets = [];
        
        if (hasMinMaxData) {
            datasets.push({
                label: `Min (${unit})`,
                data: minValues,
                borderColor: hrMinColor,
                borderDash: [5, 5],
                backgroundColor: 'transparent',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: false
            });
            
            datasets.push({
                label: `Max (${unit})`,
                data: maxValues,
                borderColor: hrMaxColor,
                borderDash: [5, 5],
                backgroundColor: 'transparent',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: false
            });
        }
        
        datasets.push({
            label: `Average (${unit})`,
            data: avgValues,
            borderColor: hrColor,
            backgroundColor: addAlphaToColor(hrColor, 0.3),
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: hrColor,
            borderWidth: 2
        });
        
        heartRateChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dateLabels,
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
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.raw === null) return 'No data';
                                if (context.dataset.label.includes('Min')) return `Min: ${context.raw} ${unit}`;
                                if (context.dataset.label.includes('Max')) return `Max: ${context.raw} ${unit}`;
                                return `Avg: ${context.raw} ${unit}`;
                            }
                        }
                    },
                    legend: {
                        labels: {
                            color: textColor
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 7,
                            color: textColor
                        },
                        grid: {
                            display: true,
                            color: gridColor
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: unit,
                            color: textColor
                        },
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            display: true,
                            color: gridColor
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating heart rate chart:', error);
        displayNoDataMessage(ctx, 'Error creating chart');
    }
}

/**
 * Create activity chart
 */
function createActivityChart(activityData, days = null) {
    const ctx = document.getElementById('activity-chart').getContext('2d');
    
    if (activityChart) {
        activityChart.destroy();
    }
    
    if (!activityData || activityData.length === 0) {
        displayNoDataMessage(ctx, 'No activity data available');
        return;
    }
    
    try {
        const cleanData = activityData.filter(a => a && a.date);
        
        if (cleanData.length === 0) {
            displayNoDataMessage(ctx, 'No valid activity data available');
            return;
        }
        
        // Use provided days parameter if available, otherwise check DOM
        const daysToShow = days || (document.getElementById('range-30d').classList.contains('active') ? 30 : 7);
        
        console.log(`Creating activity chart with ${cleanData.length} data points for ${daysToShow} days`);
        
        // Force complete date range from today back daysToShow days
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const startDate = new Date(today);
        startDate.setDate(startDate.getDate() - daysToShow + 1);
        console.log(`Activity chart date range: ${startDate.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
        
        // Ensure we have complete date coverage
        const completeDataArray = ensureFullDateRange(cleanData, daysToShow);
        
        // Generate the date labels
        const dateLabels = [];
        const currentDate = new Date(startDate);
        while (currentDate <= today) {
            dateLabels.push(currentDate.toISOString().split('T')[0]);
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        // Extract values from the complete data array
        const values = completeDataArray.map(item => {
            if (!item) return null;
            
            if (item.steps !== undefined) return parseFloat(item.steps);
            if (item.total_steps !== undefined) return parseFloat(item.total_steps);
            if (item.value !== undefined) return parseFloat(item.value);
            
            return null;
        });
        
        console.log(`Activity chart has ${dateLabels.length} date labels and ${values.filter(v => v !== null).length} values`);
        
        const style = getComputedStyle(document.documentElement);
        const activityColor = style.getPropertyValue('--chart-2').trim() || '#4CD964';
        const gridColor = style.getPropertyValue('--color-chart-grid').trim() || 'rgba(0, 0, 0, 0.05)';
        const textColor = style.getPropertyValue('--color-chart-text').trim() || '#666666';
        
        activityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dateLabels,
                datasets: [{
                    label: 'Steps',
                    data: values,
                    backgroundColor: activityColor,
                    borderColor: activityColor,
                    borderWidth: 1,
                    borderRadius: 4,
                    maxBarThickness: 25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.raw === null) return 'No data';
                                return `Steps: ${Math.round(context.raw).toLocaleString()}`;
                            }
                        }
                    },
                    legend: {
                        labels: {
                            color: textColor
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 7,
                            color: textColor
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        beginAtZero: true,
                        ticks: {
                            color: textColor,
                            callback: function(value) {
                                if (value >= 1000) {
                                    return (value / 1000) + 'k';
                                }
                                return value;
                            }
                        },
                        grid: {
                            display: true,
                            color: gridColor
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating activity chart:', error);
        displayNoDataMessage(ctx, 'Error creating chart');
    }
}

/**
 * Create sleep chart
 */
function createSleepChart(sleepData, days = null) {
    const ctx = document.getElementById('sleep-chart').getContext('2d');
    
    if (sleepChart) {
        sleepChart.destroy();
    }
    
    if (!sleepData || sleepData.length === 0) {
        displayNoDataMessage(ctx, 'No sleep data available');
        return;
    }
    
    try {
        const cleanData = sleepData.filter(s => s && s.date);
        
        if (cleanData.length === 0) {
            displayNoDataMessage(ctx, 'No valid sleep data available');
            return;
        }
        
        // Use provided days parameter if available, otherwise check DOM
        const daysToShow = days || (document.getElementById('range-30d').classList.contains('active') ? 30 : 7);
        
        console.log(`Creating sleep chart with ${cleanData.length} data points for ${daysToShow} days`);
        
        // Force complete date range from today back daysToShow days
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const startDate = new Date(today);
        startDate.setDate(startDate.getDate() - daysToShow + 1);
        console.log(`Sleep chart date range: ${startDate.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
        
        // Ensure we have complete date coverage
        const completeDataArray = ensureFullDateRange(cleanData, daysToShow);
        
        // Generate the date labels
        const dateLabels = [];
        const currentDate = new Date(startDate);
        while (currentDate <= today) {
            dateLabels.push(currentDate.toISOString().split('T')[0]);
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        // Extract values from the complete data array
        const values = completeDataArray.map(item => {
            if (!item) return null;
            
            if (item.durationHours !== undefined) return parseFloat(item.durationHours);
            if (item.duration_hours !== undefined) return parseFloat(item.duration_hours);
            if (item.duration !== undefined) {
                const duration = parseFloat(item.duration);
                return duration > 24 ? duration / 60 : duration; // Convert if in minutes
            }
            
            return null;
        });
        
        console.log(`Sleep chart has ${dateLabels.length} date labels and ${values.filter(v => v !== null).length} values`);
        
        const style = getComputedStyle(document.documentElement);
        const sleepColor = style.getPropertyValue('--chart-4').trim() || '#7177F7';
        const gridColor = style.getPropertyValue('--color-chart-grid').trim() || 'rgba(0, 0, 0, 0.05)';
        const textColor = style.getPropertyValue('--color-chart-text').trim() || '#666666';
        
        sleepChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dateLabels,
                datasets: [{
                    label: 'Sleep Duration',
                    data: values,
                    backgroundColor: sleepColor,
                    borderColor: sleepColor,
                    borderWidth: 1,
                    borderRadius: 4,
                    maxBarThickness: 25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.raw === null) return 'No data';
                                const hours = Math.floor(context.raw);
                                const minutes = Math.round((context.raw - hours) * 60);
                                return `Duration: ${hours}h ${minutes}m`;
                            }
                        }
                    },
                    legend: {
                        labels: {
                            color: textColor
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 7,
                            color: textColor
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        suggestedMin: 4,
                        suggestedMax: 12,
                        ticks: {
                            stepSize: 2,
                            color: textColor,
                            callback: function(value) {
                                return value + 'h';
                            }
                        },
                        grid: {
                            display: true,
                            color: gridColor
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating sleep chart:', error);
        displayNoDataMessage(ctx, 'Error creating chart');
    }
}

export {
    createWeightChart,
    createHeartRateChart,
    createActivityChart,
    createSleepChart,
    displayNoDataMessage
}; 