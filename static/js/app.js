/**
 * RubyRidge Ammo Inventory - Main JavaScript
 * Handles common functionality across the app
 */

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Set active nav item based on current page
    setActiveNavItem();
    
    // Display toast messages if they exist
    displayToastMessages();
});

/**
 * Sets the active navigation item based on current URL
 */
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Shows toast messages (if any exist in the DOM)
 */
function displayToastMessages() {
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });
}

/**
 * Shows an alert message to the user
 * @param {string} message - The message to display
 * @param {string} type - The alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'success', container = 'body') {
    const alertContainer = document.querySelector(container);
    if (!alertContainer) return;
    
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // If container is body, create a special floating alert
    if (container === 'body') {
        const floatingAlert = document.createElement('div');
        floatingAlert.style.position = 'fixed';
        floatingAlert.style.top = '20px';
        floatingAlert.style.right = '20px';
        floatingAlert.style.zIndex = '9999';
        floatingAlert.style.maxWidth = '90%';
        floatingAlert.innerHTML = alertHTML;
        document.body.appendChild(floatingAlert);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (document.getElementById(alertId)) {
                const alert = bootstrap.Alert.getInstance(document.getElementById(alertId));
                if (alert) {
                    alert.close();
                } else {
                    document.getElementById(alertId).remove();
                }
            }
            if (document.body.contains(floatingAlert)) {
                document.body.removeChild(floatingAlert);
            }
        }, 5000);
    } else {
        // Just prepend to the specified container
        alertContainer.insertAdjacentHTML('afterbegin', alertHTML);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (document.getElementById(alertId)) {
                const alert = bootstrap.Alert.getInstance(document.getElementById(alertId));
                if (alert) {
                    alert.close();
                } else {
                    document.getElementById(alertId).remove();
                }
            }
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
