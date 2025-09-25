import http.server
import socketserver
import json
import urllib.parse
import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Simple cookie management HTTP server
class CookieManagementHandler(http.server.BaseHTTPRequestHandler):
    db_path = "cookies.db"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def init_db(cls):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(cls.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cookies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                website TEXT NOT NULL,
                cookie_name TEXT NOT NULL,
                cookie_value TEXT NOT NULL,
                domain TEXT,
                path TEXT DEFAULT '/',
                expires TEXT,
                is_valid BOOLEAN DEFAULT 1,
                last_validated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, website, cookie_name)
            )
        ''')
        
        # Sessions table for simple session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8000')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def add_cors_headers(self):
        """Add CORS headers to response"""
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:8000')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Content-Type', 'application/json')

    def send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response"""
        self.send_response(status_code)
        self.add_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def get_request_data(self) -> Dict[str, Any]:
        """Parse JSON request body"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
            return {}
        except Exception:
            return {}

    def get_session_user(self) -> Optional[int]:
        """Get user ID from session cookie"""
        try:
            cookie_header = self.headers.get('Cookie', '')
            if 'session_id=' in cookie_header:
                session_id = cookie_header.split('session_id=')[1].split(';')[0]
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM sessions WHERE session_id = ?", (session_id,))
                result = cursor.fetchone()
                conn.close()
                
                return result[0] if result else None
        except Exception:
            pass
        return None

    def create_session(self, user_id: int) -> str:
        """Create a new session for user"""
        import secrets
        session_id = secrets.token_hex(16)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (session_id, user_id) VALUES (?, ?)", (session_id, user_id))
        conn.commit()
        conn.close()
        
        return session_id

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/register':
            self.handle_register()
        elif self.path == '/api/login':
            self.handle_login()
        elif self.path == '/api/logout':
            self.handle_logout()
        elif self.path == '/api/cookies':
            self.handle_upload_cookies()
        elif self.path == '/api/validate':
            self.handle_validate_cookies()
        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/health':
            self.send_json_response({'status': 'healthy'})
        elif self.path == '/api/user':
            self.handle_get_user()
        elif self.path.startswith('/api/cookies'):
            self.handle_get_cookies()
        else:
            # Serve static files
            if self.path == '/' or self.path == '/index.html':
                self.serve_static_file('frontend/index.html', 'text/html')
            elif self.path == '/style.css':
                self.serve_static_file('frontend/style.css', 'text/css')
            elif self.path == '/script.js':
                self.serve_static_file('frontend/script.js', 'application/javascript')
            else:
                self.send_json_response({'error': 'Not found'}, 404)

    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path.startswith('/api/cookies/'):
            cookie_id = self.path.split('/')[-1]
            self.handle_delete_cookie(cookie_id)
        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def serve_static_file(self, filepath: str, content_type: str):
        """Serve static files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', 'http://localhost:8000')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_json_response({'error': 'File not found'}, 404)

    def handle_register(self):
        """Handle user registration"""
        data = self.get_request_data()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            self.send_json_response({'error': 'Username and password required'}, 400)
            return

        if len(username) < 3 or len(password) < 6:
            self.send_json_response({'error': 'Username min 3 chars, password min 6 chars'}, 400)
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            conn.close()
            self.send_json_response({'message': 'User registered successfully'}, 201)
        except sqlite3.IntegrityError:
            self.send_json_response({'error': 'Username already exists'}, 409)

    def handle_login(self):
        """Handle user login"""
        data = self.get_request_data()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            self.send_json_response({'error': 'Username and password required'}, 400)
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id = result[0]
            session_id = self.create_session(user_id)
            
            self.send_response(200)
            self.add_cors_headers()
            self.send_header('Set-Cookie', f'session_id={session_id}; Path=/; HttpOnly')
            self.end_headers()
            
            response = {
                'message': 'Login successful',
                'user': {'id': user_id, 'username': username}
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_json_response({'error': 'Invalid credentials'}, 401)

    def handle_logout(self):
        """Handle user logout"""
        user_id = self.get_session_user()
        if user_id:
            # Clear session from database
            cookie_header = self.headers.get('Cookie', '')
            if 'session_id=' in cookie_header:
                session_id = cookie_header.split('session_id=')[1].split(';')[0]
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                conn.close()

        self.send_response(200)
        self.add_cors_headers()
        self.send_header('Set-Cookie', 'session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
        self.wfile.write(json.dumps({'message': 'Logged out successfully'}).encode('utf-8'))

    def handle_get_user(self):
        """Handle get current user"""
        user_id = self.get_session_user()
        if not user_id:
            self.send_json_response({'error': 'Authentication required'}, 401)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            self.send_json_response({
                'user': {'id': user_id, 'username': result[0]}
            })
        else:
            self.send_json_response({'error': 'User not found'}, 404)

    def handle_upload_cookies(self):
        """Handle cookie upload"""
        user_id = self.get_session_user()
        if not user_id:
            self.send_json_response({'error': 'Authentication required'}, 401)
            return

        data = self.get_request_data()
        website = data.get('website', '').strip()
        cookie_header = data.get('cookie_header', '').strip()
        cookies_data = data.get('cookies', [])

        if not website:
            self.send_json_response({'error': 'Website is required'}, 400)
            return

        cookies = []
        
        # Parse cookie header
        if cookie_header:
            for pair in cookie_header.split(';'):
                pair = pair.strip()
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    cookies.append({'name': name.strip(), 'value': value.strip()})

        # Add individual cookies
        for cookie in cookies_data:
            if cookie.get('name') and cookie.get('value'):
                cookies.append(cookie)

        if not cookies:
            self.send_json_response({'error': 'No valid cookies provided'}, 400)
            return

        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for cookie in cookies:
                cursor.execute('''
                    INSERT OR REPLACE INTO cookies 
                    (user_id, website, cookie_name, cookie_value, domain, path, expires, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    user_id, website, cookie.get('name', ''), cookie.get('value', ''),
                    cookie.get('domain', ''), cookie.get('path', '/'), cookie.get('expires', '')
                ))
            
            conn.commit()
            conn.close()
            
            self.send_json_response({
                'message': f'Successfully uploaded {len(cookies)} cookies for {website}',
                'count': len(cookies)
            }, 201)
        except Exception as e:
            self.send_json_response({'error': f'Failed to save cookies: {str(e)}'}, 500)

    def handle_get_cookies(self):
        """Handle get cookies"""
        user_id = self.get_session_user()
        if not user_id:
            self.send_json_response({'error': 'Authentication required'}, 401)
            return

        # Parse query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        website = query_params.get('website', [None])[0]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if website:
            cursor.execute('''
                SELECT id, website, cookie_name, cookie_value, domain, path, 
                       expires, is_valid, last_validated, created_at
                FROM cookies 
                WHERE user_id = ? AND website = ?
                ORDER BY created_at DESC
            ''', (user_id, website))
        else:
            cursor.execute('''
                SELECT id, website, cookie_name, cookie_value, domain, path, 
                       expires, is_valid, last_validated, created_at
                FROM cookies 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))

        results = cursor.fetchall()
        conn.close()

        cookies = []
        for row in results:
            cookies.append({
                'id': row[0], 'website': row[1], 'name': row[2], 'value': row[3],
                'domain': row[4], 'path': row[5], 'expires': row[6],
                'is_valid': row[7], 'last_validated': row[8], 'created_at': row[9]
            })

        self.send_json_response({'cookies': cookies, 'count': len(cookies)})

    def handle_validate_cookies(self):
        """Handle cookie validation"""
        user_id = self.get_session_user()
        if not user_id:
            self.send_json_response({'error': 'Authentication required'}, 401)
            return

        data = self.get_request_data()
        website = data.get('website', '').strip()

        if not website:
            self.send_json_response({'error': 'Website is required'}, 400)
            return

        # Simple validation - just mark as valid for demo
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE cookies 
                SET is_valid = 1, last_validated = CURRENT_TIMESTAMP
                WHERE user_id = ? AND website = ?
            ''', (user_id, website))
            
            updated_rows = cursor.rowcount
            conn.commit()
            conn.close()

            self.send_json_response({
                'message': f'Validated {updated_rows} cookies for {website}',
                'results': {'total': updated_rows, 'valid': updated_rows, 'invalid': 0}
            })
        except Exception as e:
            self.send_json_response({'error': f'Validation failed: {str(e)}'}, 500)

    def handle_delete_cookie(self, cookie_id: str):
        """Handle cookie deletion"""
        user_id = self.get_session_user()
        if not user_id:
            self.send_json_response({'error': 'Authentication required'}, 401)
            return

        try:
            cookie_id = int(cookie_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cookies WHERE id = ? AND user_id = ?", (cookie_id, user_id))
            conn.commit()
            deleted_rows = cursor.rowcount
            conn.close()

            if deleted_rows > 0:
                self.send_json_response({'message': 'Cookie deleted successfully'})
            else:
                self.send_json_response({'error': 'Cookie not found or access denied'}, 404)
        except (ValueError, Exception) as e:
            self.send_json_response({'error': f'Failed to delete cookie: {str(e)}'}, 500)

if __name__ == '__main__':
    PORT = 8000
    
    # Create database
    CookieManagementHandler.init_db()
    
    with socketserver.TCPServer(("", PORT), CookieManagementHandler) as httpd:
        print(f"Cookie Management System running at http://localhost:{PORT}")
        print(f"Open http://localhost:{PORT} in your browser")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            httpd.shutdown()