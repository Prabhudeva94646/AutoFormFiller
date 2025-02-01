from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import socket
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

# Add CORS headers to allow connections
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

class GoogleFormAutomation:
    def __init__(self, form_url):
        self.form_url = form_url
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Initialize the webdriver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')  # Run in headless mode for server environment
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def select_checkbox(self, group="Group 3"):
        try:
            checkbox = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@role='list']//div[@role='listitem'][3]//div[@role='checkbox']"
                ))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
            self.driver.implicitly_wait(1)
            self.driver.execute_script("arguments[0].click();", checkbox)
            return True
        except Exception as e:
            print(f"Checkbox selection failed: {str(e)}")
            return False
    
    def fill_form(self, name, email, roll_no, group="Group 3"):
        try:
            self.setup_driver()
            self.driver.get(self.form_url)
            
            text_boxes = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            if len(text_boxes) < 3:
                raise ValueError(f"Expected 3 text inputs, found {len(text_boxes)}")
            
            input_data = [(0, name), (1, email), (2, roll_no)]
            for index, value in input_data:
                text_box = text_boxes[index]
                self.wait.until(EC.element_to_be_clickable(text_box))
                text_box.clear()
                text_box.send_keys(value)
            
            if not self.select_checkbox(group):
                return False
            
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Submit']"))
            )
            submit_button.click()
            
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Your response has been recorded')]"))
                )
                return True
            except TimeoutException:
                print("Warning: Couldn't verify form submission confirmation")
                return True
            
        except Exception as e:
            print(f"Form submission error: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

# Create simple HTML pages
@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Form Automation</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 20px auto;
                    padding: 0 20px;
                }
                .button {
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                    width: 100%;
                }
                .status {
                    margin-top: 20px;
                    padding: 10px;
                    border-radius: 4px;
                }
                .success { background-color: #dff0d8; }
                .error { background-color: #f2dede; }
            </style>
        </head>
        <body>
            <h1>Form Automation</h1>
            <button class="button" onclick="submitForm()">Submit Form</button>
            <div id="status" class="status"></div>
            
            <script>
                function submitForm() {
                    document.getElementById('status').innerHTML = 'Submitting form...';
                    document.getElementById('status').className = 'status';
                    
                    fetch('/submit')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').innerHTML = data.message;
                            document.getElementById('status').className = 
                                'status ' + (data.success ? 'success' : 'error');
                        })
                        .catch(error => {
                            document.getElementById('status').innerHTML = 
                                'Error: ' + error.message;
                            document.getElementById('status').className = 'status error';
                        });
                }
            </script>
        </body>
    </html>
    '''

@app.route('/submit')
def submit_form():
    # Replace with your actual form URL and data
    form_url = "https://forms.gle/N1cV6vfekbQphKyC9"
    form_data = {
        "name": "Prabhdeep Singh",
        "email": "psingh_mca24@thapar.edu",
        "roll_no": "2024010078",
        "group": "Group 3"
    }
    
    automation = GoogleFormAutomation(form_url)
    success = automation.fill_form(
        name=form_data["name"],
        email=form_data["email"],
        roll_no=form_data["roll_no"],
        group=form_data["group"]
    )
    
    return jsonify({
        'success': success,
        'message': 'Form submitted successfully!' if success else 'Form submission failed!'
    })
# Function to find an available port
def find_available_port(start_port=8080, max_port=8100):
    """Try to find an available port starting from start_port"""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find an available port between {start_port} and {max_port}")

if __name__ == '__main__':
    try:
        port = 8081
        print(f"\nStarting server on port {port}")
        print(f"Access the application at:")
        print(f"    Local:            http://localhost:{port}")
        
        # Get all available IPs
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        for ip in ips:
            print(f"    On Your Network:  http://{ip}:{port}")
        
        print("\nTroubleshooting tips if you can't connect:")
        print("1. Make sure your phone and computer are on the same WiFi network")
        print("2. Check your computer's firewall settings")
        print("3. Try accessing the local URL first to ensure the server is running")
        
        # Use gevent WSGIServer
        http_server = WSGIServer(('0.0.0.0', port), app)
        print("\nServer started successfully! Press Ctrl+C to stop.")
        http_server.serve_forever()
        
    except Exception as e:
        print(f"Error starting server: {e}")