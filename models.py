from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import UniqueConstraint

# Initialize SQLAlchemy with no app yet
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User account model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    profile_image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    ammo_boxes = db.relationship('AmmoBox', backref='user', lazy=True)
    range_trips = db.relationship('RangeTrip', backref='user', lazy=True)
    firearms = db.relationship('Firearm', backref='owner', lazy=True)
    
    def __init__(self, username=None, email=None, password=None, first_name=None, last_name=None):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class AmmoBox(db.Model):
    """Represents an ammunition box in inventory."""
    __tablename__ = 'ammo_boxes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Allow null for existing data
    name = db.Column(db.String(255), nullable=False)
    upc = db.Column(db.String(20), nullable=False)
    caliber = db.Column(db.String(50), nullable=False)
    count_per_box = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_rounds = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=True)  # Price per box
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name, upc, caliber, count_per_box, quantity, notes="", user_id=None, purchase_price=None):
        self.name = name
        self.upc = upc
        self.caliber = caliber
        self.count_per_box = count_per_box
        self.quantity = quantity
        self.total_rounds = count_per_box * quantity
        self.notes = notes
        self.user_id = user_id
        self.purchase_price = purchase_price

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "upc": self.upc,
            "caliber": self.caliber,
            "count_per_box": self.count_per_box,
            "quantity": self.quantity,
            "total_rounds": self.total_rounds,
            "notes": self.notes
        }

    def update_total_rounds(self):
        """Recalculates the total rounds based on count_per_box and quantity"""
        self.total_rounds = self.count_per_box * self.quantity

class Firearm(db.Model):
    """Represents a firearm in the gun safe"""
    __tablename__ = 'firearms'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), nullable=True)
    caliber = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # pistol, rifle, shotgun, etc.
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, sold, etc.
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id, name, make, model, caliber, type, 
                serial_number=None, purchase_date=None, purchase_price=None, 
                notes=None, image_url=None):
        self.user_id = user_id
        self.name = name
        self.make = make
        self.model = model
        self.serial_number = serial_number
        self.caliber = caliber
        self.type = type
        self.purchase_date = purchase_date
        self.purchase_price = purchase_price
        self.notes = notes
        self.image_url = image_url
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'make': self.make,
            'model': self.model,
            'serial_number': self.serial_number,
            'caliber': self.caliber,
            'type': self.type,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_price': self.purchase_price,
            'notes': self.notes,
            'status': self.status,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UpcData(db.Model):
    """Stores UPC lookup data for ammunition"""
    __tablename__ = 'upc_data'

    id = db.Column(db.Integer, primary_key=True)
    upc = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    caliber = db.Column(db.String(50), nullable=False)
    count_per_box = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, upc, name, caliber, count_per_box):
        self.upc = upc
        self.name = name
        self.caliber = caliber
        self.count_per_box = count_per_box
    
    def to_dict(self):
        return {
            "upc": self.upc,
            "name": self.name,
            "caliber": self.caliber,
            "count_per_box": self.count_per_box
        }

class CaliberThreshold(db.Model):
    """Stores threshold values for ammunition calibers"""
    __tablename__ = 'caliber_thresholds'
    
    id = db.Column(db.Integer, primary_key=True)
    caliber = db.Column(db.String(50), nullable=False, unique=True)
    low_threshold = db.Column(db.Integer, nullable=False, default=100)
    critical_threshold = db.Column(db.Integer, nullable=False, default=50)
    target_stock = db.Column(db.Integer, nullable=False, default=500)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, caliber, low_threshold=100, critical_threshold=50, target_stock=500):
        self.caliber = caliber
        self.low_threshold = low_threshold
        self.critical_threshold = critical_threshold
        self.target_stock = target_stock
    
    def to_dict(self):
        return {
            "id": self.id,
            "caliber": self.caliber,
            "low_threshold": self.low_threshold,
            "critical_threshold": self.critical_threshold,
            "target_stock": self.target_stock
        }

class RangeTrip(db.Model):
    """Represents a range trip where ammunition was used"""
    __tablename__ = 'range_trips'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Allow null for existing data
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    location = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, completed
    
    # Weather data
    temperature = db.Column(db.Float, nullable=True)  # Temperature in °F
    weather_condition = db.Column(db.String(50), nullable=True)  # Clear, Cloudy, Rain, etc.
    wind_speed = db.Column(db.Float, nullable=True)  # Wind speed in mph
    humidity = db.Column(db.Float, nullable=True)  # Humidity percentage
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('RangeTripItem', backref='range_trip', lazy=True, cascade='all, delete-orphan')
    firearms = db.relationship('RangeTripFirearm', backref='range_trip', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, date=None, location=None, notes=None, user_id=None,
                 temperature=None, weather_condition=None, wind_speed=None, humidity=None):
        self.name = name
        self.date = date if date else datetime.utcnow().date()
        self.location = location
        self.notes = notes
        self.status = 'active'
        self.user_id = user_id
        self.temperature = temperature
        self.weather_condition = weather_condition
        self.wind_speed = wind_speed
        self.humidity = humidity

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'date': self.date.isoformat() if self.date else None,
            'location': self.location,
            'notes': self.notes,
            'status': self.status,
            'temperature': self.temperature,
            'weather_condition': self.weather_condition,
            'wind_speed': self.wind_speed,
            'humidity': self.humidity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items],
            'firearms': [firearm.to_dict() for firearm in self.firearms]
        }

class RangeTripFirearm(db.Model):
    """Represents firearms used during a range trip"""
    __tablename__ = 'range_trip_firearms'
    
    id = db.Column(db.Integer, primary_key=True)
    range_trip_id = db.Column(db.Integer, db.ForeignKey('range_trips.id'), nullable=False)
    firearm_id = db.Column(db.Integer, db.ForeignKey('firearms.id'), nullable=False)
    rounds_fired = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to access firearm details
    firearm = db.relationship('Firearm', backref='range_trips_used', lazy=True)
    
    def __init__(self, range_trip_id, firearm_id, rounds_fired=0, notes=None):
        self.range_trip_id = range_trip_id
        self.firearm_id = firearm_id
        self.rounds_fired = rounds_fired
        self.notes = notes
    
    def to_dict(self):
        return {
            'id': self.id,
            'range_trip_id': self.range_trip_id,
            'firearm_id': self.firearm_id,
            'firearm': self.firearm.to_dict() if self.firearm else None,
            'rounds_fired': self.rounds_fired,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RangeTripItem(db.Model):
    """Represents ammo items checked out for a range trip"""
    __tablename__ = 'range_trip_items'

    id = db.Column(db.Integer, primary_key=True)
    range_trip_id = db.Column(db.Integer, db.ForeignKey('range_trips.id'), nullable=False)
    ammo_box_id = db.Column(db.Integer, db.ForeignKey('ammo_boxes.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    caliber = db.Column(db.String(50), nullable=False)
    count_per_box = db.Column(db.Integer, nullable=False)
    quantity_out = db.Column(db.Integer, nullable=False)  # Quantity checked out
    quantity_in = db.Column(db.Integer, nullable=False, default=0)  # Quantity checked back in
    rounds_used = db.Column(db.Integer, nullable=False, default=0)  # Rounds used during trip
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, range_trip_id, name, caliber, count_per_box, quantity_out, ammo_box_id=None):
        self.range_trip_id = range_trip_id
        self.ammo_box_id = ammo_box_id
        self.name = name
        self.caliber = caliber
        self.count_per_box = count_per_box
        self.quantity_out = quantity_out
        self.quantity_in = 0
        self.rounds_used = 0

    def to_dict(self):
        return {
            'id': self.id,
            'range_trip_id': self.range_trip_id,
            'ammo_box_id': self.ammo_box_id,
            'name': self.name,
            'caliber': self.caliber,
            'count_per_box': self.count_per_box,
            'quantity_out': self.quantity_out,
            'quantity_in': self.quantity_in,
            'rounds_used': self.rounds_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
