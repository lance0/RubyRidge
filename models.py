from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy with no app yet
db = SQLAlchemy()

class AmmoBox(db.Model):
    """Represents an ammunition box in inventory."""
    __tablename__ = 'ammo_boxes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    upc = db.Column(db.String(20), nullable=False)
    caliber = db.Column(db.String(50), nullable=False)
    count_per_box = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_rounds = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name, upc, caliber, count_per_box, quantity, notes=""):
        self.name = name
        self.upc = upc
        self.caliber = caliber
        self.count_per_box = count_per_box
        self.quantity = quantity
        self.total_rounds = count_per_box * quantity
        self.notes = notes

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
