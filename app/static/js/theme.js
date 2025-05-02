/**
 * Theme Switching Functionality
 * 
 * This script handles dark/light mode theme switching for the HealthTrack application.
 * It supports both manual user toggling and system preference detection.
 */

// Check for saved theme preference or use system preference
document.addEventListener('DOMContentLoaded', function() {
    // Check if user has a saved preference
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        // Apply saved preference
        document.body.classList.toggle('dark-mode', savedTheme === 'dark');
        updateThemeToggle(savedTheme === 'dark');
    } else {
        // Check system preference
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.body.classList.toggle('dark-mode', prefersDarkMode);
        updateThemeToggle(prefersDarkMode);
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.body.classList.toggle('dark-mode', e.matches);
            updateThemeToggle(e.matches);
        }
    });
    
    // Initialize theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});

/**
 * Toggles between light and dark themes
 */
function toggleTheme() {
    const isDarkMode = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    updateThemeToggle(isDarkMode);
    
    // If we have charts, update them for the new theme
    updateChartsForTheme(isDarkMode);
}

/**
 * Updates the theme toggle button icon and text
 * @param {boolean} isDarkMode - Whether dark mode is active
 */
function updateThemeToggle(isDarkMode) {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    // Add theme-toggle class if it doesn't exist
    if (!themeToggle.classList.contains('theme-toggle')) {
        themeToggle.classList.add('theme-toggle');
    }
    
    const themeIcon = themeToggle.querySelector('i');
    if (themeIcon) {
        themeIcon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    const themeText = themeToggle.querySelector('span');
    if (themeText) {
        themeText.textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';
    }
}

/**
 * Updates chart colors based on the current theme
 * @param {boolean} isDarkMode - Whether dark mode is active
 */
function updateChartsForTheme(isDarkMode) {
    // Check if Chart object exists
    if (typeof Chart !== 'undefined') {
        // Define chart colors for light and dark mode
        const chartColors = {
            light: {
                weight: {
                    borderColor: '#5AC8FA',
                    backgroundColor: 'rgba(90, 200, 250, 0.2)'
                },
                heartRate: {
                    avg: {
                        borderColor: '#FF2D55',
                        backgroundColor: 'rgba(255, 45, 85, 0.2)'
                    },
                    min: {
                        borderColor: '#FF9500',
                        backgroundColor: 'rgba(255, 149, 0, 0.2)'
                    },
                    max: {
                        borderColor: '#FF3B30',
                        backgroundColor: 'rgba(255, 59, 48, 0.2)'
                    }
                },
                activity: {
                    borderColor: '#4CD964',
                    backgroundColor: 'rgba(76, 217, 100, 0.2)'
                },
                sleep: {
                    borderColor: '#7177F7',
                    backgroundColor: 'rgba(113, 119, 247, 0.2)'
                }
            },
            dark: {
                weight: {
                    borderColor: '#70D3FF',
                    backgroundColor: 'rgba(112, 211, 255, 0.4)'
                },
                heartRate: {
                    avg: {
                        borderColor: '#FF4D6D',
                        backgroundColor: 'rgba(255, 77, 109, 0.4)'
                    },
                    min: {
                        borderColor: '#FFAA33',
                        backgroundColor: 'rgba(255, 170, 51, 0.4)'
                    },
                    max: {
                        borderColor: '#FF5E54',
                        backgroundColor: 'rgba(255, 94, 84, 0.4)'
                    }
                },
                activity: {
                    borderColor: '#57E370',
                    backgroundColor: 'rgba(87, 227, 112, 0.4)'
                },
                sleep: {
                    borderColor: '#8A90FF',
                    backgroundColor: 'rgba(138, 144, 255, 0.4)'
                }
            }
        };

        // Update all charts with new colors
        Chart.instances.forEach(chart => {
            // Get the active color set based on theme
            const colors = isDarkMode ? chartColors.dark : chartColors.light;
            
            // Update datasets based on chart type/id
            if (chart.canvas && chart.canvas.id) {
                const chartId = chart.canvas.id;
                
                if (chartId === 'weight-chart' && chart.data.datasets.length > 0) {
                    chart.data.datasets[0].borderColor = colors.weight.borderColor;
                    chart.data.datasets[0].backgroundColor = colors.weight.backgroundColor;
                    chart.data.datasets[0].pointBackgroundColor = colors.weight.borderColor;
                }
                else if (chartId === 'heart-rate-chart') {
                    chart.data.datasets.forEach((dataset, index) => {
                        if (dataset.label && dataset.label.includes('Average')) {
                            dataset.borderColor = colors.heartRate.avg.borderColor;
                            dataset.backgroundColor = colors.heartRate.avg.backgroundColor;
                            dataset.pointBackgroundColor = colors.heartRate.avg.borderColor;
                        }
                        else if (dataset.label && dataset.label.includes('Min')) {
                            dataset.borderColor = colors.heartRate.min.borderColor;
                            dataset.backgroundColor = colors.heartRate.min.backgroundColor;
                            dataset.pointBackgroundColor = colors.heartRate.min.borderColor;
                        }
                        else if (dataset.label && dataset.label.includes('Max')) {
                            dataset.borderColor = colors.heartRate.max.borderColor;
                            dataset.backgroundColor = colors.heartRate.max.backgroundColor;
                            dataset.pointBackgroundColor = colors.heartRate.max.borderColor;
                        }
                    });
                }
                else if (chartId === 'activity-chart' && chart.data.datasets.length > 0) {
                    chart.data.datasets[0].borderColor = colors.activity.borderColor;
                    chart.data.datasets[0].backgroundColor = colors.activity.backgroundColor;
                    chart.data.datasets[0].pointBackgroundColor = colors.activity.borderColor;
                }
                else if (chartId === 'sleep-chart' && chart.data.datasets.length > 0) {
                    chart.data.datasets[0].borderColor = colors.sleep.borderColor;
                    chart.data.datasets[0].backgroundColor = colors.sleep.backgroundColor;
                    chart.data.datasets[0].pointBackgroundColor = colors.sleep.borderColor;
                }
            }
            
            // Update grid lines
            if (chart.config.options.scales?.x?.grid) {
                chart.config.options.scales.x.grid.color = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
            }
            if (chart.config.options.scales?.y?.grid) {
                chart.config.options.scales.y.grid.color = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
            }
            
            // Update tick colors
            if (chart.config.options.scales?.x?.ticks) {
                chart.config.options.scales.x.ticks.color = isDarkMode ? '#cccccc' : '#666666';
            }
            if (chart.config.options.scales?.y?.ticks) {
                chart.config.options.scales.y.ticks.color = isDarkMode ? '#cccccc' : '#666666';
            }
            
            // Update title color
            if (chart.config.options.plugins?.title?.color) {
                chart.config.options.plugins.title.color = isDarkMode ? '#ffffff' : '#333333';
            }
            
            // Update legend color
            if (chart.config.options.plugins?.legend?.labels) {
                chart.config.options.plugins.legend.labels.color = isDarkMode ? '#ffffff' : '#333333';
            }
            
            chart.update();
        });
    }
} 