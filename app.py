from flask import Flask, request, jsonify
from profilescraper import LinkedInScraper
import os
from dotenv import load_dotenv
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets
import logging
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# API key validation
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('API_KEY', 'your-secret-api-key'):
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "LinkedIn Employee Scraper API",
        "endpoints": {
            "/search-employees": {
                "method": "POST",
                "description": "Search for employees at a company",
                "required_fields": ["linkedin_email", "linkedin_password", "company_name"],
                "optional_fields": ["search_result_count"],
                "example_request": {
                    "linkedin_email": "your_email@example.com",
                    "linkedin_password": "your_password",
                    "company_name": "Google",
                    "search_result_count": 10
                },
                "headers": {
                    "X-API-Key": "your-api-key",
                    "Content-Type": "application/json"
                }
            }
        }
    })

@app.route("/search-employees", methods=["POST"])
@require_api_key
@limiter.limit("10 per minute")
def search_employees():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Input validation
        required_fields = ["linkedin_email", "linkedin_password", "company_name"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        email = data["linkedin_email"]
        password = data["linkedin_password"]
        company_name = data["company_name"]
        result_count = int(data.get("search_result_count", 10))

        # Validate result_count
        if result_count < 1 or result_count > 100:
            return jsonify({"error": "search_result_count must be between 1 and 100"}), 400

        logger.info(f"Starting search for company: {company_name}")
        scraper = LinkedInScraper(email, password)
        
        if not scraper.login():
            logger.error(f"Login failed for email: {email}")
            return jsonify({"error": "Login failed. Check credentials or verification challenge."}), 401

        result = scraper.search_company_employees(company_name, max_profiles=result_count)
        scraper.close()
        
        logger.info(f"Successfully scraped {len(result)} profiles for {company_name}")
        return jsonify(result)

    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    # Generate a random API key if not set
    if not os.getenv('API_KEY'):
        api_key = secrets.token_hex(16)
        logger.info(f"Generated API key: {api_key}")
        with open('.env', 'a') as f:
            f.write(f'\nAPI_KEY={api_key}')
    
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port) 