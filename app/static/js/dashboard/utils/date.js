/**
 * Dashboard Date Utilities Module
 * Handles date-related functionality
 */

/**
 * Generate a complete date range array
 */
function generateDateRange(startDate, endDate) {
    const dates = [];
    const currentDate = new Date(startDate);
    
    function formatDate(date) {
        return date.toISOString().split('T')[0];
    }
    
    while (currentDate <= endDate) {
        dates.push(formatDate(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return dates;
}

/**
 * Create dataset with a complete date range
 * Completely rewritten to ensure correct date range creation
 */
function createDataWithFullDateRange(data, days) {
    if (!data || data.length === 0) {
        console.warn('No data provided to createDataWithFullDateRange');
        return { labels: [], values: [] };
    }
    
    console.log(`createDataWithFullDateRange called with ${data.length} data points and ${days} days`);
    
    // ALWAYS use today as the reference point for consistency
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset time to start of day
    
    // Calculate the start date
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - days + 1);
    
    console.log(`Creating date range from ${startDate.toISOString().split('T')[0]} to ${today.toISOString().split('T')[0]}`);
    
    // Create an array of all dates in the range
    const dateLabels = [];
    const currentDate = new Date(startDate);
    
    while (currentDate <= today) {
        dateLabels.push(currentDate.toISOString().split('T')[0]);
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Check if we have the expected number of days
    if (dateLabels.length !== days) {
        console.warn(`Expected ${days} days in date range but got ${dateLabels.length}`);
    }
    
    // Create a map from date to data point
    const dateValueMap = {};
    data.forEach(item => {
        if (item && item.date) {
            try {
                const itemDate = new Date(item.date);
                const dateKey = itemDate.toISOString().split('T')[0];
                dateValueMap[dateKey] = item;
            } catch (e) {
                console.error(`Error parsing date: ${item.date}`, e);
            }
        }
    });
    
    // Map each date in the range to its data point (or null if no data)
    const values = dateLabels.map(date => dateValueMap[date] || null);
    
    // Log a summary of what we're returning
    const filledDates = values.filter(v => v !== null).length;
    console.log(`Date range created with ${dateLabels.length} days, ${filledDates} have data (${Math.round(filledDates/dateLabels.length*100)}% coverage)`);
    
    return { labels: dateLabels, values: values };
}

/**
 * Ensure that data covers the full date range requested
 * 
 * This function generates a complete array of data for each day in the range,
 * handling cases where the server might return fewer records than days requested.
 * 
 * @param {Array} data - The array of data points with date properties
 * @param {number} days - Number of days to ensure coverage for
 * @return {Array} An array with exactly 'days' entries, filled with actual data or null
 */
function ensureFullDateRange(data, days) {
    // Always use today as the end date
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Calculate the start date based on days
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - days + 1);
    
    // Generate the full date range as strings (YYYY-MM-DD)
    const dateRange = [];
    const currentDate = new Date(startDate);
    while (currentDate <= today) {
        dateRange.push(currentDate.toISOString().split('T')[0]);
        currentDate.setDate(currentDate.getDate() + 1);
    }
    
    console.log(`ensureFullDateRange: Generated ${dateRange.length} days from ${dateRange[0]} to ${dateRange[dateRange.length-1]}`);
    
    // Create a lookup map from date strings to data points
    const dateMap = {};
    data.forEach(item => {
        if (item && item.date) {
            const dateKey = new Date(item.date).toISOString().split('T')[0];
            dateMap[dateKey] = item;
        }
    });
    
    // Create a new array with an entry for each day in the range
    const result = dateRange.map(date => dateMap[date] || null);
    
    // Log statistics about the data coverage
    const filledDates = result.filter(v => v !== null).length;
    console.log(`Data coverage: ${filledDates}/${result.length} days (${Math.round(filledDates/result.length*100)}%)`);
    
    return result;
}

export { generateDateRange, createDataWithFullDateRange, ensureFullDateRange }; 