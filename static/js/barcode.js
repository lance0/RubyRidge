/**
 * RubyRidge Ammo Inventory - Barcode Scanning Script
 * Handles barcode scanning and UPC lookup functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const startButton = document.getElementById('startButton');
    const resetButton = document.getElementById('resetButton');
    const scanMessage = document.getElementById('scanMessage');
    const scannerContainer = document.getElementById('scannerContainer');
    const scanResults = document.getElementById('scanResults');
    const manualUpcInput = document.getElementById('manualUpc');
    const manualLookupBtn = document.getElementById('manualLookupBtn');
    const addAmmoForm = document.getElementById('addAmmoForm');
    
    // Form fields
    const ammoUpcField = document.getElementById('ammoUpc');
    const ammoNameField = document.getElementById('ammoName');
    const ammoCaliberField = document.getElementById('ammoCaliber');
    const ammoCountPerBoxField = document.getElementById('ammoCountPerBox');
    const ammoQuantityField = document.getElementById('ammoQuantity');
    const ammoNotesField = document.getElementById('ammoNotes');
    
    // Scanner state
    let quaggaScanner = null;
    let scanning = false;
    
    // Start scanner button click handler
    if (startButton) {
        startButton.addEventListener('click', function() {
            if (!scanning) {
                startScanner();
            }
        });
    }
    
    // Reset scanner button click handler
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            resetScanner();
        });
    }
    
    // Manual UPC lookup button click handler
    if (manualLookupBtn) {
        manualLookupBtn.addEventListener('click', function() {
            const upc = manualUpcInput.value.trim();
            if (upc) {
                lookupUpc(upc);
            } else {
                showAlert('Please enter a UPC code', 'warning');
            }
        });
    }
    
    // Manual UPC input enter key handler
    if (manualUpcInput) {
        manualUpcInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const upc = manualUpcInput.value.trim();
                if (upc) {
                    lookupUpc(upc);
                } else {
                    showAlert('Please enter a UPC code', 'warning');
                }
            }
        });
    }
    
    // Add ammo form submit handler
    if (addAmmoForm) {
        addAmmoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const ammoData = {
                upc: ammoUpcField.value,
                name: ammoNameField.value,
                caliber: ammoCaliberField.value,
                count_per_box: ammoCountPerBoxField.value,
                quantity: ammoQuantityField.value,
                notes: ammoNotesField.value
            };
            
            addToInventory(ammoData);
        });
    }
    
    /**
     * Initialize and start the barcode scanner
     */
    function startScanner() {
        if (!Quagga) {
            showAlert('Barcode scanning library not available', 'danger');
            return;
        }
        
        scanning = true;
        scannerContainer.style.display = 'block';
        startButton.style.display = 'none';
        resetButton.style.display = 'inline-block';
        scanMessage.textContent = 'Point camera at a barcode...';
        
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector('#scanner'),
                constraints: {
                    width: 640,
                    height: 480,
                    facingMode: "environment", // Use back camera on mobile devices
                    // Add advanced camera constraints for better focus
                    advanced: [
                        { 
                            focusMode: "continuous",
                            zoom: 1.0
                        }
                    ]
                },
                area: { // This helps define a scanning area to improve accuracy
                    top: "25%",    
                    right: "10%",  
                    left: "10%",   
                    bottom: "25%"  
                },
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            frequency: 10, // Increase scanning frequency for better results
            decoder: {
                readers: [
                    "upc_reader", 
                    "upc_e_reader", 
                    "ean_reader", 
                    "ean_8_reader", 
                    "code_39_reader", 
                    "code_128_reader"
                ],
                multiple: false
            }
        }, function(err) {
            if (err) {
                console.error("Error initializing Quagga:", err);
                scanMessage.textContent = 'Camera access error. Check permissions.';
                scanMessage.style.color = 'red';
                resetScanner();
                showAlert('Camera access error: ' + err.name, 'danger');
                return;
            }
            
            quaggaScanner = Quagga;
            Quagga.start();
        });
        
        // Add a visual scanning guide for better focus
        const scannerElement = document.querySelector('#scanner');
        if (scannerElement) {
            const overlay = document.createElement('div');
            overlay.className = 'barcode-scanner-overlay';
            overlay.innerHTML = '<div class="scanning-area"><div class="scanner-line"></div></div>';
            scannerElement.appendChild(overlay);
        }

        // Add event for processing result with confidence check
        Quagga.onProcessed(function(result) {
            const drawingCtx = Quagga.canvas.ctx.overlay;
            const drawingCanvas = Quagga.canvas.dom.overlay;
            
            if (result) {
                if (result.boxes) {
                    drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                    result.boxes.filter(function(box) {
                        return box !== result.box;
                    }).forEach(function(box) {
                        Quagga.ImageDebug.drawPath(box, {x: 0, y: 1}, drawingCtx, {color: "yellow", lineWidth: 2});
                    });
                }
                
                if (result.box) {
                    Quagga.ImageDebug.drawPath(result.box, {x: 0, y: 1}, drawingCtx, {color: "#00F", lineWidth: 2});
                }
                
                if (result.codeResult && result.codeResult.code) {
                    Quagga.ImageDebug.drawPath(result.line, {x: 'x', y: 'y'}, drawingCtx, {color: 'red', lineWidth: 3});
                }
            }
        });

        // When a barcode is detected
        Quagga.onDetected(function(result) {
            if (result && result.codeResult && result.codeResult.code) {
                // Check confidence level - only accept high confidence results
                if (result.codeResult.startInfo.error > 0.1) {
                    return; // Skip low-confidence scans
                }
                
                const code = result.codeResult.code;
                scanMessage.textContent = `Barcode detected: ${code}`;
                
                // Play a success sound
                const successAudio = new Audio("data:audio/wav;base64,//uQRAAAAWMSLwUIYAAsYkXgoQwAEaYLWfkWgAI0wWs/ItAAAGDgYtAgAyN+QWaAAihwMWm4G8QQRDiMcCBcH3Cc+CDv/7xA4Tvh9Rz/y8QADBwMWgQAZG/ILNAARQ4GLTcDeIIIhxGOBAuD7hOfBB3/94gcJ3w+o5/5eIAIAAAVwWgQAVQ2ORaIQwEMAJiDg95G4nQL7mQVWI6GwRcfsZAcsKkJvxgxEjzFUgfHoSQ9Qq7KNwqHwuB13MA4a1q/DmBrHgPcmjiGoh//EwC5nGPEmS4RcfkVKOhJf+WOgoxJclFz3kgn//dBA+ya1GhurNn8zb//9NNutNuhz31f////9vt///z+IdAEAAAK4LQIAKobHItEIYCGAExBwe8jcToF9zIKrEdDYIuP2MgOWFSE34wYiR5iqQPj0JIeoVdlG4VD4XA67mAcNa1fhzA1jwHuTRxDUQ//iYBczjHiTJcIuPyKlHQkv/LHQUYkuSi57yQT//uggfZNajQ3Vm//Lm//GTZuDtj4YeLw3w8y8IBFcG9f9dgobm1vbW7Fksnk0v/homAAAU1wXgQAVlDXGfkuCqAqPU0rHMkhyahkNXdDqYkMZhXnP+eQYwLeuiVk7lXdhOm3+/h7hM9HqNg+wKrMslkUFz4b9vr+Y8oDeNLXT0rHrXt4Me4/XPgT3+3G+AdqHR0FMTgI3LhtOXT+tmzsamS1n9JmNKuQxpipn/0+b3oqc8gqBgXRTmocm995h++U1GrtUXAzevBDZR3B/2b+gP0jIvfOxTM267OAK7s8kUYl/RIuy/xYv7O1DiYjZ1GJgYcPzITdGXPmOvYvzG8xDZ/ZX8lPRi6E+CVvYp/qwmw58jH6gYWVaUDhDI309/bJHTS5aLukpzKGUUtZrt0SAgLCQS/e9KdI2iwHA+sFpRrZKaXfZSnKuc5dRw5Le9ia7KUqy1htZKaXfZSnKuc5dRw5Le9ia7K20QQn13yV34VQFdwwDV0Y0nCcBtIRDjXDG7HNpCIJGOYWBgDUq9IKjm15/F3+EUZVCe3WSbvY7Lm5X9ORdXzvjRnaVaOT9ha7NGJBQlGJSs6CCSaG0mN1pwkyVbG0tdFLAZiEgW/uFpNBbloE9yQkN0xQh9Ww0VARPn60Bvr7dJnFAA1r9PGe/LhR+/3alxgMRUJkAKmdfKsF4wZrQ8aH0YiYKI6aOKuwjDfiCBXCpKYY2L3stctoXe6ED1QjEYbQGP4MBB2/GnYwDI0kS8JL1b35FD/uuxWD9yIDD/4YF+sRUBgvpOmoxzm62yPRFEhGEeSGpFQ6gEy+U0NwQp6ZvkuVKBnSCQxB/DHi4giAOQJ5FofEYXgV5WEYCAsOvwsKMR4ZsA+EBgUCw+KBSIHhYWBY8Kg5MGhbXBYUFhUNgUGhkdgUHhUdgoUGokHhkegcIDEUCcH01+AxiAe0EAYQRXMARMIsUK1RKIxmIxmImWLGEYjGcjMbiAxEjmYyW42OmJeOx+MnZrPAJPwQCWYABgAIAGBZuOWpQBJoQAAIAxGMDsdjcbjMZhMJhMJgkEgkMikMCmczGI34vEwkmovF4vF4vF4vE4nFYri4jjYrFYrFYOLxUAwUDQVlcpnslj8vl8hj8Zi8DhsXxcRx8Tw8Lw8JhMJhMJhMJisXisNCOGxWOAIAAJhMJhMJhMJw2Gw2Gw2GweEwmDwcCgcEAf//Z");
                successAudio.play();
                
                // Create a slight vibration on success (for mobile devices)
                if (navigator.vibrate) {
                    navigator.vibrate(200);
                }
                
                // Stop the scanner and look up the UPC
                Quagga.stop();
                scanning = false;
                
                // Look up the UPC information
                lookupUpc(code);
            }
        });
    }
    
    /**
     * Reset the barcode scanner
     */
    function resetScanner() {
        if (quaggaScanner) {
            quaggaScanner.stop();
            quaggaScanner = null;
        }
        
        scanning = false;
        scannerContainer.style.display = 'none';
        startButton.style.display = 'inline-block';
        resetButton.style.display = 'none';
        scanMessage.textContent = '';
        scanResults.style.display = 'none';
    }
    
    /**
     * Look up UPC code from server
     * @param {string} upc - The UPC code to look up
     */
    function lookupUpc(upc) {
        scanMessage.textContent = `Looking up UPC: ${upc}...`;
        
        fetch(`/api/lookup_upc/${upc}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    scanMessage.textContent = `UPC found: ${data.data.name}`;
                    
                    // Populate the form fields with the UPC data
                    ammoUpcField.value = upc;
                    ammoNameField.value = data.data.name;
                    ammoCaliberField.value = data.data.caliber;
                    ammoCountPerBoxField.value = data.data.count_per_box;
                    ammoQuantityField.value = 1; // Default to 1 box
                    ammoNotesField.value = ''; // Clear any previous notes
                    
                    // Show the scan results form
                    scanResults.style.display = 'block';
                    
                    // Scroll to the form
                    scanResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    scanMessage.textContent = `UPC not found: ${upc}`;
                    showAlert('UPC not found in database. Enter details manually.', 'warning');
                    
                    // Show the form with empty fields for manual entry
                    ammoUpcField.value = upc;
                    ammoNameField.value = '';
                    ammoCaliberField.value = '';
                    ammoCountPerBoxField.value = '';
                    ammoQuantityField.value = 1;
                    ammoNotesField.value = '';
                    
                    scanResults.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error looking up UPC:', error);
                scanMessage.textContent = 'Error looking up UPC';
                showAlert('Error looking up UPC: ' + error.message, 'danger');
            });
    }
    
    /**
     * Add ammunition to inventory
     * @param {Object} data - The ammunition data to add
     */
    function addToInventory(data) {
        fetch('/api/add_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showAlert('Ammunition added to inventory!', 'success');
                    
                    // Reset the form and scanner
                    resetScanner();
                    scanResults.style.display = 'none';
                    
                    // Redirect to inventory page after 1 second
                    setTimeout(() => {
                        window.location.href = '/inventory';
                    }, 1000);
                } else {
                    showAlert('Error adding to inventory: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error adding to inventory:', error);
                showAlert('Error adding to inventory: ' + error.message, 'danger');
            });
    }
});
