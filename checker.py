#!/usr/bin/env python3

import os
import sys
import time
import random
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Literal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL = os.getenv('ZOHO_EMAIL')
PASSWORD = os.getenv('ZOHO_PASSWORD')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'

if not EMAIL or not PASSWORD:
    print("[-] ZOHO_EMAIL and ZOHO_PASSWORD not set")
    sys.exit(1)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)
    
    def send_message(
        self, 
        message: str, 
        status: Literal["success", "error", "info"] = "info"
    ):
        if not self.enabled:
            print("[!] Telegram notifications disabled (no credentials)")
            return False
        
        emoji_map = {
            "success": "✅",
            "error": "❌",
            "info": "ℹ️"
        }
        
        emoji = emoji_map.get(status, "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted_message = f"{emoji} *Check-In/Out Automation*\n\n{message}\n\n__{timestamp}__"
        
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": formatted_message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[+] Telegram notification sent")
                return True
            else:
                print(f"[-] Telegram error: {response.text}")
                return False
                
        except Exception as e:
            print(f"[-] Error sending Telegram: {e}")
            return False
    
    def send_checkin_success(self, time_str: str):
        message = f"*Check-In Successful* 🚀\n\nTime: {time_str}"
        self.send_message(message, "success")
    
    def send_checkout_success(self, time_str: str):
        message = f"*Check-Out Successful* 👋\n\nTime: {time_str}"
        self.send_message(message, "success")
    
    def send_error(self, action: str, error_message: str = None):
        msg = f"*{action} Failed* ⚠️\n\n"
        if error_message:
            msg += f"Details: `{error_message}`\n\n"
        msg += "Please check in manually!"
        self.send_message(msg, "error")


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
        
    def get_signin_page(self):
        print("[*] Getting initial sign-in page...")
        url = "https://accounts.zoho.com/signin"
        params = {
            'service_language': 'ar',
            'servicename': self.servicename,
            'signupurl': f'https://www.zoho.com/ar/people/signup.html?servicename={self.servicename}&service_language=ar'
        }
        
        try:
            response = self.session.get(url, params=params, allow_redirects=True, timeout=10)
            print(f"[+] Initial page status: {response.status_code}")
            return True
        except Exception as e:
            print(f"[-] Error getting sign-in page: {e}")
            return False
    
    def lookup_user(self):
        print(f"[*] Performing user lookup...")
        
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
        }
        
        try:
            response = self.session.post(url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                lookup_response = response.json()
                
                if 'lookup' in lookup_response:
                    self.identifier = lookup_response['lookup']['identifier']
                    self.digest = lookup_response['lookup']['digest']
                    print(f"[+] User lookup successful")
                    return True
            
            print(f"[-] Lookup failed: {response.status_code}")
            return False
                
        except Exception as e:
            print(f"[-] Error during lookup: {e}")
            return False
    
    def signin(self):
        print("[*] Performing sign-in...")
        
        if not hasattr(self, 'identifier') or not hasattr(self, 'digest'):
            print("[-] Missing identifier or digest")
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
        }

        print(f"[DEBUG] URL: {url}")
        print(f"[DEBUG] Params: {params}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Body: {json.dumps(password_data)}")
        print(f"[DEBUG] Identifier: {self.identifier}")
        print(f"[DEBUG] Digest: {self.digest[:50]}...")
        
        try:
            response = self.session.post(
                url,
                params=params,
                data=json.dumps(password_data),
                headers=headers,
                timeout=10
            )

            print(f"[DEBUG] Response Status: {response.status_code}")
            print(f"[DEBUG] Response Headers: {dict(response.headers)}")
            print(f"[DEBUG] Response Body: {response.text}")
            
            if response.status_code == 200:
                try:
                    signin_response = response.json()
                    print(f"[DEBUG] JSON Response: {json.dumps(signin_response, indent=2)}")
                    
                    if signin_response.get('code') == 'SI200':
                        print("[+] Sign-in successful")
                        return True
                    else:
                        print(f"[-] Sign-in code was: {signin_response.get('code')}")
                        print(f"[-] Full response: {signin_response}")
                        return False
                except json.JSONDecodeError as e:
                    print(f"[-] Failed to parse JSON response: {e}")
                    print(f"[-] Raw response: {response.text}")
                    return False
            
            print(f"[-] Sign-in failed with status {response.status_code}")
            return False
                
        except Exception as e:
            print(f"[-] Error during sign-in: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_csrf_token_from_people(self):
        print("[*] Fetching CSRF token...")
        
        try:
            response = self.session.get(
                "https://people.zoho.com/hrportal1524040394558/zp",
                timeout=10
            )
            
            if 'CSRF_TOKEN' in self.session.cookies:
                self.csrf_token = self.session.cookies.get('CSRF_TOKEN')
                print(f"[+] CSRF token obtained")
                return True
            elif 'CT_CSRF_TOKEN' in self.session.cookies:
                self.csrf_token = self.session.cookies.get('CT_CSRF_TOKEN')
                print(f"[+] CSRF token obtained")
                return True
            
            print("[-] Could not extract CSRF token")
            return False
                
        except Exception as e:
            print(f"[-] Error getting CSRF token: {e}")
            return False
    
    def punch_in(self):
        print("[*] Performing check-in...")
        
        if not self.csrf_token:
            print("[-] CSRF token not available")
            return False
        
        url = "https://people.zoho.com/hrportal1524040394558/AttendanceAction.zp"
        params = {'mode': 'punchIn'}
        
        files = {
            'conreqcsr': (None, self.csrf_token),
            'urlMode': (None, 'myspace')
        }
        
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        try:
            response = self.session.post(url, params=params, files=files, headers=headers, timeout=10)
            
            if response.status_code == 200:
                punch_response = response.json()
                if 'msg' in punch_response:
                    print(f"[+] Check-in successful")
                    return True
            
            print(f"[-] Check-in failed: {response.status_code}")
            return False
                
        except Exception as e:
            print(f"[-] Error during check-in: {e}")
            return False
    
    def punch_out(self):
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
        }
        
        try:
            response = self.session.post(url, params=params, files=files, headers=headers, timeout=10)
            
            if response.status_code == 200:
                punch_response = response.json()
                if 'punchOut' in punch_response:
                    print(f"[+] Check-out successful")
                    return True
            
            print(f"[-] Check-out failed: {response.status_code}")
            return False
                
        except Exception as e:
            print(f"[-] Error during check-out: {e}")
            return False
    
    def automate_signin(self):
        if not self.get_signin_page():
            return False
        if not self.lookup_user():
            return False
        if not self.signin():
            return False
        if not self.get_csrf_token_from_people():
            return False
        
        print("[+] Sign-in process completed")
        return True


def apply_jitter(max_jitter_minutes: int = 5) -> int:
    """Apply random jitter in seconds"""
    jitter_seconds = random.randint(-max_jitter_minutes * 60, max_jitter_minutes * 60)
    print(f"[*] Jitter applied: {jitter_seconds//60:+d}m {jitter_seconds%60:+d}s")
    return jitter_seconds


def main():
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    print("="*60)
    print(f"[*] Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Apply jitter
    #jitter = apply_jitter(max_jitter_minutes=5)
    #if jitter != 0:
        #print(f"[*] Waiting {abs(jitter)} seconds for jitter...")
        #time.sleep(abs(jitter))
    
    automation = ZohoPeopleAutomation(EMAIL, PASSWORD)
    
    try:
        if not automation.automate_signin():
            notifier.send_error("Sign-In", "Failed to authenticate with Zoho")
            sys.exit(1)
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Determine if this is check-in or check-out based on time
        hour = datetime.now().hour
        
        if 21 <= hour < 23:  # Between 9 PM and 11 PM (check-in window)
            if automation.punch_in():
                notifier.send_checkin_success(current_time)
                print("[+] All done!")
            else:
                notifier.send_error("Check-In")
                sys.exit(1)
        
        elif 17 <= hour < 19:  # Between 5 PM and 7 PM (check-out window)
            if automation.punch_out():
                notifier.send_checkout_success(current_time)
                print("[+] All done!")
            else:
                notifier.send_error("Check-Out")
                sys.exit(1)
        
        else:
            print("[!] Current time is outside check-in/check-out windows")
            notifier.send_message("⚠️ Executed outside scheduled time window", "info")
    
    except Exception as e:
        print(f"[-] Unexpected error: {e}")
        notifier.send_error("Automation", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
