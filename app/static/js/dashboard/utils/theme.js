/**
 * Dashboard Theme Utilities Module
 * Handles theme-related functionality
 */

/**
 * Apply theme colors to charts
 */
function applyThemeColors(isDarkMode) {
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
            },
            grid: 'rgba(0, 0, 0, 0.1)',
            text: '#666666'
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
            },
            grid: 'rgba(255, 255, 255, 0.1)',
            text: '#cccccc'
        }
    };

    const root = document.documentElement;
    const colors = isDarkMode ? chartColors.dark : chartColors.light;
    
    root.style.setProperty('--chart-1', colors.weight.borderColor);
    root.style.setProperty('--chart-2', colors.sleep.borderColor);
    root.style.setProperty('--chart-3', colors.heartRate.avg.borderColor);
    root.style.setProperty('--chart-4', colors.activity.borderColor);
    root.style.setProperty('--chart-5', colors.weight.borderColor);
    root.style.setProperty('--chart-6', colors.heartRate.max.borderColor);
    root.style.setProperty('--chart-7', colors.heartRate.min.borderColor);
    
    root.style.setProperty('--color-chart-grid', colors.grid);
    root.style.setProperty('--color-chart-text', colors.text);
}

/**
 * Add alpha channel to color
 */
function addAlphaToColor(color, alpha) {
    if (color.startsWith('#')) {
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    else if (color.startsWith('rgba')) {
        return color.replace(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d\.]+\)/, `rgba($1, $2, $3, ${alpha})`);
    }
    else if (color.startsWith('rgb')) {
        return color.replace(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/, `rgba($1, $2, $3, ${alpha})`);
    }
    return `rgba(90, 200, 250, ${alpha})`;
}

export { applyThemeColors, addAlphaToColor }; 