/**
 * RubyRidge Ammo Inventory - UPC Management Script
 * Handles UPC database functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const upcsTable = document.getElementById('upcsTable');
    const upcSearch = document.getElementById('upcSearch');
    const caliberFilter = document.getElementById('caliberFilter');
    
    // Form elements for adding UPCs
    const addUpcForm = document.getElementById('addUpcForm');
    const newUpc = document.getElementById('newUpc');
    const newName = document.getElementById('newName');
    const newCaliber = document.getElementById('newCaliber');
    const newCountPerBox = document.getElementById('newCountPerBox');
    const saveNewUpc = document.getElementById('saveNewUpc');
    
    // Form elements for editing UPCs
    const editUpcForm = document.getElementById('editUpcForm');
    const editUpcId = document.getElementById('editUpcId');
    const editUpcCode = document.getElementById('editUpcCode');
    const editName = document.getElementById('editName');
    const editCaliber = document.getElementById('editCaliber');
    const editCountPerBox = document.getElementById('editCountPerBox');
    const saveUpcChanges = document.getElementById('saveUpcChanges');
    
    // Elements for deleting UPCs
    const deleteUpcName = document.getElementById('deleteUpcName');
    const confirmDeleteUpc = document.getElementById('confirmDeleteUpc');
    
    // Elements for scraping
    const scrapeQuery = document.getElementById('scrapeQuery');
    const scrapeLimit = document.getElementById('scrapeLimit');
    const scrapeSearchBtn = document.getElementById('scrapeSearchBtn');
    const scrapeLoading = document.getElementById('scrapeLoading');
    const scrapeResults = document.getElementById('scrapeResults');
    const scrapeResultsList = document.getElementById('scrapeResultsList');
    const scrapeNoResults = document.getElementById('scrapeNoResults');
    const scrapeError = document.getElementById('scrapeError');
    
    // Modal instances
    let addModal = document.getElementById('addUpcModal') ? new bootstrap.Modal(document.getElementById('addUpcModal')) : null;
    let editModal = document.getElementById('editUpcModal') ? new bootstrap.Modal(document.getElementById('editUpcModal')) : null;
    let deleteModal = document.getElementById('deleteUpcModal') ? new bootstrap.Modal(document.getElementById('deleteUpcModal')) : null;
    
    // Attach event listeners for search and filter
    if (upcSearch) {
        upcSearch.addEventListener('input', filterUpcs);
    }
    
    if (caliberFilter) {
        caliberFilter.addEventListener('change', filterUpcs);
    }
    
    // Attach click handlers for edit and delete buttons
    if (upcsTable) {
        upcsTable.addEventListener('click', function(e) {
            const target = e.target.closest('button');
            if (!target) return;
            
            const row = target.closest('tr');
            const upcId = row.dataset.id;
            
            if (target.classList.contains('edit-upc')) {
                openEditModal(upcId, row);
            } else if (target.classList.contains('delete-upc')) {
                openDeleteModal(upcId, row);
            }
        });
    }
    
    // Save new UPC button click handler
    if (saveNewUpc) {
        saveNewUpc.addEventListener('click', function() {
            if (addUpcForm.checkValidity()) {
                addUpc();
            } else {
                // Trigger form validation
                addUpcForm.reportValidity();
            }
        });
    }
    
    // Save UPC changes button click handler
    if (saveUpcChanges) {
        saveUpcChanges.addEventListener('click', function() {
            if (editUpcForm.checkValidity()) {
                updateUpc();
            } else {
                // Trigger form validation
                editUpcForm.reportValidity();
            }
        });
    }
    
    // Confirm delete button click handler
    if (confirmDeleteUpc) {
        confirmDeleteUpc.addEventListener('click', function() {
            deleteUpc();
        });
    }
    
    // Scrape Search button click handler
    if (scrapeSearchBtn) {
        scrapeSearchBtn.addEventListener('click', function() {
            searchAmmo();
        });
    }
    
    // Enter key handler for scrape search input
    if (scrapeQuery) {
        scrapeQuery.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchAmmo();
            }
        });
    }
    
    // Quick search buttons click handlers
    const quickSearchButtons = document.querySelectorAll('.quick-search-btn');
    if (quickSearchButtons.length > 0) {
        quickSearchButtons.forEach(button => {
            button.addEventListener('click', function() {
                const caliber = this.getAttribute('data-caliber');
                if (caliber && scrapeQuery) {
                    scrapeQuery.value = caliber;
                    searchAmmo();
                }
            });
        });
    }
    
    /**
     * Filter UPCs table based on search and filter inputs
     */
    function filterUpcs() {
        const searchTerm = upcSearch.value.toLowerCase();
        const caliber = caliberFilter.value;
        
        const rows = upcsTable.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            // Skip header row
            if (!row.dataset.id) return;
            
            const rowCaliber = row.dataset.caliber;
            const cells = row.querySelectorAll('td');
            const textContent = Array.from(cells).slice(0, 4).map(cell => cell.textContent.toLowerCase()).join(' ');
            
            let showRow = true;
            
            // Apply search filter
            if (searchTerm && !textContent.includes(searchTerm)) {
                showRow = false;
            }
            
            // Apply caliber filter
            if (caliber && rowCaliber !== caliber) {
                showRow = false;
            }
            
            row.style.display = showRow ? '' : 'none';
        });
    }
    
    /**
     * Open the edit modal for a UPC item
     * @param {string} upcId - The ID of the UPC to edit
     * @param {HTMLElement} row - The table row element
     */
    function openEditModal(upcId, row) {
        const cells = row.querySelectorAll('td');
        
        // Populate the form with the current values
        editUpcId.value = upcId;
        editUpcCode.value = cells[0].textContent;
        editName.value = cells[1].textContent;
        editCaliber.value = cells[2].textContent;
        editCountPerBox.value = cells[3].textContent;
        
        // Show the modal
        editModal.show();
    }
    
    /**
     * Open the delete confirmation modal
     * @param {string} upcId - The ID of the UPC to delete
     * @param {HTMLElement} row - The table row element
     */
    function openDeleteModal(upcId, row) {
        const cells = row.querySelectorAll('td');
        const upcName = cells[1].textContent;
        
        // Set the UPC ID on the modal
        deleteUpcModal.dataset.upcId = upcId;
        
        // Show the UPC name in the confirmation message
        deleteUpcName.textContent = upcName;
        
        // Show the modal
        deleteModal.show();
    }
    
    /**
     * Add a new UPC to the database
     */
    function addUpc() {
        const upcData = {
            upc: newUpc.value,
            name: newName.value,
            caliber: newCaliber.value,
            count_per_box: parseInt(newCountPerBox.value)
        };
        
        fetch('/api/add_upc', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(upcData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Hide the modal
                    addModal.hide();
                    
                    // Show success message
                    showAlert('UPC added successfully!', 'success');
                    
                    // Reload the page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error adding UPC: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error adding UPC:', error);
                showAlert('Error adding UPC: ' + error.message, 'danger');
            });
    }
    
    /**
     * Update a UPC in the database
     */
    function updateUpc() {
        const upcId = editUpcId.value;
        
        const updatedData = {
            upc: editUpcCode.value,
            name: editName.value,
            caliber: editCaliber.value,
            count_per_box: parseInt(editCountPerBox.value)
        };
        
        fetch(`/api/update_upc/${upcId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Hide the modal
                    editModal.hide();
                    
                    // Show success message
                    showAlert('UPC updated successfully!', 'success');
                    
                    // Reload the page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error updating UPC: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error updating UPC:', error);
                showAlert('Error updating UPC: ' + error.message, 'danger');
            });
    }
    
    /**
     * Delete a UPC from the database
     */
    function deleteUpc() {
        const upcId = deleteUpcModal.dataset.upcId;
        
        fetch(`/api/delete_upc/${upcId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Hide the modal
                    deleteModal.hide();
                    
                    // Show success message
                    showAlert('UPC deleted successfully!', 'success');
                    
                    // Reload the page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error deleting UPC: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error deleting UPC:', error);
                showAlert('Error deleting UPC: ' + error.message, 'danger');
            });
    }
    
    /**
     * Search for ammunition products using the scraper
     */
    function searchAmmo() {
        const query = scrapeQuery.value.trim();
        
        if (!query) {
            showAlert('Please enter a search term', 'warning');
            return;
        }
        
        // Reset UI
        scrapeLoading.style.display = 'block';
        scrapeResults.style.display = 'none';
        scrapeNoResults.style.display = 'none';
        scrapeError.style.display = 'none';
        scrapeResultsList.innerHTML = '';
        
        // Get the product limit
        const limit = parseInt(scrapeLimit.value) || 5;
        
        // Make API request
        fetch('/api/scrape_ammo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                max_products: limit
            })
        })
            .then(response => response.json())
            .then(result => {
                // Hide loading indicator
                scrapeLoading.style.display = 'none';
                
                if (result.success) {
                    const products = result.results;
                    
                    if (products && products.length > 0) {
                        // Show results
                        scrapeResults.style.display = 'block';
                        
                        // Create result cards
                        renderProductResults(products);
                    } else {
                        // Show no results message
                        scrapeNoResults.style.display = 'block';
                    }
                } else {
                    // Show error message
                    scrapeError.textContent = result.message || 'An error occurred while scraping ammo data';
                    scrapeError.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error scraping ammunition:', error);
                
                // Hide loading indicator
                scrapeLoading.style.display = 'none';
                
                // Show error message
                scrapeError.textContent = 'Error: ' + error.message;
                scrapeError.style.display = 'block';
            });
    }
    
    /**
     * Render product results from scraper
     * @param {Array} products - Array of product objects
     */
    function renderProductResults(products) {
        scrapeResultsList.innerHTML = '';
        
        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'card bg-secondary mb-3';
            
            let html = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <h5 class="card-title text-white">${product.name}</h5>
                        <span class="badge bg-danger">${product.price || 'Price N/A'}</span>
                    </div>
                    <div class="product-details mb-3">
                        <div class="row">
                            <div class="col-md-4 mb-2">
                                <div class="text-muted">UPC:</div>
                                <div class="fw-bold text-white">${product.upc}</div>
                            </div>
                            <div class="col-md-4 mb-2">
                                <div class="text-muted">Caliber:</div>
                                <div class="fw-bold text-white">${product.caliber}</div>
                            </div>
                            <div class="col-md-4 mb-2">
                                <div class="text-muted">Count Per Box:</div>
                                <div class="fw-bold text-white">${product.count_per_box}</div>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between">
                        <a href="${product.url}" target="_blank" class="btn btn-sm btn-outline-light">
                            <i class="fas fa-external-link-alt me-1"></i> View on PSA
                        </a>
                        <button class="btn btn-sm btn-success import-upc-btn" 
                            data-upc="${product.upc}" 
                            data-name="${product.name}" 
                            data-caliber="${product.caliber}" 
                            data-count="${product.count_per_box}">
                            <i class="fas fa-file-import me-1"></i> Import to Database
                        </button>
                    </div>
                </div>
            `;
            
            card.innerHTML = html;
            scrapeResultsList.appendChild(card);
            
            // Add click event to import button
            const importBtn = card.querySelector('.import-upc-btn');
            if (importBtn) {
                importBtn.addEventListener('click', function() {
                    const upcData = {
                        upc: this.dataset.upc,
                        name: this.dataset.name,
                        caliber: this.dataset.caliber,
                        count_per_box: parseInt(this.dataset.count)
                    };
                    
                    importUpcData(upcData, this);
                });
            }
        });
    }
    
    /**
     * Import UPC data from scraper results
     * @param {Object} upcData - UPC data object to import
     * @param {HTMLElement} button - The button element that was clicked
     */
    function importUpcData(upcData, button) {
        // Disable button and show loading
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Importing...';
        
        fetch('/api/add_upc', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(upcData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Update button to show success
                    button.className = 'btn btn-sm btn-success';
                    button.innerHTML = '<i class="fas fa-check me-1"></i> Imported!';
                    button.disabled = true;
                    
                    // Show success message
                    showAlert('UPC imported successfully!', 'success');
                } else {
                    // Re-enable button
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-file-import me-1"></i> Import to Database';
                    
                    // Show error message
                    showAlert('Error importing UPC: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error importing UPC:', error);
                
                // Re-enable button
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-file-import me-1"></i> Import to Database';
                
                // Show error message
                showAlert('Error importing UPC: ' + error.message, 'danger');
            });
    }
});