# This file would contain SQLAlchemy models if we were using a database.
# For this application, we're using in-memory storage (session-based) for simplicity.
# In a production app, you would define models for Ammunition, Calibers, etc.

class AmmoBox:
    """Represents an ammunition box in inventory."""
    def __init__(self, id, name, upc, caliber, count_per_box, quantity, notes=""):
        self.id = id
        self.name = name
        self.upc = upc
        self.caliber = caliber
        self.count_per_box = count_per_box
        self.quantity = quantity
        self.notes = notes
        self.total_rounds = count_per_box * quantity
    
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

# Note: We're not actually using these models in the current implementation,
# but they're provided for reference on how the data is structured.
