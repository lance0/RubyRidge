import requests
from bs4 import BeautifulSoup
import re
import logging
import json
import time
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PalmettoScraper:
    """A class to scrape ammunition data from Palmetto State Armory."""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://palmettostatearmory.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://palmettostatearmory.com/',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)
    
    def search_ammo(self, query, page=1):
        """
        Search for ammunition on Palmetto State Armory.
        
        Args:
            query: Search terms (e.g., "9mm ammo")
            page: Page number to fetch
            
        Returns:
            List of ammunition products with details
        """
        results = []
        
        try:
            # Add "ammo" to query if it doesn't already contain ammo-related keywords
            search_terms = query.lower()
            ammo_keywords = ['ammo', 'ammunition', 'round', 'rounds', 'cartridge', 'cartridges']
            if not any(keyword in search_terms for keyword in ammo_keywords):
                query = f"{query} ammo"
                logger.info(f"Modified search query to: {query}")
            
            # Construct the search URL
            search_url = f"{self.base_url}/search/?q={query}&page={page}"
            logger.info(f"Searching {search_url}")
            
            # Make the request with a timeout
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all product items
            product_items = soup.select('.product-item')
            logger.info(f"Found {len(product_items)} product items")
            
            # If no results with standard selectors, try alternative selectors
            if not product_items:
                logger.info("No products found with standard selectors, trying alternatives")
                product_items = soup.select('.product-grid-tile')
            
            if not product_items:
                logger.info("Still no products found, trying generic product containers")
                product_items = soup.select('.product')
            
            logger.info(f"After trying alternative selectors: {len(product_items)} products")
            
            # For debugging - log the first 200 chars of the HTML
            logger.info(f"HTML snippet: {response.text[:200]}...")
            
            for item in product_items:
                try:
                    # Try different selectors for product details based on site structure
                    title_elem = (item.select_one('.product-title') or 
                                 item.select_one('.product-name') or 
                                 item.select_one('h2.name') or
                                 item.select_one('.title'))
                    
                    price_elem = (item.select_one('.price .price-sales') or 
                                 item.select_one('.product-price') or
                                 item.select_one('.price'))
                    
                    link_elem = (item.select_one('a.name-link') or 
                                item.select_one('a.product-link') or
                                item.select_one('a'))
                    
                    if not title_elem or not link_elem:
                        logger.info("Skipping item: missing title or link element")
                        continue
                    
                    # Get text content
                    title = title_elem.text.strip() if hasattr(title_elem, 'text') else "Unknown Product"
                    logger.info(f"Found product: {title}")
                    
                    # Use query terms to determine if this is ammo
                    search_calibers = ['9mm', '5.56', '223', '.223', '22lr', '.22', '308', '.308', '45acp', '.45']
                    is_relevant = False
                    
                    # Check if any of our search calibers is in the title
                    for caliber in search_calibers:
                        if caliber in title.lower().replace(' ', ''):
                            is_relevant = True
                            break
                    
                    # Also check for ammunition keywords
                    ammo_keywords = ['ammo', 'ammunition', 'round', 'rounds', 'cartridge', 'cartridges', 'bullet', 'bullets']
                    if any(keyword in title.lower() for keyword in ammo_keywords):
                        is_relevant = True
                    
                    if not is_relevant:
                        logger.info(f"Skipping - not ammunition: {title}")
                        continue
                    
                    # Extract price if available
                    price = price_elem.text.strip() if (price_elem and hasattr(price_elem, 'text')) else "Price not available"
                    
                    # Extract product link
                    if hasattr(link_elem, 'get') and link_elem.get('href'):
                        product_link = link_elem['href']
                        if product_link.startswith('http'):
                            full_url = product_link
                        else:
                            full_url = urljoin(self.base_url, product_link)
                    else:
                        logger.info(f"Skipping - no valid link for: {title}")
                        continue
                    
                    # Add to results
                    results.append({
                        'title': title,
                        'price': price,
                        'url': full_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting product details: {e}")
                    continue
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def extract_product_details(self, product_url):
        """
        Extract detailed information from a product page.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with product details including UPC if available
        """
        try:
            # Add a small delay to avoid being rate-limited
            time.sleep(1)
            
            # Make the request
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract product name
            product_name = soup.select_one('h1.product-name')
            name = product_name.text.strip() if product_name else "Name not found"
            
            # Extract UPC from product details
            upc = None
            product_info = soup.select('.product-info-container .attribute-group')
            for info in product_info:
                # Look for UPC in product attributes
                upc_label = info.find(string=re.compile(r'UPC', re.IGNORECASE))
                if upc_label:
                    # Get the next sibling which should contain the UPC value
                    upc_value = upc_label.find_next(string=True)
                    if upc_value:
                        upc = upc_value.strip()
                        # Clean up UPC to get only numbers
                        upc = re.sub(r'[^0-9]', '', upc)
                        break
            
            # Extract description which may contain caliber info
            description_elem = soup.select_one('.product-description')
            description = description_elem.text.strip() if description_elem else ""
            
            # Try to extract caliber from name or description
            caliber_patterns = [
                r'(\d+\s*mm)',                     # matches like "9mm"
                r'(\.\d+\s*[A-Za-z]+)',            # matches like ".223 Remington"
                r'(5\.56)',                        # matches "5.56"
                r'(7\.62)',                        # matches "7.62"
                r'(\d+\s*[Gg]auge)',               # matches like "12 gauge"
                r'(\d+\s*[Aa][Cc][Pp])',           # matches like "45 ACP"
                r'(10mm)',                          # specific case for 10mm
                r'(38 Special)',                    # specific case
                r'(357 Magnum)',                    # specific case
                r'(44 Magnum)',                     # specific case
                r'(300 Blackout)',                  # specific case
                r'(6\.5 Creedmoor)',                # specific case
                r'(7mm-\d+)',                       # matches like "7mm-08"
                r'(30-\d+)',                        # matches like "30-06"
                r'(6\.5x\d+)',                      # matches like "6.5x55"
            ]
            
            caliber = None
            text_to_search = f"{name} {description}"
            
            for pattern in caliber_patterns:
                match = re.search(pattern, text_to_search, re.IGNORECASE)
                if match:
                    caliber = match.group(1).strip()
                    break
            
            # Try to extract rounds per box from description
            count_per_box = None
            count_patterns = [
                r'(\d+)\s*(?:rd|round|count|ct)\b',  # matches like "20 rd" or "50 round" or "100 count"
                r'(?:box\s*of\s*)(\d+)',             # matches like "box of 50"
                r'(\d+)(?:\s*-\s*|\s+)(?:round|rd|count|ct)\b'  # matches like "20-round" or "50 rd"
            ]
            
            for pattern in count_patterns:
                match = re.search(pattern, text_to_search, re.IGNORECASE)
                if match:
                    count_per_box = int(match.group(1).strip())
                    break
            
            # Extract image URL if available
            image_elem = soup.select_one('.product-image-container img')
            image_url = image_elem.get('src') if image_elem else None
            
            # Extract price
            price_elem = soup.select_one('.prices .price-sales')
            price = price_elem.text.strip() if price_elem else "Price not available"
            
            # Return the extracted details
            details = {
                'name': name,
                'url': product_url,
                'price': price,
                'description': description[:200] + '...' if len(description) > 200 else description,
                'image_url': image_url
            }
            
            if upc:
                details['upc'] = upc
            
            if caliber:
                details['caliber'] = caliber
            
            if count_per_box:
                details['count_per_box'] = count_per_box
            
            return details
            
        except requests.RequestException as e:
            logger.error(f"Request failed for product page: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting product details: {e}")
            return None
    
    def search_and_get_details(self, query, max_products=5):
        """
        Search for products and get detailed information for each.
        
        Args:
            query: Search terms
            max_products: Maximum number of products to fetch details for
            
        Returns:
            List of products with detailed information
        """
        # Search for products
        search_results = self.search_ammo(query)
        
        # Get details for each product, limited by max_products
        detailed_results = []
        for product in search_results[:max_products]:
            logger.info(f"Getting details for: {product['title']}")
            details = self.extract_product_details(product['url'])
            if details:
                detailed_results.append(details)
        
        return detailed_results

# Example usage
if __name__ == "__main__":
    scraper = PalmettoScraper()
    results = scraper.search_and_get_details("9mm ammo", max_products=3)
    print(json.dumps(results, indent=2))