import os
import logging
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# In-memory storage for ammunition data
# We'll use a default inventory to start with
DEFAULT_INVENTORY = [
    {
        "id": 1,
        "name": "Federal Premium .223 Rem 55gr FMJ",
        "upc": "604544617375",
        "caliber": ".223 Remington",
        "count_per_box": 20,
        "quantity": 3,
        "total_rounds": 60,
        "notes": "Range ammo"
    },
    {
        "id": 2,
        "name": "Winchester 9mm Luger 115gr FMJ",
        "upc": "020892212602",
        "caliber": "9mm Luger",
        "count_per_box": 50,
        "quantity": 5,
        "total_rounds": 250,
        "notes": "Training ammo"
    }
]

# We'll use a session-based approach for storing inventory data
def get_inventory():
    if 'inventory' not in session:
        session['inventory'] = DEFAULT_INVENTORY
        session['next_id'] = 3  # Start after the default items
    return session['inventory']

def save_inventory(inventory):
    session['inventory'] = inventory

def get_next_id():
    if 'next_id' not in session:
        session['next_id'] = 3  # Start after the default items
    next_id = session['next_id']
    session['next_id'] = next_id + 1
    return next_id

# UPC lookup function (simulated for now, in a real app you'd use an API)
def lookup_upc(upc):
    # This would be replaced with a real API call
    upc_database = {
        "604544617375": {
            "name": "Federal Premium .223 Rem 55gr FMJ",
            "caliber": ".223 Remington",
            "count_per_box": 20
        },
        "020892212602": {
            "name": "Winchester 9mm Luger 115gr FMJ",
            "caliber": "9mm Luger",
            "count_per_box": 50
        },
        "029465088414": {
            "name": "Remington UMC .45 ACP 230gr FMJ",
            "caliber": ".45 ACP",
            "count_per_box": 50
        },
        "076683051202": {
            "name": "CCI Blazer Brass 9mm 115gr FMJ",
            "caliber": "9mm Luger",
            "count_per_box": 50
        },
        "090255815511": {
            "name": "Federal American Eagle 5.56mm 55gr FMJ",
            "caliber": "5.56 NATO",
            "count_per_box": 20
        }
    }
    
    if upc in upc_database:
        return upc_database[upc]
    
    # In a real app, you'd call an API here to get unknown UPCs
    return None

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    ammo_inventory = get_inventory()
    
    # Calculate totals by caliber
    caliber_totals = {}
    total_rounds = 0
    
    for item in ammo_inventory:
        caliber = item['caliber']
        rounds = item['total_rounds']
        total_rounds += rounds
        
        if caliber in caliber_totals:
            caliber_totals[caliber] += rounds
        else:
            caliber_totals[caliber] = rounds
    
    return render_template('inventory.html', 
                          inventory=ammo_inventory, 
                          caliber_totals=caliber_totals,
                          total_rounds=total_rounds)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/api/lookup_upc/<upc>', methods=['GET'])
def api_lookup_upc(upc):
    ammo_data = lookup_upc(upc)
    if ammo_data:
        return jsonify({"success": True, "data": ammo_data})
    else:
        return jsonify({"success": False, "message": "UPC not found in database"})

@app.route('/api/add_inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    required_fields = ['name', 'upc', 'caliber', 'count_per_box', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing required field: {field}"})
    
    inventory = get_inventory()
    
    # Calculate total rounds
    count_per_box = int(data['count_per_box'])
    quantity = int(data['quantity'])
    total_rounds = count_per_box * quantity
    
    # Create new inventory item
    new_item = {
        "id": get_next_id(),
        "name": data['name'],
        "upc": data['upc'],
        "caliber": data['caliber'],
        "count_per_box": count_per_box,
        "quantity": quantity,
        "total_rounds": total_rounds,
        "notes": data.get('notes', '')
    }
    
    inventory.append(new_item)
    save_inventory(inventory)
    
    return jsonify({"success": True, "message": "Inventory added successfully", "item": new_item})

@app.route('/api/delete_inventory/<int:item_id>', methods=['POST'])
def delete_inventory(item_id):
    inventory = get_inventory()
    
    # Find and remove the item
    for i, item in enumerate(inventory):
        if item['id'] == item_id:
            del inventory[i]
            save_inventory(inventory)
            return jsonify({"success": True, "message": "Item deleted successfully"})
    
    return jsonify({"success": False, "message": "Item not found"})

@app.route('/api/update_inventory/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    data = request.get_json()
    inventory = get_inventory()
    
    # Find and update the item
    for i, item in enumerate(inventory):
        if item['id'] == item_id:
            # Update fields that were provided
            if 'name' in data:
                item['name'] = data['name']
            if 'caliber' in data:
                item['caliber'] = data['caliber']
            if 'count_per_box' in data:
                item['count_per_box'] = int(data['count_per_box'])
            if 'quantity' in data:
                item['quantity'] = int(data['quantity'])
            if 'notes' in data:
                item['notes'] = data['notes']
            
            # Recalculate total rounds
            item['total_rounds'] = item['count_per_box'] * item['quantity']
            
            save_inventory(inventory)
            return jsonify({"success": True, "message": "Item updated successfully", "item": item})
    
    return jsonify({"success": False, "message": "Item not found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
