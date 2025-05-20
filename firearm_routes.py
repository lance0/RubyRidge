from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Firearm
from datetime import datetime
from sqlalchemy import func

firearms = Blueprint('firearms', __name__)

@firearms.route('/gunsafe')
@login_required
def gunsafe():
    """Display the user's firearms collection (GunSafe)"""
    user_firearms = Firearm.query.filter_by(user_id=current_user.id).all()
    
    # Get unique calibers and manufacturers for filtering
    calibers = db.session.query(Firearm.caliber).filter_by(user_id=current_user.id).distinct().all()
    calibers = [c[0] for c in calibers]
    
    makes = db.session.query(Firearm.make).filter_by(user_id=current_user.id).distinct().all()
    makes = [m[0] for m in makes]
    
    return render_template('gunsafe_simple.html', 
                          firearms=user_firearms, 
                          calibers=calibers, 
                          makes=makes)

@firearms.route('/add_firearm', methods=['POST'])
@login_required
def add_firearm():
    """Add a new firearm to the user's collection"""
    try:
        # Get form data
        name = request.form.get('name')
        make = request.form.get('make')
        model = request.form.get('model')
        caliber = request.form.get('caliber')
        firearm_type = request.form.get('type')
        serial_number = request.form.get('serial_number')
        notes = request.form.get('notes')
        image_url = request.form.get('image_url')
        
        # Handle optional numeric fields
        purchase_price = request.form.get('purchase_price')
        if purchase_price:
            purchase_price = float(purchase_price)
        
        # Handle optional date fields
        purchase_date = request.form.get('purchase_date')
        if purchase_date:
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        
        # Create new firearm
        new_firearm = Firearm(
            user_id=current_user.id,
            name=name,
            make=make,
            model=model,
            caliber=caliber,
            type=firearm_type,
            serial_number=serial_number,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            notes=notes,
            image_url=image_url
        )
        
        db.session.add(new_firearm)
        db.session.commit()
        
        flash(f'"{name}" has been added to your GunSafe!', 'success')
        return redirect(url_for('firearms.gunsafe'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding firearm: {str(e)}', 'danger')
        return redirect(url_for('firearms.gunsafe'))

@firearms.route('/firearm/<int:firearm_id>')
@login_required
def get_firearm(firearm_id):
    """Get a single firearm's details for editing"""
    firearm = Firearm.query.filter_by(id=firearm_id, user_id=current_user.id).first()
    
    if not firearm:
        return jsonify({'success': False, 'message': 'Firearm not found'})
    
    # Convert to dict for JSON response
    firearm_data = firearm.to_dict()
    
    return jsonify({'success': True, 'firearm': firearm_data})

@firearms.route('/edit_firearm', methods=['POST'])
@login_required
def edit_firearm():
    """Update an existing firearm"""
    try:
        firearm_id = request.form.get('firearm_id')
        firearm = Firearm.query.filter_by(id=firearm_id, user_id=current_user.id).first()
        
        if not firearm:
            flash('Firearm not found', 'danger')
            return redirect(url_for('firearms.gunsafe'))
        
        # Update fields
        firearm.name = request.form.get('name')
        firearm.make = request.form.get('make')
        firearm.model = request.form.get('model')
        firearm.caliber = request.form.get('caliber')
        firearm.type = request.form.get('type')
        firearm.serial_number = request.form.get('serial_number')
        firearm.notes = request.form.get('notes')
        firearm.image_url = request.form.get('image_url')
        
        # Handle optional numeric fields
        purchase_price = request.form.get('purchase_price')
        if purchase_price:
            firearm.purchase_price = float(purchase_price)
        else:
            firearm.purchase_price = None
            
        # Handle optional date fields
        purchase_date = request.form.get('purchase_date')
        if purchase_date:
            firearm.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        else:
            firearm.purchase_date = None
        
        # Update timestamp
        firearm.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'"{firearm.name}" has been updated!', 'success')
        return redirect(url_for('firearms.gunsafe'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating firearm: {str(e)}', 'danger')
        return redirect(url_for('firearms.gunsafe'))
        
@firearms.route('/delete_firearm', methods=['POST'])
@login_required
def delete_firearm():
    """Delete a firearm from the collection"""
    try:
        firearm_id = request.form.get('firearm_id')
        firearm = Firearm.query.filter_by(id=firearm_id, user_id=current_user.id).first()
        
        if not firearm:
            flash('Firearm not found', 'danger')
            return redirect(url_for('firearms.gunsafe'))
        
        firearm_name = firearm.name
        
        db.session.delete(firearm)
        db.session.commit()
        
        flash(f'"{firearm_name}" has been removed from your GunSafe.', 'success')
        return redirect(url_for('firearms.gunsafe'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting firearm: {str(e)}', 'danger')
        return redirect(url_for('firearms.gunsafe'))