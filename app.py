import os
import logging
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
from models import db, AmmoBox, UpcData
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Create default UPC data
DEFAULT_UPC_DATA = [
    {
        "upc": "604544617375",
        "name": "Federal Premium .223 Rem 55gr FMJ",
        "caliber": ".223 Remington",
        "count_per_box": 20
    },
    {
        "upc": "020892212602",
        "name": "Winchester 9mm Luger 115gr FMJ",
        "caliber": "9mm Luger",
        "count_per_box": 50
    },
    {
        "upc": "029465088414",
        "name": "Remington UMC .45 ACP 230gr FMJ",
        "caliber": ".45 ACP",
        "count_per_box": 50
    },
    {
        "upc": "076683051202",
        "name": "CCI Blazer Brass 9mm 115gr FMJ",
        "caliber": "9mm Luger",
        "count_per_box": 50
    },
    {
        "upc": "090255815511",
        "name": "Federal American Eagle 5.56mm 55gr FMJ",
        "caliber": "5.56 NATO",
        "count_per_box": 20
    }
]

# Default inventory items to add
DEFAULT_INVENTORY = [
    {
        "name": "Federal Premium .223 Rem 55gr FMJ",
        "upc": "604544617375",
        "caliber": ".223 Remington",
        "count_per_box": 20,
        "quantity": 3,
        "notes": "Range ammo"
    },
    {
        "name": "Winchester 9mm Luger 115gr FMJ",
        "upc": "020892212602",
        "caliber": "9mm Luger",
        "count_per_box": 50,
        "quantity": 5,
        "notes": "Training ammo"
    }
]

# Initialize database with default data
def initialize_database():
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Add default UPC data if it doesn't exist
        for upc_item in DEFAULT_UPC_DATA:
            if not UpcData.query.filter_by(upc=upc_item["upc"]).first():
                upc_data = UpcData(
                    upc=upc_item["upc"],
                    name=upc_item["name"],
                    caliber=upc_item["caliber"],
                    count_per_box=upc_item["count_per_box"]
                )
                db.session.add(upc_data)
        
        # Add default inventory if no items exist
        if AmmoBox.query.count() == 0:
            for item in DEFAULT_INVENTORY:
                ammo_box = AmmoBox(
                    name=item["name"],
                    upc=item["upc"],
                    caliber=item["caliber"],
                    count_per_box=item["count_per_box"],
                    quantity=item["quantity"],
                    notes=item["notes"]
                )
                db.session.add(ammo_box)
        
        db.session.commit()
        logging.info("Database initialized with default data")

# Call initialize_database function
initialize_database()

# Get inventory from database
def get_inventory():
    return AmmoBox.query.all()

# UPC lookup function from database or external API if needed
def lookup_upc(upc):
    # First check our database
    upc_data = UpcData.query.filter_by(upc=upc).first()
    
    if upc_data:
        return upc_data.to_dict()
    
    # In a real app, you'd call an API here to get unknown UPCs
    # For now we'll just return None for unknown UPCs
    return None

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inventory')
def inventory():
    # Get all inventory items from database
    ammo_inventory = AmmoBox.query.all()
    
    # Calculate totals by caliber using SQLAlchemy 
    caliber_totals = {}
    caliber_results = db.session.query(
        AmmoBox.caliber,
        func.sum(AmmoBox.total_rounds).label('total')
    ).group_by(AmmoBox.caliber).all()
    
    for result in caliber_results:
        caliber_totals[result.caliber] = result.total
    
    # Calculate total rounds
    total_rounds = db.session.query(func.sum(AmmoBox.total_rounds)).scalar() or 0
    
    # Convert database objects to dictionaries for the template
    inventory_items = [item.to_dict() for item in ammo_inventory]
    
    return render_template('inventory.html', 
                          inventory=inventory_items, 
                          caliber_totals=caliber_totals,
                          total_rounds=total_rounds)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/upcs')
def upcs():
    # Get all UPC data from database
    upc_data = UpcData.query.order_by(UpcData.name).all()
    return render_template('upcs.html', upcs=upc_data)

@app.route('/api/scrape_ammo', methods=['POST'])
def scrape_ammo():
    from scraper import PalmettoScraper
    
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"success": False, "message": "No search query provided"})
    
    query = data['query']
    max_products = data.get('max_products', 5)
    
    try:
        # Create scraper and search for products
        scraper = PalmettoScraper()
        results = scraper.search_and_get_details(query, max_products=max_products)
        
        # Filter results to only include those with UPC, caliber, and count_per_box
        valid_results = []
        for product in results:
            if 'upc' in product and 'caliber' in product and 'count_per_box' in product:
                valid_results.append(product)
        
        return jsonify({"success": True, "results": valid_results})
    
    except Exception as e:
        logging.error(f"Error scraping ammunition: {str(e)}")
        return jsonify({"success": False, "message": f"Error scraping ammunition: {str(e)}"})

@app.route('/api/lookup_upc/<upc>', methods=['GET'])
def api_lookup_upc(upc):
    ammo_data = lookup_upc(upc)
    if ammo_data:
        return jsonify({"success": True, "data": ammo_data})
    else:
        return jsonify({"success": False, "message": "UPC not found in database"})

@app.route('/api/add_upc', methods=['POST'])
def add_upc():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    required_fields = ['upc', 'name', 'caliber', 'count_per_box']
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing required field: {field}"})
    
    try:
        # Check if UPC already exists
        existing_upc = UpcData.query.filter_by(upc=data['upc']).first()
        if existing_upc:
            return jsonify({"success": False, "message": "UPC already exists in database"})
        
        # Create new UPC data
        new_upc = UpcData(
            upc=data['upc'],
            name=data['name'],
            caliber=data['caliber'],
            count_per_box=int(data['count_per_box'])
        )
        
        # Add to database
        db.session.add(new_upc)
        db.session.commit()
        
        return jsonify({"success": True, "message": "UPC added successfully", "upc": new_upc.to_dict()})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding UPC: {str(e)}")
        return jsonify({"success": False, "message": f"Error adding UPC: {str(e)}"})

@app.route('/api/update_upc/<int:upc_id>', methods=['POST'])
def update_upc(upc_id):
    data = request.get_json()
    
    try:
        # Find UPC by ID
        upc_data = UpcData.query.get(upc_id)
        
        if not upc_data:
            return jsonify({"success": False, "message": "UPC not found"})
        
        # Check if updating to a UPC that already exists (but different ID)
        if 'upc' in data and data['upc'] != upc_data.upc:
            existing = UpcData.query.filter_by(upc=data['upc']).first()
            if existing and existing.id != upc_id:
                return jsonify({"success": False, "message": "Cannot update: UPC code already exists"})
        
        # Update fields
        if 'upc' in data:
            upc_data.upc = data['upc']
        if 'name' in data:
            upc_data.name = data['name']
        if 'caliber' in data:
            upc_data.caliber = data['caliber']
        if 'count_per_box' in data:
            upc_data.count_per_box = int(data['count_per_box'])
        
        db.session.commit()
        
        # Update any inventory items using this UPC
        if any(key in data for key in ['name', 'caliber', 'count_per_box']):
            ammo_boxes = AmmoBox.query.filter_by(upc=upc_data.upc).all()
            for box in ammo_boxes:
                if 'name' in data:
                    box.name = data['name']
                if 'caliber' in data:
                    box.caliber = data['caliber']
                if 'count_per_box' in data:
                    box.count_per_box = int(data['count_per_box'])
                    box.update_total_rounds()
            
            db.session.commit()
        
        return jsonify({"success": True, "message": "UPC updated successfully", "upc": upc_data.to_dict()})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating UPC: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating UPC: {str(e)}"})

@app.route('/api/delete_upc/<int:upc_id>', methods=['POST'])
def delete_upc(upc_id):
    try:
        # Find UPC by ID
        upc_data = UpcData.query.get(upc_id)
        
        if not upc_data:
            return jsonify({"success": False, "message": "UPC not found"})
        
        # Check if this UPC is being used in inventory
        inventory_items = AmmoBox.query.filter_by(upc=upc_data.upc).count()
        if inventory_items > 0:
            return jsonify({
                "success": False, 
                "message": f"Cannot delete: UPC is used by {inventory_items} inventory items"
            })
        
        # Delete from database
        db.session.delete(upc_data)
        db.session.commit()
        
        return jsonify({"success": True, "message": "UPC deleted successfully"})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting UPC: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting UPC: {str(e)}"})

@app.route('/api/add_inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"})
    
    required_fields = ['name', 'upc', 'caliber', 'count_per_box', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing required field: {field}"})
    
    try:
        # Convert to integers
        count_per_box = int(data['count_per_box'])
        quantity = int(data['quantity'])
        
        # Create new AmmoBox object
        new_item = AmmoBox(
            name=data['name'],
            upc=data['upc'],
            caliber=data['caliber'],
            count_per_box=count_per_box,
            quantity=quantity,
            notes=data.get('notes', '')
        )
        
        # Add to database
        db.session.add(new_item)
        db.session.commit()
        
        # Check if we need to add this as UPC data for future lookups
        if not UpcData.query.filter_by(upc=data['upc']).first():
            upc_data = UpcData(
                upc=data['upc'],
                name=data['name'],
                caliber=data['caliber'],
                count_per_box=count_per_box
            )
            db.session.add(upc_data)
            db.session.commit()
        
        # Return success with item data
        return jsonify({
            "success": True, 
            "message": "Inventory added successfully", 
            "item": new_item.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding inventory: {str(e)}")
        return jsonify({"success": False, "message": f"Error adding inventory: {str(e)}"})

@app.route('/api/delete_inventory/<int:item_id>', methods=['POST'])
def delete_inventory(item_id):
    try:
        # Find the item by ID
        item = AmmoBox.query.get(item_id)
        
        if item:
            # Delete from database
            db.session.delete(item)
            db.session.commit()
            return jsonify({"success": True, "message": "Item deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Item not found"})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting inventory: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting inventory: {str(e)}"})

@app.route('/api/update_inventory/<int:item_id>', methods=['POST'])
def update_inventory(item_id):
    data = request.get_json()
    
    try:
        # Find the item by ID
        item = AmmoBox.query.get(item_id)
        
        if item:
            # Update fields that were provided
            if 'name' in data:
                item.name = data['name']
            if 'caliber' in data:
                item.caliber = data['caliber']
            if 'count_per_box' in data:
                item.count_per_box = int(data['count_per_box'])
            if 'quantity' in data:
                item.quantity = int(data['quantity'])
            if 'notes' in data:
                item.notes = data['notes']
            
            # Recalculate total rounds
            item.update_total_rounds()
            
            # Save changes
            db.session.commit()
            
            # Update UPC data if this is more current information
            if 'upc' in data:
                upc_item = UpcData.query.filter_by(upc=data['upc']).first()
                if upc_item and 'name' in data and 'caliber' in data and 'count_per_box' in data:
                    upc_item.name = data['name']
                    upc_item.caliber = data['caliber']
                    upc_item.count_per_box = int(data['count_per_box'])
                    db.session.commit()
            
            return jsonify({
                "success": True, 
                "message": "Item updated successfully", 
                "item": item.to_dict()
            })
        else:
            return jsonify({"success": False, "message": "Item not found"})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating inventory: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating inventory: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
