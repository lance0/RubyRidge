/**
 * RubyRidge Ammo Inventory
 * Main JavaScript file for common functionality
 */

/**
 * Sets the active navigation item based on current URL
 */
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });
}

/**
 * Shows toast messages (if any exist in the DOM)
 */
function displayToastMessages() {
    // Initialize all toasts
    var toasts = document.querySelectorAll('.toast');
    toasts.forEach(function(toast) {
        var bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
    });
}

/**
 * Shows an alert message to the user
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'success', container = 'body') {
    // Create the alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find the container to append the alert to
    const containerEl = container === 'body' ? document.body : document.querySelector(container);
    
    // If container exists, prepend the alert
    if (containerEl) {
        // If container is body, create a container for the alert
        if (container === 'body') {
            const alertContainer = document.createElement('div');
            alertContainer.className = 'container mt-3';
            alertContainer.appendChild(alertDiv);
            containerEl.prepend(alertContainer);
        } else {
            containerEl.prepend(alertDiv);
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => {
                alertDiv.remove();
            }, 150);
        }, 5000);
    }
}

/**
 * Helper function to format numbers with commas
 * @param {number} num - The number to format
 * @returns {string} Formatted number string
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setActiveNavItem();
    displayToastMessages();
});