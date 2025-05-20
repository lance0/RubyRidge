from flask import jsonify, request, session, Response
from models import db, AmmoBox, UpcData

# API endpoint to save threshold settings
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