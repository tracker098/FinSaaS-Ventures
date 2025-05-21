from flask import Flask, request, jsonify
from profilescraper import LinkedInScraper
import os
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv()

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
                }
            }
        }
    })

@app.route("/search-employees", methods=["POST"])
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

        scraper = LinkedInScraper(email, password)
        if not scraper.login():
            return jsonify({"error": "Login failed. Check credentials or verification challenge."}), 401

        result = scraper.search_company_employees(company_name, max_profiles=result_count)
        scraper.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port) 