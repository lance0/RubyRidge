# RubyRidge Ammo Inventory

A mobile-responsive ammunition inventory web application with barcode scanning capabilities. RubyRidge offers advanced inventory tracking for ammunition with a tactical aesthetic and modern, responsive design.

![RubyRidge Ammo Inventory](https://github.com/yourname/rubyridge-ammo-inventory/raw/main/static/img/screenshot.png)

## Features

- **Barcode Scanning**: Scan ammunition UPCs directly with your mobile device's camera
- **Inventory Management**: Track ammunition by caliber, count, and quantity
- **UPC Database**: Maintain a database of ammunition UPC codes
- **Product Search**: Find ammunition by caliber and import details to your database
- **UPC Item DB API Integration**: Automatic lookup of UPCs in external database
- **Range Trip Tracking**: Plan range trips, check out ammo, and track usage with weather data
- **Inventory Visualization**: Charts with threshold settings for low inventory warnings
- **CSV Import/Export**: Easily transfer inventory data with standardized templates
- **GunSafe**: Manage your firearms collection with detailed tracking
- **Account Management**: Secure user authentication with account settings
- **Toast Notifications**: User-friendly feedback for all operations
- **Mobile-Responsive**: Works on all devices from desktop to smartphones
- **Tactical Design**: Modern UI with a tactical aesthetic

## Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Barcode Scanning**: QuaggaJS library for in-browser scanning
- **Web Scraping**: Product lookup capabilities for ammunition data
- **External APIs**: UPC Item DB API integration
- **Containerization**: Docker and Docker Compose support

## Installation

### Standard Installation

1. Clone this repository
   ```
   git clone https://github.com/yourname/rubyridge-ammo-inventory.git
   cd rubyridge-ammo-inventory
   ```

2. Set up a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -e .
   ```
   
   Alternatively, if you have `uv` installed:
   ```
   uv pip install -e .
   ```

4. Set up PostgreSQL database
   - Install PostgreSQL if not already installed
   - Create a database: `createdb ammo_inventory`

5. Set up the environment variables
   ```
   export DATABASE_URL=postgresql://user:password@localhost/ammo_inventory
   export SESSION_SECRET=your_secret_key
   ```

6. Initialize the database
   ```
   python main.py
   ```
   
   This will create the necessary tables and initialize default data.

7. Run the application
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

8. Access the application at http://localhost:5000 and log in with the default credentials (see Authentication & Security section below).

### Docker Installation (Recommended for Production)

1. Clone this repository
   ```
   git clone https://github.com/yourname/rubyridge-ammo-inventory.git
   cd rubyridge-ammo-inventory
   ```

2. Edit the `docker-compose.yml` file and update the following environment variables:
   ```yaml
   environment:
     - SESSION_SECRET=your_strong_random_key_here
     - POSTGRES_PASSWORD=your_secure_database_password
   ```

3. Build and start the containers
   ```
   docker-compose up -d
   ```

4. The application will be available at http://localhost:5000

5. Log in with the default credentials (see Authentication & Security section below)

6. To stop the application
   ```
   docker-compose down
   ```

7. To view logs
   ```
   docker-compose logs -f web
   ```

### Production Deployment Considerations

1. **Security**: Immediately after deployment:
   - Change the default credentials through the Account Settings page
   - Set strong, unique passwords for all services

2. **Environment Variables**: Update environment variables in docker-compose.yml with secure values:
   - SESSION_SECRET: Use a strong, randomly generated key (at least 32 characters)
   - PostgreSQL credentials: Change from default values

3. **HTTPS Setup**: In production, configure a reverse proxy (Nginx, Traefik) to handle HTTPS
   ```yaml
   # Example Nginx configuration
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/fullchain.pem;
       ssl_certificate_key /path/to/privkey.pem;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Database Backups**: Configure regular PostgreSQL backups
   ```
   # Add to crontab
   0 2 * * * docker exec rubyridge-ammo-inventory_db_1 pg_dump -U postgres ammo_inventory > /backup/ammo_inventory_$(date +\%Y\%m\%d).sql
   ```

5. **Logging**: Set up external logging service or volume mount for log persistence
   ```yaml
   # Update in docker-compose.yml
   services:
     web:
       volumes:
         - ./logs:/app/logs
   ```

6. **Resource Limits**: Set resource limits in the docker-compose.yml
   ```yaml
   services:
     web:
       deploy:
         resources:
           limits:
             cpus: '1'
             memory: 512M
   ```

## Authentication & Security

### Default Credentials

For testing and initial setup, the application comes with a default user account:
- **Username**: budd
- **Password**: dwyer

⚠️ **IMPORTANT SECURITY NOTICE**: These default credentials are provided for initial setup only. 
You should change both the username and password immediately after your first login by following these steps:

1. Log in with the default credentials
2. Click on your username in the top right corner of the navigation bar
3. Select "Account Settings" from the dropdown menu
4. Update your username, email, and password
5. Click "Save Changes" to apply the new credentials

Continuing to use the default credentials poses a significant security risk. The application will display warnings until you change these default values.

## Usage

1. **Access the application** at http://localhost:5000
2. **Log in** with the default credentials (or your custom credentials if already changed)
3. **Add UPC data** by navigating to the UPC Database page
4. **Scan barcodes** using the Scan Barcode page (works best on mobile devices)
5. **Manage inventory** on the Inventory page
6. **Set thresholds** for low ammunition warnings by caliber
7. **Create range trips** to track ammunition usage
8. **Check out ammunition** for a range trip
9. **Check in unused ammunition** when you return from the range
10. **Import/Export inventory** using the CSV functionality
11. **Manage firearms** in the GunSafe feature

## Data Structure

The application uses several database models:

- **AmmoBox**: Represents an ammunition box in inventory with quantity information
- **UpcData**: Stores UPC lookup data for ammunition products
- **CaliberThreshold**: Stores threshold settings for ammunition calibers (low, critical, target)
- **RangeTrip**: Represents a range trip with date, location, and status information
- **RangeTripItem**: Tracks ammunition checked out, used, and returned for a range trip

## Mobile Usage

For the best barcode scanning experience:

1. Access the application on your mobile device
2. Navigate to the Scan Barcode page
3. Allow camera access when prompted
4. Position the barcode within the scanning area
5. The application will automatically detect and process valid UPC codes

## API Integrations

### UPC Item DB API

The application integrates with the UPC Item DB API to look up UPC codes that aren't found in the local database. This provides a fallback for identifying ammunition products. The free tier allows 100 lookups per day.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- QuaggaJS for the barcode scanning capabilities
- Bootstrap for the responsive design framework
- Font Awesome for the icon set
- UPC Item DB for the UPC lookup API