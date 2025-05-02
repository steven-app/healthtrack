/**
 * Dashboard Summary Module
 * Handles updating the summary cards with the latest data
 */

/**
 * Update all summary cards with the provided data
 */
function updateSummaryCards(data) {
    if (!data) {
        console.warn('No data provided to update cards');
        return;
    }

    // Extract summary data, handle various formats
    const summary = data.summary || data;
    
    if (!summary) {
        console.warn('No summary data provided to update cards');
        return;
    }
    
    // Debug log the data we're using
    console.log('Updating summary cards with data:', summary);
    
    // Update each card if data is available
    if (summary.weight) updateWeightSummary(summary.weight);
    if (summary.heart_rate) updateHeartRateSummary(summary.heart_rate);
    if (summary.activity) updateActivitySummary(summary.activity);
    if (summary.sleep) updateSleepSummary(summary.sleep);
}

/**
 * Update weight summary card
 */
function updateWeightSummary(weightSummary) {
    if (!weightSummary) return;

    const valueElement = document.querySelector('#weight-summary .metric-value');
    const unitElement = document.getElementById('weight-unit');
    const changeElement = document.getElementById('weight-change');

    // Ensure we have data before updating
    if (weightSummary.latest === undefined && weightSummary.current !== undefined) {
        weightSummary.latest = weightSummary.current;
    }
    
    if (weightSummary.latest === undefined) {
        console.warn('No latest weight value found in data');
        return;
    }

    // Update the weight value
    valueElement.textContent = parseFloat(weightSummary.latest).toFixed(2);
    unitElement.textContent = weightSummary.unit || 'kg';

    // Update change if available
    if ('change' in weightSummary) {
        const change = parseFloat(weightSummary.change).toFixed(2);
        const changePercent = parseFloat(weightSummary.change_percent || 0).toFixed(2);
        const changeText = `${weightSummary.change > 0 ? '+' : ''}${change} ${weightSummary.unit || 'kg'} (${changePercent}%)`;
        changeElement.textContent = changeText;
        
        changeElement.className = 'metric-change';
        if (weightSummary.change < 0) {
            changeElement.classList.add('positive');
        } else if (weightSummary.change > 0) {
            changeElement.classList.add('negative');
        }
    } else {
        changeElement.textContent = '';
    }
}

/**
 * Update heart rate summary card
 */
function updateHeartRateSummary(hrSummary) {
    if (!hrSummary) return;

    const valueElement = document.querySelector('#heart-rate-summary .metric-value');
    const rangeElement = document.getElementById('heart-rate-range');

    // Ensure we have all required data
    if (hrSummary.avg === undefined || hrSummary.min === undefined || hrSummary.max === undefined) {
        console.warn('Heart rate summary missing required data:', hrSummary);
        return;
    }

    valueElement.textContent = parseFloat(hrSummary.avg).toFixed(0);
    rangeElement.textContent = `Range: ${parseFloat(hrSummary.min).toFixed(0)} - ${parseFloat(hrSummary.max).toFixed(0)} ${hrSummary.unit || 'bpm'}`;
}

/**
 * Update activity summary card
 */
function updateActivitySummary(activitySummary) {
    if (!activitySummary) return;

    const valueElement = document.querySelector('#activity-summary .metric-value');
    const avgElement = document.getElementById('activity-avg');

    // Check if we have the expected data
    if (activitySummary.total_steps === undefined) {
        console.warn('Activity summary missing total_steps:', activitySummary);
        return;
    }

    valueElement.textContent = parseInt(activitySummary.total_steps).toLocaleString();
    
    if (activitySummary.avg_steps !== undefined) {
        avgElement.textContent = `Average: ${parseInt(activitySummary.avg_steps).toLocaleString()} steps/day`;
    } else {
        avgElement.textContent = '';
    }
}

/**
 * Update sleep summary card
 */
function updateSleepSummary(sleepSummary) {
    if (!sleepSummary) return;

    const valueElement = document.querySelector('#sleep-summary .metric-value');
    const qualityElement = document.getElementById('sleep-quality');

    // Check if we have the expected data
    if (sleepSummary.avg_duration_hours === undefined) {
        console.warn('Sleep summary missing avg_duration_hours:', sleepSummary);
        return;
    }

    valueElement.textContent = parseFloat(sleepSummary.avg_duration_hours).toFixed(2);

    // Check which data format we have for quality
    const qualityData = sleepSummary.quality || sleepSummary.quality_distribution;
    
    if (qualityData) {
        const goodCount = qualityData.good || 0;
        const fairCount = qualityData.fair || 0;
        const poorCount = qualityData.poor || 0;
        const excellentCount = qualityData.excellent || 0;
        const totalDays = goodCount + fairCount + poorCount + excellentCount;
        
        if (totalDays > 0) {
            const goodPercent = Math.round(((goodCount + excellentCount) / totalDays) * 100);
            qualityElement.textContent = `${goodPercent}% good quality sleep`;
        } else {
            qualityElement.textContent = 'Quality data not available';
        }
    } else {
        qualityElement.textContent = 'Quality data not available';
    }
}

export { updateSummaryCards }; 