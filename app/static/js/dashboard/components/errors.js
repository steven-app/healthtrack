/**
 * Dashboard Errors Module
 * Handles error display and management
 */

/**
 * Display an error message to the user
 */
function displayError(message) {
    console.error('Error displayed to user:', message);
    
    // Display detailed error for debugging
    const errorContainer = document.createElement('div');
    errorContainer.style.position = 'fixed';
    errorContainer.style.top = '10px';
    errorContainer.style.right = '10px';
    errorContainer.style.backgroundColor = 'var(--error)';
    errorContainer.style.color = 'var(--on-error)';
    errorContainer.style.padding = '10px';
    errorContainer.style.borderRadius = '5px';
    errorContainer.style.zIndex = '9999';
    errorContainer.style.maxWidth = '500px';
    errorContainer.style.overflow = 'auto';
    errorContainer.innerText = 'Dashboard Error: ' + message;
    document.body.appendChild(errorContainer);
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        errorContainer.style.opacity = '0';
        errorContainer.style.transition = 'opacity 1s';
        // Remove from DOM after fade out
        setTimeout(() => errorContainer.remove(), 1000);
    }, 10000);
    
    // Update summary metric values with error indicator
    document.querySelectorAll('.metric-value').forEach(element => {
        element.textContent = '--';
    });
    
    // Display error message on canvases
    document.querySelectorAll('canvas').forEach(canvas => {
        const ctx = canvas.getContext('2d');
        displayNoDataMessage(ctx, 'Error loading data');
    });
    
    // Show the no-data message with upload suggestion
    document.getElementById('no-data-message').style.display = 'block';
}

/**
 * Display a no data message on a chart canvas
 */
function displayNoDataMessage(ctx, message) {
    // Clear the canvas
    const canvas = ctx.canvas;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Display the message
    ctx.save();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '16px Arial';
    ctx.fillStyle = 'var(--text-secondary)';
    ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    ctx.restore();
}

export { displayError, displayNoDataMessage }; 