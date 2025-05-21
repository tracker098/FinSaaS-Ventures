from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time
import json
from datetime import datetime
import requests
import zipfile
import io
import platform

# --- CONFIGURATION ---
LINKEDIN_EMAIL = "your_email@example.com"  # <-- Replace with your email
LINKEDIN_PASSWORD = "your_password"        # <-- Replace with your password

class LinkedInScraper:
    def __init__(self, email=None, password=None):
        load_dotenv()
        self.email = email or os.getenv('LINKEDIN_EMAIL', 'techtush2023@gmail.com')
        self.password = password or os.getenv('LINKEDIN_PASSWORD', 'Growth@2025')
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # Uncomment to run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--remote-debugging-port=9222')
            
            # Add user agent to appear more like a regular browser
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            
            # Try to use system ChromeDriver first
            try:
                print("Attempting to use system ChromeDriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                print(f"System ChromeDriver failed: {str(e)}")
                print("Trying ChromeDriverManager with specific version...")
                
                try:
                    # Try using ChromeDriverManager with specific version
                    service = Service(ChromeDriverManager(version="114.0.5735.90").install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    print(f"ChromeDriverManager failed: {str(e)}")
                    print("Trying direct download method...")
                    
                    try:
                        # Determine system architecture
                        system = platform.system().lower()
                        machine = platform.machine().lower()
                        
                        if system == "darwin":  # macOS
                            if "arm" in machine:  # Apple Silicon
                                driver_url = "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/mac-arm64/chromedriver-mac-arm64.zip"
                                driver_path = "./chromedriver-mac-arm64/chromedriver"
                            else:  # Intel
                                driver_url = "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/mac-x64/chromedriver-mac-x64.zip"
                                driver_path = "./chromedriver-mac-x64/chromedriver"
                        else:
                            raise Exception("Unsupported operating system")
                        
                        # Download and extract ChromeDriver
                        print(f"Downloading ChromeDriver from {driver_url}")
                        response = requests.get(driver_url)
                        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                            zip_file.extractall(".")
                        
                        # Make ChromeDriver executable
                        os.chmod(driver_path, 0o755)
                        
                        # Set up ChromeDriver
                        service = Service(executable_path=driver_path)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        
                    except Exception as e:
                        print(f"Direct download method failed: {str(e)}")
                        raise Exception("All ChromeDriver setup methods failed")
            
            # Test the driver
            print("Testing Chrome WebDriver...")
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            if "Google" in self.driver.title:
                print("Chrome WebDriver initialized and tested successfully!")
                self.driver.maximize_window()
            else:
                raise Exception("Chrome WebDriver test failed")
            
        except Exception as e:
            print(f"\nFailed to initialize Chrome WebDriver: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Make sure Chrome browser is installed and up to date")
            print("2. Try running: brew install --cask chromedriver")
            print("3. Or download ChromeDriver manually from: https://chromedriver.chromium.org/downloads")
            print("4. Make sure you have the correct ChromeDriver version for your Chrome browser")
            print("5. Try running: xattr -d com.apple.quarantine /path/to/chromedriver")
            raise Exception("Could not initialize Chrome WebDriver. Please follow the troubleshooting steps above.")

    def login(self):
        """Log in to LinkedIn using credentials with verification handling."""
        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(3)  # Increased wait time

            # Enter email with human-like typing
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            for char in self.email:
                email_field.send_keys(char)
                time.sleep(0.1)  # Simulate human typing
            time.sleep(1)

            # Enter password with human-like typing
            password_field = self.driver.find_element(By.ID, "password")
            for char in self.password:
                password_field.send_keys(char)
                time.sleep(0.1)  # Simulate human typing
            time.sleep(1)

            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            time.sleep(3)

            # Check for verification
            try:
                # Look for verification elements
                verification_elements = [
                    "//input[@id='input__phone_verification_pin']",  # Phone verification
                    "//input[@id='captcha-challenge']",  # Captcha
                    "//input[@id='pin']",  # PIN verification
                    "//div[contains(@class, 'challenge-dialog')]"  # General challenge dialog
                ]

                for element in verification_elements:
                    try:
                        if self.driver.find_element(By.XPATH, element).is_displayed():
                            print("\nVerification required! Please complete the verification manually.")
                            print("Waiting for 60 seconds for manual verification...")
                            
                            # Wait for manual verification
                            time.sleep(60)
                            break
                    except:
                        continue

            except:
                pass

            # Wait for login to complete
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "global-nav"))
                )
                print("Successfully logged in to LinkedIn!")
                return True
            except TimeoutException:
                print("Login timeout. Please check if you need to complete verification.")
                return False

        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    def scroll_page(self, scroll_pause_time=2):
        """Scroll the page to load more content."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            
            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Break if no more content
            if new_height == last_height:
                break
            last_height = new_height

    def search_company_employees(self, company_name, max_profiles=100):
        """Search for employees of a specific company using direct search."""
        try:
            # Direct search for employees
            print(f"\nSearching for employees at {company_name}...")
            search_url = f'https://www.linkedin.com/search/results/people/?keywords={company_name}&origin=GLOBAL_SEARCH_HEADER'
            self.driver.get(search_url)
            time.sleep(5)

            # Initialize list to store employee data
            employees_data = []
            profiles_processed = 0
            page = 1

            while profiles_processed < max_profiles:
                print(f"\nProcessing page {page}...")
                
                # Wait for results to load
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.pKsbWMnFecAMkbmRPTyNqWWHZRXnvc"))
                    )
                except TimeoutException:
                    print("No results found or page load timeout")
                    break

                # Scroll slowly to load all content
                self.scroll_page(scroll_pause_time=2)
                
                # Get all profile cards
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.pKsbWMnFecAMkbmRPTyNqWWHZRXnvc")
                
                if not profile_cards:
                    print("No profile cards found on this page")
                    break

                for card in profile_cards:
                    if profiles_processed >= max_profiles:
                        break

                    try:
                        # Wait for card to be fully loaded
                        WebDriverWait(card, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.JiqGGlfdRvGyLDagRgfieHwryrPZtObosBPKU"))
                        )

                        # Extract basic info
                        name_element = card.find_element(By.CSS_SELECTOR, "span.JiqGGlfdRvGyLDagRgfieHwryrPZtObosBPKU a")
                        name = name_element.text.strip()
                        profile_url = name_element.get_attribute("href")

                        # Extract title
                        try:
                            title = card.find_element(By.CSS_SELECTOR, "div.pxUtFAnNAlQUqKbhgaSFYXfZujHHeMMyHYkPM").text.strip()
                        except:
                            title = "Not available"

                        # Extract location
                        try:
                            location = card.find_element(By.CSS_SELECTOR, "div.dckMfiyJszFLylsZdQUdDdjNLVwdiBBmvz").text.strip()
                        except:
                            location = "Not available"

                        print(f"Found profile: {name} - {title}")

                        # Get detailed profile data
                        try:
                            # Open profile in new tab
                            self.driver.execute_script(f"window.open('{profile_url}', '_blank');")
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            time.sleep(3)

                            profile_data = self.get_profile_data(profile_url)
                            
                            employee_data = {
                                'name': name,
                                'title': title,
                                'location': location,
                                'profile_url': profile_url,
                                'headline': profile_data.get('headline', 'Not available'),
                                'about': profile_data.get('about', 'Not available'),
                                'experience': profile_data.get('experience', []),
                                'education': profile_data.get('education', [])
                            }
                            
                            employees_data.append(employee_data)
                            profiles_processed += 1
                            print(f"Successfully processed profile {profiles_processed}: {name}")

                            # Close tab and switch back
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                            time.sleep(1)

                        except Exception as e:
                            print(f"Error getting detailed profile data for {name}: {str(e)}")
                            # Make sure we're back on the main window
                            if len(self.driver.window_handles) > 1:
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                            continue

                    except Exception as e:
                        print(f"Error processing profile card: {str(e)}")
                        continue

                # Try to click "Next" button if available
                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-pagination__button--next"))
                    )
                    if "artdeco-button--disabled" in next_button.get_attribute("class"):
                        print("Reached last page")
                        break
                    next_button.click()
                    time.sleep(5)
                    page += 1
                except:
                    print("No more pages available")
                    break

            return employees_data

        except Exception as e:
            print(f"Error during company search: {str(e)}")
            return []

    def get_profile_data(self, profile_url):
        """Scrape detailed profile data from the given LinkedIn profile URL."""
        try:
            self.driver.get(profile_url)
            time.sleep(3)  # Wait for page to load

            # Initialize profile data dictionary
            profile_data = {
                'headline': '',
                'about': '',
                'experience': [],
                'education': []
            }

            # Get headline
            try:
                headline_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-body-medium"))
                )
                profile_data['headline'] = headline_element.text.strip()
            except:
                print("Could not find headline")

            # Get about section
            try:
                about_section = self.driver.find_element(By.CSS_SELECTOR, "div.display-flex.ph5.pv3")
                profile_data['about'] = about_section.text.strip()
            except:
                print("Could not find about section")

            # Get experience
            try:
                experience_section = self.driver.find_element(By.ID, "experience")
                experience_items = experience_section.find_elements(By.CSS_SELECTOR, "li.pv-entity__position-group-pager")
                
                for item in experience_items:
                    try:
                        title = item.find_element(By.CSS_SELECTOR, "h3.t-16.t-black.t-bold").text.strip()
                        company = item.find_element(By.CSS_SELECTOR, "p.pv-entity__secondary-title").text.strip()
                        duration = item.find_element(By.CSS_SELECTOR, "span.pv-entity__date-range").text.strip()
                        
                        profile_data['experience'].append({
                            'title': title,
                            'company': company,
                            'duration': duration
                        })
                    except:
                        continue
            except:
                print("Could not find experience section")

            # Get education
            try:
                education_section = self.driver.find_element(By.ID, "education")
                education_items = education_section.find_elements(By.CSS_SELECTOR, "li.pv-education-entity")
                
                for item in education_items:
                    try:
                        school = item.find_element(By.CSS_SELECTOR, "h3.pv-entity__school-name").text.strip()
                        degree = item.find_element(By.CSS_SELECTOR, "p.pv-entity__degree-name").text.strip()
                        field = item.find_element(By.CSS_SELECTOR, "p.pv-entity__fos").text.strip()
                        
                        profile_data['education'].append({
                            'school': school,
                            'degree': degree,
                            'field': field
                        })
                    except:
                        continue
            except:
                print("Could not find education section")

            return profile_data

        except Exception as e:
            print(f"Error scraping profile: {str(e)}")
            return {}

    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()

def main():
    scraper = LinkedInScraper()
    
    try:
        # Login to LinkedIn
        if scraper.login():
            # Get company name from user
            company_name = input("Enter the company name: ")
            max_profiles = int(input("Enter maximum number of profiles to scrape (default 100): ") or "100")
            
            print(f"\nSearching for employees at {company_name}...")
            employees = scraper.search_company_employees(company_name, max_profiles=max_profiles)
            
            if employees:
                # Create timestamp for filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{company_name}_employees_{timestamp}.json"
                
                # Save results to a JSON file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(employees, f, indent=2, ensure_ascii=False)
                print(f"\nResults saved to {filename}")
                
                # Print summary
                print(f"\nSummary:")
                print(f"Total profiles scraped: {len(employees)}")
                print(f"Company: {company_name}")
                print(f"Timestamp: {timestamp}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 