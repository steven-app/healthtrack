/**
 * Bootstrap Modal Flickering Fix
 * 
 * This script applies global fixes to prevent Bootstrap modal dialog boxes
 * from flickering or jumping when interacted with.
 * 
 * NOTE: This script doesn't apply to custom modals that use their own implementation.
 */

document.addEventListener('DOMContentLoaded', function() {
    // We're now using custom modals for these IDs, so don't apply Bootstrap fixes to them
    const customModals = ['customDeleteModal', 'deleteConfirmModal'];
    
    // Completely remove any Bootstrap modal functionality from our custom modals
    customModals.forEach(modalId => {
        const element = document.getElementById(modalId);
        if (element) {
            // Remove all Bootstrap modal data and classes
            element.removeAttribute('aria-hidden');
            element.removeAttribute('aria-labelledby');
            element.removeAttribute('tabindex');
            element.removeAttribute('data-bs-backdrop');
            element.removeAttribute('data-bs-keyboard');
            
            // Remove the Bootstrap modal initialization
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const bsModalInstance = bootstrap.Modal.getInstance(element);
                if (bsModalInstance) {
                    bsModalInstance.dispose();
                }
            }
        }
    });
    
    // Also handle any legacy modal backdrops that might be left over
    const existingBackdrops = document.querySelectorAll('.modal-backdrop');
    existingBackdrops.forEach(node => {
        node.parentNode.removeChild(node);
    });
    
    // 如果正在dashboard页面，确保不影响dashboard按钮的事件处理
    if (window.location.pathname.includes('/dashboard')) {
        console.log('Detected dashboard page, ensuring button functionality.');
        
        // 确保Dashboard页面的按钮功能正常
        setTimeout(function() {
            const range7dBtn = document.getElementById('range-7d');
            const range30dBtn = document.getElementById('range-30d');
            const refreshBtn = document.getElementById('refresh-dashboard');
            
            if (range7dBtn && !range7dBtn.onclick) {
                console.log('Re-binding 7d button click event');
                range7dBtn.onclick = function(e) {
                    e.preventDefault();
                    const days = 7;
                    const icon = refreshBtn?.querySelector('i');
                    if (icon) icon.classList.add('fa-spin');
                    window.location.href = `/dashboard?days=${days}`;
                    return false;
                };
            }
            
            if (range30dBtn && !range30dBtn.onclick) {
                console.log('Re-binding 30d button click event');
                range30dBtn.onclick = function(e) {
                    e.preventDefault();
                    const days = 30;
                    const icon = refreshBtn?.querySelector('i');
                    if (icon) icon.classList.add('fa-spin');
                    window.location.href = `/dashboard?days=${days}`;
                    return false;
                };
            }
            
            if (refreshBtn && !refreshBtn.onclick) {
                console.log('Re-binding refresh button click event');
                refreshBtn.onclick = function(e) {
                    e.preventDefault();
                    this.classList.add('disabled');
                    const icon = this.querySelector('i');
                    if (icon) icon.classList.add('fa-spin');
                    const days = document.getElementById('range-30d').classList.contains('active') ? 30 : 7;
                    window.location.href = `/dashboard?refresh=1&days=${days}`;
                    return false;
                };
            }
        }, 100); // 稍微延迟，确保页面完全加载
    }
}); 