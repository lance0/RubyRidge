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
    
    // Chart data from server (if available)
    let chartData = null;
    try {
        if (document.getElementById('chart-data')) {
            chartData = JSON.parse(document.getElementById('chart-data').textContent);
        }
    } catch (e) {
        console.error('Error parsing chart data:', e);
    }
    
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
});
