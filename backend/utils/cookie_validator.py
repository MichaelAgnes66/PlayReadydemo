import requests
from datetime import datetime
from typing import Dict, List, Tuple
from urllib.parse import urlparse

class CookieValidator:
    def __init__(self):
        self.session = requests.Session()
    
    def validate_cookies_for_website(self, website: str, cookies: List[Dict]) -> List[Tuple[int, bool]]:
        """
        Validate cookies by making a request to the website
        Returns list of (cookie_id, is_valid) tuples
        """
        results = []
        
        # Ensure website has proper protocol
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            # Create cookies dict for requests
            cookie_dict = {}
            cookie_map = {}  # Map cookie names to IDs
            
            for cookie in cookies:
                cookie_name = cookie.get('name', '')
                cookie_value = cookie.get('value', '')
                cookie_id = cookie.get('id')
                
                if cookie_name and cookie_value:
                    cookie_dict[cookie_name] = cookie_value
                    cookie_map[cookie_name] = cookie_id
            
            if not cookie_dict:
                return results
            
            # Make request with cookies
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(
                website,
                cookies=cookie_dict,
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            
            # Check response status
            is_valid = response.status_code in [200, 201, 202, 301, 302, 304]
            
            # Check if cookies were returned/accepted by the server
            response_cookies = response.cookies.get_dict()
            
            for cookie_name, cookie_id in cookie_map.items():
                # Cookie is considered valid if:
                # 1. Request was successful
                # 2. Cookie wasn't rejected (still present in response or not explicitly removed)
                cookie_valid = is_valid and self._check_cookie_acceptance(
                    cookie_name, response, response_cookies
                )
                results.append((cookie_id, cookie_valid))
            
        except requests.exceptions.RequestException as e:
            print(f"Error validating cookies for {website}: {e}")
            # If there's an error, mark all cookies as potentially invalid
            for cookie in cookies:
                results.append((cookie.get('id'), False))
        
        return results
    
    def _check_cookie_acceptance(self, cookie_name: str, response: requests.Response, response_cookies: Dict) -> bool:
        """
        Check if a cookie was accepted by the server
        """
        # If the cookie is returned in the response, it was accepted
        if cookie_name in response_cookies:
            return True
        
        # Check if the response contains any authentication errors or login redirects
        response_text = response.text.lower()
        
        # Common indicators that cookies might be invalid
        invalid_indicators = [
            'login',
            'sign in',
            'authentication required',
            'session expired',
            'unauthorized',
            'access denied'
        ]
        
        # If we find too many invalid indicators, the cookie might be invalid
        invalid_count = sum(1 for indicator in invalid_indicators if indicator in response_text)
        
        # Simple heuristic: if we find multiple invalid indicators, cookie might be invalid
        return invalid_count < 2
    
    def parse_cookies_from_header(self, cookie_header: str) -> List[Dict]:
        """
        Parse cookies from a raw cookie header string
        Format: "name1=value1; name2=value2; name3=value3"
        """
        cookies = []
        
        if not cookie_header:
            return cookies
        
        cookie_pairs = cookie_header.split(';')
        
        for pair in cookie_pairs:
            pair = pair.strip()
            if '=' in pair:
                name, value = pair.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '',
                    'path': '/',
                    'expires': ''
                })
        
        return cookies
    
    def is_cookie_expired(self, expires_str: str) -> bool:
        """
        Check if a cookie has expired based on its expires string
        """
        if not expires_str:
            return False
        
        try:
            # Try parsing different date formats
            date_formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d-%b-%Y %H:%M:%S %Z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            for fmt in date_formats:
                try:
                    expires_date = datetime.strptime(expires_str, fmt)
                    return datetime.now() > expires_date
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False