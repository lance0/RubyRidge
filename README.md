# RubyRidge Ammo Inventory

A mobile-responsive ammunition inventory web application with barcode scanning capabilities. RubyRidge offers advanced inventory tracking for ammunition with a tactical aesthetic and modern, responsive design.

![RubyRidge Ammo Inventory](https://github.com/yourname/rubyridge-ammo-inventory/raw/main/static/img/screenshot.png)

## Features

- **Barcode Scanning**: Scan ammunition UPCs directly with your mobile device's camera
- **Inventory Management**: Track ammunition by caliber, count, and quantity
- **UPC Database**: Maintain a database of ammunition UPC codes
- **Product Search**: Find ammunition by caliber and import details to your database
- **Mobile-Responsive**: Works on all devices from desktop to smartphones
- **Tactical Design**: Modern UI with a tactical aesthetic

## Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Barcode Scanning**: QuaggaJS library for in-browser scanning
- **Web Scraping**: Product lookup capabilities for ammunition data

## Installation

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
   pip install -r requirements.txt
   ```

4. Set up the environment variables
   ```
   export DATABASE_URL=postgresql://user:password@localhost/ammo_inventory
   export FLASK_SECRET_KEY=your_secret_key
   ```

5. Initialize the database
   ```
   flask db upgrade
   ```

6. Run the application
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## Usage

1. **Access the application** at http://localhost:5000
2. **Add UPC data** by navigating to the UPC Database page
3. **Scan barcodes** using the Scan Barcode page (works best on mobile devices)
4. **Manage inventory** on the Inventory page

## Data Structure

The application uses two primary database models:

- **AmmoBox**: Represents an ammunition box in inventory with quantity information
- **UpcData**: Stores UPC lookup data for ammunition products

## Mobile Usage

For the best barcode scanning experience:

1. Access the application on your mobile device
2. Navigate to the Scan Barcode page
3. Allow camera access when prompted
4. Position the barcode within the scanning area
5. The application will automatically detect and process valid UPC codes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- QuaggaJS for the barcode scanning capabilities
- Bootstrap for the responsive design framework
- Font Awesome for the icon set