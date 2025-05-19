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
});