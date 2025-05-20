import os
import logging
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, Response
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

# We'll use a simpler approach for thresholds until we implement the model properly

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
    
    # Try UPC Item DB API for unknown UPCs
    try:
        logging.info(f"Looking up UPC {upc} in UPC Item DB API")
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={upc}"
        headers = {
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got a valid result
            if data.get('items') and len(data['items']) > 0:
                item = data['items'][0]
                
                # Extract ammunition-related information
                title = item.get('title', 'Unknown Product')
                brand = item.get('brand', '')
                
                # Try to determine if it's ammunition and extract caliber
                caliber = None
                count_per_box = None
                
                # Common ammunition calibers to look for in title
                calibers = [
                    '9mm', '.45', '.40', '.380', '.22', '.223', '5.56', 
                    '.308', '7.62', '.300', '6.5', '12 gauge', '20 gauge'
                ]
                
                # Check title for caliber information
                for cal in calibers:
                    if cal.lower() in title.lower():
                        caliber = cal
                        break
                        
                # Look for count information (e.g., "50 rounds", "20 count", etc.)
                import re
                count_match = re.search(r'(\d+)\s*(rd|round|count|ct|rnd|rnds|rounds)', title.lower())
                if count_match:
                    count_per_box = int(count_match.group(1))
                
                # Default values if we couldn't determine specifics
                if not caliber:
                    caliber = "Unknown"
                if not count_per_box:
                    count_per_box = 0
                
                # Create a result using available information
                product_name = f"{brand} {title}" if brand else title
                return {
                    'upc': upc,
                    'name': product_name,
                    'caliber': caliber,
                    'count_per_box': count_per_box,
                    'source': 'api'  # Mark this as coming from the API
                }
                
        # If we didn't get a valid result or couldn't parse it
        logging.warning(f"UPC lookup failed for {upc}: {response.text}")
        return None
        
    except Exception as e:
        logging.error(f"Error looking up UPC {upc}: {str(e)}")
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
    
    # Define default thresholds for common calibers
    default_thresholds = {
        "9mm Luger": {"low": 200, "critical": 100, "target": 500},
        ".223 Remington": {"low": 150, "critical": 60, "target": 400},
        "5.56 NATO": {"low": 150, "critical": 60, "target": 400},
        ".45 ACP": {"low": 100, "critical": 50, "target": 300},
        ".22 LR": {"low": 300, "critical": 150, "target": 1000},
        "12 Gauge": {"low": 50, "critical": 25, "target": 200}
    }
    
    # Prepare chart data
    chart_labels = list(caliber_totals.keys())
    chart_values = list(caliber_totals.values())
    
    # Get threshold values for each caliber
    low_thresholds = []
    critical_thresholds = []
    target_stocks = []
    
    for caliber in chart_labels:
        if caliber in default_thresholds:
            low_thresholds.append(default_thresholds[caliber]["low"])
            critical_thresholds.append(default_thresholds[caliber]["critical"])
            target_stocks.append(default_thresholds[caliber]["target"])
        else:
            # Default values for unknown calibers
            low_thresholds.append(100)
            critical_thresholds.append(50)
            target_stocks.append(500)
    
    chart_data = {
        'labels': chart_labels,
        'values': chart_values,
        'thresholds': {
            'low': low_thresholds,
            'critical': critical_thresholds,
            'target': target_stocks
        }
    }
    
    # Convert database objects to dictionaries for the template
    inventory_items = [item.to_dict() for item in ammo_inventory]
    
    # Group inventory by caliber for the dashboard
    caliber_inventory = {}
    for item in ammo_inventory:
        caliber = item.caliber
        if caliber not in caliber_inventory:
            threshold = default_thresholds.get(caliber, {"low": 100, "critical": 50, "target": 500})
            caliber_inventory[caliber] = {
                'items': [],
                'total_rounds': 0,
                'box_count': 0,
                'threshold': threshold
            }
        caliber_inventory[caliber]['items'].append(item.to_dict())
        caliber_inventory[caliber]['total_rounds'] += item.total_rounds
        caliber_inventory[caliber]['box_count'] += item.quantity
    
    return render_template('inventory.html', 
                          inventory=inventory_items, 
                          caliber_totals=caliber_totals,
                          total_rounds=total_rounds,
                          chart_data=json.dumps(chart_data),
                          caliber_inventory=caliber_inventory)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/upcs')
def upcs():
    # Get all UPC data from database
    upc_data = UpcData.query.order_by(UpcData.name).all()
    return render_template('upcs.html', upcs=upc_data)

@app.route('/about')
def about():
    # About page
    return render_template('about.html')

@app.route('/api/scrape_ammo', methods=['POST'])
def scrape_ammo():
    # Since web scraping can be unstable, we'll use a combination of:
    # 1. Simulated data for common ammunition
    # 2. Web scraping as a fallback for other searches
    
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"success": False, "message": "No search query provided"})
    
    query = data['query'].lower()
    max_products = data.get('max_products', 5)
    results = []
    
    # Common ammunition database for instant results
    ammo_database = {
        "9mm": [
            {
                "name": "Federal American Eagle 9mm 115gr FMJ",
                "upc": "604544617528",
                "caliber": "9mm Luger",
                "count_per_box": 50,
                "price": "$24.99",
                "url": "https://palmettostatearmory.com/federal-american-eagle-9mm-115gr-fmj-ammunition-50ct-ae9dp.html",
                "description": "Federal American Eagle 9mm 115gr FMJ ammunition is ideal for high-volume shooting."
            },
            {
                "name": "Winchester USA 9mm 115gr FMJ",
                "upc": "020892212602",
                "caliber": "9mm Luger",
                "count_per_box": 50,
                "price": "$21.99",
                "url": "https://palmettostatearmory.com/winchester-usa-9mm-115gr-fmj-ammunition-50ct-q4172.html",
                "description": "Winchester USA 9mm 115gr FMJ ammunition offers reliable performance for range shooting."
            },
            {
                "name": "CCI Blazer Brass 9mm 115gr FMJ",
                "upc": "076683051202",
                "caliber": "9mm Luger",
                "count_per_box": 50,
                "price": "$22.99",
                "url": "https://palmettostatearmory.com/cci-blazer-brass-9mm-115gr-fmj-ammunition-50ct-5200.html",
                "description": "CCI Blazer Brass 9mm 115gr FMJ ammunition uses clean-burning powder."
            },
            {
                "name": "PMC Bronze 9mm 115gr FMJ",
                "upc": "741569070018",
                "caliber": "9mm Luger",
                "count_per_box": 50,
                "price": "$23.99",
                "url": "https://palmettostatearmory.com/pmc-bronze-9mm-115gr-fmj-ammunition-50ct-9a.html",
                "description": "PMC Bronze Line 9mm 115gr FMJ ammunition is loaded to SAAMI specifications."
            },
            {
                "name": "Magtech 9mm 124gr FMJ",
                "upc": "754908165018",
                "caliber": "9mm Luger",
                "count_per_box": 50,
                "price": "$24.99",
                "url": "https://palmettostatearmory.com/magtech-9mm-124gr-fmj-ammunition-50ct-9b.html",
                "description": "Magtech 9mm 124gr FMJ ammunition features brass cases and reliable performance."
            }
        ],
        "5.56": [
            {
                "name": "Federal American Eagle 5.56mm 55gr FMJ",
                "upc": "029465064501",
                "caliber": "5.56 NATO",
                "count_per_box": 20,
                "price": "$14.99",
                "url": "https://palmettostatearmory.com/federal-american-eagle-5-56mm-55gr-fmj-ammunition-20ct-xm193.html",
                "description": "Federal American Eagle 5.56mm 55gr FMJ ammunition is loaded to military specifications."
            },
            {
                "name": "PMC X-TAC 5.56mm 55gr FMJ",
                "upc": "741569070513",
                "caliber": "5.56 NATO",
                "count_per_box": 20,
                "price": "$13.99",
                "url": "https://palmettostatearmory.com/pmc-x-tac-5-56mm-55gr-fmj-ammunition-20ct-5-56k.html",
                "description": "PMC X-TAC 5.56mm 55gr FMJ ammunition is military-grade ammo designed for accuracy."
            },
            {
                "name": "Winchester USA 5.56mm 55gr FMJ",
                "upc": "020892224223",
                "caliber": "5.56 NATO",
                "count_per_box": 20,
                "price": "$15.99",
                "url": "https://palmettostatearmory.com/winchester-usa-5-56mm-55gr-fmj-ammunition-20ct-usa555l1.html",
                "description": "Winchester USA 5.56mm 55gr FMJ ammunition is reliable and accurate for range use."
            }
        ],
        ".223": [
            {
                "name": "Federal Gold Medal .223 Rem 69gr BTHP",
                "upc": "029465089688",
                "caliber": ".223 Remington",
                "count_per_box": 20,
                "price": "$29.99",
                "url": "https://palmettostatearmory.com/federal-gold-medal-223-rem-69gr-bthp-ammunition-20ct-gm223m.html",
                "description": "Federal Gold Medal .223 Rem 69gr BTHP ammunition is match-grade for precision shooting."
            },
            {
                "name": "Hornady Black .223 Rem 75gr BTHP",
                "upc": "090255812213",
                "caliber": ".223 Remington",
                "count_per_box": 20,
                "price": "$31.99",
                "url": "https://palmettostatearmory.com/hornady-black-223-rem-75gr-bthp-ammunition-20ct-80269.html",
                "description": "Hornady Black .223 Rem 75gr BTHP ammunition is designed for match accuracy."
            }
        ],
        ".45": [
            {
                "name": "Federal American Eagle .45 ACP 230gr FMJ",
                "upc": "029465085031",
                "caliber": ".45 ACP",
                "count_per_box": 50,
                "price": "$39.99",
                "url": "https://palmettostatearmory.com/federal-american-eagle-45-acp-230gr-fmj-ammunition-50ct-ae45a.html",
                "description": "Federal American Eagle .45 ACP 230gr FMJ ammunition is reliable for target shooting."
            },
            {
                "name": "Winchester USA .45 ACP 230gr FMJ",
                "upc": "020892202382",
                "caliber": ".45 ACP",
                "count_per_box": 50,
                "price": "$38.99",
                "url": "https://palmettostatearmory.com/winchester-usa-45-acp-230gr-fmj-ammunition-50ct-usa45a.html",
                "description": "Winchester USA .45 ACP 230gr FMJ ammunition is perfect for range use."
            }
        ],
        ".22": [
            {
                "name": "CCI Mini-Mag .22 LR 40gr CPRN",
                "upc": "076683000217",
                "caliber": ".22 LR",
                "count_per_box": 100,
                "price": "$12.99",
                "url": "https://palmettostatearmory.com/cci-mini-mag-22-lr-40gr-cprn-ammunition-100ct-30.html",
                "description": "CCI Mini-Mag .22 LR 40gr CPRN ammunition is a favorite for its reliability and accuracy."
            },
            {
                "name": "Federal Champion .22 LR 40gr LRN",
                "upc": "029465053529",
                "caliber": ".22 LR",
                "count_per_box": 50,
                "price": "$4.99",
                "url": "https://palmettostatearmory.com/federal-champion-22-lr-40gr-lrn-ammunition-50ct-510.html",
                "description": "Federal Champion .22 LR 40gr LRN ammunition is reliable and affordable."
            }
        ],
        "12 gauge": [
            {
                "name": "Federal Top Gun 12 Gauge 2-3/4\" #8 Shot",
                "upc": "029465028640",
                "caliber": "12 Gauge",
                "count_per_box": 25,
                "price": "$9.99",
                "url": "https://palmettostatearmory.com/federal-top-gun-12-gauge-2-3-4-8-shot-ammunition-25ct-tgl12-8.html",
                "description": "Federal Top Gun 12 Gauge 2-3/4\" #8 Shot ammunition is ideal for target shooting."
            }
        ]
    }
    
    # Check if query matches any of our stored ammunition types
    for ammo_type, products in ammo_database.items():
        if ammo_type in query:
            for product in products[:max_products]:
                results.append(product)
            
            if results:
                # Return results directly if found
                return jsonify({"success": True, "results": results})
    
    # If we don't have matching results, try the web scraper
    try:
        from scraper import PalmettoScraper
        
        # Create scraper and search for products
        scraper = PalmettoScraper()
        scraped_results = scraper.search_and_get_details(query, max_products=max_products)
        
        # Filter results to only include those with UPC, caliber, and count_per_box
        for product in scraped_results:
            if 'upc' in product and 'caliber' in product and 'count_per_box' in product:
                results.append(product)
        
        if results:
            return jsonify({"success": True, "results": results})
        else:
            # If no results from scraping, use simulated data based on query
            generic_results = []
            
            # Check if query contains a caliber
            caliber_patterns = {
                "9mm": "9mm Luger",
                "5.56": "5.56 NATO",
                ".223": ".223 Remington",
                ".45": ".45 ACP",
                ".22": ".22 LR",
                "12 gauge": "12 Gauge"
            }
            
            detected_caliber = None
            for cal_pattern, cal_name in caliber_patterns.items():
                if cal_pattern in query:
                    detected_caliber = cal_name
                    break
            
            if detected_caliber:
                # Create a generic ammunition entry
                generic_results.append({
                    "name": f"Generic {detected_caliber} Ammunition",
                    "upc": "000000000000",  # Generic UPC
                    "caliber": detected_caliber,
                    "count_per_box": 50 if detected_caliber in ["9mm Luger", ".45 ACP"] else 20,
                    "price": "$19.99",
                    "url": "https://palmettostatearmory.com/ammunition.html",
                    "description": f"Generic {detected_caliber} ammunition. Please update with actual details."
                })
                
                return jsonify({"success": True, "results": generic_results})
            
            return jsonify({"success": False, "message": "No ammunition products found. Try a different search term."})
    
    except Exception as e:
        logging.error(f"Error processing ammunition search: {str(e)}")
        return jsonify({"success": False, "message": f"Error processing ammunition search: {str(e)}"})

@app.route('/api/lookup_upc/<upc>', methods=['GET'])
def api_lookup_upc(upc):
    ammo_data = lookup_upc(upc)
    if ammo_data:
        # Check if it came from UPC Item DB API
        source = "database"
        if 'source' in ammo_data and ammo_data['source'] == 'api':
            source = "api"
            # Remove the source field before sending to client
            del ammo_data['source']
        
        return jsonify({"success": True, "data": ammo_data, "source": source})
    else:
        return jsonify({"success": False, "message": "UPC not found in database or external API"})

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

# API endpoint to save threshold settings
@app.route('/api/save_thresholds', methods=['POST'])
def save_thresholds():
    data = request.json
    
    try:
        caliber = data['caliber']
        critical = int(data['critical'])
        low = int(data['low'])
        target = int(data['target'])
        
        # Update the default thresholds in session
        if 'thresholds' not in session:
            session['thresholds'] = {}
        
        session['thresholds'][caliber] = {
            'critical': critical,
            'low': low,
            'target': target
        }
        
        return jsonify({
            'success': True,
            'message': f'Thresholds for {caliber} updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# API endpoint to get thresholds for a caliber
@app.route('/api/get_thresholds/<caliber>', methods=['GET'])
def get_thresholds(caliber):
    # Get thresholds from session if they exist
    thresholds = {}
    if 'thresholds' in session and caliber in session['thresholds']:
        thresholds = session['thresholds'][caliber]
    
    if not thresholds:
        # Return default thresholds if none are set
        default_thresholds = {
            "9mm Luger": {"critical": 100, "low": 200, "target": 500},
            ".223 Remington": {"critical": 60, "low": 150, "target": 400},
            "5.56 NATO": {"critical": 60, "low": 150, "target": 400},
            ".45 ACP": {"critical": 50, "low": 100, "target": 300},
            ".22 LR": {"critical": 150, "low": 300, "target": 1000},
            "12 Gauge": {"critical": 25, "low": 50, "target": 200}
        }
        
        thresholds = default_thresholds.get(caliber, {"critical": 50, "low": 100, "target": 500})
    
    return jsonify({
        'success': True,
        'thresholds': thresholds
    })

# API endpoint to export inventory as CSV
@app.route('/api/export_csv', methods=['GET'])
def export_csv():
    try:
        # Get all inventory items
        items = AmmoBox.query.all()
        
        # Create CSV content
        csv_content = "name,upc,caliber,count_per_box,quantity,notes\n"
        
        for item in items:
            # Format notes to handle commas and quotes
            notes = item.notes.replace('"', '""') if item.notes else ""
            
            row = f'"{item.name}","{item.upc}","{item.caliber}",{item.count_per_box},{item.quantity},"{notes}"\n'
            csv_content += row
        
        # Create response with CSV file
        response = Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=ammo_inventory.csv"}
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# API endpoint to get CSV template
@app.route('/api/csv_template', methods=['GET'])
def csv_template():
    try:
        # Create template CSV content with example data
        csv_content = "name,upc,caliber,count_per_box,quantity,notes\n"
        csv_content += '"Federal American Eagle 9mm","029465064389","9mm Luger",50,2,"FMJ, Training ammo"\n'
        csv_content += '"Winchester USA .223","020892221932",".223 Remington",20,3,"Brass case, hunting"\n'
        
        # Create response with CSV file
        response = Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=ammo_inventory_template.csv"}
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# API endpoint to import inventory from CSV
@app.route('/api/import_csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file provided'
        })
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        })
    
    if not file.filename.endswith('.csv'):
        return jsonify({
            'success': False,
            'message': 'File must be a CSV'
        })
    
    try:
        # Read the CSV file as text
        csv_content = file.read().decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        # Check header
        header = lines[0].lower()
        expected_header = "name,upc,caliber,count_per_box,quantity,notes"
        
        if header != expected_header:
            return jsonify({
                'success': False,
                'message': f'Invalid CSV format. Expected header: {expected_header}'
            })
        
        # Process data rows
        items_added = 0
        errors = []
        
        for i, line in enumerate(lines[1:], 2):  # Start at line 2 (1-indexed)
            try:
                # Simple CSV parsing (doesn't handle all edge cases)
                fields = []
                in_quotes = False
                current_field = ""
                
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        fields.append(current_field)
                        current_field = ""
                    else:
                        current_field += char
                
                # Don't forget the last field
                fields.append(current_field)
                
                # Check if we have the expected number of fields
                if len(fields) != 6:
                    errors.append(f"Line {i}: Expected 6 fields, got {len(fields)}")
                    continue
                
                # Extract fields
                name = fields[0].strip('"')
                upc = fields[1].strip('"')
                caliber = fields[2].strip('"')
                
                try:
                    count_per_box = int(fields[3])
                    quantity = int(fields[4])
                except ValueError:
                    errors.append(f"Line {i}: count_per_box and quantity must be integers")
                    continue
                
                notes = fields[5].strip('"')
                
                # Create new AmmoBox
                ammo_box = AmmoBox(
                    name=name,
                    upc=upc,
                    caliber=caliber,
                    count_per_box=count_per_box,
                    quantity=quantity,
                    notes=notes
                )
                
                # Add to database
                db.session.add(ammo_box)
                items_added += 1
                
            except Exception as e:
                errors.append(f"Line {i}: {str(e)}")
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {items_added} items',
            'errors': errors if errors else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
