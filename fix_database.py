import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash

# Create a minimal Flask app for migration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

def fix_database():
    """
    Fix the database issues by recreating tables with proper structures and relationships.
    This is a more aggressive approach that should fix relationship and constraint issues.
    """
    with app.app_context():
        conn = db.engine.connect()
        
        # First check if we have the default user
        try:
            result = conn.execute(text("""
                SELECT id FROM users WHERE username = 'budd'
            """))
            has_default_user = result.rowcount > 0
        except Exception:
            has_default_user = False
        
        # Drop the OAuth table if it exists to avoid constraint issues
        conn.execute(text("""
            DROP TABLE IF EXISTS oauth CASCADE
        """))
        
        # Recreate the OAuth table with proper constraints
        print("Updating oauth table for authentication...")
        # First remove constraint if it exists
        try:
            conn.execute(text("""
                ALTER TABLE oauth DROP CONSTRAINT IF EXISTS uq_user_browser_session_key_provider
            """))
        except Exception as e:
            print(f"Note: Could not drop constraint: {e}")
            
        # Then ensure table exists
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS oauth (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    provider VARCHAR(50) NOT NULL,
                    browser_session_key VARCHAR NOT NULL,
                    token JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        except Exception as e:
            print(f"Note: Could not create table: {e}")
            
        # Add constraint if needed
        try:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_browser_session_key_provider'
                    ) THEN
                        ALTER TABLE oauth ADD CONSTRAINT uq_user_browser_session_key_provider 
                        UNIQUE (user_id, browser_session_key, provider);
                    END IF;
                END
                $$;
            """))
        except Exception as e:
            print(f"Note: Could not add constraint: {e}")
        
        # Ensure the firearms table exists with proper structure
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS firearms (
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
        
        # Create default user if needed
        if not has_default_user:
            print("Creating default user 'budd'...")
            password_hash = generate_password_hash('dwyer')
            conn.execute(text(f"""
                INSERT INTO users (username, email, password_hash, first_name, last_name)
                VALUES ('budd', 'budd@example.com', '{password_hash}', 'Budd', 'Dwyer')
            """))
            
        # Commit changes
        db.session.commit()
        print("Database fix completed successfully!")

if __name__ == "__main__":
    fix_database()