/**
 * Dashboard Data Utilities Module
 * Handles data processing and manipulation
 */

/**
 * Filter data array by date
 */
function filterDataByDate(dataArray, startDate) {
    if (!dataArray || !Array.isArray(dataArray)) return [];
    
    return dataArray.filter(item => {
        if (!item || !item.date) return false;
        
        try {
            const itemDate = new Date(item.date);
            return itemDate >= startDate;
        } catch (e) {
            console.error(`Error parsing date: ${item.date}`, e);
            return false;
        }
    });
}

/**
 * Safely parse JSON string, handling invalid values
 */
function safeParseJson(jsonString) {
    let cleanedString = jsonString
        .replace(/NaN/g, "null")
        .replace(/Infinity/g, "null")
        .replace(/-Infinity/g, "null");
    
    try {
        return JSON.parse(cleanedString);
    } catch (e) {
        console.error("First cleaning attempt failed:", e);
        
        cleanedString = jsonString.replace(/"[^"]+":(?:\s*)(NaN|-?Infinity)/g, function(match) {
            return match.replace(/(NaN|-?Infinity)/, "null");
        });
        
        try {
            return JSON.parse(cleanedString);
        } catch (e2) {
            console.error("Second cleaning attempt failed:", e2);
            
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

/**
 * Calculate and update summary based on filtered data
 */
function calculateAndUpdateSummary(data, days) {
    if (!data) return {};
    
    // Get start date for filtering
    const now = new Date();
    const startDate = new Date(now);
    startDate.setDate(startDate.getDate() - days);
    
    // Ensure data has the expected structure
    const dataToUse = {
        weight: Array.isArray(data.weight) ? data.weight : 
               (Array.isArray(data.weights) ? data.weights : []),
        heart_rate: Array.isArray(data.heart_rate) ? data.heart_rate : 
                   (Array.isArray(data.heartRates) ? data.heartRates : []),
        activity: Array.isArray(data.activity) ? data.activity : 
                 (Array.isArray(data.activities) ? data.activities : []),
        sleep: Array.isArray(data.sleep) ? data.sleep : 
              (Array.isArray(data.sleeps) ? data.sleeps : [])
    };
    
    // Filter data based on selected days
    const filtered = {
        weight: filterDataByDate(dataToUse.weight, startDate),
        heart_rate: filterDataByDate(dataToUse.heart_rate, startDate),
        activity: filterDataByDate(dataToUse.activity, startDate),
        sleep: filterDataByDate(dataToUse.sleep, startDate)
    };
    
    console.log(`Data filtered for ${days} days:`, filtered);
    
    const summary = {};
    
    // Weight summary
    if (filtered.weight && filtered.weight.length > 0) {
        // Sort by date (most recent first)
        const sortedWeights = [...filtered.weight].sort((a, b) => {
            return new Date(b.date) - new Date(a.date);
        });
        
        // Get values from objects, handling different data formats
        const getValue = (obj) => {
            if (obj.value !== undefined) return parseFloat(obj.value);
            if (obj.weight !== undefined) return parseFloat(obj.weight);
            return 0;
        };
        
        const latest = getValue(sortedWeights[0]);
        const unit = sortedWeights[0].unit || 'kg';
        
        let change = 0;
        let change_percent = 0;
        
        if (sortedWeights.length > 1) {
            const oldest = getValue(sortedWeights[sortedWeights.length - 1]);
            change = latest - oldest;
            change_percent = oldest > 0 ? ((latest - oldest) / oldest * 100) : 0;
        }
        
        summary.weight = { latest, unit, change, change_percent };
    }
    
    // Heart rate summary
    if (filtered.heart_rate && filtered.heart_rate.length > 0) {
        const getValues = (obj) => {
            const values = [];
            
            // Handle different data formats
            if (obj.min !== undefined) values.push(parseFloat(obj.min));
            if (obj.max !== undefined) values.push(parseFloat(obj.max));
            if (obj.avg !== undefined) values.push(parseFloat(obj.avg));
            if (obj.value !== undefined) values.push(parseFloat(obj.value));
            
            return values.filter(v => !isNaN(v) && v > 0);
        };
        
        // Collect all valid HR values
        let allValues = [];
        filtered.heart_rate.forEach(hr => {
            allValues = allValues.concat(getValues(hr));
        });
        
        if (allValues.length > 0) {
            const min = Math.min(...allValues);
            const max = Math.max(...allValues);
            const avg = allValues.reduce((sum, val) => sum + val, 0) / allValues.length;
            summary.heart_rate = { min, max, avg, unit: 'bpm' };
        }
    }
    
    // Activity summary
    if (filtered.activity && filtered.activity.length > 0) {
        const stepValues = filtered.activity.map(a => {
            if (a.steps !== undefined) return parseFloat(a.steps);
            if (a.total_steps !== undefined) return parseFloat(a.total_steps);
            if (a.value !== undefined) return parseFloat(a.value);
            return 0;
        }).filter(v => !isNaN(v) && v >= 0);
        
        if (stepValues.length > 0) {
            const total_steps = stepValues.reduce((sum, val) => sum + val, 0);
            const avg_steps = total_steps / days; // Average over selected days, not just days with data
            summary.activity = { total_steps, avg_steps };
        }
    }
    
    // Sleep summary
    if (filtered.sleep && filtered.sleep.length > 0) {
        const durationValues = filtered.sleep.map(s => {
            if (s.durationHours !== undefined) return parseFloat(s.durationHours);
            if (s.duration_hours !== undefined) return parseFloat(s.duration_hours);
            if (s.duration !== undefined) {
                const duration = parseFloat(s.duration);
                // If duration is in minutes, convert to hours
                return duration > 24 ? duration / 60 : duration;
            }
            return 0;
        }).filter(v => !isNaN(v) && v > 0);
        
        if (durationValues.length > 0) {
            const avg_duration_hours = durationValues.reduce((sum, val) => sum + val, 0) / durationValues.length;
            const best_duration_hours = Math.max(...durationValues);
            
            // Calculate quality distribution if available
            const qualityDistribution = { excellent: 0, good: 0, fair: 0, poor: 0 };
            let qualityCount = 0;
            
            filtered.sleep.forEach(s => {
                if (s.quality) {
                    const quality = s.quality.toLowerCase();
                    if (quality in qualityDistribution) {
                        qualityDistribution[quality]++;
                        qualityCount++;
                    }
                }
            });
            
            summary.sleep = { 
                avg_duration_hours, 
                best_duration_hours,
                quality_distribution: qualityCount > 0 ? qualityDistribution : null
            };
        }
    }
    
    return summary;
}

export { filterDataByDate, safeParseJson, calculateAndUpdateSummary }; 