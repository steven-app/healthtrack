/**
 * Dark Mode Toggle Functionality
 * 
 * This script implements dark mode toggle functionality for the application.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check for saved theme preference or use the system preference
    const currentTheme = localStorage.getItem('theme') || 
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    // Apply the theme
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    
    // Function to update button icon/text
    function updateButtonState(button) {
        if (!button) return;
        
        if (document.body.classList.contains('dark-mode')) {
            button.innerHTML = '<i class="fas fa-sun"></i>';
            button.setAttribute('title', 'Switch to Light Mode');
        } else {
            button.innerHTML = '<i class="fas fa-moon"></i>';
            button.setAttribute('title', 'Switch to Dark Mode');
        }
    }
    
    // Toggle theme function
    function toggleTheme(e) {
        // Prevent default anchor behavior
        e.preventDefault();
        
        // Toggle dark mode class on body
        document.body.classList.toggle('dark-mode');
        
        // Save preference to localStorage
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
        
        // Update all toggle buttons
        document.querySelectorAll('.theme-toggle').forEach(function(button) {
            updateButtonState(button);
        });
    }
    
    // Find all theme toggle buttons and set up event listeners
    const themeToggleButtons = document.querySelectorAll('.theme-toggle');
    themeToggleButtons.forEach(function(button) {
        updateButtonState(button);
        
        // Remove any existing event listeners first
        button.removeEventListener('click', toggleTheme);
        
        // Add the event listener
        button.addEventListener('click', toggleTheme);
    });
}); 