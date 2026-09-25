import os
import requests
import json
import time
import random
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL = os.getenv('ZOHO_EMAIL')
PASSWORD = os.getenv('ZOHO_PASSWORD')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'


class ZohoPeopleAutomation:
    def __init__(self, email, password, servicename="zohopeople"):
        self.email = email
        self.password = password
        self.servicename = servicename
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
        })
        self.csrf_token = None
        self.cookies = None
        
    def get_signin_page(self):
        """Get the initial sign-in page to collect cookies and initial CSRF tokens"""
        print("[*] Getting initial sign-in page...")
        url = "https://accounts.zoho.com/signin"
        params = {
            'service_language': 'ar',
            'servicename': self.servicename,
            'signupurl': f'https://www.zoho.com/ar/people/signup.html?servicename={self.servicename}&service_language=ar'
        }
        
        try:
            response = self.session.get(url, params=params, allow_redirects=True)
            print(f"[+] Initial page status: {response.status_code}")
            
            # Extract CSRF token from page if present
            if 'iamcsr' in response.text:
                # Try to extract from HTML or cookies
                if 'iamcsr' in self.session.cookies:
                    self.csrf_token = self.session.cookies.get('iamcsr')
                    print(f"[+] CSRF Token extracted: {self.csrf_token}")
            
            return True
        except Exception as e:
            print(f"[-] Error getting sign-in page: {e}")
            return False
    
    def lookup_user(self):
        """Perform the lookup request to get user identifier and digest"""
        print(f"[*] Performing user lookup for {self.email}...")
        
        url = f"https://accounts.zoho.com/signin/v2/lookup/{self.email}"
        
        cli_time = int(time.time() * 1000)
        
        data = {
            'mode': 'primary',
            'cli_time': cli_time,
            'servicename': self.servicename,
            'service_language': 'ar',
            'signupurl': f'https://www.zoho.com/ar/people/signup.html?servicename={self.servicename}&service_language=ar',
            'serviceurl': 'https://people.zoho.com/people'
        }
        
        headers = {
            'X-Zcsrf-Token': f'iamcsrcoo={self.session.cookies.get("iamcsr", "")}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://accounts.zoho.com/signin'
        }
        
        try:
            response = self.session.post(url, data=data, headers=headers)
            print(f"[+] Lookup status: {response.status_code}")
            
            if response.status_code == 200:
                lookup_response = response.json()
                print(f"[+] Lookup response: {json.dumps(lookup_response, indent=2)}")
                
                if 'lookup' in lookup_response:
                    self.identifier = lookup_response['lookup']['identifier']
                    self.digest = lookup_response['lookup']['digest']
                    print(f"[+] User identifier: {self.identifier}")
                    print(f"[+] Digest obtained")
                    return True
            else:
                print(f"[-] Lookup failed with status {response.status_code}")
                print(f"[-] Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[-] Error during lookup: {e}")
            return False
    
    def signin(self):
        """Perform the actual sign-in with password"""
        print("[*] Performing sign-in...")
        
        if not hasattr(self, 'identifier') or not hasattr(self, 'digest'):
            print("[-] Missing identifier or digest. Run lookup_user first.")
            return False
        
        cli_time = int(time.time() * 1000)
        
        url = f"https://accounts.zoho.com/signin/v2/primary/{self.identifier}/password"
        
        params = {
            'digest': self.digest,
            'cli_time': cli_time,
            'servicename': self.servicename,
            'service_language': 'ar',
            'signupurl': f'https://www.zoho.com/ar/people/signup.html?servicename={self.servicename}&service_language=ar',
            'serviceurl': 'https://people.zoho.com/people'
        }
        
        password_data = {
            'passwordauth': {
                'password': self.password
            }
        }
        
        headers = {
            'X-Zcsrf-Token': f'iamcsrcoo={self.session.cookies.get("iamcsr", "")}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://accounts.zoho.com/signin'
        }
        
        try:
            response = self.session.post(
                url,
                params=params,
                data=json.dumps(password_data),
                headers=headers
            )
            print(f"[+] Sign-in status: {response.status_code}")
            
            if response.status_code == 200:
                signin_response = response.json()
                print(f"[+] Sign-in response: {json.dumps(signin_response, indent=2)}")
                
                code = signin_response.get('code')

                if code == 'SI200':
                    print("[+] Sign-in successful!")
                    return True
                
                elif code == 'SI302':
                    redirect_uri = (
                        signin_response
                        .get('passwordauth', {})
                        .get('redirect_uri')
                    )
                
                    if not redirect_uri:
                        print("[-] SI302 received but no redirect URI was provided.")
                        return False
                
                    print("[*] Following Zoho announcement redirect...")
                    print(f"[*] Redirect URL: {redirect_uri}")
                
                    redirect_response = self.session.get(
                        redirect_uri,
                        allow_redirects=True
                    )
                
                    print(f"[+] Announcement status: {redirect_response.status_code}")
                    print(f"[+] Final URL: {redirect_response.url}")
                
                    if redirect_response.status_code == 200:
                        print("[+] Announcement redirect completed.")
                        return True
                
                    print("[-] Announcement redirect failed.")
                    return False
                
                else:
                    print(
                        f"[-] Sign-in failed: "
                        f"{signin_response.get('message')}"
                    )
                    return False
            else:
                print(f"[-] Sign-in failed with status {response.status_code}")
                print(f"[-] Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[-] Error during sign-in: {e}")
            return False
    
    def get_csrf_token_from_people(self):
        """Get the CSRF token from people.zoho.com"""
        print("[*] Getting CSRF token from people.zoho.com...")
        
        try:
            response = self.session.get("https://people.zoho.com/hrportal1524040394558/zp")
            print(f"[+] People page status: {response.status_code}")
            
            # Extract CSRF token from cookies or response
            if 'CSRF_TOKEN' in self.session.cookies:
                self.csrf_token = self.session.cookies.get('CSRF_TOKEN')
                print(f"[+] CSRF Token extracted: {self.csrf_token}")
                return True
            elif 'CT_CSRF_TOKEN' in self.session.cookies:
                self.csrf_token = self.session.cookies.get('CT_CSRF_TOKEN')
                print(f"[+] CSRF Token extracted: {self.csrf_token}")
                return True
            else:
                print("[-] Could not extract CSRF token")
                return False
                
        except Exception as e:
            print(f"[-] Error getting CSRF token: {e}")
            return False
    
    def punch_out(self):
        """Perform check-out"""
        print("[*] Performing check-out...")
        
        if not self.csrf_token:
            print("[-] CSRF token not available")
            return False
        
        url = "https://people.zoho.com/hrportal1524040394558/AttendanceAction.zp"
        params = {'mode': 'punchOut'}
        
        files = {
            'conreqcsr': (None, self.csrf_token),
            'urlMode': (None, 'myspace')
        }
        
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://people.zoho.com/hrportal1524040394558/zp'
        }
        
        try:
            response = self.session.post(url, params=params, files=files, headers=headers)
            print(f"[+] Check-out status: {response.status_code}")
            
            if response.status_code == 200:
                punch_response = response.json()
                print(f"[+] Check-out response: {json.dumps(punch_response, indent=2)}")
                
                if 'punchOut' in punch_response:
                    print(f"[+] Check-out successful")
                    return True
                else:
                    print("[-] Unexpected response format")
                    return False
            else:
                print(f"[-] Check-out failed with status {response.status_code}")
                print(f"[-] Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[-] Error during check-out: {e}")
            return False
    
    def automate_signin(self):
        """Complete sign-in flow"""
        if not self.get_signin_page():
            return False
        
        if not self.lookup_user():
            return False
        
        if not self.signin():
            return False
        
        if not self.get_csrf_token_from_people():
            return False
        
        print("[+] Sign-in process completed successfully!")
        return True


def send_telegram_notification(title, message, status):
    """Send notification via Telegram"""
    try:
        status_emoji = "✅" if status == "success" else "❌"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"{status_emoji} *{title}*\n\n{message}\n\n_Time: {timestamp}_"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"[-] Failed to send Telegram notification: {response.text}")
        else:
            print("[+] Telegram notification sent successfully")
    except Exception as e:
        print(f"[-] Error sending Telegram notification: {str(e)}")


def apply_jitter(max_jitter_minutes: int = 5) -> int:
    """Apply random jitter in seconds"""
    jitter_seconds = random.randint(-max_jitter_minutes * 60, max_jitter_minutes * 60)
    print(f"[*] Jitter applied: {jitter_seconds//60:+d}m {jitter_seconds%60:+d}s")
    return jitter_seconds

def main():
    """Main execution function"""
    try:
        if not EMAIL or not PASSWORD:
            raise ValueError("ZOHO_EMAIL and ZOHO_PASSWORD environment variables are required")

        # Apply jitter
        jitter = apply_jitter(max_jitter_minutes=5)
        if jitter != 0:
            print(f"[*] Waiting {abs(jitter)} seconds for jitter...")
            time.sleep(abs(jitter))
        
        automation = ZohoPeopleAutomation(EMAIL, PASSWORD)
        
        # Perform sign-in
        if automation.automate_signin():
            print("\n" + "="*50)
            print("Performing Check-Out")
            print("="*50)
            
            if automation.punch_out():
                message = "Successfully checked out"
                print(f"\n[+] {message}")
                send_telegram_notification("✅ Check-Out Successful", message, "success")
            else:
                message = "Check-out operation failed"
                print(f"\n[-] {message}")
                send_telegram_notification("❌ Check-Out Failed", message, "failure")
        else:
            message = "Sign-in failed. Cannot proceed with check-out."
            print(f"[-] {message}")
            send_telegram_notification("❌ Check-Out Failed", message, "failure")
    
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(f"[-] {error_message}")
        send_telegram_notification("❌ Check-Out Error", error_message, "failure")


if __name__ == "__main__":
    main()
