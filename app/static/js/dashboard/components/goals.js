/**
 * Dashboard Goals Module
 * Handles loading and displaying goals and achievements
 */

/**
 * Load goals and achievements data
 */
function loadGoalsAndAchievements() {
    const goalsContainer = document.getElementById('goals-achievements-container');
    
    // Get current active view
    const days = document.getElementById('range-30d').classList.contains('active') ? 30 : 7;
    
    // Show loading state
    goalsContainer.innerHTML = `
        <div class="col-12 text-center py-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading goals and achievements...</span>
            </div>
        </div>
    `;
    
    fetch(`/dashboard/goals-achievements?days=${days}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.text();
        })
        .then(html => {
            // Update container with the HTML
            document.getElementById('goals-achievements-container').innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading goals and achievements:', error);
            document.getElementById('goals-achievements-container').innerHTML = 
                '<div class="col-12"><div class="alert alert-warning">Failed to load goals and achievements. Please refresh the page to try again.</div></div>';
        });
}

export { loadGoalsAndAchievements }; 