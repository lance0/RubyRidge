/**
 * RubyRidge Ammo Inventory - Inventory Management Script
 * Handles inventory page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const inventoryTable = document.getElementById('inventoryTable');
    const inventorySearch = document.getElementById('inventorySearch');
    const caliberFilter = document.getElementById('caliberFilter');
    const editItemModal = document.getElementById('editItemModal');
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const ammoChartCanvas = document.getElementById('ammoChart');
    
    // Chart data is directly available from the template
    
    // Form fields for editing
    const editItemForm = document.getElementById('editItemForm');
    const editItemId = document.getElementById('editItemId');
    const editName = document.getElementById('editName');
    const editCaliber = document.getElementById('editCaliber');
    const editCountPerBox = document.getElementById('editCountPerBox');
    const editQuantity = document.getElementById('editQuantity');
    const editNotes = document.getElementById('editNotes');
    
    // Buttons
    const saveItemChanges = document.getElementById('saveItemChanges');
    const confirmDelete = document.getElementById('confirmDelete');
    const deleteItemName = document.getElementById('deleteItemName');
    
    // Modal instances
    let editModal = null;
    let deleteModal = null;
    
    // Initialize modals if they exist
    if (editItemModal) {
        editModal = new bootstrap.Modal(editItemModal);
    }
    
    if (deleteConfirmModal) {
        deleteModal = new bootstrap.Modal(deleteConfirmModal);
    }
    
    // Attach event listeners for search and filter
    if (inventorySearch) {
        inventorySearch.addEventListener('input', filterInventory);
    }
    
    if (caliberFilter) {
        caliberFilter.addEventListener('change', filterInventory);
    }
    
    // Attach click handlers for edit and delete buttons
    if (inventoryTable) {
        inventoryTable.addEventListener('click', function(e) {
            const target = e.target.closest('button');
            if (!target) return;
            
            const row = target.closest('tr');
            const itemId = row.dataset.id;
            
            if (target.classList.contains('edit-item')) {
                openEditModal(itemId, row);
            } else if (target.classList.contains('delete-item')) {
                openDeleteModal(itemId, row);
            }
        });
    }
    
    // Initialize ammo chart if canvas and data are available
    if (ammoChartCanvas && window.inventoryChartData) {
        initializeAmmoChart();
    }
    
    // Save changes button click handler
    if (saveItemChanges) {
        saveItemChanges.addEventListener('click', function() {
            if (editItemForm.checkValidity()) {
                saveItemEdits();
            } else {
                // Trigger form validation
                editItemForm.reportValidity();
            }
        });
    }
    
    // Confirm delete button click handler
    if (confirmDelete) {
        confirmDelete.addEventListener('click', function() {
            deleteInventoryItem();
        });
    }
    
    // Manual inventory addition
    const saveNewItem = document.getElementById('saveNewItem');
    const addInventoryForm = document.getElementById('addInventoryForm');
    
    if (saveNewItem) {
        saveNewItem.addEventListener('click', function() {
            if (addInventoryForm.checkValidity()) {
                addInventoryItem();
            } else {
                addInventoryForm.reportValidity();
            }
        });
    }
    
    // CSV Import/Export
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const importCsvBtn = document.getElementById('importCsvBtn');
    const downloadTemplateBtn = document.getElementById('downloadTemplateBtn');
    
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', exportInventoryCSV);
    }
    
    if (importCsvBtn) {
        importCsvBtn.addEventListener('click', importInventoryCSV);
    }
    
    if (downloadTemplateBtn) {
        downloadTemplateBtn.addEventListener('click', downloadCsvTemplate);
    }
    
    // Threshold settings
    const thresholdCaliber = document.getElementById('thresholdCaliber');
    const criticalThreshold = document.getElementById('criticalThreshold');
    const lowThreshold = document.getElementById('lowThreshold');
    const targetStock = document.getElementById('targetStock');
    const saveThresholds = document.getElementById('saveThresholds');
    
    if (thresholdCaliber) {
        thresholdCaliber.addEventListener('change', function() {
            if (thresholdCaliber.value) {
                loadThresholdsForCaliber(thresholdCaliber.value);
            }
        });
    }
    
    if (saveThresholds) {
        saveThresholds.addEventListener('click', saveThresholdSettings);
    }
    
    /**
     * Filter inventory table based on search and filter inputs
     */
    function filterInventory() {
        const searchTerm = inventorySearch.value.toLowerCase();
        const caliber = caliberFilter.value;
        
        const rows = inventoryTable.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            // Skip header row
            if (!row.dataset.id) return;
            
            const rowCaliber = row.dataset.caliber;
            const cells = row.querySelectorAll('td');
            const textContent = Array.from(cells).slice(0, 6).map(cell => cell.textContent.toLowerCase()).join(' ');
            
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
     * Open the edit modal for an inventory item
     * @param {string} itemId - The ID of the item to edit
     * @param {HTMLElement} row - The table row element
     */
    function openEditModal(itemId, row) {
        const cells = row.querySelectorAll('td');
        
        // Populate the form with the current values
        editItemId.value = itemId;
        editName.value = cells[0].textContent;
        editCaliber.value = cells[1].textContent;
        editCountPerBox.value = cells[2].textContent;
        editQuantity.value = cells[3].textContent;
        editNotes.value = cells[5].textContent;
        
        // Show the modal
        editModal.show();
    }
    
    /**
     * Save edits to an inventory item
     */
    function saveItemEdits() {
        const itemId = editItemId.value;
        
        const updatedData = {
            name: editName.value,
            caliber: editCaliber.value,
            count_per_box: editCountPerBox.value,
            quantity: editQuantity.value,
            notes: editNotes.value
        };
        
        fetch(`/api/update_inventory/${itemId}`, {
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
                    showAlert('Item updated successfully!', 'success');
                    
                    // Reload the page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error updating item: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error updating item:', error);
                showAlert('Error updating item: ' + error.message, 'danger');
            });
    }
    
    /**
     * Open the delete confirmation modal
     * @param {string} itemId - The ID of the item to delete
     * @param {HTMLElement} row - The table row element
     */
    function openDeleteModal(itemId, row) {
        const cells = row.querySelectorAll('td');
        const itemName = cells[0].textContent;
        
        // Set the item ID on the modal
        deleteConfirmModal.dataset.itemId = itemId;
        
        // Show the item name in the confirmation message
        deleteItemName.textContent = itemName;
        
        // Show the modal
        deleteModal.show();
    }
    
    /**
     * Delete an inventory item
     */
    function deleteInventoryItem() {
        const itemId = deleteConfirmModal.dataset.itemId;
        
        fetch(`/api/delete_inventory/${itemId}`, {
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
                    showAlert('Item deleted successfully!', 'success');
                    
                    // Reload the page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error deleting item: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error deleting item:', error);
                showAlert('Error deleting item: ' + error.message, 'danger');
            });
    }
    
    /**
     * Add a new inventory item manually
     */
    function addInventoryItem() {
        const addName = document.getElementById('addName');
        const addUpc = document.getElementById('addUpc');
        const addCaliber = document.getElementById('addCaliber');
        const addCountPerBox = document.getElementById('addCountPerBox');
        const addQuantity = document.getElementById('addQuantity');
        const addNotes = document.getElementById('addNotes');
        
        const newItemData = {
            name: addName.value,
            upc: addUpc.value || 'Unknown',
            caliber: addCaliber.value,
            count_per_box: parseInt(addCountPerBox.value),
            quantity: parseInt(addQuantity.value),
            notes: addNotes.value || ''
        };
        
        fetch('/api/add_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newItemData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Hide the modal
                    const addModal = bootstrap.Modal.getInstance(document.getElementById('addInventoryModal'));
                    addModal.hide();
                    
                    // Show success message
                    showAlert('Item added successfully!', 'success');
                    
                    // Reload the page to show updated data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showAlert('Error adding item: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error adding item:', error);
                showAlert('Error adding item: ' + error.message, 'danger');
            });
    }
    
    /**
     * Load threshold values for a selected caliber
     * @param {string} caliber - The caliber to load thresholds for
     */
    function loadThresholdsForCaliber(caliber) {
        fetch(`/api/get_thresholds/${encodeURIComponent(caliber)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Set the threshold values in the form
                    criticalThreshold.value = data.thresholds.critical || 50;
                    lowThreshold.value = data.thresholds.low || 100;
                    targetStock.value = data.thresholds.target || 500;
                }
            })
            .catch(error => {
                console.error('Error loading thresholds:', error);
            });
    }
    
    /**
     * Save threshold settings for a caliber
     */
    function saveThresholdSettings() {
        const caliber = thresholdCaliber.value;
        
        if (!caliber) {
            showAlert('Please select a caliber', 'warning');
            return;
        }
        
        const thresholdData = {
            caliber: caliber,
            critical: parseInt(criticalThreshold.value),
            low: parseInt(lowThreshold.value),
            target: parseInt(targetStock.value)
        };
        
        fetch('/api/save_thresholds', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(thresholdData)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showAlert('Threshold settings saved! Reload page to see updated charts.', 'success');
                    
                    // Optional: reload after a delay to show updated charts
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    showAlert('Error saving thresholds: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error saving thresholds:', error);
                showAlert('Error saving thresholds: ' + error.message, 'danger');
            });
    }
    
    /**
     * Export inventory data as CSV
     */
    function exportInventoryCSV() {
        // Direct download by redirecting to the export endpoint
        window.location.href = '/api/export_csv';
    }
    
    /**
     * Download CSV template
     */
    function downloadCsvTemplate() {
        // Direct download by redirecting to the template endpoint
        window.location.href = '/api/csv_template';
    }
    
    /**
     * Import inventory data from CSV
     */
    function importInventoryCSV() {
        const csvFile = document.getElementById('csvFile');
        const csvImportError = document.getElementById('csvImportError');
        const csvImportSuccess = document.getElementById('csvImportSuccess');
        
        // Reset alerts
        csvImportError.classList.add('d-none');
        csvImportSuccess.classList.add('d-none');
        
        if (!csvFile.files || csvFile.files.length === 0) {
            csvImportError.textContent = 'Please select a CSV file';
            csvImportError.classList.remove('d-none');
            return;
        }
        
        const file = csvFile.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/api/import_csv', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    csvImportSuccess.textContent = result.message;
                    csvImportSuccess.classList.remove('d-none');
                    
                    // If there are any errors, show them as well
                    if (result.errors && result.errors.length > 0) {
                        csvImportError.textContent = 'Some rows had errors: ' + result.errors.join('; ');
                        csvImportError.classList.remove('d-none');
                    }
                    
                    // Reload after a delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                } else {
                    csvImportError.textContent = result.message;
                    csvImportError.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error importing CSV:', error);
                csvImportError.textContent = 'Error importing CSV: ' + error.message;
                csvImportError.classList.remove('d-none');
            });
    }
    
    /**
     * Initialize the ammunition inventory chart with threshold visualization
     */
    function initializeAmmoChart() {
        if (!window.inventoryChartData) {
            console.error("Chart data not available");
            return;
        }
        
        const ctx = ammoChartCanvas.getContext('2d');
        
        // Convert the chart data
        const labels = window.inventoryChartData.labels;
        const values = window.inventoryChartData.values;
        
        // Set up threshold data
        const lowThresholds = window.inventoryChartData.thresholds.low;
        const criticalThresholds = window.inventoryChartData.thresholds.critical;
        const targetStocks = window.inventoryChartData.thresholds.target;
        
        // Create horizontal line annotations for thresholds
        const thresholdDatasets = [];
        
        // Create the main bar chart with custom colors based on thresholds
        const barColors = values.map((value, index) => {
            if (value <= criticalThresholds[index]) {
                return 'rgba(220, 53, 69, 0.8)'; // Danger red
            } else if (value <= lowThresholds[index]) {
                return 'rgba(255, 193, 7, 0.8)'; // Warning yellow
            } else {
                return 'rgba(40, 167, 69, 0.8)'; // Success green
            }
        });
        
        // Create the chart
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Current Inventory',
                    data: values,
                    backgroundColor: barColors,
                    borderColor: barColors.map(color => color.replace('0.8', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                return [
                                    `Critical: ${criticalThresholds[index]} rounds`,
                                    `Low: ${lowThresholds[index]} rounds`,
                                    `Target: ${targetStocks[index]} rounds`
                                ];
                            }
                        }
                    }
                }
            }
        });
    }
});
