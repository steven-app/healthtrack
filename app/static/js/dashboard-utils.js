/**
 * Dashboard utilities for handling data and chart creation
 */

// Safe JSON parsing that handles NaN and Infinity values
function safeParseJson(jsonString) {
    // First try to clean the string of known problematic values
    let cleanedString = jsonString
        .replace(/NaN/g, "null")
        .replace(/Infinity/g, "null")
        .replace(/-Infinity/g, "null");
    
    try {
        // Try parsing the cleaned string
        return JSON.parse(cleanedString);
    } catch (e) {
        console.error("First cleaning attempt failed:", e);
        
        // More aggressive cleaning - find JSON properties with invalid values
        cleanedString = jsonString.replace(/"[^"]+":(?:\s*)(NaN|-?Infinity)/g, function(match) {
            console.warn("Replacing invalid value in:", match);
            // Extract the property name and replace the value with null
            return match.replace(/(NaN|-?Infinity)/, "null");
        });
        
        try {
            return JSON.parse(cleanedString);
        } catch (e2) {
            console.error("Second cleaning attempt failed:", e2);
            
            // Last resort - try to construct a minimal valid object
            console.warn("Constructing minimal valid response");
            return {
                weights: [],
                heartRates: [],
                activities: [],
                sleeps: [],
                summary: {
                    weight: { latest: 0 },
                    heart_rate: { avg: 0, min: 0, max: 0 },
                    activity: { avg_steps: 0, total_steps: 0 },
                    sleep: { avg_duration_hours: 0 }
                }
            };
        }
    }
}

// Check if a value is numeric and valid (not NaN or Infinity)
function isValidNumber(value) {
    if (value === null || value === undefined) return false;
    const num = parseFloat(value);
    return !isNaN(num) && isFinite(num);
}

// Safe parsing of numeric values with fallback
function safeNumber(value, defaultValue = 0) {
    if (!isValidNumber(value)) return defaultValue;
    return parseFloat(value);
}

// Clean chart data to remove invalid numeric values
function cleanChartData(dataArray, valueKey) {
    if (!Array.isArray(dataArray)) return [];
    
    return dataArray.filter(item => {
        if (!item || typeof item !== 'object') return false;
        if (valueKey && !isValidNumber(item[valueKey])) return false;
        return true;
    }).map(item => {
        if (!valueKey) return item;
        
        // Create a copy to avoid modifying the original
        const newItem = {...item};
        if (newItem[valueKey] !== undefined) {
            newItem[valueKey] = safeNumber(newItem[valueKey]);
        }
        return newItem;
    });
} 