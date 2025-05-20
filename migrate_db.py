import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

# Create a minimal Flask app for migration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

def migrate_database():
    """
    Execute database migrations to add new columns and update table structures
    """
    with app.app_context():
        conn = db.engine.connect()
        
        # Check if ammo_boxes.user_id exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='ammo_boxes' AND column_name='user_id'
        """))
        if result.rowcount == 0:
            print("Adding user_id column to ammo_boxes table...")
            conn.execute(text("""
                ALTER TABLE ammo_boxes 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """))
            
        # Check if ammo_boxes.purchase_price exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='ammo_boxes' AND column_name='purchase_price'
        """))
        if result.rowcount == 0:
            print("Adding purchase_price column to ammo_boxes table...")
            conn.execute(text("""
                ALTER TABLE ammo_boxes 
                ADD COLUMN purchase_price FLOAT
            """))
            
        # Check if users table exists
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name='users'
        """))
        if result.rowcount == 0:
            print("Creating users table...")
            conn.execute(text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(64),
                    last_name VARCHAR(64),
                    profile_image_url VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """))
        else:
            # Check if profile_image_url column exists in users table
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='users' AND column_name='profile_image_url'
            """))
            if result.rowcount == 0:
                print("Adding profile_image_url column to users table...")
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN profile_image_url VARCHAR(255)
                """))
                
            # Update users.id to VARCHAR if it's INTEGER
            result = conn.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name='users' AND column_name='id'
            """))
            data_type = result.scalar()
            if data_type and data_type.upper() == 'INTEGER':
                print("Changing users.id column type from INTEGER to VARCHAR...")
                # This is complex and might require a table rebuild
                print("NOTE: You may need to recreate the users table manually.")
            
        # Check if oauth table exists
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name='oauth'
        """))
        if result.rowcount == 0:
            print("Creating oauth table for authentication...")
            conn.execute(text("""
                CREATE TABLE oauth (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    provider VARCHAR(50) NOT NULL,
                    browser_session_key VARCHAR NOT NULL,
                    token JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_user_browser_session_key_provider UNIQUE (user_id, browser_session_key, provider)
                )
            """))
        
        # Create the firearms table if it doesn't exist
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name='firearms'
        """))
        if result.rowcount == 0:
            print("Creating firearms table for GunSafe feature...")
            conn.execute(text("""
                CREATE TABLE firearms (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    make VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    serial_number VARCHAR(100),
                    caliber VARCHAR(50) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    purchase_date DATE,
                    purchase_price FLOAT,
                    notes TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    image_url VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        # Create range_trip_firearms table if it doesn't exist
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name='range_trip_firearms'
        """))
        if result.rowcount == 0:
            print("Creating range_trip_firearms table for tracking firearms used in range trips...")
            conn.execute(text("""
                CREATE TABLE range_trip_firearms (
                    id SERIAL PRIMARY KEY,
                    range_trip_id INTEGER REFERENCES range_trips(id) NOT NULL,
                    firearm_id INTEGER REFERENCES firearms(id) NOT NULL,
                    rounds_fired INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        # Check and add weather-related columns to range_trips
        weather_columns = [
            ('temperature', 'FLOAT'),
            ('weather_condition', 'VARCHAR(50)'),
            ('wind_speed', 'FLOAT'),
            ('humidity', 'FLOAT')
        ]
        
        for col_name, col_type in weather_columns:
            result = conn.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='range_trips' AND column_name='{col_name}'
            """))
            if result.rowcount == 0:
                print(f"Adding {col_name} column to range_trips table...")
                conn.execute(text(f"""
                    ALTER TABLE range_trips 
                    ADD COLUMN {col_name} {col_type}
                """))
                
        # Check if user_id exists in range_trips
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='range_trips' AND column_name='user_id'
        """))
        if result.rowcount == 0:
            print("Adding user_id column to range_trips table...")
            conn.execute(text("""
                ALTER TABLE range_trips 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """))
            
        # Commit all changes
        db.session.commit()
        print("Database migration completed successfully!")
        
if __name__ == "__main__":
    migrate_database()