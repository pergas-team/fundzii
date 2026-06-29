import requests
import re
import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import json
import time


class LabsNetClient:
    def __init__(self):
        self.base_url = "https://labsnet.ir"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/lab_admin/service_request/",
        }

    def fetch_captcha(self, captcha_url):

        """Fetch and process the CAPTCHA image."""
        response = self.session.get(captcha_url)
        response.raise_for_status()

        # Load the CAPTCHA image
        captcha_image = Image.open(BytesIO(response.content)).convert("L")
        captcha_array = np.array(captcha_image)

        # Preprocess the CAPTCHA for recognition
        _, binary_image = cv2.threshold(captcha_array, 128, 255, cv2.THRESH_BINARY_INV)
        return binary_image

    def solve_captcha(self, captcha_binary, characters_dir="Characters"):
        """Solve the CAPTCHA by matching against predefined character images."""
        # Load predefined character images
        character_images = {}
        for filename in os.listdir(characters_dir):
            if filename.lower().endswith(('.png', '.jpg', '.bmp')):
                char = os.path.splitext(filename)[0]
                img = cv2.imread(os.path.join(characters_dir, filename), cv2.IMREAD_GRAYSCALE)
                _, char_binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV)
                character_images[char] = char_binary

        # Match characters in the CAPTCHA
        captcha_text = ""
        for i in range(0, captcha_binary.shape[1], 20):  # Adjust sliding window width as needed
            region = captcha_binary[:, i:i + 20]
            best_match = None
            best_score = 0

            for char, char_img in character_images.items():
                result = cv2.matchTemplate(region, char_img, cv2.TM_CCOEFF_NORMED)
                _, score, _, _ = cv2.minMaxLoc(result)
                if score > best_score:
                    best_score = score
                    best_match = char

            if best_match:
                captcha_text += best_match
        return captcha_text

    def login(self, username, password):
        """Log in to the LabsNet system."""
        self.username = username
        self.password = password

        get_login_url = f"https://login.labsnet.ir"
        post_login_url = f"https://account.labsnet.ir/index.php?ctrl=index&actn=login"

        if (self.ensure_dashboard_access()):
            return True
        response = self.session.get(get_login_url, headers=self.headers)
        response.raise_for_status()

        # Extract hidden fields
        csrf_token_match = re.search(r'name="_token" value="([^"]+)"', response.text)
        callback_s_match = re.search(r'name="callback_s" value="([^"]+)"', response.text)
        callback_e_match = re.search(r'name="callback_e" value="([^"]+)"', response.text)

        csrf_token = csrf_token_match.group(1) if csrf_token_match else None
        callback_s = callback_s_match.group(1) if callback_s_match else None
        callback_e = callback_e_match.group(1) if callback_e_match else None

        # Use regex to extract the CAPTCHA URL (if present)
        captcha_match = re.search(r'<img src="([^"]*captcha[^"]*)"', response.text)
        if captcha_match:
            captcha_url = captcha_match.group(1)
            captcha_url = f"https://account.labsnet.ir" + captcha_url
            print("Extracted CAPTCHA URL:", captcha_url)
        else:
            print("No CAPTCHA URL found.")

        captcha_text = None
        if captcha_match:
            print("CAPTCHA required. Solving...")
            captcha_binary = self.fetch_captcha(captcha_url)
            captcha_text = self.solve_captcha(captcha_binary)
            print("CAPTCHA solved:", captcha_text)
        else:
            captcha_text = None
            print("No CAPTCHA required: ", captcha_match)

        # Prepare login payload
        login_payload = {
            "_token": csrf_token,
            "login_type": "lab",
            "username": username,
            "password": password,
        }

        # Include optional fields only if present
        if callback_s:
            login_payload["callback_s"] = callback_s
        if callback_e:
            login_payload["callback_e"] = callback_e
        if captcha_text:
            login_payload["captcha_code"] = captcha_text

        try:
            login_response = self.session.post(post_login_url, headers=self.headers, data=login_payload)
            login_response.raise_for_status()
            if login_response.status_code == 200 and "dashboard" in login_response.text:
                print("✅ Login successful.")
                return True
            else:
                print("⚠️ Login failed.")
                return False
        except Exception as e:
            print(f"❌ Login Exception: {e}")
            return False

        # Perform login

        self.session.cookies.update(login_response.cookies)
        return self.ensure_login(login_response)

    def safe_post(self, url, data, retries=3):
        for attempt in range(retries):
            try:
                response = self.session.post(url, data=data, headers=self.headers,
                                             cookies=self.session.cookies.get_dict(), timeout=30)
                response.raise_for_status()
                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                print(f"❗ Request error on attempt {attempt + 1}: {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(2)
                # Try re-login if session seems broken
                if self.username and self.password:
                    self.login(self.username, self.password)

    def ensure_login(self, login_response):
        # Check login response
        username_error_pattern = r"نام کاربری یا رمز عبور وارد شده صحیح نیست"
        captcha_error_pattern = r"عبارت امنیتی وارد شده صحیح نیست!"

        if login_response.status_code in [200, 302] and 'PHPSESSID' in self.session.cookies:
            response_text = login_response.text.strip()
            # print(response_text)

            # Handle known login errors
            if re.search(r"عبارت\s*امنیتی\s*اجباریست", response_text):
                print("Login failed: CAPTCHA required.")
                return False
            elif re.search(username_error_pattern, response_text):
                print("Login failed: Incorrect username or password.")
                return False
            elif re.search(captcha_error_pattern, response_text):
                print("Login failed: Incorrect captcha.")
                return False
            else:
                print("Login successful.")
                return True
        else:
            print(f"Login failed. Status code: {login_response.status_code}")
            return False

    def ensure_dashboard_access(self):
        """Ensure the session is active by checking dashboard data."""

        response = self.session.get(f"{self.base_url}/dashboard", headers=self.headers)
        print(response.url)
        if "login" in response.url or "my.labsnet" in response.url:  # Redirected to login page
            print("Login Required.")
            return False
        elif response.status_code == 200:
            print("Status code is 200.")
            if re.search(r"ایوبی", response.text):
                print("Authenticated dashboard content found.")
                return True
            else:
                print("Authenticated dashboard content not found.")
                return False
        else:
            print(f"Dashboard access failed with status code {response.status_code}.")
            return False

    def submit_with_credit_request(self, payload, national_id, srv_id):
        """Submit a service request."""

        request_url = f"https://labsnet.ir/lab_admin/service_request"

        # Fetch the page to retrieve a new _token
        response = self.session.get(request_url, headers=self.headers)
        response.raise_for_status()

        # Extract _token
        csrf_token_match = re.search(r"window\._token\s*=\s*'([^']+)'", response.text)
        csrf_token = csrf_token_match.group(1) if csrf_token_match else None
        if not csrf_token:
            print("❌ CSRF Token not found.")
            return None
        print(f"🔑 CSRF Token: {csrf_token}")

        print(self.session.cookies.get_dict())

        # Build a new list of tuples for the form-data
        payload_items = list(payload) if isinstance(payload, list) else list(payload.items())

        # Add the _token
        payload_items.append(('_token', csrf_token))

        # Get customer and center IDs
        name, family, national_code_id, center_id = self.get_customer_and_center_ids(self.session, national_id,
                                                                                     csrf_token)

        payload_items.append(('name', name))
        payload_items.append(('family', family))
        payload_items.append(('national_code_id', national_code_id))
        payload_items.append(('center_id', center_id))

        # Get inst_srv_id
        inst_srv_id = self.get_inst_srv_id(self.session, srv_id, csrf_token)
        if inst_srv_id:
            print(f"Successfully retrieved inst_srv_id: {inst_srv_id}")
        else:
            print("Failed to retrieve inst_srv_id.")
        payload_items.append(('inst_srv_id', inst_srv_id))

        # Step 3: POST the final payload
        print(f"🚀 Sending payload with {len(payload_items)} fields...")
        print(f"Final payload ready to be sent:\n{payload_items}\n")  # <<< Important: passing list of tuples now
        response = self.safe_post(request_url, data=payload_items)
        print(f"✅ Response Code: {response.status_code}")

        if response.status_code == 200:
            match = re.search(r"content\s*:\s*'([^']+ثبت شد[^']+)'", response.text)
            if match:
                print("Submission confirmed:", match.group(1))
                conf_num = re.search(r"\d+", match.group(1))
                return conf_num.group() if conf_num else None
            else:
                print("Submission may have failed.")
                # print(response.text)
                return None
        else:
            print("POST request failed with status code:", response.status_code)
            return None

    def get_customer_and_center_ids(self, session, national_id, _token):
        # URL to which the request will be sent
        id_url = "https://labsnet.ir/index.php?ctrl=lab_admin&actn=search_with_customer_ID"

        # Payload as a dictionary (the body of your POST request)
        id_payload = {
            "type": 1,
            "title": national_id,
            "_token": _token
        }

        try:
            # Send a POST request (adjust method/type as needed)
            print("→ labsnet payload:", id_payload)
            response = session.post(id_url, data=id_payload)

            print("← labsnet response code:", response.status_code)
            print("← labsnet response body:", response.text)

            # Raise an exception if the status code is not 200
            response.raise_for_status()

            # Convert the JSON response to a Python dictionary
            data = response.json()

            if not isinstance(data, dict):
                print("Expected JSON dict but got something else.")
                print("Response text:", response.text)
                return None, None

            if "d" not in data:
                print("'d' key not found in response JSON.")
                return (None, None)

            # Extract customer_id and center_id from the JSON
            name = data["d"]["name"]
            family = data["d"]["family"]
            customer_id = data["d"]["id"]  # For example: "2457678"
            center_id = data["d"]["center_id"]  # For example: "105"
            print("name:", name, "family:", family, "Center ID:", center_id, "Customer ID:", customer_id)
            return name, family, customer_id, center_id

        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Parsing Error: {e}")

    def get_inst_srv_id(self, session, srv_id, _token):
        """
        Sends a POST request to the given URL with the given payload
        and returns the 'inst_srv_id' from the JSON response if available.
        """
        inst_srv_url = "https://labsnet.ir//index.php?ctrl=lab_admin&actn=inst_srv_auto_complete"
        # Replace with the actual form fields you need to send.
        # For example, if the server expects a field named 'input_value' or something similar:
        payload = {
            # Adjust key-value pairs as needed for your request
            "lab_id": 343,
            "title": srv_id,
            "_token": _token
        }

        try:
            response = session.post(inst_srv_url, data=payload)
            response.raise_for_status()  # Raise an error if status code != 200

            # For debugging, you can print the raw response:
            # print("Raw response text:", response.text)

            data = response.json()

            # Check if the "d" key exists and is a list
            if "d" not in data or not isinstance(data["d"], list):
                print("Error: 'd' key not found or is not a list.")
                return None

            # Ensure that the list is not empty
            if not data["d"]:
                print("Error: 'd' list is empty.")
                return None

            # The first element in "d"
            first_item = data["d"][0]

            # The "id" field holds the service ID in the form "3719-3840-2678"
            inst_srv_id = first_item.get("id")

            if not inst_srv_id:
                print("Error: 'id' field not found in the first element of 'd'.")
                return '0-41402-650'
                # return None

            print("inst_srv_id:", inst_srv_id)
            return inst_srv_id if inst_srv_id else '0-41402-650'

        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print("Raw response was:", response.text)
            return None
        except KeyError as e:
            print(f"Key Error: {e}")
            return None